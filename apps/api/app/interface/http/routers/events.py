import base64
import json
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from app.deps import get_deps, Deps
from app.application.usecases.agent_usecase import AgentUseCase
from app.interface.http.routers.agents import get_agent_usecase

logger = logging.getLogger(__name__)
router = APIRouter()

class PubSubMessage(BaseModel):
    data: str
    attributes: Optional[Dict[str, str]] = None
    messageId: str

class PubSubPushRequest(BaseModel):
    message: PubSubMessage
    subscription: str

async def run_usecase_task(task_name: str, usecase: AgentUseCase, func_name: str, *args):
    try:
        func = getattr(usecase, func_name)
        await func(*args)
    except Exception as e:
        logger.error(f"Event handler '{task_name}' failed: {e}", exc_info=True)
        # Note: robust error handling / retry should go here

@router.post("/events/pubsub")
async def handle_pubsub_event(
    req: PubSubPushRequest, 
    usecase: AgentUseCase = Depends(get_agent_usecase)
):
    """
    Push endpoint for Google Cloud Pub/Sub.
    Expects event_type in message attributes.
    """
    try:
        data_decoded = base64.b64decode(req.message.data).decode("utf-8")
        payload = json.loads(data_decoded)
    except Exception as e:
        logger.error(f"Failed to decode Pub/Sub message: {e}")
        raise HTTPException(status_code=400, detail="Invalid message data")

    event_type = req.message.attributes.get("event_type") if req.message.attributes else None
    if not event_type:
        logger.warning("Received Pub/Sub message without event_type attribute")
        return {"status": "ignored", "reason": "no event_type"}
        
    upload_id = payload.get("upload_id")
    if not upload_id:
        logger.warning(f"Received {event_type} event without upload_id")
        return {"status": "ignored", "reason": "no upload_id"}

    logger.info(f"Handling Pub/Sub event: {event_type} for upload_id {upload_id}")

    # Await usecase synchronously to prevent Cloud Run CPU throttling
    if event_type == "analyze":
        await run_usecase_task(event_type, usecase, "analyze", upload_id)
    elif event_type == "register":
        await run_usecase_task(event_type, usecase, "register", upload_id)
    elif event_type == "plan_issues":
        await run_usecase_task(event_type, usecase, "plan_issues", upload_id)
    elif event_type == "implement_issue":
        issue_id = payload.get("issue_id")
        await run_usecase_task(event_type, usecase, "implement_issue", upload_id, issue_id)
    elif event_type == "review_pull":
        pr_number_str = payload.get("pr_number")
        if pr_number_str and pr_number_str.isdigit():
            await run_usecase_task(event_type, usecase, "review_pull", upload_id, int(pr_number_str))
    else:
        logger.warning(f"Unknown event_type: {event_type}")

    return {"status": "ok"}
