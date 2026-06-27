from fastapi import APIRouter, Depends, HTTPException
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

@router.post("/agents:analyze")
async def analyze_agent(req: AnalyzeRequest, usecase: AgentUseCase = Depends(get_agent_usecase)):
    try:
        return await usecase.analyze(req.uploadId)
    except Exception as e:
        logger.error(f"Failed to analyze agent {req.uploadId}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/agents/{upload_id}:register")
async def register_agent(upload_id: str, usecase: AgentUseCase = Depends(get_agent_usecase)):
    try:
        return await usecase.register(upload_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to register agent {upload_id}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/agents/{upload_id}/issues:plan")
async def plan_issues(upload_id: str, usecase: AgentUseCase = Depends(get_agent_usecase)):
    try:
        return await usecase.plan_issues(upload_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to plan issues for agent {upload_id}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/agents/{upload_id}/issues/{issue_id}:implement")
async def implement_issue(upload_id: str, issue_id: str, usecase: AgentUseCase = Depends(get_agent_usecase)):
    try:
        return await usecase.implement_issue(upload_id, issue_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to implement issue {issue_id} for agent {upload_id}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/agents/{upload_id}/pulls/{pr_number}:review")
async def review_pull(upload_id: str, pr_number: int, usecase: AgentUseCase = Depends(get_agent_usecase)):
    try:
        return await usecase.review_pull(upload_id, pr_number)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to review PR {pr_number} for agent {upload_id}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

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
