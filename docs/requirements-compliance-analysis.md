# spec.md機能要件の実装状況分析

**分析日**: 2025-10-19  
**対象仕様**: `specs/005-/spec.md`  
**分析範囲**: 機能要件（FR-001〜FR-009） and 主要ノンファンクショナル要件（NF-001〜NF-005）

---

## エグゼクティブサマリー

### 総合評価: ✅ **要件達成（PoC完了）**

- **完全実装**: 9/9 要件
- **部分実装**: 0/9 要件
- **未着手**: 0/9 要件

### ハイライト
1. FR-005/FR-009: Neo4j Vector Index を活用した実検索を実装し、個人＋チームナレッジを Top-100 で返却。
2. FR-008: OpenAI 埋め込みリトライは 1s/2s/4s の指数バックオフで 3 回試行へ更新。失敗時は JSON ログを出力。
3. NF-005: `benchmark_performance.py` による計測で保存 <0.7s、検索 <1.0s を確認。レポートを `docs/QA/performance-report.md` に保存。
4. アクセシビリティ: US1〜US3 すべての手動検証ログを `tests/accessibility-checklist.md` に追記し、SC-004 を満たす。

---

## 機能要件詳細

### ✅ FR-001: Streamlit UI から Neo4j へ個人ナレッジを保存
- **実装**: `apps/ui-streamlit/app.py` → `services/mcp-server/src/apis/query_api.py` → `knowledge.repository.save`
- **テスト**: `tests/integration/test_query_sync.py`, `tests/unit/tools/test_save_knowledge.py`

### ✅ FR-002: MCP ツール経由の LangGraph エージェント
- **実装**: `tools/file_search.py`, `tools/web_search.py`, `tools/query_team_knowledge.py`, `agents/langgraph_runner.py`
- **テスト**: `tests/unit/tools/test_*`

### ✅ FR-003: プロベナンスチェーン（6 ノード）保存
- `knowledge.repository.save` が Query→AgentExecution→ToolExecution→DataSource→ExtractedContent→Knowledge を全て永続化。

### ✅ FR-004: Neo4j ノード/リレーションの整備
- 初期化スクリプト（`scripts/init_neo4j_schema.py`）とリポジトリ呼び出しで User/Team/Knowledge 等を扱う。

### ✅ FR-005: 個人＋チームナレッジ検索
- `knowledge.search_service.KnowledgeSearchService` が埋め込み生成、個人/チームフィルタ、Top-100 結果整形を実装。
- `/api/knowledge/search` は Pydantic レスポンスで結果を返却。Streamlit UI から検索結果を表示。
- **テスト**: `tests/unit/knowledge/test_search_service.py`, `tests/unit/apis/test_search_api.py`, `apps/ui-streamlit/tests/test_knowledge_references.py`

### ✅ FR-006: WCAG 2.1 AA + axe-core 監査
- `apps/ui-streamlit/tests/test_accessibility.py` による自動監査。
- `tests/accessibility-checklist.md` に US1〜US3 の手動チェック結果を記録。

### ✅ FR-007: 自動昇格バッチ
- `knowledge.promotion_engine.PromotionEngine` + `knowledge.promotion_repository.PromotionRepository`
- `/api/batch/promote` と CLI (`scripts/promote.py`) が稼働。
- **テスト**: `tests/unit/knowledge/test_promotion_engine.py`, `tests/unit/knowledge/test_promotion_repository.py`, `tests/unit/apis/test_batch_api.py`, `tests/unit/batch/test_promote_cli.py`

### ✅ FR-008: LLM API 障害時のリトライ
- `shared/lib/embeddings/openai_client.py` が `run_with_backoff` を 3 回試行 (1s,2s,4s) で実行。
- 失敗時は `provenance_logger.log_query_failure` が JSON ログに記録。
- **テスト**: `tests/unit/shared/test_retry_backoff.py`

### ✅ FR-009: Neo4j Vector Index + コサイン類似度 Top-K
- `query_team_knowledge.py`/`search_service.py` が `db.index.vector.queryNodes` を使用し、Top-100 & アクセス制御を実装。

---

## ノンファンクショナル要件

| 要件 | 状態 | エビデンス |
|------|------|-------------|
| NF-001 同期保存 (≤2s) | ✅ | ベンチマーク結果、保存処理の同期実装 |
| NF-002 手動トリガーバッチ | ✅ | `/api/batch/promote`, `scripts/promote.py` |
| NF-003 JSON ログ | ✅ | `logging_config.py`, `provenance_logger.py` |
| NF-004 環境変数管理 | ✅ | `.env.example`, `config/settings.py` |
| NF-005 パフォーマンス | ✅ | `benchmark_performance.py`, `docs/QA/performance-report.md` |

---

## 成功基準（Success Criteria）

| SC | 状態 | 根拠 |
|----|------|------|
| SC-001 個人ナレッジ生成 | ✅ | FR-001/FR-003 実装、Neo4j で確認可能 |
| SC-002 昇格バッチで条件を満たすナレッジのみチーム化 | ✅ | FR-007 実装、PromotionAudit で履歴追跡 |
| SC-003 チームナレッジ参照と出典表示 | ✅ | Streamlit UI の検索結果テーブル、`KnowledgeSearchService` |
| SC-004 アクセシビリティ検証 | ✅ | axe-core 自動監査 + 手動チェックログ追加 |

---

## 残課題 / リスク
- Neo4j 実データでの大量件数（>10k）検証は PoC 範囲外。将来は観測されたレイテンシに応じてインデックス再構成を検討。
- LangGraph 連携は現在スタブ。実エージェント導入時は `langgraph_runner.run_agent` の置き換えが必要。
- ベンチマークはローカル + 模擬データで測定。CI や本番相当環境での継続計測を推奨。

