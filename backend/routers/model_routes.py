"""REST endpoints for ModelRoute configuration."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.model_route import ModelRoute
from backend.schemas.model_route import ModelRouteResponse, ModelRouteUpdate
from backend.services.model_router import TASK_KEYS, test_connection
from backend.utils.crypto import decrypt_api_key, encrypt_api_key, mask_api_key

router = APIRouter(prefix="/api/v1", tags=["model-routes"])


def _build_response(route: ModelRoute) -> ModelRouteResponse:
    decrypted = decrypt_api_key(route.api_key_encrypted) if route.api_key_encrypted else None
    return ModelRouteResponse(
        task_key=route.task_key,
        provider=route.provider,
        model_name=route.model_name,
        api_key_masked=mask_api_key(decrypted) if decrypted else None,
        api_base_url=route.api_base_url,
        enabled=route.enabled,
        max_tokens=route.max_tokens,
        temperature=route.temperature,
        updated_at=route.updated_at,
    )


@router.get("/model-routes", response_model=list[ModelRouteResponse])
def list_routes(db: Session = Depends(get_db)):
    """Get all model route configurations (API keys returned masked)."""
    routes = db.query(ModelRoute).order_by(ModelRoute.task_key).all()
    route_map = {r.task_key: r for r in routes}
    # Return in predefined order, include unconfigured routes as blanks
    result = []
    for key in TASK_KEYS:
        if key in route_map:
            result.append(_build_response(route_map[key]))
        else:
            result.append(
                ModelRouteResponse(
                    task_key=key,
                    enabled=False,
                )
            )
    return result


@router.put("/model-routes/{task_key}", response_model=ModelRouteResponse)
def update_route(task_key: str, body: ModelRouteUpdate, db: Session = Depends(get_db)):
    """Update a model route configuration for the given task key."""
    if task_key not in TASK_KEYS:
        raise HTTPException(status_code=400, detail=f"Unknown task key: {task_key}")

    route = db.query(ModelRoute).filter(ModelRoute.task_key == task_key).first()
    if not route:
        route = ModelRoute(task_key=task_key)
        db.add(route)

    update_data = body.model_dump(exclude_unset=True)
    if "api_key" in update_data:
        if update_data["api_key"]:
            route.api_key_encrypted = encrypt_api_key(update_data["api_key"])
        else:
            route.api_key_encrypted = None
        del update_data["api_key"]

    for field, value in update_data.items():
        setattr(route, field, value)

    route.enabled = body.enabled if body.enabled is not None else route.enabled
    db.commit()
    db.refresh(route)
    return _build_response(route)


@router.post("/model-routes/{task_key}/test")
async def test_route(task_key: str, db: Session = Depends(get_db)):
    """Send a test request to verify LLM connectivity for the given task key."""
    if task_key not in TASK_KEYS:
        raise HTTPException(status_code=400, detail=f"Unknown task key: {task_key}")

    route = db.query(ModelRoute).filter(ModelRoute.task_key == task_key).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not configured. Save a configuration first.")

    result = await test_connection(route)
    return result
