"""Pydantic schemas for ApiPlan, PlanApi, TaskPlanBinding."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ApiPlanCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    api_ids: list[int] = Field(default_factory=list)


class ApiPlanUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    api_ids: Optional[list[int]] = None


class PlanApiItem(BaseModel):
    id: int
    name: str
    provider: str
    model_name: str
    enabled: bool

    model_config = {"from_attributes": True}


class ApiPlanResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    apis: list[PlanApiItem] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TaskBindingResponse(BaseModel):
    task_key: str
    plan_id: Optional[int] = None
    plan_name: Optional[str] = None

    model_config = {"from_attributes": True}


class TaskBindingUpdate(BaseModel):
    plan_id: int
