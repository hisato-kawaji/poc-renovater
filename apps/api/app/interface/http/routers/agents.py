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

async def _analyze_background(upload_id: str, usecase: AgentUseCase):
    try:
        await usecase.analyze(upload_id)
    except Exception as e:
        logger.error(f"Background analyze failed for {upload_id}: {e}", exc_info=True)

@router.post("/agents:analyze", status_code=status.HTTP_202_ACCEPTED)
async def analyze_agent(req: AnalyzeRequest, background_tasks: BackgroundTasks, usecase: AgentUseCase = Depends(get_agent_usecase)):
    background_tasks.add_task(_analyze_background, req.uploadId, usecase)
    return {"message": "Analysis started in background", "uploadId": req.uploadId}

async def _register_background(upload_id: str, usecase: AgentUseCase):
    try:
        await usecase.register(upload_id)
    except Exception as e:
        logger.error(f"Background register failed for {upload_id}: {e}", exc_info=True)

@router.post("/agents/{upload_id}:register", status_code=status.HTTP_202_ACCEPTED)
async def register_agent(upload_id: str, background_tasks: BackgroundTasks, usecase: AgentUseCase = Depends(get_agent_usecase)):
    # Quick check for initial status
    try:
        doc = await usecase.repo.get(upload_id)
        if not doc:
            raise NotFoundError(f"Agent {upload_id} not found")
        if doc.get("status") != "PASSED":
             raise ConflictError("Agent has not passed the Charter Gate")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
        
    background_tasks.add_task(_register_background, upload_id, usecase)
    return {"message": "Registration started in background"}

async def _plan_issues_background(upload_id: str, usecase: AgentUseCase):
    try:
        await usecase.plan_issues(upload_id)
    except Exception as e:
        logger.error(f"Background plan issues failed for {upload_id}: {e}", exc_info=True)

@router.post("/agents/{upload_id}/issues:plan", status_code=status.HTTP_202_ACCEPTED)
async def plan_issues(upload_id: str, background_tasks: BackgroundTasks, usecase: AgentUseCase = Depends(get_agent_usecase)):
    try:
        doc = await usecase.repo.get(upload_id)
        if not doc:
            raise NotFoundError(f"Agent {upload_id} not found")
        if doc.get("status") not in ["REGISTERED", "MERGED", "IDLE"]:
             raise ConflictError("Agent is not ready for issue planning")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
        
    background_tasks.add_task(_plan_issues_background, upload_id, usecase)
    return {"message": "Issue planning started in background"}

async def _implement_issue_background(upload_id: str, issue_id: str, usecase: AgentUseCase):
    try:
        await usecase.implement_issue(upload_id, issue_id)
    except Exception as e:
        logger.error(f"Background implement failed for {upload_id}, issue {issue_id}: {e}", exc_info=True)

@router.post("/agents/{upload_id}/issues/{issue_id}:implement", status_code=status.HTTP_202_ACCEPTED)
async def implement_issue(upload_id: str, issue_id: str, background_tasks: BackgroundTasks, usecase: AgentUseCase = Depends(get_agent_usecase)):
    try:
        doc = await usecase.repo.get(upload_id)
        if not doc:
            raise NotFoundError(f"Agent {upload_id} not found")
        issues = await usecase.repo.get_issues(upload_id)
        if not any(i["id"] == issue_id for i in issues):
            raise NotFoundError(f"Issue {issue_id} not found")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    background_tasks.add_task(_implement_issue_background, upload_id, issue_id, usecase)
    return {"message": "Implementation started in background"}

async def _review_pull_background(upload_id: str, pr_number: int, usecase: AgentUseCase):
    try:
        await usecase.review_pull(upload_id, pr_number)
    except Exception as e:
        logger.error(f"Background review failed for {upload_id}, PR {pr_number}: {e}", exc_info=True)

@router.post("/agents/{upload_id}/pulls/{pr_number}:review", status_code=status.HTTP_202_ACCEPTED)
async def review_pull(upload_id: str, pr_number: int, background_tasks: BackgroundTasks, usecase: AgentUseCase = Depends(get_agent_usecase)):
    try:
        doc = await usecase.repo.get(upload_id)
        if not doc:
            raise NotFoundError(f"Agent {upload_id} not found")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    background_tasks.add_task(_review_pull_background, upload_id, pr_number, usecase)
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
