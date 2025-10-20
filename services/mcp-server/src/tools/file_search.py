"""Local file search tool."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Dict


def file_search(
    *,
    query: str,
    file_types: Iterable[str],
    root: Path | None = None,
) -> List[Dict[str, str]]:
    root = root or Path("docs")
    query_lower = query.lower()
    results: List[Dict[str, str]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if file_types and path.suffix not in file_types:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if query_lower in content.lower():
            results.append(
                {
                    "path": str(path),
                    "content": content,
                    "metadata": {
                        "size": path.stat().st_size,
                    },
                }
            )
    return results
