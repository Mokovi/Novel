"""REST endpoints for ModelApi CRUD and connection testing."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.model_api import ModelApi
from backend.models.user import User
from backend.routers.deps import get_current_user
from backend.schemas.model_api import ModelApiCreate, ModelApiResponse, ModelApiUpdate
from backend.services.model_router import test_connection_for_api
from backend.utils.crypto import decrypt_api_key, encrypt_api_key, mask_api_key

router = APIRouter(prefix="/api/v1", tags=["model-apis"])


def _build_response(api: ModelApi) -> ModelApiResponse:
    decrypted = decrypt_api_key(api.api_key_encrypted) if api.api_key_encrypted else None
    return ModelApiResponse(
        id=api.id,
        name=api.name,
        provider=api.provider,
        model_name=api.model_name,
        api_key_masked=mask_api_key(decrypted) if decrypted else None,
        api_base_url=api.api_base_url,
        enabled=api.enabled,
        max_tokens=api.max_tokens,
        temperature=api.temperature,
        created_at=api.created_at,
        updated_at=api.updated_at,
    )


@router.get("/model-apis", response_model=list[ModelApiResponse])
def list_apis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return [_build_response(a) for a in db.query(ModelApi).filter(ModelApi.user_id == current_user.id).order_by(ModelApi.id).all()]


@router.post("/model-apis", response_model=ModelApiResponse, status_code=201)
def create_api(
    body: ModelApiCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    api = ModelApi(
        user_id=current_user.id,
        name=body.name,
        provider=body.provider,
        model_name=body.model_name,
        api_base_url=body.api_base_url,
        enabled=body.enabled,
        max_tokens=body.max_tokens,
        temperature=body.temperature,
    )
    if body.api_key:
        api.api_key_encrypted = encrypt_api_key(body.api_key)
    db.add(api)
    db.commit()
    db.refresh(api)
    return _build_response(api)


@router.put("/model-apis/{api_id}", response_model=ModelApiResponse)
def update_api(
    api_id: int,
    body: ModelApiUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    api = db.query(ModelApi).filter(ModelApi.id == api_id, ModelApi.user_id == current_user.id).first()
    if not api:
        raise HTTPException(status_code=404, detail="Model API not found")

    update_data = body.model_dump(exclude_unset=True)
    if "api_key" in update_data:
        if update_data["api_key"]:
            api.api_key_encrypted = encrypt_api_key(update_data["api_key"])
        else:
            api.api_key_encrypted = None
        del update_data["api_key"]

    for field, value in update_data.items():
        setattr(api, field, value)

    db.commit()
    db.refresh(api)
    return _build_response(api)


@router.delete("/model-apis/{api_id}", status_code=204)
def delete_api(
    api_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    api = db.query(ModelApi).filter(ModelApi.id == api_id, ModelApi.user_id == current_user.id).first()
    if not api:
        raise HTTPException(status_code=404, detail="Model API not found")
    db.delete(api)
    db.commit()


@router.post("/model-apis/{api_id}/test")
async def test_api(
    api_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    api = db.query(ModelApi).filter(ModelApi.id == api_id, ModelApi.user_id == current_user.id).first()
    if not api:
        raise HTTPException(status_code=404, detail="Model API not found")
    result = await test_connection_for_api(api)
    return result
