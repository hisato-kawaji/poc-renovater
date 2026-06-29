from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict
import logging
from app.deps import get_deps, Deps
from app.application.usecases.agent_usecase import AgentUseCase
from app.domain.models import NotFoundError, ConflictError

logger = logging.getLogger(__name__)
router = APIRouter()

class AnalyzeRequest(BaseModel):
    uploadId: str

def get_agent_usecase(deps: Deps = Depends(get_deps)) -> AgentUseCase:
    return AgentUseCase(deps.agent_repo, deps.storage, deps.scm, deps.settings, deps)

async def publish_event(deps: Deps, event_type: str, payload: Dict[str, str]):
    topic = deps.settings.pubsub_topic_tasks
    try:
        await deps.event_publisher.publish(topic, event_type, payload)
    except Exception as e:
        logger.error(f"Failed to publish {event_type} event: {e}")
        raise HTTPException(status_code=500, detail="Failed to publish event")

@router.post("/agents:analyze", status_code=status.HTTP_202_ACCEPTED)
async def analyze_agent(req: AnalyzeRequest, deps: Deps = Depends(get_deps), usecase: AgentUseCase = Depends(get_agent_usecase)):
    await publish_event(deps, "analyze", {"upload_id": req.uploadId})
    return {"message": "Analysis started in background", "uploadId": req.uploadId}

@router.get("/agents/{upload_id}")
async def get_agent(upload_id: str, usecase: AgentUseCase = Depends(get_agent_usecase)):
    try:
        return await usecase.get_agent(upload_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/agents/{upload_id}:register", status_code=status.HTTP_202_ACCEPTED)
async def register_agent(upload_id: str, deps: Deps = Depends(get_deps), usecase: AgentUseCase = Depends(get_agent_usecase)):
    try:
        await usecase.ensure_can_register(upload_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
        
    await publish_event(deps, "register", {"upload_id": upload_id})
    return {"message": "Registration started in background"}

@router.post("/agents/{upload_id}/issues:plan", status_code=status.HTTP_202_ACCEPTED)
async def plan_issues(upload_id: str, deps: Deps = Depends(get_deps), usecase: AgentUseCase = Depends(get_agent_usecase)):
    try:
        await usecase.ensure_can_plan_issues(upload_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
        
    await publish_event(deps, "plan_issues", {"upload_id": upload_id})
    return {"message": "Issue planning started in background"}

@router.get("/agents/{upload_id}/issues")
async def get_issues(upload_id: str, usecase: AgentUseCase = Depends(get_agent_usecase)):
    try:
        return await usecase.get_issues(upload_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/agents/{upload_id}/issues/{issue_id}:implement", status_code=status.HTTP_202_ACCEPTED)
async def implement_issue(upload_id: str, issue_id: str, deps: Deps = Depends(get_deps), usecase: AgentUseCase = Depends(get_agent_usecase)):
    try:
        await usecase.ensure_can_implement_issue(upload_id, issue_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    await publish_event(deps, "implement_issue", {"upload_id": upload_id, "issue_id": issue_id})
    return {"message": "Implementation started in background"}

@router.post("/agents/{upload_id}/pulls/{pr_number}:review", status_code=status.HTTP_202_ACCEPTED)
async def review_pull(upload_id: str, pr_number: int, deps: Deps = Depends(get_deps), usecase: AgentUseCase = Depends(get_agent_usecase)):
    try:
        await usecase.ensure_can_review_pull(upload_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    await publish_event(deps, "review_pull", {"upload_id": upload_id, "pr_number": str(pr_number)})
    return {"message": "Review started in background"}

class ChatMessageRequest(BaseModel):
    message: str

@router.get("/agents/{upload_id}/charter/messages")
async def get_charter_messages(upload_id: str, usecase: AgentUseCase = Depends(get_agent_usecase)):
    try:
        return await usecase.get_charter_messages(upload_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/agents/{upload_id}/charter/messages")
async def send_charter_message(upload_id: str, req: ChatMessageRequest, usecase: AgentUseCase = Depends(get_agent_usecase)):
    try:
        return await usecase.send_charter_message(upload_id, req.message)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to send chat message for agent {upload_id}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/agents/{upload_id}/pulls/{pr_number}/diff")
async def get_pull_diff(upload_id: str, pr_number: int, usecase: AgentUseCase = Depends(get_agent_usecase)):
    try:
        diff_text = await usecase.get_pull_diff(upload_id, pr_number)
        return {"diff": diff_text}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get diff for PR {pr_number} on agent {upload_id}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/agents/{upload_id}/pulls/{pr_number}:deploy-preview")
async def deploy_preview(upload_id: str, pr_number: int, usecase: AgentUseCase = Depends(get_agent_usecase)):
    try:
        return await usecase.deploy_preview(upload_id, pr_number)
    except Exception as e:
        logger.error(f"Failed to deploy preview for PR {pr_number} on agent {upload_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/{upload_id}/pulls/{pr_number}:approve")
async def approve_pull(upload_id: str, pr_number: int, usecase: AgentUseCase = Depends(get_agent_usecase)):
    try:
        return await usecase.approve_pull(upload_id, pr_number)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to approve PR {pr_number} for agent {upload_id}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/agents/{upload_id}:stop")
async def stop_agent(upload_id: str, usecase: AgentUseCase = Depends(get_agent_usecase)):
    try:
        return await usecase.stop_agent(upload_id)
    except Exception as e:
        logger.error(f"Failed to stop agent {upload_id}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")
