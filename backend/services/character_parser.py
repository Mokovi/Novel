"""Parse AI-generated character markdown into structured dicts.

Never raises exceptions — returns [] on any parse failure.
"""

import re
from typing import Any

_FIELD_MAP: dict[str, str] = {
    "角色类型": "role_type",
    "状态": "status",
    "别名": "aliases",
    "描述": "description",
    "外貌": "appearance",
    "性格": "personality",
    "背景": "background",
    "目标": "goals",
}

# Match: `- **字段名**：值` or `- **字段名**: 值` or `- 字段名: 值`
_FIELD_RE = re.compile(r"^\s*-\s*(?:\*\*)?(.+?)(?:\*\*)?\s*[:：]\s*(.*)$")


def parse_character_markdown(text: str) -> list[dict[str, Any]]:
    """Parse AI-generated markdown into a list of character dicts.

    Each character block is delimited by a ``## `` heading.  Text before the
    first ``## `` is discarded.  Fields are extracted by matching known Chinese
    labels mapped to English schema keys.
    """
    if not text or not text.strip():
        return []

    blocks = re.split(r"(?=^## )", text, flags=re.MULTILINE)
    results: list[dict[str, Any]] = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        char: dict[str, Any] = {}

        lines = block.splitlines()
        for i, line in enumerate(lines):
            if line.startswith("## "):
                name = line[3:].strip()
                if name:
                    char["name"] = name
                continue
            m = _FIELD_RE.match(line)
            if m:
                label, value = m.group(1).strip(), m.group(2).strip()
                key = _FIELD_MAP.get(label)
                if key:
                    char[key] = value

        if char.get("name"):
            results.append(char)

    return results
