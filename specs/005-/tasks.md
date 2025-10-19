---
description: "Task list for Crystal Intelligence風ナレッジ統合システム PoC"
---

# Tasks: Crystal Intelligence風ナレッジ統合システム PoC

**Input**: Design documents from `/specs/005-/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: List the unit tests that will cover every new or modified code path. Add integration/contract or accessibility tests when the specification or risk profile requires them.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Status**: 49/52 tasks complete (94%) - Core implementation 100% complete

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initializationと基本構造の確立

**⚠️ CONSTITUTION REQUIREMENT**: Virtual environment setup is mandatory per Principle VI (Isolated Python Environments)

- [X] T000 [P] Create Python virtual environment at repository root (`.venv/`) and document activation in README.md
- [X] T001 Create directory skeleton for apps/ui-streamlit/, services/mcp-server/, shared/lib/, infra/neo4j/, tests/
- [X] T002 Add `.env.example` with required variables at .env.example
- [X] T003 Create Python dependency manifest (runtime + dev tooling) at pyproject.toml
- [X] T004 Create Python lint configuration (ruff, black) at ruff.toml and update pyproject.toml tool.black section
- [X] T005 Create `.prettierrc.cjs` and `.editorconfig` for markdown/docs formatting at repository root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 全ストーリー共通の構成要素を整備

- [X] T006 Implement environment settings loader using python-dotenv at services/mcp-server/src/config/settings.py
- [X] T007 Implement Neo4j driver factory with health check at services/mcp-server/src/infra/neo4j_client.py
- [X] T008 Implement OpenAI embedding client wrapper at shared/lib/embeddings/openai_client.py
- [X] T009 Configure project-wide logging to JSON file (`logs/app.log`) at services/mcp-server/src/logging_config.py
- [X] T010 Seed pytest fixture utilities for MCP server at services/mcp-server/tests/unit/conftest.py
- [X] T011 Create accessibility checklist stub and reporting template at tests/accessibility-checklist.md
- [X] T012 Add axe-core scripted audit runner at apps/ui-streamlit/tests/test_accessibility.py

---

## Phase 3: User Story 1 - 自動ナレッジ蓄積と可観測性 (Priority: P1) 🎯 MVP

**Goal**: 対話完了ごとにクエリ・応答・プロベナンスをNeo4jへ同期保存し、参照可能なログを残す

**Independent Test**: pytestによるKnowledgeRepository/save_knowledgeユニットテストと手動E2EでNeo4jノード作成・axe-coreレポート・ログ出力を確認

### Tests for User Story 1 (Unit tests REQUIRED; add others as needed) ⚠️

**NOTE: Write the listed tests FIRST, ensure they FAIL before implementation**

- [X] T013 [P] [US1] Write unit tests for KnowledgeRepository persistence in services/mcp-server/tests/unit/knowledge/test_repository.py
- [X] T014 [P] [US1] Write unit tests for save_knowledge tool error handling in services/mcp-server/tests/unit/tools/test_save_knowledge.py
- [X] T015 [P] [US1] Write unit tests for file_search MCP tool in services/mcp-server/tests/unit/tools/test_file_search.py
- [X] T016 [P] [US1] Write unit tests for web_search MCP tool in services/mcp-server/tests/unit/tools/test_web_search.py
- [X] T017 [P] [US1] Write unit tests for query_team_knowledge tool graph lookups in services/mcp-server/tests/unit/tools/test_query_team_knowledge.py
- [X] T018 [P] [US1] Write unit tests for retry/backoff utility logging in tests/unit/shared/test_retry_policy.py
- [X] T019 [P] [US1] Write integration test ensuring `/api/query` waits for knowledge persistence in services/mcp-server/tests/integration/test_query_sync.py

### Implementation for User Story 1

- [X] T020 [US1] Implement knowledge domain models and data mappers at services/mcp-server/src/knowledge/models.py
- [X] T021 [US1] Implement KnowledgeRepository with vector index writes at services/mcp-server/src/knowledge/repository.py
- [X] T022 [US1] Implement save_knowledge MCP tool orchestrating embeddings + provenance at services/mcp-server/src/tools/save_knowledge.py
- [X] T023 [US1] Implement file_search MCP tool using local file system at services/mcp-server/src/tools/file_search.py
- [X] T024 [US1] Implement web_search MCP tool consuming web client at services/mcp-server/src/tools/web_search.py
- [X] T025 [US1] Implement query_team_knowledge MCP tool querying Neo4j at services/mcp-server/src/tools/query_team_knowledge.py
- [X] T026 [US1] Implement retry/backoff utility and integrate with logging at shared/lib/retry/backoff.py
- [X] T027 [US1] Implement `/api/query` endpoint to run agent and store knowledge at services/mcp-server/src/apis/query_api.py
- [X] T028 [US1] Wire Streamlit UI to submit queries and display agent response at apps/ui-streamlit/app.py
- [X] T029 [US1] Implement LangChain/LangGraph runner integration at services/mcp-server/src/agents/langgraph_runner.py
- [X] T030 [US1] Automate axe-core audit execution and store report artifact at apps/ui-streamlit/tests/test_accessibility.py
- [X] T031 [US1] Update accessibility checklist with Story 1 findings in tests/accessibility-checklist.md

**Checkpoint**: Story 1完了時に個人ナレッジ保存とログ確認が可能

---

## Phase 4: User Story 2 - 個人・チームナレッジ検索 (Priority: P2)

**Goal**: 個人＋チームナレッジを横断検索し、UIで参照情報を提示する

**Independent Test**: KnowledgeSearchServiceとAPIのユニットテスト、および手動UI操作で参照ナレッジ表示を確認

### Tests for User Story 2 (Unit tests REQUIRED; add others as needed) ⚠️

- [X] T032 [P] [US2] Write unit tests for KnowledgeSearchService ranking logic at services/mcp-server/tests/unit/knowledge/test_search_service.py
- [X] T033 [P] [US2] Write unit tests for `/api/knowledge/search` validation at services/mcp-server/tests/unit/apis/test_search_api.py

### Implementation for User Story 2

- [X] T034 [US2] Implement KnowledgeSearchService combining vector query and graph filters at services/mcp-server/src/knowledge/search_service.py
- [X] T035 [US2] Implement `/api/knowledge/search` endpoint returning ranked hits at services/mcp-server/src/apis/search_api.py
- [X] T036 [US2] Implement knowledge reference component with ID/summary/owner/time at apps/ui-streamlit/components/knowledge_references.py
- [X] T037 [US2] Integrate search results and reference section into main UI flow at apps/ui-streamlit/app.py
- [X] T038 [US2] Append search provenance logging to file sink at services/mcp-server/src/logging/provenance_logger.py

**Checkpoint**: Story 2完了で参照ナレッジのUI表示とログ追跡が可能

---

## Phase 5: User Story 3 - 自動昇格バッチ処理 (Priority: P3)

**Goal**: 手動トリガーのバッチで個人ナレッジを条件付きでチームナレッジへ昇格させる

**Independent Test**: PromotionEngineとバッチAPIのユニットテスト、およびdry-run CLIで昇格・スキップ結果を確認

### Tests for User Story 3 (Unit tests REQUIRED; add others as needed) ⚠️

- [X] T039 [P] [US3] Write unit tests for PromotionEngine thresholds at services/mcp-server/tests/unit/knowledge/test_promotion_engine.py
- [X] T040 [P] [US3] Write unit tests for `/api/batch/promote` response formatting at services/mcp-server/tests/unit/apis/test_batch_api.py

### Implementation for User Story 3

- [X] T041 [US3] Implement PromotionEngine evaluating similarity and contributor rules at services/mcp-server/src/knowledge/promotion_engine.py
- [X] T042 [US3] Implement batch runner coordinating promotion lifecycle at services/mcp-server/src/batch/promote.py
- [X] T043 [US3] Implement `/api/batch/promote` endpoint invoking promotion engine at services/mcp-server/src/apis/batch_api.py
- [X] T044 [US3] Create CLI script for manual promotion trigger at services/mcp-server/scripts/promote.py
- [X] T045 [US3] Persist batch audit entries to logging hooks at services/mcp-server/src/logging/batch_hooks.py

**Checkpoint**: Story 3完了で昇格処理のdry-runと本処理が実行可能

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: 全体の品質とCI整備

- [ ] T046 Add CI workflow for lint (`ruff check`/`black --check`), pytest, axe-core audit at .github/workflows/ci.yml
- [ ] T047 Populate accessibility checklist results after manual run at tests/accessibility-checklist.md
- [ ] T048 Document E2E verification and batch steps in docs/QA/runbook.md

---

## Bug Fixes & Quality Improvements (Post-Implementation)

**Context**: After completing initial implementation, 4 unit tests were failing due to missing mock return values. These were fixed on 2025-10-19.

**Bug Fix Tasks (All Completed)**:
- [X] Fixed test_handle_query_waits_for_persistence - Added `repo.save.return_value = "kn-10"`
- [X] Fixed test_search_endpoint_returns_results - Changed lambda to MagicMock with `.search()` method
- [X] Fixed test_save_knowledge_generates_embeddings_and_persists - Added `repo.save.return_value = "kn-1"`
- [X] Fixed test_save_knowledge_handles_embedding_failure - Added `repo.save.return_value = "kn-1"`

**Result**: All 15 unit tests passing, linting clean

**Commits**:
- `a396ab4` - fix: correct mock return values in failing unit tests
- `86e45ed` - docs: mark all test bug fix tasks as complete in tasks.md

---

## Dependencies & Execution Order

### Phase Dependencies
- Setup (Phase 1) → Foundational (Phase 2) → User Stories (Phase 3,4,5) → Polish
- User Story 1 (P1) MUST complete before Story 2 and Story 3
- User Story 2 can start once Story 1 completes; User Story 3 can run in parallel with late Story 2 tasks after common services ready

### User Story Dependencies
- **US1**: depends on Setup + Foundational
- **US2**: depends on US1 (requires saved knowledge + UI scaffolding)
- **US3**: depends on US1 (requires stored knowledge) and partially on Neo4j search utilities from US2 for contributor checks

### Parallel Opportunities
- T013〜T019 (unit tests) can run in parallel once fixtures exist
- T034とT035、T036とT037は別コードパスのため並行可能
- T041完了後にT044/T045を並行担当可能
- UI work (T028, T037) とLangChain統合 (T029) はリポジトリ実装完了後に並行進行可能

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete Phase 1 + Phase 2
2. Deliver Story 1 (T013〜T031)
3. Verify Neo4j保存・ログ・axe-coreレポートの成立後にステークホルダーへPoC初期デモ

### Incremental Delivery
1. Story 1完了後、Story 2で検索と参照表示を追加
2. Story 3で昇格バッチを追加し、PoC成功シナリオを完成

### Parallel Team Strategy
- Developer A: Story 1（保存パイプライン） → Story 3（PromotionEngine）
- Developer B: Story 1 UI連携 → Story 2 UI/検索
- QA/Designer: アクセシビリティチェックと手動E2E検証（T030, T031, T047)
