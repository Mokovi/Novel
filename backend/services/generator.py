"""Generation engine — assemble prompts, stream from LLM, save results."""

import json
from pathlib import Path
from typing import AsyncGenerator, Optional

import httpx
from loguru import logger
from sqlalchemy.orm import Session

from backend.config import DATA_DIR, load_config
from backend.repositories import chapter_repo
from backend.models.book import Book
from backend.models.chapter import Volume
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
        "outline_generation_count": gen.get("outline_generation_count", 1),
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


# ── Prompt variable assembly ────────────────────────────────


def build_prompt_variables(db: Session, chapter_id: int, book_id: Optional[int] = None) -> dict:
    """Assemble all prompt variables for a chapter without streaming.

    *book_id* — if provided, worldview and writing_style are loaded from the
    Book DB record. Otherwise falls back to disk files.

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

    # 3. Build variables from DB (book) or disk files + chapter data
    if book_id:
        book = db.get(Book, book_id)
        worldview_raw = book.worldview if book and book.worldview else "{}"
        writing_style_text = book.writing_style if book and book.writing_style else ""
    else:
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
    book_id: Optional[int] = None,
) -> AsyncGenerator[str, None]:
    """Async generator yielding SSE events for chapter generation.

    *book_id* — if provided, worldview and writing_style are loaded from the
    Book DB record. Otherwise falls back to disk files.
    """
    # 1-5. Assemble prompt variables
    ctx = build_prompt_variables(db, chapter_id, book_id=book_id)
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


# ── Outline generation ─────────────────────────────────────


def _load_book_worldview(db: Session, book_id: Optional[int] = None) -> str:
    """Load worldview from Book DB record, falling back to disk file."""
    if book_id:
        book = db.get(Book, book_id)
        if book and book.worldview:
            try:
                d = json.loads(book.worldview) if book.worldview.strip() else {}
            except json.JSONDecodeError:
                d = {}
            return _filter_worldview(d, "medium")
    # Fallback: read from disk
    raw = _read_json_file(DATA_DIR / "worldview.json", "{}")
    try:
        d = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        d = {}
    return _filter_worldview(d, "medium")


def _load_book_writing_style(db: Session, book_id: Optional[int] = None) -> str:
    """Load writing style from Book DB record, falling back to disk file."""
    if book_id:
        book = db.get(Book, book_id)
        if book and book.writing_style:
            return book.writing_style
    return _read_json_file(DATA_DIR / "writing_style.json", "")


def build_arc_prompt_variables(db: Session, arc_id: int, book_id: Optional[int] = None) -> dict:
    """Assemble prompt variables for generating an arc outline.

    *book_id* — if provided, worldview and writing_style are loaded from the
    Book DB record. Otherwise falls back to disk files.
    """
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

    worldview_text = _load_book_worldview(db, book_id)
    writing_style_text = _load_book_writing_style(db, book_id)

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


def build_volume_prompt_variables(db: Session, volume_id: int, book_id: Optional[int] = None) -> dict:
    """Assemble prompt variables for generating a volume outline.

    *book_id* — if provided, worldview and writing_style are loaded from the
    Book DB record. Otherwise falls back to disk files.
    """
    volumes = chapter_repo.list_volumes(db)
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

    worldview_text = _load_book_worldview(db, book_id)
    writing_style_text = _load_book_writing_style(db, book_id)

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
        book_outline_text = ""
        if book_id:
            book = db.get(Book, book_id)
            if book and book.outline:
                book_outline_text = book.outline
        if not book_outline_text:
            book_outline_text = load_config().get("book_outline", "")
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


def build_book_prompt_variables(db: Session, book_id: Optional[int] = None) -> dict:
    """Assemble prompt variables for generating a book-level outline.

    *book_id* — if provided, worldview, writing_style, and book outline are
    loaded from the Book DB record. Otherwise falls back to disk files / config.
    """
    try:
        template = prompt_builder.load_template("outline_design", "outline_design_book.md")
    except (FileNotFoundError, ValueError) as e:
        return {"error": str(e)}

    volume_outlines_list = chapter_repo.get_all_volume_outlines(db, book_id=book_id)
    vol_lines = []
    for v in volume_outlines_list:
        vol_lines.append(f"卷: {v['volume_title']}\n描述: {v['volume_description']}\n卷纲: {v['volume_outline']}")
    volume_outlines = "\n\n".join(vol_lines) if vol_lines else "（暂无卷）"

    worldview_text = _load_book_worldview(db, book_id)
    writing_style_text = _load_book_writing_style(db, book_id)

    variables = {
        "volume_outlines": volume_outlines,
        "worldview": worldview_text,
        "writing_style": writing_style_text,
    }

    # Inject book outline from the Book record
    if book_id:
        book = db.get(Book, book_id)
        if book and book.outline:
            variables["book_outline"] = book.outline
            logger.info("Injected book outline from DB for book {}", book_id)

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


