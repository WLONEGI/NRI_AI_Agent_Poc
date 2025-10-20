from __future__ import annotations

from pathlib import Path

from tools.file_search import file_search


def test_file_search_returns_matching_files(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    file_path = docs / "sample.txt"
    file_path.write_text("hello crystal intelligence", encoding="utf-8")

    results = file_search(query="crystal", file_types=[".txt"], root=docs)

    assert len(results) == 1
    assert results[0]["path"].endswith("sample.txt")
    assert "crystal" in results[0]["content"]


def test_file_search_handles_no_matches(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "other.txt").write_text("nothing here", encoding="utf-8")

    results = file_search(query="crystal", file_types=[".md"], root=docs)

    assert results == []
