"""Model routing — Plan-based resolution with Round-Robin."""

import httpx
from loguru import logger

from backend.models.api_plan import ApiPlan, PlanApi, TaskPlanBinding
from backend.models.model_api import ModelApi
from backend.utils.crypto import decrypt_api_key

# Predefined task keys
TASK_KEYS = [
    "outline_design",
    "chapter_writing",
    "character_design",
    "location_design",
    "worldbuilding",
    "revision",
]

# Default API base URLs by provider
_DEFAULT_API_BASES = {
    "openai": "https://api.openai.com/v1",
    "deepseek": "https://api.deepseek.com",
    "anthropic": "https://api.anthropic.com",
}


def resolve_api_for_task(db, task_key: str) -> dict | None:
    """Resolve a ModelApi config for *task_key* via Plan → Round-Robin.

    Returns a dict with decrypted api_key, or None if no API is available.
    """
    binding = (
        db.query(TaskPlanBinding)
        .filter(TaskPlanBinding.task_key == task_key)
        .first()
    )
    if not binding or binding.plan_id is None:
        return None

    plan = db.query(ApiPlan).filter(ApiPlan.id == binding.plan_id).first()
    if not plan:
        return None

    # Get enabled APIs in sort_order
    rows = (
        db.query(PlanApi, ModelApi)
        .join(ModelApi, PlanApi.api_id == ModelApi.id)
        .filter(PlanApi.plan_id == plan.id, ModelApi.enabled == True)
        .order_by(PlanApi.sort_order)
        .all()
    )
    if not rows:
        return None

    apis = [ma for _pa, ma in rows]
    idx = plan.round_robin_index % len(apis)
    selected = apis[idx]

    # Advance round-robin index for next call
    plan.round_robin_index = (idx + 1) % len(apis)
    db.commit()

    config = {
        "task_key": task_key,
        "provider": selected.provider,
        "model_name": selected.model_name,
        "api_key": decrypt_api_key(selected.api_key_encrypted) if selected.api_key_encrypted else None,
        "api_base_url": selected.api_base_url,
        "enabled": selected.enabled,
        "max_tokens": selected.max_tokens,
        "temperature": selected.temperature,
    }
    logger.info(
        "Resolved API for '{}': {} (round-robin idx={})",
        task_key, selected.model_name, idx,
    )
    return config


async def test_connection_for_api(api: ModelApi) -> dict:
    """Send a minimal test request for a single ModelApi instance."""
    if not api.api_key_encrypted or not api.provider:
        return {"success": False, "error": "Provider or API key not configured"}

    api_key = decrypt_api_key(api.api_key_encrypted)
    base_url = api.api_base_url or _DEFAULT_API_BASES.get(api.provider, "")
    if not base_url:
        return {"success": False, "error": "No API base URL configured"}

    base_url = base_url.rstrip("/")

    if api.provider == "anthropic":
        url = f"{base_url}/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        body = {
            "model": api.model_name or "claude-3-haiku-20240307",
            "max_tokens": 10,
            "messages": [{"role": "user", "content": "hello"}],
        }
    else:
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": api.model_name or "gpt-4o-mini",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 5,
        }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=body, headers=headers)
        if resp.is_success:
            return {"success": True}
        else:
            return {
                "success": False,
                "error": f"HTTP {resp.status_code}: {resp.text[:300]}",
            }
    except httpx.TimeoutException:
        return {"success": False, "error": "Request timed out after 15s"}
    except httpx.RequestError as e:
        return {"success": False, "error": f"Connection failed: {e}"}
