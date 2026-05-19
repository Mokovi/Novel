"""Generation engine — assemble prompts, stream from LLM, save results."""

import json
from pathlib import Path
from typing import AsyncGenerator, Optional

import httpx
from loguru import logger
from sqlalchemy.orm import Session

from backend.config import DATA_DIR, load_config
from backend.models.chapter import Volume
from backend.repositories import book_repo, chapter_repo
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


def _filter_worldview(worldview_text: str, level: str) -> str:
    """Filter worldview markdown based on chapter's worldview_level."""
    if level == "high":
        return worldview_text
    if level == "low":
        # Return first ~500 chars as a brief summary
        return worldview_text[:500] if len(worldview_text) > 500 else worldview_text
    # medium: return as-is
    return worldview_text


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
        "outline_generation_count": gen.get("outline_generation_count", 1),
    }


def _read_book_worldview(db: Session, book_id: int) -> str:
    """Load worldview from Book DB record (raw markdown)."""
    book = book_repo.get_book(db, book_id)
    if book and book.worldview:
        try:
            # Try parsing as legacy JSON for migration
            d = json.loads(book.worldview)
            return _format_worldview_text_dict(d)
        except (json.JSONDecodeError, TypeError):
            # Already markdown text
            return book.worldview
    else:
        # Fallback to legacy file
        raw = _read_json_file(DATA_DIR / "worldview.json", "{}")
        try:
            d = json.loads(raw) if raw.strip() else {}
            return _format_worldview_text_dict(d) if d else ""
        except json.JSONDecodeError:
            return ""
    return ""


def _read_book_writing_style(db: Session, book_id: int) -> str:
    """Load writing style from Book DB record."""
    book = book_repo.get_book(db, book_id)
    if book and book.writing_style:
        return book.writing_style
    return _read_json_file(DATA_DIR / "writing_style.json", "")


def _read_book_outline(db: Session, book_id: int) -> str:
    """Load book outline from Book DB record."""
    book = book_repo.get_book(db, book_id)
    if book and book.outline:
        return book.outline
    return load_config().get("book_outline", "")


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


# ── Prompt variable assembly ────────────────────────────────


def build_prompt_variables(db: Session, chapter_id: int, book_id: int) -> dict:
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

    # 3. Build variables from Book DB + chapter data
    book = book_repo.get_book(db, book_id)
    worldview_text = ""
    if book and book.worldview:
        try:
            d = json.loads(book.worldview)
            worldview_text = _format_worldview_text_dict(d)
        except (json.JSONDecodeError, TypeError):
            worldview_text = book.worldview
    if not worldview_text:
        worldview_raw = _read_json_file(DATA_DIR / "worldview.json", "{}")
        try:
            d = json.loads(worldview_raw) if worldview_raw.strip() else {}
            worldview_text = _format_worldview_text_dict(d) if d else ""
        except json.JSONDecodeError:
            pass
    worldview_text = _filter_worldview(worldview_text, chapter.worldview_level or "medium")

    writing_style_text = ""
    if book and book.writing_style:
        writing_style_text = book.writing_style
    if not writing_style_text:
        writing_style_text = _read_json_file(DATA_DIR / "writing_style.json", "")

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

    # Inject parent arc outline (if configured)
    if gen_config.get("outline_injection_depth", 1) >= 1 and chapter.arc and chapter.arc.outline:
        variables["chapter_outline"] = chapter.arc.outline
        logger.info("Injected arc outline for chapter {}", chapter_id)

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
    user_id: int = 1,
    user_prompt: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """Async generator yielding SSE events for chapter generation."""
    # Get book_id from volume
    chapter = chapter_repo.get_chapter(db, chapter_id)
    if not chapter:
        yield _sse_event("error", {"message": "Chapter not found"})
        return
    volume = db.get(Volume, chapter.volume_id)
    book_id = volume.book_id if volume else 1

    # 1-5. Assemble prompt variables
    ctx = build_prompt_variables(db, chapter_id, book_id)
    if ctx.get("error"):
        yield _sse_event("error", {"message": ctx["error"]})
        return

    if user_prompt:
        ctx["prompt"] = ctx["prompt"] + "\n\n## 用户补充要求\n\n" + user_prompt

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


# ── Outline generation ─────────────────────────────────────


