"""Generation engine — assemble prompts, stream from LLM, save results."""

import json
from pathlib import Path
from typing import AsyncGenerator, Optional

import httpx
from loguru import logger
from sqlalchemy.orm import Session

from backend.config import DATA_DIR, load_config
from backend.repositories import chapter_repo
from backend.services import prompt_builder
from backend.services.model_router import resolve_api_for_task

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


def _filter_worldview(worldview: dict, level: str) -> str:
    """Filter worldview content based on chapter's worldview_level."""
    if level == "high":
        return json.dumps(worldview, ensure_ascii=False, indent=2)

    if level == "low":
        filtered = {"背景": worldview.get("背景", {})}
        return json.dumps(filtered, ensure_ascii=False, indent=2)

    # medium: include top-level sections that have meaningful content
    filtered = {}
    for k, v in worldview.items():
        if isinstance(v, dict):
            has_content = any(
                isinstance(vv, str) and vv.strip()
                or isinstance(vv, list) and len(vv) > 0
                for vv in v.values()
            )
            if has_content:
                filtered[k] = v
        elif isinstance(v, list) and len(v) > 0:
            filtered[k] = v
        elif isinstance(v, str) and v.strip():
            filtered[k] = v
    return json.dumps(filtered, ensure_ascii=False, indent=2)


def _format_character_profiles(characters: list) -> str:
    """Format character data into a prompt-ready profile block."""
    parts = []
    for c in characters:
        lines = [f"## {c.name}"]
        if c.role_type:
            lines[0] += f" ({c.role_type})"
        if c.description:
            lines.append(f"描述：{c.description}")
        if c.appearance:
            lines.append(f"外貌：{c.appearance}")
        if c.personality:
            lines.append(f"性格：{c.personality}")
        if c.background:
            lines.append(f"背景：{c.background}")
        if c.goals:
            lines.append(f"目标：{c.goals}")
        parts.append("\n".join(lines))
    return "\n\n".join(parts)


def _get_gen_config() -> dict:
    """Read the 'generation' section from config.json with defaults."""
    cfg = load_config()
    gen = cfg.get("generation", {})
    return {
        "previous_chapter_count": gen.get("previous_chapter_count", 1),
        "auto_split_target_words": gen.get("auto_split_target_words", 2000),
    }


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


# ── Non-streaming (sync) API helpers ───────────────────────


async def _call_openai_sync(route_config: dict, prompt: str) -> str:
    """Non-streaming OpenAI-compatible chat completions call. Returns full response text."""
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
        "max_tokens": route_config.get("max_tokens") or 4096,
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, json=body, headers=headers)
        if not resp.is_success:
            raise RuntimeError(
                f"LLM API error (HTTP {resp.status_code}): {resp.text[:300]}"
            )
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")


async def _call_anthropic_sync(route_config: dict, prompt: str) -> str:
    """Non-streaming Anthropic Messages API call. Returns full response text."""
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
        "max_tokens": route_config.get("max_tokens") or 4096,
        "messages": [{"role": "user", "content": prompt}],
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, json=body, headers=headers)
        if not resp.is_success:
            raise RuntimeError(
                f"Anthropic API error (HTTP {resp.status_code}): {resp.text[:300]}"
            )
        data = resp.json()
        content_blocks = data.get("content", [])
        return "".join(b.get("text", "") for b in content_blocks)


# ── AI Summary generation ──────────────────────────────────


async def generate_ai_summary(
    db: Session, content: str, title: str, author_summary: str = ""
) -> str:
    """Call the LLM (non-streaming) to generate a 150-300 character Chinese summary.

    Returns the summary string, or "" on failure.
    """
    route_config = resolve_api_for_task(db, "chapter_writing")
    if not route_config or not route_config.get("api_key"):
        logger.warning("Cannot generate AI summary: no route config for chapter_writing")
        return ""

    prompt_parts = [
        "请用中文为以下小说章节写一段简洁的摘要（150-300字），只写摘要本身，不要额外说明。",
    ]
    if author_summary:
        prompt_parts.append(f"\n作者摘要：{author_summary}")
    prompt_parts.append(f"\n章节标题：{title}")
    prompt_parts.append(f"\n章节内容：\n{content[:3000]}")

    prompt = "\n".join(prompt_parts)

    try:
        provider = route_config.get("provider", "openai")
        if provider == "anthropic":
            result = await _call_anthropic_sync(route_config, prompt)
        else:
            result = await _call_openai_sync(route_config, prompt)
        logger.info("AI summary generated for '{}': {} chars", title, len(result))
        return result.strip()
    except Exception as e:
        logger.error("Failed to generate AI summary for '{}': {}", title, e)
        return ""


