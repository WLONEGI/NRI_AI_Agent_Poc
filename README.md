# NRI AI Agent PoC - Crystal Intelligence Knowledge Integration

AI-driven knowledge management system with hierarchical accumulation and automatic team knowledge promotion.

## Overview

This PoC demonstrates an automated knowledge capture and sharing system that:
- Captures knowledge from AI agent interactions with full provenance tracking
- Stores information in a hierarchical structure (Personal → Team)
- Automatically promotes frequently-referenced knowledge to team level
- Enables knowledge reuse across team members through intelligent search

**Status**: PoC Implementation (Phase 1-3)
**Tech Stack**: Python 3.11 + Streamlit + LangChain/LangGraph + OpenAI + Neo4j

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

## Success Criteria (PoC)

1. ✅ 3 users interact with AI on similar topics
2. ✅ Personal knowledge accumulates for each user
3. ✅ Batch process auto-creates team knowledge
4. ✅ 4th user queries and receives team knowledge

## Resources

- **Requirements**: `docs/requirements.md` - Detailed PoC specifications
- **Constitution**: `.specify/memory/constitution.md` - Governance principles
- **AGENTS.md**: Auto-generated development guidelines

## License

Internal PoC - NRI Proprietary

---

**Version**: 0.1.0
**Last Updated**: 2025-10-19
**Maintainer**: NRI AI Team

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/query | LangGraphエージェント実行・ナレッジ保存 |
| GET | /api/knowledge/search | 個人＋チームナレッジ検索（Top-100） |
| POST | /api/batch/promote | 昇格バッチの実行（ドライラン対応） |
| GET | /healthz | Neo4j ヘルスチェック |

## Performance Benchmark

```bash
python services/mcp-server/scripts/benchmark_performance.py --include-search --output reports/perf-latest.json
```

- NF-005 目標: 保存 ≤ 2000ms、検索 ≤ 1500ms
- 結果は `docs/QA/performance-report.md` に記録し、Slack #ai-agent-perf へ共有
