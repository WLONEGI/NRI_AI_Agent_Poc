from __future__ import annotations

import os
from typing import Any, Dict, List

import requests
import streamlit as st

from components.knowledge_references import render_references


API_BASE_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000").rstrip("/")
QUERY_API_URL = f"{API_BASE_URL}/api/query"
SEARCH_API_URL = f"{API_BASE_URL}/api/knowledge/search"
DEFAULT_CHANNELS = ["file_search", "web_search", "query_team_knowledge"]


st.set_page_config(page_title="Crystal Intelligence PoC")
st.markdown(
    """
    <style>
    .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        border: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Crystal Intelligence Knowledge Builder")
st.caption("LangGraphエージェントの応答を保存し、ベクトル検索で参照ナレッジを確認できます。")


if "current_user" not in st.session_state:
    st.session_state.current_user = "user-1"
if "team_id" not in st.session_state:
    st.session_state.team_id = "team-demo"
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "search_executed" not in st.session_state:
    st.session_state.search_executed = False

status_region = st.empty()
aria_region = st.empty()


def announce(message: str) -> None:
    aria_region.markdown(f"<div class='sr-only' role='status' aria-live='polite'>{message}</div>", unsafe_allow_html=True)


with st.sidebar:
    st.header("ユーザー設定")
    st.session_state.current_user = st.text_input("ユーザーID", value=st.session_state.current_user)
    st.session_state.team_id = st.text_input("チームID", value=st.session_state.team_id)
    use_file_search = st.checkbox("file_search を利用", value=True)
    use_web_search = st.checkbox("web_search を利用", value=True)
    use_team_knowledge = st.checkbox("query_team_knowledge を利用", value=True)


with st.form("query_form", clear_on_submit=False):
    prompt = st.text_area(
        "質問内容",
        height=180,
        placeholder="例: 顧客サポート向けのベストプラクティスをまとめて",
        help="Shift+Enter で改行、Enter で送信",
    )
    metadata_team = st.text_input("メタデータ: team_id", value=st.session_state.team_id, key="metadata_team")
    submitted = st.form_submit_button("送信", use_container_width=True)

channels = []
if use_file_search:
    channels.append("file_search")
if use_web_search:
    channels.append("web_search")
if use_team_knowledge:
    channels.append("query_team_knowledge")
if not channels:
    channels = DEFAULT_CHANNELS

if submitted:
    if not prompt.strip():
        status_region.warning("質問内容を入力してください。")
        announce("質問内容が空のため送信に失敗しました。")
    else:
        status_region.info("エージェントに問い合わせ中です…")
        announce("エージェントに問い合わせ中です。")
        payload: Dict[str, Any] = {
            "user_id": st.session_state.current_user or "user-1",
            "query": prompt,
            "channels": channels,
            "metadata": {"team_id": metadata_team},
            "attachments": [],
        }
        try:
            response = requests.post(QUERY_API_URL, json=payload, timeout=20)
            response.raise_for_status()
            data = response.json()
            st.session_state.last_result = data
            status_region.success("ナレッジを保存しました。")
            announce("ナレッジの保存に成功しました。")

            try:
                search_resp = requests.get(
                    SEARCH_API_URL,
                    params={
                        "query": prompt,
                        "user_id": st.session_state.current_user,
                        "top_k": 100,
                    },
                    timeout=10,
                )
                search_resp.raise_for_status()
                st.session_state.search_results = search_resp.json().get("results", [])
            except requests.RequestException:
                st.session_state.search_results = []
            finally:
                st.session_state.search_executed = True
        except requests.RequestException as exc:
            st.session_state.last_result = None
            status_region.error(f"保存に失敗しました: {exc}")
            announce("ナレッジの保存に失敗しました。")
            st.session_state.search_results = []
            st.session_state.search_executed = False


if st.session_state.last_result:
    result = st.session_state.last_result
    st.subheader("エージェント応答", anchor="agent-response")
    st.write(result.get("answer", ""))
    st.caption(f"Knowledge ID: {result.get('knowledge_id')} (Latency: {result.get('latency_ms', 0):.0f} ms)")

    st.subheader("参照したナレッジ")
    render_references(result.get("references", []), caption="エージェント応答で利用したナレッジ")

if st.session_state.search_executed:
    st.subheader("検索結果")
    render_references(
        st.session_state.search_results,
        caption="個人・チームナレッジ検索結果",
        include_owner=True,
    )