# ── Content splitting ──────────────────────────────────────


def split_content_into_segments(content: str, target_words: int) -> list[str]:
    """Split content at paragraph boundaries, targeting *target_words* per segment.

    Splits on ``\\n\\n``. Tries to keep each segment close to target_words
    without truncating individual paragraphs.
    """
    paragraphs = content.split("\n\n")
    if not paragraphs:
        return [content]

    segments = []
    current = []
    current_len = 0

    for para in paragraphs:
        para_len = len(para)
        if current_len > 0 and current_len + para_len > target_words * 1.4:
            segments.append("\n\n".join(current))
            current = [para]
            current_len = para_len
        else:
            current.append(para)
            current_len += para_len

    if current:
        segments.append("\n\n".join(current))

    # If only one segment, return as-is
    if len(segments) <= 1:
        return [content]

    logger.info(
        "Split {} chars into {} segments (target={} words/segment)",
        len(content), len(segments), target_words,
    )
    return segments


# ── Prompt variable assembly ────────────────────────────────


def build_prompt_variables(db: Session, chapter_id: int) -> dict:
    """Assemble all prompt variables for a chapter without streaming.

    Returns a dict with keys:
        chapter, template, variables, prompt, token_estimate,
        route_config, model_name, template_name, error
    On error, ``error`` is set and the caller should not proceed.
    """
    # 1. Load chapter
    chapter = chapter_repo.get_chapter(db, chapter_id)
    if not chapter:
        return {"error": "Chapter not found"}

    # 2. Load template
    try:
        template = prompt_builder.load_template("chapter_writing")
    except (FileNotFoundError, ValueError) as e:
        return {"error": str(e)}

    # 3. Build variables from JSON files + chapter data
    worldview_raw = _read_json_file(DATA_DIR / "worldview.json", "{}")
    writing_style_text = _read_json_file(DATA_DIR / "writing_style.json", "")

    try:
        worldview_dict = json.loads(worldview_raw) if worldview_raw.strip() else {}
    except json.JSONDecodeError:
        worldview_dict = {}
    worldview_text = _filter_worldview(worldview_dict, chapter.worldview_level or "medium")

    characters = chapter_repo.get_chapter_characters(db, chapter_id)
    character_profiles = _format_character_profiles(characters) if characters else ""

    variables = {
        "chapter_title": chapter.title or "",
        "chapter_summary": chapter.summary or "",
        "worldview": worldview_text,
        "writing_style": writing_style_text,
        "character_profiles": character_profiles,
    }

    # Inject previous chapter AI summaries
    gen_config = _get_gen_config()
    prev_count = gen_config["previous_chapter_count"]
    if prev_count > 0:
        summaries = chapter_repo.get_previous_chapter_summaries(db, chapter_id, prev_count)
        if summaries:
            parts = []
            for i, s in enumerate(summaries, 1):
                parts.append(f"前{i}章摘要：{s}")
            variables["previous_chapter_summary"] = "\n".join(parts)
            logger.info("Injected {} previous chapter summaries", len(summaries))

    logger.info(
        "Generated vars: worldview={} chars (level={}), style={} chars, characters={}",
        len(worldview_text), chapter.worldview_level, len(writing_style_text), len(characters),
    )

    # 4. Build prompt
    try:
        prompt = prompt_builder.build_prompt(template, variables)
    except ValueError as e:
        return {"error": str(e)}

    token_estimate = prompt_builder.estimate_tokens(prompt)
    logger.info("Prompt built for chapter {}: {} chars, ~{} tokens",
                chapter_id, len(prompt), token_estimate)

    # 5. Get model config
    route_config = resolve_api_for_task(db, "chapter_writing")
    if not route_config:
        return {"error": "No API resolved for chapter_writing. Bind a plan to this task."}
    if not route_config.get("api_key"):
        return {"error": "API key not configured for the resolved API"}

    model_name = route_config.get("model_name", "")
    template_name = template.get("frontmatter", {}).get("name", template.get("file_name", ""))

    return {
        "chapter": chapter,
        "template": template,
        "variables": variables,
        "prompt": prompt,
        "token_estimate": token_estimate,
        "route_config": route_config,
        "model_name": model_name,
        "template_name": template_name,
    }


# ── Public API ─────────────────────────────────────────────


