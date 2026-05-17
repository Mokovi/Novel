"""AI_Novel — FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import chapters, model_routes

app = FastAPI(
    title="AI_Novel",
    description="Local human-AI collaborative novel writing system",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chapters.router)
app.include_router(model_routes.router)


@app.get("/api/v1/health")
async def health():
    return {"status": "ok"}
