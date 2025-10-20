from __future__ import annotations

from unittest.mock import MagicMock

import streamlit as st

from components.knowledge_references import render_references


def test_render_references_renders_table(monkeypatch):
    markdown_calls = []
    caption_calls = []
    info_calls = []

    monkeypatch.setattr(st, "markdown", lambda *args, **kwargs: markdown_calls.append((args, kwargs)))
    monkeypatch.setattr(st, "caption", lambda text: caption_calls.append(text))
    monkeypatch.setattr(st, "info", lambda text: info_calls.append(text))

    references = [
        {
            "id": "kn-1",
            "summary": "summary",
            "similarity": 0.9,
            "source_type": "agent_synthesis",
            "created_at": "2025-10-19T00:00:00Z",
            "owner": {"user_id": "user-1", "team_id": "team-1"},
        }
    ]

    render_references(references, caption="test", include_owner=True)

    assert caption_calls == ["test"]
    assert not info_calls
    table_html = markdown_calls[0][0][0]
    assert "kn-1" in table_html
    assert "agent_synthesis" in table_html
    assert "user: user-1" in table_html


def test_render_references_handles_empty(monkeypatch):
    info_calls = []
    monkeypatch.setattr(st, "info", lambda text: info_calls.append(text))
    monkeypatch.setattr(st, "caption", MagicMock())
    monkeypatch.setattr(st, "markdown", MagicMock())

    render_references([], caption="empty")

    assert info_calls == ["参照情報はありません。"]


def test_render_references_renders_multiple_rows(monkeypatch):
    markdown_calls = []
    monkeypatch.setattr(st, "info", MagicMock())
    monkeypatch.setattr(st, "caption", MagicMock())
    monkeypatch.setattr(st, "markdown", lambda html, unsafe_allow_html: markdown_calls.append(html))

    references = [
        {
            "id": "kn-1",
            "summary": "first",
            "similarity": 0.9,
            "source_type": "agent_synthesis",
            "created_at": "2025-10-19T00:00:00Z",
        },
        {
            "id": "kn-2",
            "summary": "second",
            "similarity": 0.8,
            "source_type": "file_search",
            "created_at": "2025-10-19T00:01:00Z",
        },
    ]

    render_references(references)

    assert markdown_calls, "Expected markdown to be rendered"
    table_html = markdown_calls[0]
    assert table_html.count("<tr>") == 2 + 1  # header row + two data rows
    assert "kn-1" in table_html and "kn-2" in table_html
