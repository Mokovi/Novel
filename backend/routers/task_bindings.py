"""REST endpoints for task → plan bindings."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.api_plan import ApiPlan, TaskPlanBinding
from backend.models.user import User
from backend.routers.deps import get_current_user
from backend.schemas.api_plan import TaskBindingResponse, TaskBindingUpdate
from backend.services.model_router import TASK_KEYS

router = APIRouter(prefix="/api/v1", tags=["task-bindings"])


@router.get("/task-bindings", response_model=list[TaskBindingResponse])
def list_bindings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bindings = (
        db.query(TaskPlanBinding, ApiPlan.name)
        .outerjoin(ApiPlan, TaskPlanBinding.plan_id == ApiPlan.id)
        .order_by(TaskPlanBinding.task_key)
        .all()
    )
    binding_map = {}
    for tb, plan_name in bindings:
        # Only include plans that belong to the current user or are unowned (global)
        if tb.plan_id is not None:
            plan = db.query(ApiPlan).filter(ApiPlan.id == tb.plan_id).first()
            if plan and plan.user_id != current_user.id:
                continue
        binding_map[tb.task_key] = TaskBindingResponse(
            task_key=tb.task_key,
            plan_id=tb.plan_id,
            plan_name=plan_name,
        )
    result = []
    for key in TASK_KEYS:
        if key in binding_map:
            result.append(binding_map[key])
        else:
            result.append(TaskBindingResponse(task_key=key))
    return result


@router.put("/task-bindings/{task_key}", response_model=TaskBindingResponse)
def bind_task(
    task_key: str,
    body: TaskBindingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if task_key not in TASK_KEYS:
        raise HTTPException(status_code=400, detail=f"Unknown task key: {task_key}")

    plan = db.query(ApiPlan).filter(ApiPlan.id == body.plan_id, ApiPlan.user_id == current_user.id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    binding = db.query(TaskPlanBinding).filter(TaskPlanBinding.task_key == task_key).first()
    if not binding:
        binding = TaskPlanBinding(task_key=task_key)
        db.add(binding)

    binding.plan_id = body.plan_id
    db.commit()
    db.refresh(binding)
    return TaskBindingResponse(task_key=binding.task_key, plan_id=binding.plan_id, plan_name=plan.name)


@router.delete("/task-bindings/{task_key}", status_code=204)
def unbind_task(
    task_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if task_key not in TASK_KEYS:
        raise HTTPException(status_code=400, detail=f"Unknown task key: {task_key}")

    binding = db.query(TaskPlanBinding).filter(TaskPlanBinding.task_key == task_key).first()
    if binding:
        # Verify the plan belongs to current user
        plan = db.query(ApiPlan).filter(ApiPlan.id == binding.plan_id).first()
        if plan and plan.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        db.delete(binding)
        db.commit()