def build_arc_prompt_variables(db: Session, arc_id: int, book_id: int) -> dict:
    """Assemble prompt variables for generating an arc outline."""
    arc = chapter_repo.get_arc(db, arc_id)
    if not arc:
        return {"error": "Arc not found"}

    try:
        template = prompt_builder.load_template("outline_design", "outline_design_arc.md")
    except (FileNotFoundError, ValueError) as e:
        return {"error": str(e)}

    chapters = chapter_repo.get_arc_chapter_summaries(db, arc_id)
    chapter_lines = []
    for i, ch in enumerate(chapters, 1):
        summary = ch.get("ai_summary") or ch.get("summary") or ""
        chapter_lines.append(f"第{i}章: {ch.get('title', '')}\n摘要: {summary}")
    chapter_summaries = "\n\n".join(chapter_lines) if chapter_lines else "（暂无章节）"

    worldview_text = _read_book_worldview(db, book_id)
    writing_style_text = _read_book_writing_style(db, book_id)

    variables = {
        "arc_title": arc.title or "",
        "arc_description": arc.description or "",
        "chapter_summaries": chapter_summaries,
        "worldview": worldview_text,
        "writing_style": writing_style_text,
    }

    # Inject parent volume outline (if configured)
    gen_config = _get_gen_config()
    if gen_config.get("outline_injection_depth", 1) >= 1 and arc.volume_id:
        volume = db.get(Volume, arc.volume_id)
        if volume and volume.outline:
            variables["volume_outline"] = volume.outline
            logger.info("Injected volume outline for arc {}", arc_id)

    try:
        prompt = prompt_builder.build_prompt(template, variables)
    except ValueError as e:
        return {"error": str(e)}

    token_estimate = prompt_builder.estimate_tokens(prompt)
    route_config = resolve_api_for_task(db, "outline_design")
    if not route_config or not route_config.get("api_key"):
        return {"error": "No API configured for outline_design task"}
    model_name = route_config.get("model_name", "")
    template_name = template.get("frontmatter", {}).get("name", template.get("file_name", ""))

    return {
        "arc": arc,
        "template": template,
        "variables": variables,
        "prompt": prompt,
        "token_estimate": token_estimate,
        "route_config": route_config,
        "model_name": model_name,
        "template_name": template_name,
    }


def build_volume_prompt_variables(db: Session, volume_id: int, book_id: int) -> dict:
    """Assemble prompt variables for generating a volume outline."""
    volumes = chapter_repo.list_volumes(db, book_id=book_id)
    volume = next((v for v in volumes if v.id == volume_id), None)
    if not volume:
        return {"error": "Volume not found"}

    try:
        template = prompt_builder.load_template("outline_design", "outline_design_volume.md")
    except (FileNotFoundError, ValueError) as e:
        return {"error": str(e)}

    arcs = chapter_repo.get_volume_arc_outlines(db, volume_id)
    arc_lines = []
    for a in arcs:
        arc_lines.append(f"节: {a['arc_title']}\n描述: {a['arc_description']}\n节纲: {a['arc_outline']}")
        for j, ch in enumerate(a.get("chapters", []), 1):
            summary = ch.get("ai_summary") or ch.get("summary") or ""
            arc_lines.append(f"  第{j}章 ({ch.get('title', '')}): {summary}")
    arc_outlines = "\n\n".join(arc_lines) if arc_lines else "（暂无节纲）"

    worldview_text = _read_book_worldview(db, book_id)
    writing_style_text = _read_book_writing_style(db, book_id)

    variables = {
        "volume_title": volume.title or "",
        "volume_description": volume.description or "",
        "arc_outlines": arc_outlines,
        "worldview": worldview_text,
        "writing_style": writing_style_text,
    }

    # Inject book outline (if configured)
    gen_config = _get_gen_config()
    if gen_config.get("outline_injection_depth", 1) >= 1:
        book_outline_text = _read_book_outline(db, book_id)
        if book_outline_text:
            variables["book_outline"] = book_outline_text
            logger.info("Injected book outline for volume {}", volume_id)

    try:
        prompt = prompt_builder.build_prompt(template, variables)
    except ValueError as e:
        return {"error": str(e)}

    token_estimate = prompt_builder.estimate_tokens(prompt)
    route_config = resolve_api_for_task(db, "outline_design")
    if not route_config or not route_config.get("api_key"):
        return {"error": "No API configured for outline_design task"}
    model_name = route_config.get("model_name", "")
    template_name = template.get("frontmatter", {}).get("name", template.get("file_name", ""))

    return {
        "volume": volume,
        "template": template,
        "variables": variables,
        "prompt": prompt,
        "token_estimate": token_estimate,
        "route_config": route_config,
        "model_name": model_name,
        "template_name": template_name,
    }


