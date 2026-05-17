"""AI_Novel — FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import load_config
from backend.routers import api_plans, chapters, generate, model_apis, task_bindings, templates, worldview

config = load_config()

app = FastAPI(
    title="AI_Novel",
    description="Local human-AI collaborative novel writing system",
    version=config.get("version", "0.1.0"),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_plans.router)
app.include_router(chapters.router)
app.include_router(generate.router)
app.include_router(model_apis.router)
app.include_router(task_bindings.router)
app.include_router(templates.router)
app.include_router(worldview.router)


@app.get("/api/v1/health")
async def health():
    cfg = load_config()
    return {"status": "ok", "version": cfg.get("version", "0.1.0")}
