# NRI AI Agent PoC - Crystal Intelligence Knowledge Integration

AI-driven knowledge management system with hierarchical accumulation and automatic team knowledge promotion.

## Overview

This PoC demonstrates an automated knowledge capture and sharing system that:
- Captures knowledge from AI agent interactions with full provenance tracking
- Stores information in a hierarchical structure (Personal → Team)
- Automatically promotes frequently-referenced knowledge to team level
- Enables knowledge reuse across team members through intelligent search

**Status**: ✅ Ready for Release (60/65 tasks complete, US1/US2/US3 fully implemented)
**Tech Stack**: Python 3.11 + Streamlit + LangChain/LangGraph + OpenAI + Neo4j
**Compliance**: WCAG 2.1 AA ✅ | Performance NF-005 ✅ | 45+ Unit Tests ✅

## System Architecture

```
User (Streamlit UI)
    ↓
LangChain/LangGraph Agent
    ↓ (MCP Protocol)
MCP Server
    ├→ Tools (file_search, web_search, query_team_knowledge, save_knowledge)
    └→ Knowledge Engine
        └→ Neo4j (Vector + Graph Database)
```

## Prerequisites

- **Python**: 3.11 or higher
- **Neo4j**: Docker-based instance (provided via Docker Compose)
- **OpenAI API Key**: For LLM and embeddings

## Virtual Environment Setup (REQUIRED)

Per project constitution (Principle VI: Isolated Python Environments), all Python execution MUST occur within a virtual environment.

### Create Virtual Environment

```bash
# Navigate to project root
cd /path/to/NRI_AI_Agent_Poc

# Create virtual environment
python3.11 -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### Verify Activation

Your terminal prompt should show `(.venv)` prefix when the virtual environment is active.

```bash
# Verify Python version
python --version  # Should show Python 3.11.x

# Verify pip is using venv
which pip  # Should point to .venv/bin/pip
```

## Dependency Installation

With virtual environment activated:

```bash
# Install production dependencies
pip install -e .

# Install development dependencies (testing, linting)
pip install -e ".[dev]"

# Verify installation
pip list
```

### Dependency Management

Dependencies are managed via `pyproject.toml` with exact version pinning:
- **Core**: streamlit, langchain>=0.2, langgraph, openai>=1.0.0
- **Database**: neo4j, python-dotenv
- **Utilities**: tenacity>=8.0.0, apscheduler>=3.10, pydantic>=2.6
- **API**: fastapi>=0.110, uvicorn[standard]>=0.29
- **Dev**: pytest, pytest-asyncio, pytest-cov, ruff, black

## Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or your preferred editor
```

### Required Environment Variables

```bash
OPENAI_API_KEY=sk-your-openai-api-key
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password
MCP_SERVER_URL=http://localhost:3000
```

## Development Workflow

### Running Tests

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Run all tests with coverage
pytest

# Run specific test suite
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/unit/
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/integration/

# Run with coverage report
pytest --cov=services --cov=shared --cov=apps
```

### Code Quality Checks

```bash
# Lint checking (Ruff)
ruff check .

# Code formatting (Black)
black .

# Type checking (if enabled)
mypy src/
```

### Running the Application

```bash
# Start Neo4j (if using Docker Compose)
docker-compose up -d neo4j

# Activate virtual environment
source .venv/bin/activate

# Run Streamlit UI
cd apps/ui-streamlit
streamlit run app.py

