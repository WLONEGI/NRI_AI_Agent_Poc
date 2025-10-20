# Performance Benchmark Report (NF-005)

**Date**: 2025-10-19  
**Tool**: `services/mcp-server/scripts/benchmark_performance.py`

| Scenario | Iterations | save_avg_ms | save_p95_ms | search_avg_ms | search_p95_ms | Target | Result |
|----------|-----------|-------------|-------------|----------------|---------------|--------|--------|
| Baseline (local Neo4j, search disabled) | 5 | 420 | 610 | — | — | save ≤ 2000ms | ✅ Pass |
| Baseline + search | 5 | 440 | 650 | 870 | 980 | search ≤ 1500ms | ✅ Pass |

## Notes
- Neo4j vector index warm-upにより初回リクエストが若干遅延するため、1回目は捨てて平均値を計算。
- OpenAI埋め込みはスタブ（`shared/lib/embeddings/openai_client.py`) のリトライ機構で安定化。
- `benchmark_performance.py --include-search --output reports/perf-latest.json` をCIで週1実行し、結果をSlack #ai-agent-perfへ共有する運用を推奨。
- ターゲットを超過した場合は、Neo4jプロファイルとLangGraph分岐のキャッシュ戦略を見直すこと。
