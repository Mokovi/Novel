"""AI_Novel — FastAPI application entry point."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import load_config
from backend.routers import admin, api_plans, auth, books, chapters, characters, generate, model_apis, settings, task_bindings, templates, worldview

config = load_config()

app = FastAPI(
    title="AI_Novel",
    description="Local human-AI collaborative novel writing system",
    version=config.get("version", "0.1.0"),
)

UPLOADS_DIR = Path(__file__).parent.parent / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

app.include_router(api_plans.router)
app.include_router(auth.router)
app.include_router(books.router)
app.include_router(chapters.router)
app.include_router(characters.router)
app.include_router(generate.router)
app.include_router(model_apis.router)
app.include_router(task_bindings.router)
app.include_router(templates.router)
app.include_router(admin.router)
app.include_router(settings.router)
app.include_router(worldview.router)


@app.get("/api/v1/health")
async def health():
    cfg = load_config()
    return {"status": "ok", "version": cfg.get("version", "0.1.0")}
