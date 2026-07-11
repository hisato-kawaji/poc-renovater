from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
import logging
from app.deps import get_deps, Deps
from app.application.usecases.agent_usecase import AgentUseCase
from app.domain.models import NotFoundError, ConflictError

logger = logging.getLogger(__name__)
router = APIRouter()

def get_agent_usecase(deps: Deps = Depends(get_deps)) -> AgentUseCase:
    return AgentUseCase(deps.agent_repo, deps.storage, deps.scm, deps.settings, deps)

@router.get("/agents/{upload_id}/jobs")
async def get_jobs(upload_id: str, usecase: AgentUseCase = Depends(get_agent_usecase)):
    try:
        return await usecase.get_jobs(upload_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/agents/{upload_id}/jobs/{job_id}/retry", status_code=status.HTTP_202_ACCEPTED)
async def retry_job(upload_id: str, job_id: str, deps: Deps = Depends(get_deps), usecase: AgentUseCase = Depends(get_agent_usecase)):
    try:
        return await usecase.retry_job(upload_id, job_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to retry job {job_id} for agent {upload_id}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")
