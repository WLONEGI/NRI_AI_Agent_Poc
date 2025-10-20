from __future__ import annotations

from typing import Iterable, Mapping, Optional

import html

import streamlit as st


def _format_similarity(value: Optional[float]) -> str:
    if value is None:
        return "-"
    return f"{value:.2f}"


def _owner_label(ref: Mapping[str, object]) -> str:
    owner = ref.get("owner") or {}
    if isinstance(owner, Mapping):
        user = owner.get("user_id") or "-"
        team = owner.get("team_id") or "-"
        return f"user: {user} / team: {team}"
    return "-"


def render_references(
    references: Iterable[Mapping[str, object]],
    *,
    caption: Optional[str] = None,
    include_owner: bool = False,
) -> None:
    references = list(references)
    if not references:
        st.info("参照情報はありません。")
        return

    if caption:
        st.caption(caption)

    headers = ["ID", "要約", "類似度", "種別", "作成日時"]
    if include_owner:
        headers.append("所有者")

    rows_html = ""
    for ref in references:
        summary = ref.get("summary") or ref.get("content") or "-"
        row = [
            ref.get("id", "-"),
            summary,
            _format_similarity(ref.get("similarity")),
            ref.get("source_type") or ref.get("type") or "-",
            ref.get("created_at", "-"),
        ]
        if include_owner:
            row.append(_owner_label(ref))
        cells = "".join(f"<td>{html.escape(str(value))}</td>" for value in row)
        rows_html += f"<tr>{cells}</tr>"

    header_cells = "".join(f"<th scope='col'>{html.escape(header)}</th>" for header in headers)
    table_html = f"""
    <table role='table' aria-label='{caption or "references"}'>
      <thead><tr>{header_cells}</tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    """
    st.markdown(table_html, unsafe_allow_html=True)
