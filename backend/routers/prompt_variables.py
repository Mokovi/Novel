"""REST endpoints for aggregated prompt variable listing.

Returns all known template variables and their current values for a given book.
Book-type variables are read from the Book ORM; context/derived variables are
read-only placeholders with help text explaining where they come from.
"""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.repositories import book_repo
from backend.routers.deps import get_current_user

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _read_writing_style_default() -> str:
    """Fallback: read writing_style from the JSON file and format as markdown text."""
    path = DATA_DIR / "writing_style.json"
    if path.exists():
        try:
            data = json.loads(path.read_text("utf-8"))
        except (json.JSONDecodeError, OSError):
            return ""
        lines = []
        if style := data.get("style"):
            lines.append(f"写作视角与风格：{style}")
        if taboo := data.get("taboo_words"):
            lines.append(f"\n禁用词汇：{'、'.join(taboo) if taboo else '（无）'}")
        else:
            lines.append("\n禁用词汇：（无）")
        if techniques := data.get("preferred_techniques"):
            lines.append("\n偏好技巧：")
            for t in techniques:
                lines.append(f"- {t}")
        if refs := data.get("reference_works"):
            lines.append("\n参考作品：")
            for r in refs:
                lines.append(f"- {r}")
        return "\n".join(lines)
    return ""

router = APIRouter(prefix="/api/v1/books/{book_id}/prompt-variables", tags=["prompt-variables"])

# ── Variable registry ────────────────────────────────────────────────

VARIABLE_REGISTRY = [
    # ── book (editable) ──
    {"name": "book_name", "category": "book", "label": "书名", "editable": True, "editor": "input", "help_text": "小说的标题"},
    {"name": "book_description", "category": "book", "label": "书籍描述", "editable": True, "editor": "textarea_3", "help_text": "书籍的简要描述"},
    {"name": "worldview", "category": "book", "label": "世界观", "editable": True, "editor": "markdown", "help_text": "世界设定，支持 Markdown 格式"},
    {"name": "writing_style", "category": "book", "label": "写作风格", "editable": True, "editor": "markdown", "help_text": "写作风格设定，支持 Markdown 格式"},
    {"name": "book_outline", "category": "book", "label": "全书大纲", "editable": True, "editor": "markdown", "help_text": "全书整体大纲"},
    # ── context (read-only, dynamically generated) ──
    {"name": "chapter_title", "category": "context", "label": "当前章节标题", "editable": False, "editor": None, "help_text": "由当前正在生成的章节标题自动填充"},
    {"name": "chapter_summary", "category": "context", "label": "当前章节摘要", "editable": False, "editor": None, "help_text": "由当前章节的摘要自动填充"},
    {"name": "chapter_outline", "category": "context", "label": "当前章节大纲", "editable": False, "editor": None, "help_text": "由当前章节的大纲自动填充"},
    {"name": "previous_chapter_summary", "category": "context", "label": "上一章摘要", "editable": False, "editor": None, "help_text": "由上一章的摘要自动填充（由生成设置控制章节数）"},
    {"name": "volume_title", "category": "context", "label": "当前卷标题", "editable": False, "editor": None, "help_text": "由当前卷的标题自动填充"},
    {"name": "volume_description", "category": "context", "label": "当前卷描述", "editable": False, "editor": None, "help_text": "由当前卷的描述自动填充"},
    {"name": "volume_outline", "category": "context", "label": "当前卷大纲", "editable": False, "editor": None, "help_text": "由当前卷的大纲自动填充"},
    {"name": "arc_title", "category": "context", "label": "当前故事弧标题", "editable": False, "editor": None, "help_text": "由当前故事弧的标题自动填充"},
    {"name": "arc_description", "category": "context", "label": "当前故事弧描述", "editable": False, "editor": None, "help_text": "由当前故事弧的描述自动填充"},
    {"name": "event_outline", "category": "context", "label": "当前事件大纲", "editable": False, "editor": None, "help_text": "由当前事件的大纲自动填充"},
    {"name": "chapter_summaries", "category": "context", "label": "章节摘要列表", "editable": False, "editor": None, "help_text": "多章节摘要聚合列表（由生成设置控制数量）"},
    {"name": "arc_outlines", "category": "context", "label": "故事弧大纲列表", "editable": False, "editor": None, "help_text": "相关故事弧的大纲聚合列表"},
    {"name": "volume_outlines", "category": "context", "label": "卷大纲列表", "editable": False, "editor": None, "help_text": "相关卷的大纲聚合列表"},
    {"name": "current_worldview", "category": "context", "label": "当前世界观", "editable": False, "editor": None, "help_text": "由世界观设定值动态注入的上下文"},
    # ── derived (read-only, referenced) ──
    {"name": "character_profiles", "category": "derived", "label": "角色档案", "editable": False, "editor": None, "help_text": "由角色管理中的角色信息聚合生成，前往「人物」页面编辑"},
]

# Maps variable name → Book ORM attribute
BOOK_FIELD_MAP = {
    "book_name": "name",
    "book_description": "description",
    "worldview": "worldview",
    "writing_style": "writing_style",
    "book_outline": "outline",
}


@router.get("")
def get_prompt_variables(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all known prompt variables and their current values for a book."""
    book = book_repo.get_book_for_user(db, book_id, current_user.id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    variables = []
    for v in VARIABLE_REGISTRY:
        entry = {k: v[k] for k in ("name", "category", "label", "editable", "editor", "help_text")}
        if v["category"] == "book":
            field = BOOK_FIELD_MAP.get(v["name"])
            raw = str(getattr(book, field, "") or "")
            if v["name"] == "writing_style" and not raw:
                raw = _read_writing_style_default()
            entry["value"] = raw
        else:
            entry["value"] = ""
        variables.append(entry)

    return {"variables": variables}
