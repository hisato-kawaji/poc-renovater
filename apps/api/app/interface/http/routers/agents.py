from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
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

async def run_with_error_handling(resource_id: str, task_name: str, usecase: AgentUseCase, func_name: str, *args):
    try:
        func = getattr(usecase, func_name)
        await func(*args)
    except Exception as e:
        logger.error(f"Background '{task_name}' failed for {resource_id}: {e}", exc_info=True)
        import asyncio
        asyncio.create_task(usecase.mark_as_failed(resource_id, str(e)))

@router.post("/agents:analyze", status_code=status.HTTP_202_ACCEPTED)
async def analyze_agent(req: AnalyzeRequest, background_tasks: BackgroundTasks, usecase: AgentUseCase = Depends(get_agent_usecase)):
    background_tasks.add_task(run_with_error_handling, req.uploadId, "analyze", usecase, "analyze", req.uploadId)
    return {"message": "Analysis started in background", "uploadId": req.uploadId}

@router.post("/agents/{upload_id}:register", status_code=status.HTTP_202_ACCEPTED)
async def register_agent(upload_id: str, background_tasks: BackgroundTasks, usecase: AgentUseCase = Depends(get_agent_usecase)):
    try:
        await usecase.ensure_can_register(upload_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
        
    background_tasks.add_task(run_with_error_handling, upload_id, "register", usecase, "register", upload_id)
    return {"message": "Registration started in background"}

@router.post("/agents/{upload_id}/issues:plan", status_code=status.HTTP_202_ACCEPTED)
async def plan_issues(upload_id: str, background_tasks: BackgroundTasks, usecase: AgentUseCase = Depends(get_agent_usecase)):
    try:
        await usecase.ensure_can_plan_issues(upload_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
        
    background_tasks.add_task(run_with_error_handling, upload_id, "plan_issues", usecase, "plan_issues", upload_id)
    return {"message": "Issue planning started in background"}

@router.post("/agents/{upload_id}/issues/{issue_id}:implement", status_code=status.HTTP_202_ACCEPTED)
async def implement_issue(upload_id: str, issue_id: str, background_tasks: BackgroundTasks, usecase: AgentUseCase = Depends(get_agent_usecase)):
    try:
        await usecase.ensure_can_implement_issue(upload_id, issue_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    background_tasks.add_task(run_with_error_handling, upload_id, "implement_issue", usecase, "implement_issue", upload_id, issue_id)
    return {"message": "Implementation started in background"}

@router.post("/agents/{upload_id}/pulls/{pr_number}:review", status_code=status.HTTP_202_ACCEPTED)
async def review_pull(upload_id: str, pr_number: int, background_tasks: BackgroundTasks, usecase: AgentUseCase = Depends(get_agent_usecase)):
    try:
        await usecase.ensure_can_review_pull(upload_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    background_tasks.add_task(run_with_error_handling, upload_id, "review_pull", usecase, "review_pull", upload_id, pr_number)
    return {"message": "Review started in background"}

@router.post("/agents/{upload_id}/pulls/{pr_number}:deploy-preview")
async def deploy_preview(upload_id: str, pr_number: int, usecase: AgentUseCase = Depends(get_agent_usecase)):
    try:
        return await usecase.deploy_preview(upload_id, pr_number)
    except Exception as e:
        logger.error(f"Failed to deploy preview for PR {pr_number} on agent {upload_id}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

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
