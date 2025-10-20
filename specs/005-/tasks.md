---
description: "Task list for Crystal Intelligence風ナレッジ統合システム PoC"
---

# Tasks: Crystal Intelligence風ナレッジ統合システム PoC

**Input**: Design documents from `/specs/005-/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Status**: 60/65 tasks complete (92.3%)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: リポジトリ基盤と開発規約を整備し、以降の実装が憲章準拠で進められる状態にする。

- [X] T001 Document mandatory virtual environment workflow in README.md
- [X] T002 Scaffold project directories (`apps/ui-streamlit/`, `services/mcp-server/`, `shared/lib/`, `infra/neo4j/`) per plan.md
- [X] T003 Ship environment template with required keys at .env.example
- [X] T004 Define runtime & dev dependencies in pyproject.toml
- [X] T005 Configure lint/format tooling via ruff.toml and pyproject.toml tool.black section
- [X] T006 Add docs formatting configs in .prettierrc.cjs and .editorconfig

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 共通設定・ドライバ・スクリプト類を整備し、全ユーザーストーリーで使う基盤を完成させる。

- [X] T007 Implement environment settings loader in services/mcp-server/src/config/settings.py
- [X] T008 Implement Neo4j driver factory with health check in services/mcp-server/src/infra/neo4j_client.py
- [X] T009 Implement JSON logging configuration in services/mcp-server/src/logging_config.py
- [X] T010 Implement OpenAI embedding client wrapper in shared/lib/embeddings/openai_client.py
- [X] T011 Seed pytest fixtures for MCP server tests in services/mcp-server/tests/unit/conftest.py
- [X] T012 Create accessibility checklist ledger required by constitution in tests/accessibility-checklist.md
- [X] T013 Add axe-core automated audit runner in apps/ui-streamlit/tests/test_accessibility.py
- [X] T014 Provide Neo4j schema initialization script in services/mcp-server/scripts/init_neo4j_schema.py
- [X] T015 Provide user/team seed utility referencing infra/users_teams.yaml in services/mcp-server/scripts/seed_users.py
- [X] T016 Add Neo4j Docker Compose definition in infra/neo4j/docker-compose.yml
- [X] T017 Create performance benchmark runner for NF-005 (Top-100 @ 1.5s, save @ 2s) in services/mcp-server/scripts/benchmark_performance.py
- [X] T018 Implement exponential backoff retry (1s/2s/4s, max 3 attempts) in shared/lib/retry/backoff.py
- [X] T019 Add retry backoff unit tests covering exponential delays and failure logging in services/mcp-server/tests/unit/shared/test_retry_backoff.py

---

## Phase 3: User Story 1 - 自動ナレッジ蓄積と可観測性 (Priority: P1) 🎯 MVP

**Goal**: 対話完了ごとにクエリ・応答・ツール実行を同期保存し、axe/ログで可観測性を確保する。

**Independent Test**: `services/mcp-server/tests/unit` のリポジトリ/ツールテストと `test_query_sync.py` をRed→Greenで回し、UIからの手動操作でNeo4jノードと `logs/app.log` を確認。アクセシビリティ手動チェックを `tests/accessibility-checklist.md` に記録。

### Tests for User Story 1

- [X] T020 [P] [US1] Unit test KnowledgeRepository persistence in services/mcp-server/tests/unit/knowledge/test_repository.py
- [X] T021 [P] [US1] Unit test save_knowledge tool error handling in services/mcp-server/tests/unit/tools/test_save_knowledge.py
- [X] T022 [P] [US1] Unit test file_search MCP tool in services/mcp-server/tests/unit/tools/test_file_search.py
- [X] T023 [P] [US1] Unit test web_search MCP tool in services/mcp-server/tests/unit/tools/test_web_search.py
- [X] T024 [P] [US1] Unit test query_team_knowledge MCP tool in services/mcp-server/tests/unit/tools/test_query_team_knowledge.py
- [X] T025 [US1] Integration test query→persistence flow in services/mcp-server/tests/integration/test_query_sync.py

### Implementation for User Story 1

- [X] T026 [US1] Implement knowledge domain models (User/Team/Query/AgentExecution/ToolExecution/DataSource/ExtractedContent/Knowledge) in services/mcp-server/src/knowledge/models.py
- [X] T027 [US1] Implement KnowledgeRepository save graph (FR-003: 6-node provenance chain) in services/mcp-server/src/knowledge/repository.py
- [X] T028 [US1] Implement save_knowledge MCP tool in services/mcp-server/src/tools/save_knowledge.py
- [X] T029 [P] [US1] Implement file_search MCP tool (text-based files only per clarification) in services/mcp-server/src/tools/file_search.py
- [X] T030 [P] [US1] Implement web_search MCP tool in services/mcp-server/src/tools/web_search.py
- [X] T031 [P] [US1] Enhance query_team_knowledge tool with embedding filters in services/mcp-server/src/tools/query_team_knowledge.py
- [X] T032 [US1] Update shared/lib/embeddings/openai_client.py to attempt 3 retries with 1s/2s/4s backoff and structured logging (FR-008)
- [X] T033 [US1] Create FastAPI entrypoint registering routers & logging in services/mcp-server/src/main.py
- [X] T034 [US1] Refactor services/mcp-server/src/apis/query_api.py to accept QueryRequest, invoke run_agent, and persist provenance with logging
- [X] T035 [US1] Implement LangGraph agent workflow with MCP tools in services/mcp-server/src/agents/langgraph_runner.py
- [X] T036 [US1] Align contracts/openapi.yaml Query schema with new request/response shape
- [X] T037 [US1] Add query API unit tests for agent integration in services/mcp-server/tests/unit/apis/test_query_api.py
- [X] T038 [US1] Update apps/ui-streamlit/app.py to call new query API, manage session state, and surface agent response/errors
- [X] T039 [P] [US1] Improve Streamlit accessibility (aria labels, focus, live region) in apps/ui-streamlit/app.py and apps/ui-streamlit/components/
- [X] T040 [US1] Emit JSON log events for query success/failure in services/mcp-server/src/apis/query_api.py and provenance/logging modules
- [X] T041 [US1] Record Story 1 manual accessibility results in tests/accessibility-checklist.md

---

## Phase 4: User Story 2 - 個人・チームナレッジ検索 (Priority: P2)

**Goal**: 個人＋チームナレッジをベクトル検索で順位付けし、WCAG準拠UIで参照情報を提示する。

**Independent Test**: 更新した `test_search_service.py`/`test_search_api.py` をGreenにし、Streamlit UIで検索結果のアクセシビリティ検証を実施。Neo4jクエリでプロベナンスが一致するか確認。

### Tests for User Story 2

- [X] T042 [P] [US2] Revise KnowledgeSearchService unit tests for vector + filter logic in services/mcp-server/tests/unit/knowledge/test_search_service.py
- [X] T043 [P] [US2] Add knowledge reference component tests in apps/ui-streamlit/tests/test_knowledge_references.py

### Implementation for User Story 2

- [X] T044 [US2] Implement Top-100 vector search (K=100 fixed per FR-009) with personal/team filters in services/mcp-server/src/knowledge/search_service.py
- [X] T045 [US2] Extend KnowledgeRepository with search metadata helpers in services/mcp-server/src/knowledge/repository.py
- [X] T046 [US2] Update search API router with parameter validation and error handling in services/mcp-server/src/apis/search_api.py
- [X] T047 [US2] Render accessible references table (ID/summary/owner/time) in apps/ui-streamlit/components/knowledge_references.py
- [X] T048 [US2] Enhance provenance logging for search events in services/mcp-server/src/provenance/provenance_logger.py
- [X] T049 [US2] Trigger search + empty-state messaging in apps/ui-streamlit/app.py after successful query run
- [X] T050 [US2] Record Story 2 manual accessibility results in tests/accessibility-checklist.md

---

## Phase 5: User Story 3 - 自動昇格バッチ処理 (Priority: P3)

**Goal**: 類似性・貢献者条件を満たす個人ナレッジを自動昇格し、監査ログとE2E検証を提供する。

**Independent Test**: 新設する PromotionRepository/CLI/API のユニットテストをGreen化し、`tests/e2e/multi_user_promotion.py` で昇格→ログ記録を確認。アクセシビリティ記録を更新。

### Tests for User Story 3

- [X] T051 [P] [US3] Add promotion repository tests in services/mcp-server/tests/unit/knowledge/test_promotion_repository.py
- [X] T052 [P] [US3] Expand batch API tests for success/error paths in services/mcp-server/tests/unit/apis/test_batch_api.py
- [X] T053 [P] [US3] Add promotion CLI tests in services/mcp-server/tests/unit/batch/test_promote_cli.py

### Implementation for User Story 3

- [X] T054 [US3] Implement promotion repository for candidate fetch/promote in services/mcp-server/src/knowledge/promotion_repository.py
- [X] T055 [US3] Update PromotionEngine to persist audit nodes and use repository metrics (experimental thresholds: similarity=0.75, contributors=3, coverage=50%) in services/mcp-server/src/knowledge/promotion_engine.py
- [X] T056 [US3] Wire /api/batch/promote endpoint with repository + engine in services/mcp-server/src/apis/batch_api.py
- [X] T057 [US3] Wire CLI script with real repository and dry-run support in services/mcp-server/scripts/promote.py
- [X] T058 [US3] Augment batch execution logging + summary in services/mcp-server/src/batch/promote.py and provenance/batch_hooks.py
- [X] T059 [US3] Create multi-user promotion E2E scenario in tests/e2e/multi_user_promotion.py
- [X] T060 [US3] Record Story 3 manual accessibility/operability results in tests/accessibility-checklist.md

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: 品質ゲート（パフォーマンス・アクセシビリティ・コンプライアンス）を締め、リリース準備を完了させる。

- [ ] T061 Summarise benchmark outputs in docs/QA/performance-report.md after running T017
- [ ] T062 Document verification/runbook steps in docs/QA/runbook.md
- [ ] T063 Update docs/requirements-compliance-analysis.md once FR-005/FR-008/FR-009 are satisfied
- [ ] T064 Consolidate accessibility audit summary (SC-004) in tests/accessibility-checklist.md and attach to release PR
- [ ] T065 Refine README.md quickstart to reflect final API contracts and workflows

---

## Dependencies & Execution Order

1. Phase 1 → Phase 2 → Phase 3 (US1) → Phase 4 (US2) → Phase 5 (US3) → Phase N
2. Blocking gates:
   - T012 (accessibility ledger) と T017 (性能ベンチマーク基盤) を完了するまで Story 着手不可
   - T018/T019 のバックオフ修正を完了してから FR-008 関連のリトライ実装 (T032) を検証
   - US1 では T026〜T041 が完了しないと US2/US3 に進まない
   - US2 完了時に T042〜T050 を満たさないと US3 の昇格ロジックは検証不能
   - US3 完了後に T061〜T065 をクリアしてリリース判定
3. Story dependencies:
   - **US1**: Setup + Foundational が完了していること
   - **US2**: US1 で保存済みナレッジとログ基盤が整っていること
   - **US3**: US1 データを利用、US2 は並行可だが検索結果仕様が固まっていることが望ましい

## Parallel Opportunities

- Phase 2: T007〜T011 を分担し、T014/T015/T016 はスクリプト系で並行可能。T018/T019 はバックオフ修正とテストでペア実施可。
- US1: テスト群 T020〜T025 とツール改修 T029〜T031 を小チームで並行しつつ、エージェント統合 (T035) と永続化/ログ (T027/T028/T040) を2ストリームで進行
- US2: T042/T043 のテスト拡張と T044〜T049 の実装を2ストリームで進行
- US3: リポジトリ＋エンジン改修 (T054〜T058) と CLI/E2E/アクセシビリティ (T053/T059/T060) を並行化

## Implementation Strategy

1. **MVP (Story 1)**: T026〜T041 を完了し、実際のエージェント実行→保存→UI表示→ログ記録までを成立させる。
2. **Incremental Delivery**:
   - Story 2でベクトル検索・参照UI・アクセシビリティ（T042〜T050）を仕上げ、検索品質を証明
   - Story 3で昇格バッチ・CLI・監査ログ（T051〜T060）を整備しPoC成功条件を満たす
3. **Quality Gates**: 各Story完了時にアクセシビリティ記録（T041/T050/T060）とNF-005性能測定（T017→T061）を更新し、最終的にコンプライアンス文書（T063/T064）を締める。

## Clarification Alignment

This tasks.md incorporates the following clarifications from Session 2025-10-20:

1. **Top-K Fixed**: T044/FR-009 implements K=100 as fixed value (no runtime configurability)
2. **Promotion Thresholds**: T055 documents experimental parameters (similarity=0.75, contributors=3, coverage=50%) requiring post-deployment validation
3. **Neo4j Logging Migration**: NF-003 clarifies migration trigger as "after PoC validation phase completes" (no task changes needed)
4. **YAML Path**: T015 references `infra/users_teams.yaml` for user/team definitions
5. **Complex Format Accessibility**: T029 limits file_search to text-based files only; complex format ARIA/accessibility deferred to post-PoC

## Validation Checklist

✅ All tasks follow required format: `- [ ] [TaskID] [P?] [Story?] Description with file path`
✅ User stories organized as independent phases (US1/US2/US3)
✅ Each story has Independent Test criteria documented
✅ Blocking dependencies clearly identified
✅ Parallel opportunities documented
✅ File paths specified for all implementation tasks
✅ Constitution compliance (accessibility, testing, linting, security, venv) enforced
✅ MVP scope clearly identified (User Story 1 = Phase 3)