# Run MCP Server (in separate terminal)
cd services/mcp-server
uvicorn src.main:app --reload --port 3000
```

## Project Structure

```
NRI_AI_Agent_Poc/
├── apps/
│   └── ui-streamlit/          # Streamlit frontend
├── services/
│   └── mcp-server/            # MCP server with knowledge engine
│       ├── src/
│       │   ├── tools/         # MCP tools (file_search, web_search, etc.)
│       │   ├── knowledge/     # Knowledge repository and search
│       │   └── apis/          # API endpoints
│       └── tests/
├── shared/
│   └── lib/                   # Shared libraries (embeddings, retry)
├── tests/                     # Cross-cutting tests
├── docs/                      # Documentation
├── specs/                     # Feature specifications
├── .specify/                  # SpecKit workflow templates
│   └── memory/
│       └── constitution.md    # Project governance principles
├── pyproject.toml             # Dependency management
└── .env.example               # Environment template
```

## Key Features

1. **Real-time Knowledge Capture**: Extracts knowledge after each AI interaction
2. **PROV-compliant Provenance**: W3C PROV ontology for complete lineage tracking
3. **Hierarchical Storage**: Personal → Team knowledge with automatic promotion
4. **Auto-Promotion Engine**: Batch process using vector similarity (threshold: 0.75)
5. **Intelligent Search**: Query personal + team knowledge simultaneously

## Development Standards

This project follows strict governance principles defined in `.specify/memory/constitution.md`:

- **Accessibility**: WCAG 2.1 AA compliance (Principle I)
- **Testing**: Unit tests required for all code paths (Principle II)
- **Code Quality**: Ruff + Black enforcement (Principle III)
- **Security**: 24-hour vulnerability remediation (Principle IV)
- **Traceability**: All decisions documented with rationale (Principle V)
- **Isolation**: Virtual environments mandatory (Principle VI)

## Common Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Navigate to source
cd services/mcp-server/src

# Run tests
pytest

# Lint code
ruff check .

# Format code
black .

# Deactivate virtual environment
deactivate
```

## Troubleshooting

### Virtual Environment Issues

**Problem**: `pip: command not found` or installing to system Python

**Solution**: Ensure virtual environment is activated (`source .venv/bin/activate`)

**Problem**: Wrong Python version

**Solution**: Recreate venv with correct version: `python3.11 -m venv .venv`

### Dependency Conflicts

**Problem**: Package version conflicts

**Solution**: Delete venv and reinstall:
```bash
deactivate
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Neo4j Connection Issues

**Problem**: Cannot connect to Neo4j

**Solution**:
1. Verify Neo4j is running: `docker ps`
2. Check credentials in `.env` match Neo4j configuration
3. Test connection: `bolt://localhost:7687`

## Contributing

1. Create feature branch from `main`
2. Ensure virtual environment is activated
3. Install dev dependencies: `pip install -e ".[dev]"`
4. Write tests first (TDD, Principle II)
5. Run tests and linting before committing
6. Create PR with constitution compliance checklist

## User Stories (Implemented)

### US1: Automatic Knowledge Accumulation (P1 - MVP)
**Scenario**: User queries via Streamlit → Agent executes → Knowledge saved with provenance

```bash
# 1. Start Streamlit UI
cd apps/ui-streamlit
streamlit run app.py

# 2. Enter query: "プロジェクトの進捗レポートを作成してください"
# 3. Agent executes (file_search, web_search, query_team_knowledge tools)
# 4. Response displayed + 6-node provenance chain saved to Neo4j
# 5. Structured JSON logs written to logs/app.log
```

**Verification**: Check Neo4j Browser for Query→AgentExecution→ToolExecution→DataSource→ExtractedContent→Knowledge nodes

**Accessibility**: ✅ WCAG 2.1 AA compliant (axe-core + manual validation in `tests/accessibility-checklist.md`)

### US2: Personal + Team Knowledge Search (P2)
**Scenario**: Search personal and team knowledge with Top-100 vector ranking

```bash
# Via Streamlit UI (auto-triggers after query completion)
# - Results displayed in accessible table (semantic HTML, ARIA labels)
# - Empty state: "参照情報はありません。"

# Via API
curl -X GET "http://localhost:8000/api/knowledge/search?user_id=user-001&team_ids=team-alpha&query=進捗レポート"
```

**Features**:
- Vector search with personal/team filters
- Top-100 fixed ranking (K=100 per FR-009)
- Summary truncation (160 chars + "…")
- Performance: 980ms P95 (34.7% under budget)

**Tests**: 13 unit tests (T042-T043) covering filters, ranking, accessibility

### US3: Automatic Batch Promotion (P3)
**Scenario**: Promote frequently-referenced personal knowledge to team level

```bash
# CLI (dry-run mode)
cd services/mcp-server
PYTHONPATH=src:../../shared/lib python scripts/promote.py --team-id team-alpha --dry-run

# CLI (live promotion)
python scripts/promote.py --team-id team-alpha

# API
curl -X POST http://localhost:8000/api/batch/promote \
  -H "Content-Type: application/json" \
  -d '{"team_id": "team-alpha", "dry_run": false}'
```

**Thresholds** (experimental, require post-deployment validation):
- Similarity: ≥0.75
- Contributors: ≥3
- Coverage: ≥50%

**Audit**: PromotionAudit nodes track all promotions with dry_run flag, status, reason

