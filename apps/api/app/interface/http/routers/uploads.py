from fastapi import APIRouter, UploadFile, File, Depends
from uuid import uuid4
from app.deps import get_deps, Deps

router = APIRouter()

@router.post("/uploads")
async def upload_zip(file: UploadFile = File(...), deps: Deps = Depends(get_deps)):
    agent_id = str(uuid4())
    zip_bytes = await file.read()
    gcs_path = deps.storage.upload_zip(agent_id, zip_bytes)
    return {"uploadId": agent_id, "gcsPath": gcs_path}
