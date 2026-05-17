"""REST endpoints for ApiPlan CRUD and plan-API management."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.api_plan import ApiPlan, PlanApi
from backend.models.model_api import ModelApi
from backend.schemas.api_plan import (
    ApiPlanCreate,
    ApiPlanResponse,
    ApiPlanUpdate,
    PlanApiItem,
)

router = APIRouter(prefix="/api/v1", tags=["api-plans"])


def _build_plan_response(plan: ApiPlan, db: Session) -> ApiPlanResponse:
    pas = (
        db.query(PlanApi, ModelApi)
        .join(ModelApi, PlanApi.api_id == ModelApi.id)
        .filter(PlanApi.plan_id == plan.id)
        .order_by(PlanApi.sort_order)
        .all()
    )
    apis = [
        PlanApiItem(
            id=ma.id,
            name=ma.name,
            provider=ma.provider,
            model_name=ma.model_name,
            enabled=ma.enabled,
        )
        for _pa, ma in pas
    ]
    return ApiPlanResponse(
        id=plan.id,
        name=plan.name,
        description=plan.description,
        apis=apis,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


def _sync_plan_apis(db: Session, plan_id: int, api_ids: list[int]):
    """Replace plan-API associations with new ordered list."""
    db.query(PlanApi).filter(PlanApi.plan_id == plan_id).delete()
    for idx, api_id in enumerate(api_ids):
        db.add(PlanApi(plan_id=plan_id, api_id=api_id, sort_order=idx))


@router.get("/api-plans", response_model=list[ApiPlanResponse])
def list_plans(db: Session = Depends(get_db)):
    plans = db.query(ApiPlan).order_by(ApiPlan.id).all()
    return [_build_plan_response(p, db) for p in plans]


@router.get("/api-plans/{plan_id}", response_model=ApiPlanResponse)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(ApiPlan).filter(ApiPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return _build_plan_response(plan, db)


@router.post("/api-plans", response_model=ApiPlanResponse, status_code=201)
def create_plan(body: ApiPlanCreate, db: Session = Depends(get_db)):
    plan = ApiPlan(name=body.name, description=body.description)
    db.add(plan)
    db.flush()
    _sync_plan_apis(db, plan.id, body.api_ids)
    db.commit()
    db.refresh(plan)
    return _build_plan_response(plan, db)


@router.put("/api-plans/{plan_id}", response_model=ApiPlanResponse)
def update_plan(plan_id: int, body: ApiPlanUpdate, db: Session = Depends(get_db)):
    plan = db.query(ApiPlan).filter(ApiPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    update_data = body.model_dump(exclude_unset=True)
    api_ids = update_data.pop("api_ids", None)
    for field, value in update_data.items():
        setattr(plan, field, value)

    if api_ids is not None:
        _sync_plan_apis(db, plan.id, api_ids)

    db.commit()
    db.refresh(plan)
    return _build_plan_response(plan, db)


@router.delete("/api-plans/{plan_id}", status_code=204)
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(ApiPlan).filter(ApiPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    db.delete(plan)
    db.commit()