**Tests**: 42 unit tests (T051-T053) covering repository, API, CLI workflows

## Comprehensive Documentation

### Quality Assurance
- **[Performance Report](docs/QA/performance-report.md)**: NF-005 validation, benchmark framework, optimization notes
- **[Verification Runbook](docs/QA/runbook.md)**: Deployment procedures, smoke tests, troubleshooting, monitoring
- **[Requirements Compliance](docs/requirements-compliance-analysis.md)**: FR-001~FR-009 + NF-001~NF-005 implementation status
- **[Accessibility Checklist](tests/accessibility-checklist.md)**: WCAG 2.1 AA validation, manual testing results, release approval

### Specifications
- **[Feature Spec](specs/005-/spec.md)**: Functional requirements, success criteria, constraints
- **[Implementation Plan](specs/005-/plan.md)**: Architecture decisions, integration points, validation strategy
- **[Tasks](specs/005-/tasks.md)**: 65-task breakdown with dependencies and parallel opportunities
- **[Data Model](specs/005-/data-model.md)**: Neo4j schema, node/relationship types, indexing strategy

### Governance
- **[Constitution](.specify/memory/constitution.md)**: 6 core principles (Accessibility, Testing, Linting, Security, Traceability, Isolation)
- **[AGENTS.md](AGENTS.md)**: Auto-generated development guidelines from constitution

## Success Criteria (PoC) - ✅ ACHIEVED

1. ✅ 3 users interact with AI on similar topics → **US1 implemented with provenance**
2. ✅ Personal knowledge accumulates for each user → **6-node chain with owner_id**
3. ✅ Batch process auto-creates team knowledge → **US3 with experimental thresholds**
4. ✅ 4th user queries and receives team knowledge → **US2 with Top-100 vector search**

**Additional Achievements**:
- ✅ WCAG 2.1 AA accessibility compliance (SC-004)
- ✅ Performance targets exceeded (NF-005: 67.5% and 34.7% margins)
- ✅ 60/65 tasks complete (92.3%), US1/US2/US3 fully implemented
- ✅ 45+ unit tests with comprehensive coverage

## License

Internal PoC - NRI Proprietary

---

**Version**: 1.0.0 (PoC Complete)
**Last Updated**: 2025-10-20
**Maintainer**: NRI AI Team
**Test Coverage**: 60/65 tasks (92.3%), 45+ unit tests
**Documentation**: Comprehensive QA reports, runbook, compliance analysis

## API Endpoints

### Query API (US1: Knowledge Accumulation)
```bash
POST /api/query
Content-Type: application/json

{
  "user_id": "user-001",
  "team_id": "team-alpha",
  "query_text": "プロジェクトの進捗状況を確認してください"
}

# Response: Agent execution result + provenance saved to Neo4j
```

### Search API (US2: Knowledge Search)
```bash
GET /api/knowledge/search?user_id=user-001&team_ids=team-alpha&query=プロジェクト進捗

# Response: Top-100 ranked results (personal + team knowledge)
# Filters: personal (owner_id) + team (owner_team_id IN team_ids)
# Performance: P95 latency 980ms (target ≤1500ms)
```

### Batch Promotion API (US3: Auto-Promotion)
```bash
POST /api/batch/promote
Content-Type: application/json

{
  "team_id": "team-alpha",
  "dry_run": true
}

# Response: Promoted/skipped candidates with audit logging
# Thresholds (experimental): similarity≥0.75, contributors≥3, coverage≥50%
```

### Health Check
```bash
GET /healthz
# Response: {"status": "ok", "neo4j": "connected"}
```

**API Documentation**: See `services/mcp-server/src/apis/` for detailed contracts

## Performance Benchmark

**NF-005 Validation**: ✅ All targets exceeded with significant margin

| Operation | Target | Actual (P95) | Margin |
|-----------|--------|--------------|--------|
| Knowledge Save | ≤ 2000ms | 650ms | **67.5% under budget** |
| Vector Search (Top-100) | ≤ 1500ms | 980ms | **34.7% under budget** |

**Run Benchmarks**:
```bash
cd services/mcp-server
PYTHONPATH=src:../../shared/lib python scripts/benchmark_performance.py \
  --iterations 10 \
  --include-search \
  --output ../../docs/QA/benchmark-results.json
```

**Report**: See [`docs/QA/performance-report.md`](docs/QA/performance-report.md) for detailed analysis
