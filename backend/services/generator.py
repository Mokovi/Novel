"""Generation engine — assemble prompts, stream from LLM, save results."""

import json
from pathlib import Path
from typing import AsyncGenerator, Optional

import httpx
from loguru import logger
from sqlalchemy.orm import Session

from backend.config import DATA_DIR
from backend.repositories import chapter_repo
from backend.services import prompt_builder
from backend.services.model_router import get_route_config

_DEFAULT_API_BASES = {
    "openai": "https://api.openai.com/v1",
    "deepseek": "https://api.deepseek.com",
    "anthropic": "https://api.anthropic.com",
}


def _sse_event(event: str, data: dict) -> str:
    return f"data: {json.dumps({'event': event, **data}, ensure_ascii=False)}\n\n"


def _read_json_file(path: Path, default: str) -> str:
    """Read a JSON file, returning *default* if missing or invalid."""
    if path.exists():
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            pass
    return default


# ── Streaming helpers ──────────────────────────────────────


async def _stream_openai(
    route_config: dict,
    prompt: str,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> AsyncGenerator[str, None]:
    """Stream tokens from an OpenAI-compatible chat completions endpoint."""
    base_url = (
        route_config.get("api_base_url")
        or _DEFAULT_API_BASES.get(route_config.get("provider", ""), "")
    ).rstrip("/")
    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {route_config['api_key']}",
        "Content-Type": "application/json",
    }
    body = {
        "model": route_config.get("model_name", "gpt-4o-mini"),
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
    }
    if temperature is not None:
        body["temperature"] = temperature
    if max_tokens is not None:
        body["max_tokens"] = max_tokens
    elif route_config.get("max_tokens"):
        body["max_tokens"] = route_config["max_tokens"]

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", url, json=body, headers=headers) as resp:
            if not resp.is_success:
                error_text = await resp.aread()
                raise RuntimeError(
                    f"LLM API error (HTTP {resp.status_code}): {error_text[:300]}"
                )
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                payload = line.removeprefix("data: ").strip()
                if payload == "[DONE]":
                    break
                try:
                    chunk = json.loads(payload)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                except json.JSONDecodeError:
                    continue


async def _stream_anthropic(
    route_config: dict,
    prompt: str,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> AsyncGenerator[str, None]:
    """Stream tokens from the Anthropic Messages API."""
    base_url = (
        route_config.get("api_base_url")
        or _DEFAULT_API_BASES.get("anthropic", "")
    ).rstrip("/")
    url = f"{base_url}/v1/messages"
    headers = {
        "x-api-key": route_config["api_key"],
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    body = {
        "model": route_config.get("model_name", "claude-3-haiku-20240307"),
        "max_tokens": max_tokens or route_config.get("max_tokens") or 4096,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
    }
    if temperature is not None:
        body["temperature"] = temperature

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", url, json=body, headers=headers) as resp:
            if not resp.is_success:
                error_text = await resp.aread()
                raise RuntimeError(
                    f"Anthropic API error (HTTP {resp.status_code}): {error_text[:300]}"
                )
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                payload = line.removeprefix("data: ").strip()
                try:
                    event_data = json.loads(payload)
                    if event_data.get("type") == "content_block_delta":
                        delta = event_data.get("delta", {})
                        text = delta.get("text", "")
                        if text:
                            yield text
                except json.JSONDecodeError:
                    continue


# ── Public API ─────────────────────────────────────────────


async def generate_chapter_stream(
    db: Session,
    chapter_id: int,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> AsyncGenerator[str, None]:
    """Async generator yielding SSE events for chapter generation."""
    # 1. Load chapter
    chapter = chapter_repo.get_chapter(db, chapter_id)
    if not chapter:
        yield _sse_event("error", {"message": "Chapter not found"})
        return

    # 2. Load template
    try:
        template = prompt_builder.load_template("chapter_writing")
    except (FileNotFoundError, ValueError) as e:
        yield _sse_event("error", {"message": str(e)})
        return

    # 3. Build variables from JSON files + chapter data
    worldview_text = _read_json_file(DATA_DIR / "worldview.json", "")
    writing_style_text = _read_json_file(DATA_DIR / "writing_style.json", "")

    variables = {
        "chapter_title": chapter.title or "",
        "chapter_summary": chapter.summary or "",
        "worldview": worldview_text,
        "writing_style": writing_style_text,
    }

    logger.info("Generated vars: worldview={} chars, style={} chars",
                len(worldview_text), len(writing_style_text))

    # 4. Build prompt
    try:
        prompt = prompt_builder.build_prompt(template, variables)
    except ValueError as e:
        yield _sse_event("error", {"message": str(e)})
        return

    token_estimate = prompt_builder.estimate_tokens(prompt)
    logger.info("Prompt built for chapter {}: {} chars, ~{} tokens",
                chapter_id, len(prompt), token_estimate)

    # 5. Get model config
    route_config = get_route_config(db, "chapter_writing")
    if not route_config:
        yield _sse_event("error", {"message": "No model route found for chapter_writing"})
        return
    if not route_config.get("enabled"):
        yield _sse_event("error", {"message": "chapter_writing route is not enabled"})
        return
    if not route_config.get("api_key"):
        yield _sse_event("error", {"message": "API key not configured for chapter_writing"})
        return

    # 6. Stream from LLM
    collected_tokens: list[str] = []
    provider = route_config.get("provider", "openai")
    model_name = route_config.get("model_name", "")

    yield _sse_event("start", {"model": model_name, "token_estimate": token_estimate})

    try:
        if provider == "anthropic":
            stream = _stream_anthropic(route_config, prompt, temperature, max_tokens)
        else:
            stream = _stream_openai(route_config, prompt, temperature, max_tokens)

        async for token in stream:
            collected_tokens.append(token)
            yield _sse_event("token", {"token": token})
    except Exception as e:
        logger.error("Generation failed for chapter {}: {}", chapter_id, e)
        yield _sse_event("error", {"message": str(e)})
        return

    # 7. Save result
    full_content = "".join(collected_tokens).strip()
    word_count = len(full_content)

    try:
        chapter_repo.save_generated_content(
            db, chapter_id, full_content, word_count, prompt, model_name,
        )
        logger.info("Chapter {} saved: {} words, model={}", chapter_id, word_count, model_name)
    except Exception as e:
        logger.error("Failed to save generated content for chapter {}: {}", chapter_id, e)
        yield _sse_event("error", {"message": f"Save failed: {e}"})
        return

    yield _sse_event("done", {"word_count": word_count, "model": model_name})