async def generate_chapter_stream(
    db: Session,
    chapter_id: int,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> AsyncGenerator[str, None]:
    """Async generator yielding SSE events for chapter generation."""
    # 1-5. Assemble prompt variables
    ctx = build_prompt_variables(db, chapter_id)
    if ctx.get("error"):
        yield _sse_event("error", {"message": ctx["error"]})
        return

    # 6. Stream from LLM
    collected_tokens: list[str] = []
    route_config = ctx["route_config"]
    prompt = ctx["prompt"]
    model_name = ctx["model_name"]
    token_estimate = ctx["token_estimate"]
    provider = route_config.get("provider", "openai")

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

    # 8. Generate AI summary
    chapter = chapter_repo.get_chapter(db, chapter_id)
    if chapter:
        ai_summary = await generate_ai_summary(
            db, full_content, chapter.title or "", chapter.summary or "",
        )
        if ai_summary:
            chapter_repo.save_chapter_ai_summary(db, chapter_id, ai_summary)
            yield _sse_event("summary", {"summary": ai_summary})

    yield _sse_event("done", {"word_count": word_count, "model": model_name})


async def generate_unlimited_stream(
    db: Session,
    chapter_id: int,
    temperature: Optional[float] = None,
) -> AsyncGenerator[str, None]:
    """Unlimited generation: stream content, then auto-split into chapters.

    SSE events: start, token, splitting, summary, done, error
    """
    # Assemble prompt
    ctx = build_prompt_variables(db, chapter_id)
    if ctx.get("error"):
        yield _sse_event("error", {"message": ctx["error"]})
        return

    # Append unlimited generation instruction
    unlimited_prompt = ctx["prompt"] + (
        "\n\n请连续撰写多个章节的内容，不要停滞，保持连贯叙事。"
        "每个章节之间用空行分隔的'---'作为分节符。"
        "\n\n请在内容中自然地在合适的位置插入分隔符 '\\n\\n---\\n\\n' 来标记章节边界。"
    )

    route_config = ctx["route_config"]
    model_name = ctx["model_name"]
    token_estimate = ctx["token_estimate"]
    provider = route_config.get("provider", "openai")

    yield _sse_event("start", {"model": model_name, "token_estimate": token_estimate, "unlimited": True})

    collected_tokens: list[str] = []
    try:
        if provider == "anthropic":
            stream = _stream_anthropic(route_config, unlimited_prompt, temperature, None)
        else:
            stream = _stream_openai(route_config, unlimited_prompt, temperature, None)

        async for token in stream:
            collected_tokens.append(token)
            yield _sse_event("token", {"token": token})
    except Exception as e:
        logger.error("Unlimited generation failed for chapter {}: {}", chapter_id, e)
        yield _sse_event("error", {"message": str(e)})
        return

    full_content = "".join(collected_tokens).strip()

    # Split content by explicit separators first, then by word count
    gen_config = _get_gen_config()
    target_words = gen_config["auto_split_target_words"]

    if "\n\n---\n\n" in full_content:
        segments = [s.strip() for s in full_content.split("\n\n---\n\n") if s.strip()]
    else:
        segments = split_content_into_segments(full_content, target_words)

    yield _sse_event("splitting", {"segment_count": len(segments)})

    # Save first segment to current chapter
    first_segment = segments[0]
    first_word_count = len(first_segment)
    try:
        chapter_repo.save_generated_content(
            db, chapter_id, first_segment, first_word_count, ctx["prompt"], model_name,
        )
    except Exception as e:
        logger.error("Failed to save first segment for chapter {}: {}", chapter_id, e)
        yield _sse_event("error", {"message": f"Save failed: {e}"})
        return

    # Create new chapters for remaining segments
    new_chapter_ids = []
    if len(segments) > 1:
        chapter = chapter_repo.get_chapter(db, chapter_id)
        if chapter:
            try:
                new_chapters = chapter_repo.create_chapters_batch(db, chapter, segments)
                new_chapter_ids = [ch.id for ch in new_chapters]
            except Exception as e:
                logger.error("Failed to create batch chapters: {}", e)
                yield _sse_event("error", {"message": f"Batch create failed: {e}"})
                return

    # Generate ONE AI summary for the entire original content
    chapter = chapter_repo.get_chapter(db, chapter_id)
    if chapter:
        ai_summary = await generate_ai_summary(
            db, full_content, chapter.title or "", chapter.summary or "",
        )
        if ai_summary:
            chapter_repo.save_chapter_ai_summary(db, chapter_id, ai_summary)
            yield _sse_event("summary", {"summary": ai_summary})

    yield _sse_event("done", {
        "word_count": len(full_content),
        "model": model_name,
        "new_chapter_ids": new_chapter_ids,
    })
