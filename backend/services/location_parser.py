"""Parse AI-generated location markdown into structured dicts.

Never raises exceptions — returns [] on any parse failure.
"""

import re
from typing import Any

# Match: `- **字段名**：值` or `- **字段名**: 值` or `- 字段名: 值`
_FIELD_RE = re.compile(r"^\s*-\s*(?:\*\*)?(.+?)(?:\*\*)?\s*[:：]\s*(.*)$")

_FIELD_MAP: dict[str, str] = {
    "地点类型": "location_type",
    "描述": "description",
}


def parse_location_markdown(text: str) -> list[dict[str, Any]]:
    """Parse AI-generated markdown into a list of location dicts.

    Each location block is delimited by a ``## `` heading.  Text before the
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

        loc: dict[str, Any] = {}

        lines = block.splitlines()
        for i, line in enumerate(lines):
            if line.startswith("## "):
                name = line[3:].strip()
                if name:
                    loc["name"] = name
                continue
            m = _FIELD_RE.match(line)
            if m:
                label, value = m.group(1).strip(), m.group(2).strip()
                key = _FIELD_MAP.get(label)
                if key:
                    loc[key] = value

        if loc.get("name"):
            results.append(loc)

    return results
