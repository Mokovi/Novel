"""Model routing — config retrieval and API connectivity test."""

from typing import Optional

import httpx
from loguru import logger

from backend.models.model_route import ModelRoute
from backend.utils.crypto import decrypt_api_key

# Predefined task keys
TASK_KEYS = [
    "outline_design",
    "chapter_writing",
    "character_design",
    "worldbuilding",
    "revision",
]

# Default API base URLs by provider
_DEFAULT_API_BASES = {
    "openai": "https://api.openai.com/v1",
    "deepseek": "https://api.deepseek.com",
    "anthropic": "https://api.anthropic.com",
}


def get_route_config(db_session, task_key: str) -> Optional[dict]:
    """Return decrypted full config for a task key, or None if not found."""
    route = (
        db_session.query(ModelRoute)
        .filter(ModelRoute.task_key == task_key)
        .first()
    )
    if not route:
        return None
    config = {
        "task_key": route.task_key,
        "provider": route.provider,
        "model_name": route.model_name,
        "api_key": decrypt_api_key(route.api_key_encrypted) if route.api_key_encrypted else None,
        "api_base_url": route.api_base_url,
        "enabled": route.enabled,
        "max_tokens": route.max_tokens,
        "temperature": route.temperature,
    }
    return config


async def test_connection(route: ModelRoute) -> dict:
    """Send a minimal test request to the configured LLM endpoint."""
    if not route.api_key_encrypted or not route.provider:
        return {"success": False, "error": "Provider or API key not configured"}

    api_key = decrypt_api_key(route.api_key_encrypted)
    base_url = route.api_base_url or _DEFAULT_API_BASES.get(route.provider, "")
    if not base_url:
        return {"success": False, "error": "No API base URL configured"}

    # Normalize base_url — strip trailing slash
    base_url = base_url.rstrip("/")

    # Build endpoint URL based on provider
    if route.provider == "anthropic":
        url = f"{base_url}/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        body = {
            "model": route.model_name or "claude-3-haiku-20240307",
            "max_tokens": 10,
            "messages": [{"role": "user", "content": "hello"}],
        }
    else:
        # OpenAI-compatible (openai, deepseek, openrouter, etc.)
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": route.model_name or "gpt-4o-mini",
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
