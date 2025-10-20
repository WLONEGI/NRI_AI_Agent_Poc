"""LangGraph-driven agent orchestration leveraging LangChain + MCP tools."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Sequence
from uuid import uuid4

try:  # pragma: no cover - optional dependency
    from langchain_core.messages import AIMessage  # type: ignore
except ImportError:  # pragma: no cover - fallback shim
    class AIMessage:  # type: ignore[override]
        """Minimal stand-in for langchain_core.messages.AIMessage."""

        def __init__(self, content: str) -> None:
            self.content = content


try:  # pragma: no cover - optional dependency
    from langchain_core.prompts import ChatPromptTemplate  # type: ignore
except ImportError:  # pragma: no cover - fallback shim
    class _PromptMessage:
        def __init__(self, content: str) -> None:
            self.content = content

    class ChatPromptTemplate:  # type: ignore[override]
        def __init__(self, messages):
            self._messages = messages

        @classmethod
        def from_messages(cls, messages):  # type: ignore[override]
            return cls(messages)

        def format_messages(self, **kwargs):
            formatted = []
            for role, template in self._messages:
                formatted.append(_PromptMessage(template.format(**kwargs)))
            return formatted


try:  # pragma: no cover - optional dependency
    from langchain_openai import ChatOpenAI  # type: ignore
except ImportError:  # pragma: no cover - fallback shim
    from openai import OpenAI

    class ChatOpenAI:  # type: ignore[override]
        def __init__(self, model: str, temperature: float = 0.0) -> None:
            self._client = OpenAI()
            self._model = model
            self._temperature = temperature

        def invoke(self, messages):
            prompt = "\n\n".join(getattr(msg, "content", str(msg)) for msg in messages)
            response = self._client.responses.create(
                model=self._model,
                input=prompt,
                temperature=self._temperature,
            )
            return AIMessage(content=response.output_text)


try:  # pragma: no cover - optional dependency
    from langgraph.graph import END, StateGraph  # type: ignore
except ImportError:  # pragma: no cover - fallback shim
    END = "__END__"

    class _CompiledGraph:
        def __init__(self, nodes, edges, entry_point):
            self._nodes = nodes
            self._edges = edges
            self._entry_point = entry_point

        def invoke(self, state):
            current = self._entry_point
            result = state
            while current and current in self._nodes:
                result = self._nodes[current](result)
                current = self._edges.get(current, END)
                if current == END:
                    break
            return result

    class StateGraph:  # type: ignore[override]
        def __init__(self, _state_type):
            self._nodes = {}
            self._edges = {}
            self._entry_point = None

        def add_node(self, name, func):
            self._nodes[name] = func

        def add_edge(self, start, end):
            self._edges[start] = end

        def set_entry_point(self, name):
            self._entry_point = name

        def compile(self):
            return _CompiledGraph(self._nodes, self._edges, self._entry_point)


from typing_extensions import TypedDict

from tools.file_search import file_search
from tools.query_team_knowledge import query_team_knowledge
from tools.web_search import web_search


LOGGER = logging.getLogger(__name__)
DEFAULT_CHANNELS = ["file_search", "web_search", "query_team_knowledge"]
REFERENCE_MAX_SUMMARY = 160


class AgentState(TypedDict, total=False):
    """Shared state propagated through the LangGraph workflow."""

    query: str
    user_id: str
    channels: List[str]
    metadata: Dict[str, str]
    attachments: List[Dict[str, str]]
    file_results: List[Dict[str, object]]
    web_results: List[Dict[str, object]]
    knowledge_results: List[Dict[str, object]]
    tool_traces: List[Dict[str, object]]
    references: List[Dict[str, object]]
    context_sections: List[str]
    answer: str
    knowledge: Dict[str, object]
    provenance: Dict[str, str]
    provenance_chain: List[Dict[str, object]]


def _truncate(text: str, limit: int = REFERENCE_MAX_SUMMARY) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _append_trace(state: AgentState, *, name: str, tool_input: Dict[str, object], outputs: Dict[str, object]) -> AgentState:
    traces = list(state.get("tool_traces", []))
    traces.append({"name": name, "input": tool_input, "output": outputs})
    new_state = dict(state)
    new_state["tool_traces"] = traces
    return new_state  # type: ignore[return-value]


def _collect_file_context(results: Iterable[Dict[str, object]], now: str) -> tuple[str, List[Dict[str, object]]]:
    summaries = []
    references: List[Dict[str, object]] = []
    for item in results:
        path = str(item.get("path"))
        content = str(item.get("content") or "")
        summaries.append(f"- {path}")
        references.append(
            {
                "id": path,
                "source_type": "file_search",
                "summary": _truncate(content),
                "created_at": now,
            }
        )
    section = "\n".join(summaries)
    if section:
        section = "File search hits:\n" + section
    return section, references


def _collect_web_context(results: Iterable[Dict[str, object]], now: str) -> tuple[str, List[Dict[str, object]]]:
    summaries = []
    references: List[Dict[str, object]] = []
    for item in results:
        url = str(item.get("url"))
        content = str(item.get("content") or "")
        summaries.append(f"- {url}")
        references.append(
            {
                "id": url,
                "source_type": "web_search",
                "summary": _truncate(content),
                "created_at": now,
            }
        )
    section = "\n".join(summaries)
    if section:
        section = "Web search insights:\n" + section
    return section, references


def _collect_knowledge_context(results: Iterable[Dict[str, object]], now: str) -> tuple[str, List[Dict[str, object]]]:
    summaries = []
    references: List[Dict[str, object]] = []
    for item in results:
        knowledge_id = str(item.get("id"))
        content = str(item.get("content") or "")
        owner = {
            "user_id": item.get("owner_id"),
            "team_id": item.get("owner_team_id"),
        }
        summaries.append(f"- Knowledge {knowledge_id} (similarity={item.get('similarity', 0):.2f})")
        references.append(
            {
                "id": knowledge_id,
                "source_type": "team_knowledge" if item.get("type") == "team" else "personal_knowledge",
                "summary": _truncate(content),
                "similarity": item.get("similarity"),
                "owner": owner,
                "created_at": now,
            }
        )
    section = "\n".join(summaries)
    if section:
        section = "Knowledge graph context:\n" + section
    return section, references


def _prepare_initial_state(
    *,
    query: str,
    user_id: str,
    metadata: Dict[str, str],
    channels: Sequence[str],
    attachments: Sequence[Dict[str, str]],
) -> AgentState:
    return {
        "query": query,
        "user_id": user_id,
        "metadata": dict(metadata),
        "channels": list(channels),
        "attachments": [dict(item) for item in attachments],
        "tool_traces": [],
        "references": [],
        "context_sections": [],
    }


def _build_graph(llm) -> StateGraph:
    graph: StateGraph = StateGraph(AgentState)

    def file_search_node(state: AgentState) -> AgentState:
        channels = state.get("channels") or DEFAULT_CHANNELS
        if "file_search" not in channels:
            return state
        try:
            results = file_search(query=state["query"], file_types=[".md", ".txt", ".mdx"])
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.warning("file_search tool failed", exc_info=exc)
            results = []
        now = datetime.now(timezone.utc).isoformat()
        section, refs = _collect_file_context(results[:5], now)
        new_state = dict(state)
        new_state["file_results"] = results
        sections = list(state.get("context_sections", []))
        if section:
            sections.append(section)
        new_state["context_sections"] = sections
        references = list(state.get("references", []))
        references.extend(refs)
        new_state["references"] = references
        new_state = _append_trace(
            new_state,
            name="file_search",
            tool_input={"query": state["query"], "file_types": [".md", ".txt", ".mdx"]},
            outputs={"hits": [r["id"] for r in refs]},
        )
        return new_state  # type: ignore[return-value]

    def web_search_node(state: AgentState) -> AgentState:
        channels = state.get("channels") or DEFAULT_CHANNELS
        if "web_search" not in channels:
            return state
        try:
            results = web_search(query=state["query"])
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.warning("web_search tool failed", exc_info=exc)
            results = []
        now = datetime.now(timezone.utc).isoformat()
        section, refs = _collect_web_context(results[:3], now)
        new_state = dict(state)
        new_state["web_results"] = results
        sections = list(state.get("context_sections", []))
        if section:
            sections.append(section)
        new_state["context_sections"] = sections
        references = list(state.get("references", []))
        references.extend(refs)
        new_state["references"] = references
        new_state = _append_trace(
            new_state,
            name="web_search",
            tool_input={"query": state["query"]},
            outputs={"urls": [r["id"] for r in refs]},
        )
        return new_state  # type: ignore[return-value]

    def knowledge_search_node(state: AgentState) -> AgentState:
        channels = state.get("channels") or DEFAULT_CHANNELS
        if "query_team_knowledge" not in channels:
            return state
        try:
            results = query_team_knowledge(query=state["query"], user_id=state["user_id"])
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.warning("query_team_knowledge tool failed", exc_info=exc)
            results = []
        now = datetime.now(timezone.utc).isoformat()
        section, refs = _collect_knowledge_context(results[:10], now)
        new_state = dict(state)
        new_state["knowledge_results"] = results
        sections = list(state.get("context_sections", []))
        if section:
            sections.append(section)
        new_state["context_sections"] = sections
        references = list(state.get("references", []))
        references.extend(refs)
        new_state["references"] = references
        new_state = _append_trace(
            new_state,
            name="query_team_knowledge",
            tool_input={"query": state["query"], "user_id": state["user_id"]},
            outputs={"knowledge_ids": [r["id"] for r in refs]},
        )
        return new_state  # type: ignore[return-value]

    def synthesise_node(state: AgentState) -> AgentState:
        sections = list(state.get("context_sections", []))
        if state.get("attachments"):
            attachments_block = "\n".join(f"- {item.get('path', 'attachment')}" for item in state["attachments"])
            sections.append(f"Attachments provided:\n{attachments_block}")
        context = "\n\n".join(filter(None, sections)) or "No supporting evidence collected."

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an AI assistant that produces knowledge entries with provenance and clear summaries.",
                ),
                (
                    "human",
                    "Question: {question}\n\nContext:\n{context}\n\nProvide a concise answer summarising key insights.",
                ),
            ]
        )
        messages = prompt.format_messages(question=state["query"], context=context)
        try:
            llm_response = llm.invoke(messages)
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.warning("LLM invocation failed", exc_info=exc)
            llm_response = AIMessage(content="Unable to generate answer at this time. Please retry later.")

        if isinstance(llm_response, AIMessage):
            answer = llm_response.content
        elif hasattr(llm_response, "content"):
            answer = str(llm_response.content)
        else:
            answer = str(llm_response)

        now = datetime.now(timezone.utc).isoformat()
        knowledge_id = f"kn-{uuid4()}"
        query_id = f"q-{uuid4()}"
        agent_execution_id = f"ae-{uuid4()}"
        tool_execution_id = f"te-{uuid4()}"
        data_source_id = f"ds-{uuid4()}"
        extracted_content_id = f"ec-{uuid4()}"
        team_id = state.get("metadata", {}).get("team_id")

        knowledge = {
            "id": knowledge_id,
            "type": "personal",
            "content": answer,
            "category": state.get("metadata", {}).get("category"),
            "hierarchy_level": 1,
            "owner_id": state["user_id"],
            "team_id": team_id,
            "confidence": 0.7,
            "embedding": None,
            "created_at": now,
            "tags": list(state.get("channels") or DEFAULT_CHANNELS),
        }

        provenance = {
            "query_id": query_id,
            "agent_execution_id": agent_execution_id,
            "tool_execution_id": tool_execution_id,
            "data_source_id": data_source_id,
            "extracted_content_id": extracted_content_id,
        }

        synthesis_reference = {
            "id": knowledge_id,
            "source_type": "agent_synthesis",
            "summary": _truncate(answer),
            "owner": {"user_id": state["user_id"], "team_id": team_id},
            "created_at": now,
        }

        references = state.get("references", []) or []
        provenance_chain = [synthesis_reference, *references]

        new_state = dict(state)
        new_state["answer"] = answer
        new_state["knowledge"] = knowledge
        new_state["provenance"] = provenance
        new_state["provenance_chain"] = provenance_chain
        if not references:
            new_state["references"] = [synthesis_reference]
        return new_state  # type: ignore[return-value]

    graph.add_node("file_search", file_search_node)
    graph.add_node("web_search", web_search_node)
    graph.add_node("knowledge_search", knowledge_search_node)
    graph.add_node("synthesise", synthesise_node)

    graph.set_entry_point("file_search")
    graph.add_edge("file_search", "web_search")
    graph.add_edge("web_search", "knowledge_search")
    graph.add_edge("knowledge_search", "synthesise")
    graph.add_edge("synthesise", END)

    return graph.compile()


def _resolve_llm(llm: Optional[object]) -> object:
    if llm is not None:
        return llm
    return ChatOpenAI(model="gpt-5-mini", temperature=0.2)


def run_agent(
    *,
    query: str,
    user_id: str,
    channels: List[str],
    metadata: Dict[str, str],
    attachments: List[Dict[str, str]],
    llm: Optional[object] = None,
    graph: Optional[StateGraph] = None,
) -> Dict[str, object]:
    """Execute the LangGraph workflow and return the agent payload."""

    resolved_llm = _resolve_llm(llm)
    initial_channels = channels or DEFAULT_CHANNELS
    state = _prepare_initial_state(
        query=query,
        user_id=user_id,
        metadata=metadata,
        channels=initial_channels,
        attachments=attachments,
    )

    compiled_graph = graph or _build_graph(resolved_llm)
    result_state = compiled_graph.invoke(state)

    answer = result_state.get("answer", "")
    knowledge = result_state.get("knowledge", {})
    provenance = result_state.get("provenance", {})
    provenance_chain = result_state.get("provenance_chain", [])
    references = result_state.get("references", [])
    tool_traces = result_state.get("tool_traces", [])

    return {
        "answer": answer,
        "knowledge": knowledge,
        "provenance": provenance,
        "provenance_chain": provenance_chain,
        "references": references,
        "retries": 0,
        "tool_traces": tool_traces,
    }
