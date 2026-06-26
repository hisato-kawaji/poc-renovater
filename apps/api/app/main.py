from fastapi import FastAPI
from app.interface.http.routers import uploads, agents

app = FastAPI(title="PoC Foundry API", version="0.1.0")

app.include_router(uploads.router, prefix="/api")
app.include_router(agents.router, prefix="/api")

@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}
