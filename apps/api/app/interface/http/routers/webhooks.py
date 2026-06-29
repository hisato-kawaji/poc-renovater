from fastapi import APIRouter, Request, Depends, HTTPException
from app.deps import get_deps, Deps

router = APIRouter()

@router.post("/webhooks/github")
async def github_webhook(request: Request, deps: Deps = Depends(get_deps)):
    # Validate signature and parse event
    # In a real app, this parses PR review / check run events
    payload = await request.json()
    event = request.headers.get("X-GitHub-Event")
    print(f"Received GitHub webhook: {event}")
    # Hand off to event orchestrator or PubSub
    return {"status": "ok"}

@router.post("/webhooks/cloudbuild")
async def cloudbuild_webhook(request: Request, deps: Deps = Depends(get_deps)):
    # Validate PubSub push token
    # Trigger DeployAgent completion or fallback
    payload = await request.json()
    print("Received Cloud Build webhook push")
    return {"status": "ok"}
