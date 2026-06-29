import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.settings import get_settings
from app.interface.http.routers import uploads, agents, webhooks

# Configure google-genai SDK to use Vertex AI
settings = get_settings()
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"
os.environ["GOOGLE_CLOUD_PROJECT"] = settings.google_cloud_project
os.environ["GOOGLE_CLOUD_LOCATION"] = settings.google_cloud_region
os.environ["GEMINI_MODEL_FLASH"] = settings.gemini_model_flash
os.environ["GEMINI_MODEL_PRO"] = settings.gemini_model_pro

from app.application.logger import setup_memory_logging, memory_handler

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_memory_logging()
    yield

app = FastAPI(title="PoC Foundry API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(uploads.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")

@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}

@app.get("/api/logs")
async def get_logs():
    return {"logs": memory_handler.get_logs()}