def build_book_prompt_variables(db: Session, book_id: int) -> dict:
    """Assemble prompt variables for generating a book-level outline."""
    try:
        template = prompt_builder.load_template("outline_design", "outline_design_book.md")
    except (FileNotFoundError, ValueError) as e:
        return {"error": str(e)}

    volume_outlines_list = chapter_repo.get_all_volume_outlines(db, book_id=book_id)
    vol_lines = []
    for v in volume_outlines_list:
        vol_lines.append(f"卷: {v['volume_title']}\n描述: {v['volume_description']}\n卷纲: {v['volume_outline']}")
    volume_outlines = "\n\n".join(vol_lines) if vol_lines else "（暂无卷）"

    worldview_text = _read_book_worldview(db, book_id)
    writing_style_text = _read_book_writing_style(db, book_id)

    variables = {
        "volume_outlines": volume_outlines,
        "worldview": worldview_text,
        "writing_style": writing_style_text,
    }

    try:
        prompt = prompt_builder.build_prompt(template, variables)
    except ValueError as e:
        return {"error": str(e)}

    token_estimate = prompt_builder.estimate_tokens(prompt)
    route_config = resolve_api_for_task(db, "outline_design")
    if not route_config or not route_config.get("api_key"):
        return {"error": "No API configured for outline_design task"}
    model_name = route_config.get("model_name", "")
    template_name = template.get("frontmatter", {}).get("name", template.get("file_name", ""))

    return {
        "template": template,
        "variables": variables,
        "prompt": prompt,
        "token_estimate": token_estimate,
        "route_config": route_config,
        "model_name": model_name,
        "template_name": template_name,
    }


def _format_worldview_text_dict(data: dict) -> str:
    """Format worldview dict as readable text for prompt injection."""
    def _format_section(name: str, content) -> str:
        lines = [f"## {name}"]
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    lines.extend(f"- {k}: {v}" for k, v in item.items() if v)
                elif item:
                    lines.append(f"- {item}")
        elif isinstance(content, dict):
            for key, value in content.items():
                if isinstance(value, list):
                    if not value:
                        continue
                    lines.append(f"\n### {key}")
                    for item in value:
                        if isinstance(item, dict):
                            lines.extend(f"  - {k}: {v}" for k, v in item.items() if v)
                        elif item:
                            lines.append(f"  - {item}")
                elif isinstance(value, str) and value:
                    lines.append(f"- {key}: {value}")
        else:
            lines.append(str(content))
        return "\n".join(lines)

    sections = []
    for name, content in data.items():
        text = _format_section(name, content)
        if text.strip():
            sections.append(text)
    return "\n\n".join(sections)


def build_worldview_prompt_variables(db: Session, book_id: int) -> dict:
    """Assemble prompt variables for worldbuilding generation."""
    try:
        template = prompt_builder.load_template("worldbuilding")
    except (FileNotFoundError, ValueError) as e:
        return {"error": str(e)}

    # Read current worldview from Book DB (raw markdown)
    book = book_repo.get_book(db, book_id)
    current_worldview = ""
    if book and book.worldview:
        try:
            d = json.loads(book.worldview)
            current_worldview = _format_worldview_text_dict(d)
        except (json.JSONDecodeError, TypeError):
            current_worldview = book.worldview
    if not current_worldview:
        current_worldview = "（暂无世界观设定）"

    writing_style_text = ""
    if book and book.writing_style:
        writing_style_text = book.writing_style
    if not writing_style_text:
        writing_style_text = _read_json_file(DATA_DIR / "writing_style.json", "")

    variables = {
        "current_worldview": current_worldview,
        "writing_style": writing_style_text,
    }

    try:
        prompt = prompt_builder.build_prompt(template, variables)
    except ValueError as e:
        return {"error": str(e)}

    token_estimate = prompt_builder.estimate_tokens(prompt)
    route_config = resolve_api_for_task(db, "worldbuilding")
    if not route_config or not route_config.get("api_key"):
        return {"error": "No API configured for worldbuilding task"}
    model_name = route_config.get("model_name", "")
    template_name = template.get("frontmatter", {}).get("name", template.get("file_name", ""))

    return {
        "template": template,
        "variables": variables,
        "prompt": prompt,
        "token_estimate": token_estimate,
        "route_config": route_config,
        "model_name": model_name,
        "template_name": template_name,
    }


async def generate_outline_stream(
    db: Session,
    prompt_ctx: dict,
) -> AsyncGenerator[str, None]:
    """Generic SSE stream generator for all outline types.

    *prompt_ctx* is the dict returned by one of the
    ``build_*_prompt_variables`` functions above.
    """
    if prompt_ctx.get("error"):
        yield _sse_event("error", {"message": prompt_ctx["error"]})
        return

    route_config = prompt_ctx["route_config"]
    prompt = prompt_ctx["prompt"]
    model_name = prompt_ctx["model_name"]
    token_estimate = prompt_ctx["token_estimate"]
    provider = route_config.get("provider", "openai")

    yield _sse_event("start", {"model": model_name, "token_estimate": token_estimate})

    collected_tokens: list[str] = []
    try:
        if provider == "anthropic":
            stream = _stream_anthropic(route_config, prompt)
        else:
            stream = _stream_openai(route_config, prompt)

        async for token in stream:
            collected_tokens.append(token)
            yield _sse_event("token", {"token": token})
    except Exception as e:
        logger.error("Outline generation failed: {}", e)
        yield _sse_event("error", {"message": str(e)})
        return

    full_content = "".join(collected_tokens).strip()
    yield _sse_event("done", {"content": full_content, "model": model_name})
