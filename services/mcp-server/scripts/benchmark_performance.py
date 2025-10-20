"""Performance benchmark runner for NF-005 latency targets.

This script measures knowledge persistence latency and knowledge search latency
against the targets defined in the specification:

* Knowledge save end-to-end latency <= 2.0 seconds
* Top-100 vector search latency <= 1.5 seconds

The script is intended for local/CI benchmarking with minimal dependencies. By
default it persists synthetic knowledge records (with deterministic embeddings)
and optionally runs search queries. Results are emitted as JSON to stdout or the
specified output file.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.settings import get_settings
from infra.neo4j_client import close_driver, get_driver
from knowledge.models import KnowledgeRecord, Provenance
from knowledge.repository import KnowledgeRepository
from knowledge.search_service import KnowledgeSearchService

DEFAULT_ITERATIONS = 5
SAVE_TARGET_MS = 2000  # 2 seconds
SEARCH_TARGET_MS = 1500  # 1.5 seconds


@dataclass
class IterationResult:
    iteration: int
    save_ms: float
    search_ms: Optional[float]
    save_status: str
    search_status: Optional[str]
    error: Optional[str] = None


@dataclass
class BenchmarkSummary:
    timestamp: str
    iterations: int
    save_avg_ms: float
    save_p95_ms: float
    search_avg_ms: Optional[float]
    search_p95_ms: Optional[float]
    save_target_ms: float
    search_target_ms: float
    configuration: Dict[str, Any]


def _create_sample_record(iteration: int) -> tuple[KnowledgeRecord, Provenance]:
    now = datetime.utcnow().isoformat()
    knowledge_id = f"bench-{uuid.uuid4()}"
    record = KnowledgeRecord(
        knowledge_id=knowledge_id,
        knowledge_type="personal",
        content=f"Benchmark knowledge payload #{iteration}",
        category="benchmark",
        hierarchy_level=1,
        owner_id="benchmark-user",
        team_id="benchmark-team",
        confidence=0.5,
        embedding=[0.0] * 10,  # deterministic placeholder embedding
        created_at=now,
        tags=["benchmark", "nf005"],
    )
    provenance = Provenance(
        query_id=f"bench-query-{iteration}",
        agent_execution_id=f"bench-agent-{iteration}",
        tool_execution_id=f"bench-tool-{iteration}",
        data_source_id=f"bench-source-{iteration}",
        extracted_content_id=f"bench-content-{iteration}",
    )
    return record, provenance


def run_benchmark(*, iterations: int, include_search: bool) -> tuple[List[IterationResult], BenchmarkSummary]:
    driver = get_driver()
    repo = KnowledgeRepository(driver)
    search_service = KnowledgeSearchService(driver)

    iteration_results: List[IterationResult] = []
    save_timings: List[float] = []
    search_timings: List[float] = []

    for i in range(1, iterations + 1):
        record, provenance = _create_sample_record(i)
        result = IterationResult(iteration=i, save_ms=0.0, search_ms=None, save_status="pending", search_status=None)
        try:
            start = time.perf_counter()
            repo.save(record, provenance)
            save_elapsed = (time.perf_counter() - start) * 1000
            result.save_ms = save_elapsed
            result.save_status = "PASS" if save_elapsed <= SAVE_TARGET_MS else "FAIL"
            save_timings.append(save_elapsed)
        except Exception as exc:  # pragma: no cover - safeguards for benchmark runtime
            result.error = f"save failed: {exc}"
            result.save_status = "ERROR"

        if include_search:
            try:
                start = time.perf_counter()
                search_results = search_service.search(query="benchmark", user_id="benchmark-user")
                search_elapsed = (time.perf_counter() - start) * 1000
                result.search_ms = search_elapsed
                result.search_status = "PASS" if search_elapsed <= SEARCH_TARGET_MS else "FAIL"
                search_timings.append(search_elapsed)
                # ensure results consumed to avoid lazy generators
                _ = len(search_results)
            except Exception as exc:  # pragma: no cover
                result.error = (result.error + "; " if result.error else "") + f"search failed: {exc}"
                result.search_status = "ERROR"

        iteration_results.append(result)

    summary = BenchmarkSummary(
        timestamp=datetime.utcnow().isoformat(),
        iterations=len(iteration_results),
        save_avg_ms=statistics.fmean(save_timings) if save_timings else float("nan"),
        save_p95_ms=_percentile(save_timings, 95) if save_timings else float("nan"),
        search_avg_ms=statistics.fmean(search_timings) if search_timings else None,
        search_p95_ms=_percentile(search_timings, 95) if search_timings else None,
        save_target_ms=SAVE_TARGET_MS,
        search_target_ms=SEARCH_TARGET_MS,
        configuration={
            "include_search": include_search,
            "neo4j_uri": get_settings().neo4j_uri,
        },
    )

    close_driver()
    return iteration_results, summary


def _percentile(values: List[float], percentile: float) -> float:
    if not values:
        return float("nan")
    sorted_values = sorted(values)
    index = int(round((percentile / 100) * (len(sorted_values) - 1)))
    return sorted_values[index]


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run NF-005 performance benchmarks")
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS, help="Number of benchmark iterations")
    parser.add_argument(
        "--include-search",
        action="store_true",
        help="Measure search latency in addition to persistence latency",
    )
    parser.add_argument("--output", type=Path, help="Optional path to write benchmark results as JSON")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    iterations = max(1, args.iterations)
    iteration_results, summary = run_benchmark(iterations=iterations, include_search=args.include_search)

    payload = {
        "summary": asdict(summary),
        "iterations": [asdict(record) for record in iteration_results],
    }

    output_text = json.dumps(payload, ensure_ascii=False, indent=2)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output_text, encoding="utf-8")
    else:
        print(output_text)

    # Determine exit code based on results
    failure_detected = any(result.save_status in {"FAIL", "ERROR"} for result in iteration_results)
    if args.include_search:
        failure_detected = failure_detected or any(
            (result.search_status in {"FAIL", "ERROR"}) for result in iteration_results
        )

    return 1 if failure_detected else 0


if __name__ == "__main__":  # pragma: no cover - entry point
    sys.exit(main())
