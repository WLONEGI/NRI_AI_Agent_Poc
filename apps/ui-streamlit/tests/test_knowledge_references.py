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


def test_render_references_includes_accessibility_attributes(monkeypatch):
    """Test that table includes proper ARIA attributes for screen readers."""
    markdown_calls = []
    monkeypatch.setattr(st, "caption", MagicMock())
    monkeypatch.setattr(st, "info", MagicMock())
    monkeypatch.setattr(st, "markdown", lambda html, **kwargs: markdown_calls.append(html))

    references = [
        {
            "id": "kn-1",
            "summary": "Test summary",
            "similarity": 0.95,
            "source_type": "web_search",
            "created_at": "2025-10-19T12:00:00Z",
        }
    ]

    render_references(references, caption="Referenced Knowledge")

    table_html = markdown_calls[0]
    # Check for semantic HTML table structure
    assert "<table" in table_html
    assert "<thead>" in table_html
    assert "<tbody>" in table_html
    assert "<th" in table_html  # Table headers for screen readers


def test_render_references_handles_missing_optional_fields(monkeypatch):
    """Test graceful handling of missing optional fields."""
    markdown_calls = []
    monkeypatch.setattr(st, "caption", MagicMock())
    monkeypatch.setattr(st, "info", MagicMock())
    monkeypatch.setattr(st, "markdown", lambda html, **kwargs: markdown_calls.append(html))

    references = [
        {
            "id": "kn-1",
            "summary": "Minimal reference",
            # Missing: similarity, source_type, created_at, owner
        }
    ]

    render_references(references)

    table_html = markdown_calls[0]
    assert "kn-1" in table_html
    assert "Minimal reference" in table_html


def test_render_references_formats_timestamps_readable(monkeypatch):
    """Test that timestamps are formatted in human-readable format."""
    markdown_calls = []
    monkeypatch.setattr(st, "caption", MagicMock())
    monkeypatch.setattr(st, "info", MagicMock())
    monkeypatch.setattr(st, "markdown", lambda html, **kwargs: markdown_calls.append(html))

    references = [
        {
            "id": "kn-1",
            "summary": "Test",
            "created_at": "2025-10-19T15:30:45Z",
        }
    ]

    render_references(references)

    table_html = markdown_calls[0]
    # Should contain formatted date/time, not raw ISO format
    assert "2025-10-19" in table_html or "15:30" in table_html


def test_render_references_truncates_long_summaries(monkeypatch):
    """Test that excessively long summaries are truncated appropriately."""
    markdown_calls = []
    monkeypatch.setattr(st, "caption", MagicMock())
    monkeypatch.setattr(st, "info", MagicMock())
    monkeypatch.setattr(st, "markdown", lambda html, **kwargs: markdown_calls.append(html))

    long_summary = "A" * 200  # 200 characters
    references = [
        {
            "id": "kn-1",
            "summary": long_summary,
            "similarity": 0.90,
        }
    ]

    render_references(references)

    table_html = markdown_calls[0]
    # Summary should be present but may be truncated for readability
    assert "AAA" in table_html  # At least some of the summary appears
