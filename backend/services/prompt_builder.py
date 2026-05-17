"""Prompt template engine — load, parse, fill, and estimate."""

import re
from pathlib import Path
from typing import Optional

import yaml
from loguru import logger

from backend.config import DATA_DIR

TEMPLATES_DIR = DATA_DIR / "templates"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_VAR_PATTERN = re.compile(r"\{\{(\w+)\}\}")
_BLOCK_PATTERN = re.compile(
    r"\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}", re.DOTALL
)


def _parse_template_file(filepath: Path) -> dict:
    """Parse a .md file with YAML frontmatter into a structured dict.

    Returns
    -------
    dict with keys: frontmatter (dict), body (str), file_name (str)
    """
    content = filepath.read_text(encoding="utf-8")
    file_name = filepath.name

    if not content.startswith("---"):
        return {"frontmatter": {}, "body": content.strip(), "file_name": file_name}

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {"frontmatter": {}, "body": content.strip(), "file_name": file_name}

    raw_frontmatter = parts[1].strip()
    try:
        frontmatter = yaml.safe_load(raw_frontmatter) or {}
    except yaml.YAMLError as e:
        logger.warning("Failed to parse YAML frontmatter in {}: {}", file_name, e)
        frontmatter = {}

    body = parts[2].strip()
    return {"frontmatter": frontmatter, "body": body, "file_name": file_name}


def _serialize_template(frontmatter: dict, body: str) -> str:
    """Serialize frontmatter dict + body back into a .md template string."""
    header = yaml.safe_dump(frontmatter, allow_unicode=True, default_flow_style=False).strip()
    return f"---\n{header}\n---\n\n{body}\n"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_template(task_type: str) -> dict:
    """Find and parse the default template for *task_type*.

    Scans ``data/templates/`` for a ``.md`` file whose frontmatter
    matches ``task_type`` and has ``is_default: true``.

    Raises
    ------
    FileNotFoundError
        If the templates directory does not exist.
    ValueError
        If no default template is found for the given task type.
    """
    if not TEMPLATES_DIR.exists():
        raise FileNotFoundError(f"Templates directory not found: {TEMPLATES_DIR}")

    for f in sorted(TEMPLATES_DIR.iterdir()):
        if f.suffix != ".md":
            continue
        tmpl = _parse_template_file(f)
        fm = tmpl["frontmatter"]
        if fm.get("task_type") == task_type and fm.get("is_default") is True:
            return tmpl

    raise ValueError(f"No default template found for task type: {task_type}")


def build_prompt(template: dict, variables: dict) -> str:
    """Fill ``{{variable}}`` placeholders in the template body.

    * Required variables: if a variable listed in
      ``frontmatter.required_variables`` is missing or empty, a
      ``ValueError`` is raised.
    * Optional block syntax ``{{#var}}...{{/var}}``: if the variable is
      falsy/absent the entire block is removed; otherwise the block tags
      themselves are stripped, leaving the inner content.
    * Unknown ``{{var}}`` placeholders (not in *variables* and not
      required) are replaced with an empty string.
    """
    body = template["body"]
    fm = template.get("frontmatter", {})

    # ---- required-var validation -------------------------------------------
    required = fm.get("required_variables") or []
    missing = [v for v in required if not variables.get(v)]
    if missing:
        raise ValueError(
            f"Missing required template variable(s): {', '.join(missing)}"
        )

    # ---- conditional blocks ------------------------------------------------
    def _replace_block(m: re.Match) -> str:
        var_name = m.group(1)
        inner = m.group(2)
        if variables.get(var_name):
            return inner
        return ""

    body = _BLOCK_PATTERN.sub(_replace_block, body)

    # ---- simple variable substitution --------------------------------------
    def _replace_var(m: re.Match) -> str:
        var_name = m.group(1)
        return variables.get(var_name) or ""

    body = _VAR_PATTERN.sub(_replace_var, body)

    # Clean up excessive blank lines left after block removal
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return body


def estimate_tokens(text: str) -> int:
    """Estimate token count from character length (chars / 3.5)."""
    return max(1, round(len(text) / 3.5))


# ---------------------------------------------------------------------------
# File-system CRUD helpers (used by the templates router)
# ---------------------------------------------------------------------------


def list_template_files() -> list[dict]:
    """Return metadata for every ``.md`` file in ``data/templates/``."""
    if not TEMPLATES_DIR.exists():
        return []

    results = []
    for f in sorted(TEMPLATES_DIR.iterdir()):
        if f.suffix != ".md":
            continue
        tmpl = _parse_template_file(f)
        fm = tmpl["frontmatter"]
        version = fm.get("version")
        if version is not None:
            version = str(version)
        results.append(
            {
                "file_name": tmpl["file_name"],
                "task_type": fm.get("task_type"),
                "name": fm.get("name"),
                "is_default": fm.get("is_default", False),
                "version": version,
                "description": fm.get("description"),
            }
        )
    return results


def read_template_file(file_name: str) -> Optional[dict]:
    """Read a single template file by name, returning full parsed content."""
    filepath = TEMPLATES_DIR / file_name
    if not filepath.exists() or not filepath.is_file():
        return None
    return _parse_template_file(filepath)


def write_template_file(file_name: str, frontmatter: dict, body: str) -> dict:
    """Write (create or overwrite) a template file on disk.

    *file_name* must end with ``.md``.
    """
    if not file_name.endswith(".md"):
        file_name += ".md"

    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    filepath = TEMPLATES_DIR / file_name
    content = _serialize_template(frontmatter, body)
    filepath.write_text(content, encoding="utf-8")
    logger.info("Template saved: {}", filepath)
    return _parse_template_file(filepath)


def delete_template_file(file_name: str) -> bool:
    """Delete a template file.  Returns ``True`` if deleted, ``False`` if not found.

    Default templates (``is_default: true``) cannot be deleted.
    """
    filepath = TEMPLATES_DIR / file_name
    if not filepath.exists():
        return False

    # Read frontmatter to check is_default
    tmpl = _parse_template_file(filepath)
    if tmpl["frontmatter"].get("is_default") is True:
        raise ValueError(f"Cannot delete default template: {file_name}")

    filepath.unlink()
    logger.info("Template deleted: {}", filepath)
    return True
