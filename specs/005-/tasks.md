# Tasks: Test Implementation Bug Fixes

**Input**: 4 failing pytest tests discovered after fixing import paths
**Prerequisites**: Import path fixes completed (specs/005-/plan.md)
**Feature Branch**: `005-`

**Context**: After resolving import path issues, 4 tests are now failing due to implementation bugs:
- test_handle_query_waits_for_persistence - repo.save mock returns MagicMock instead of knowledge_id
- test_search_endpoint_returns_results - service parameter type mismatch (lambda vs object)
- test_save_knowledge_generates_embeddings_and_persists - repo.save mock returns MagicMock instead of knowledge_id
- test_save_knowledge_handles_embedding_failure - repo.save mock returns MagicMock instead of knowledge_id

**Tests**: Not applicable - this feature IS about fixing tests

**Organization**: Single user story with focused bug fixes

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Investigation)

**Purpose**: Understand root cause of each failing test

- [X] T001 Analyze test_handle_query_waits_for_persistence failure in services/mcp-server/tests/integration/test_query_sync.py
- [X] T002 [P] Analyze test_search_endpoint_returns_results failure in services/mcp-server/tests/unit/apis/test_search_api.py
- [X] T003 [P] Analyze test_save_knowledge failures in services/mcp-server/tests/unit/tools/test_save_knowledge.py
- [X] T004 [P] Review KnowledgeRepository.save implementation in services/mcp-server/src/knowledge/repository.py

---

## Phase 2: Bug Fixes

**Purpose**: Fix the 4 failing tests by correcting mock return values and parameter types

**⚠️ CRITICAL**: Each fix must be verified with pytest immediately after implementation

### Bug #1: Mock return_value missing (3 tests affected)

- [X] T005 [P] Fix test_handle_query_waits_for_persistence by adding repo.save.return_value = "kn-10" in services/mcp-server/tests/integration/test_query_sync.py
- [X] T006 [P] Fix test_save_knowledge_generates_embeddings_and_persists by adding repo.save.return_value = "kn-1" in services/mcp-server/tests/unit/tools/test_save_knowledge.py (line 47)
- [X] T007 [P] Fix test_save_knowledge_handles_embedding_failure by adding repo.save.return_value = "kn-1" in services/mcp-server/tests/unit/tools/test_save_knowledge.py (line 62)

### Bug #2: Service parameter type mismatch

- [X] T008 Fix test_search_endpoint_returns_results by wrapping lambda in mock object with search method in services/mcp-server/tests/unit/apis/test_search_api.py

---

## Phase 3: Verification & Validation

**Purpose**: Ensure all tests pass and no regressions introduced

- [X] T009 Run pytest on services/mcp-server/tests/ to verify all 15 tests pass
- [X] T010 Run linting with ruff on modified test files
- [X] T011 Commit bug fixes with descriptive commit message

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Investigation tasks can run in parallel - no dependencies
- **Bug Fixes (Phase 2)**: Mock return_value fixes (T005-T007) can run in parallel; T008 is independent
- **Verification (Phase 3)**: Depends on Phase 2 completion - must run sequentially

### Within Each Phase

**Phase 1**: All tasks marked [P] can run in parallel (reading different files)

**Phase 2**:
- T005, T006, T007 can run in parallel (different test files, same fix pattern)
- T008 can run in parallel with T005-T007 (different bug, different file)

**Phase 3**: Sequential execution required
1. T009 must complete before T010 (verify tests pass before linting)
2. T010 must complete before T011 (verify lint before commit)

### Parallel Opportunities

```bash
# Phase 1: All investigation tasks in parallel
Task T001, T002, T003, T004

# Phase 2: All bug fixes in parallel
Task T005, T006, T007, T008

# Phase 3: Sequential only
Task T009 → T010 → T011
```

---

## Implementation Strategy

### Fix Pattern Analysis

**Root Cause**: MagicMock objects don't automatically provide return values

**Solution Pattern** (applies to T005, T006, T007):
```python
# Before (broken):
repo = MagicMock()
result = function_under_test(..., repo=repo)
assert result == "kn-10"  # FAILS: result is MagicMock

# After (fixed):
repo = MagicMock()
repo.save.return_value = "kn-10"  # ← Add this line
result = function_under_test(..., repo=repo)
assert result == "kn-10"  # PASSES
```

**Solution Pattern** (applies to T008):
```python
# Before (broken):
service = lambda q, u: [{"id": "kn"}]
response = search_endpoint(service=service)  # FAILS: service.search() doesn't exist

# After (fixed):
service = MagicMock()
service.search.return_value = [{"id": "kn"}]  # ← Change to MagicMock with method
response = search_endpoint(service=service)  # PASSES
```

### Execution Flow

1. **Phase 1** (5-10 minutes): Read and understand each failing test
2. **Phase 2** (10-15 minutes): Apply fixes in parallel
3. **Phase 3** (5-10 minutes): Verify, lint, and commit

**Total estimated time**: 20-35 minutes

### Incremental Validation

After each fix in Phase 2, optionally run pytest on that specific test:
```bash
pytest services/mcp-server/tests/integration/test_query_sync.py::test_handle_query_waits_for_persistence -v
pytest services/mcp-server/tests/unit/tools/test_save_knowledge.py::test_save_knowledge_generates_embeddings_and_persists -v
pytest services/mcp-server/tests/unit/tools/test_save_knowledge.py::test_save_knowledge_handles_embedding_failure -v
pytest services/mcp-server/tests/unit/apis/test_search_api.py::test_search_endpoint_returns_results -v
```

---

## Notes

- All fixes are in test files only - no production code changes needed
- Mock return values must match the expected knowledge_id from test payloads
- MagicMock auto-creates attributes but not return values - must be explicit
- After fixes: 15/15 tests should pass (11 currently passing + 4 fixed)
- Constitution Principle II (Testing): These fixes ensure unit tests properly validate behavior
- File paths use absolute structure: `services/mcp-server/tests/` and `services/mcp-server/src/`
