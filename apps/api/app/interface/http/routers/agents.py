from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict
from app.deps import get_deps, Deps
from app.application.usecases.agent_usecase import AgentUseCase

router = APIRouter()

class AnalyzeRequest(BaseModel):
    uploadId: str

@router.post("/agents:analyze")
async def analyze_agent(req: AnalyzeRequest, deps: Deps = Depends(get_deps)):
    usecase = AgentUseCase(deps)
    try:
        return await usecase.analyze(req.uploadId)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/{upload_id}:register")
async def register_agent(upload_id: str, deps: Deps = Depends(get_deps)):
    usecase = AgentUseCase(deps)
    try:
        return await usecase.register(upload_id)
    except ValueError as e:
        status_code = 404 if str(e) == "not found" else 409
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/{upload_id}/issues:plan")
async def plan_issues(upload_id: str, deps: Deps = Depends(get_deps)):
    usecase = AgentUseCase(deps)
    try:
        return await usecase.plan_issues(upload_id)
    except ValueError as e:
        status_code = 404 if str(e) == "not found" else 409
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/{upload_id}/issues/{issue_id}:implement")
async def implement_issue(upload_id: str, issue_id: str, deps: Deps = Depends(get_deps)):
    usecase = AgentUseCase(deps)
    try:
        return await usecase.implement_issue(upload_id, issue_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/{upload_id}/pulls/{pr_number}:review")
async def review_pull(upload_id: str, pr_number: int, deps: Deps = Depends(get_deps)):
    usecase = AgentUseCase(deps)
    try:
        return await usecase.review_pull(upload_id, pr_number)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/{upload_id}/pulls/{pr_number}:deploy-preview")
async def deploy_preview(upload_id: str, pr_number: int, deps: Deps = Depends(get_deps)):
    usecase = AgentUseCase(deps)
    try:
        return await usecase.deploy_preview(upload_id, pr_number)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/{upload_id}/pulls/{pr_number}:approve")
async def approve_pull(upload_id: str, pr_number: int, deps: Deps = Depends(get_deps)):
    usecase = AgentUseCase(deps)
    try:
        return await usecase.approve_pull(upload_id, pr_number)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/{upload_id}:stop")
async def stop_agent(upload_id: str, deps: Deps = Depends(get_deps)):
    usecase = AgentUseCase(deps)
    try:
        return await usecase.stop_agent(upload_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

