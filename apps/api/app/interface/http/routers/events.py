import base64
import json
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from app.deps import Deps
from app.settings import get_settings
from app.application.usecases.agent_usecase import AgentUseCase
from app.adapters.slack import send_slack_notification
from app.adapters.repositories.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

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
    settings = get_settings()
    upload_id = args[0] if args else "unknown"
    
    job_id = f"job-{task_name}"
    if task_name == "implement_issue":
        job_id = f"job-{task_name}-{args[1]}"
    elif task_name == "review_pull":
        job_id = f"job-{task_name}-{args[1]}"

    try:
        await usecase.repo.save_job(upload_id, job_id, {
            "id": job_id,
            "type": task_name,
            "status": "RUNNING",
            "issue_id": args[1] if task_name == "implement_issue" else None,
            "pr_number": args[1] if task_name == "review_pull" else None
        })
        
        func = getattr(usecase, func_name)
        await func(*args)
        
        await usecase.repo.update_job(upload_id, job_id, {
            "status": "COMPLETED"
        })
        
        if settings.slack_webhook_url:
            await send_slack_notification(
                settings.slack_webhook_url, 
                f"✅ Task `{task_name}` completed for Agent `{upload_id}`"
            )
    except Exception as e:
        logger.error(f"Event handler '{task_name}' failed: {e}", exc_info=True)
        import traceback
        error_details = {"error": str(e), "traceback": traceback.format_exc()}
        
        await usecase.repo.update_job(upload_id, job_id, {
            "status": "FAILED",
            "error_details": error_details
        })
        
        if task_name == "implement_issue" and len(args) > 1:
            issue_id = args[1]
            await usecase.repo.update_issue(upload_id, issue_id, {"status": "open"})
            await usecase.repo.update(upload_id, {"status": "PLANNING", "errorDetails": str(e), "failedJobId": job_id})
        else:
            await usecase.repo.update(upload_id, {"status": "ERROR", "errorDetails": str(e), "failedJobId": job_id})
        
        if settings.slack_webhook_url:
            await send_slack_notification(
                settings.slack_webhook_url, 
                f"❌ Task `{task_name}` failed for Agent `{upload_id}`\nError: {e}"
            )
@router.post("/events/pubsub")
async def handle_pubsub_event(
    req: PubSubPushRequest,
    db_session: Optional[AsyncSession] = Depends(get_db_session)
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
    tenant_id = payload.get("tenant_id")
    if not upload_id or not tenant_id:
        logger.warning(f"Received {event_type} event without upload_id or tenant_id")
        return {"status": "ignored", "reason": "missing upload_id or tenant_id"}

    logger.info(f"Handling Pub/Sub event: {event_type} for upload_id {upload_id}, tenant_id {tenant_id}")
    
    settings = get_settings()
    deps = Deps(settings, tenant_id, db_session)
    usecase = AgentUseCase(deps.agent_repo, deps.storage, deps.scm, deps.settings, deps)

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
    elif event_type == "deploy_preview":
        pr_number_str = payload.get("pr_number")
        if pr_number_str and pr_number_str.isdigit():
            await run_usecase_task(event_type, usecase, "deploy_preview", upload_id, int(pr_number_str))
    elif event_type == "deploy_production":
        await run_usecase_task(event_type, usecase, "deploy_production", upload_id)
    else:
        logger.warning(f"Unknown event_type: {event_type}")

    return {"status": "ok"}
