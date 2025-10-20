# Verification & Operations Runbook

**Version**: 1.0
**Last Updated**: 2025-10-20
**Target Audience**: Development Team, QA Engineers, DevOps

## Purpose

This runbook provides step-by-step procedures for verifying, deploying, and operating the Crystal Intelligence風ナレッジ統合システム PoC.

## Table of Contents

1. [Pre-Deployment Verification](#pre-deployment-verification)
2. [Deployment Procedures](#deployment-procedures)
3. [Post-Deployment Validation](#post-deployment-validation)
4. [Operational Procedures](#operational-procedures)
5. [Troubleshooting](#troubleshooting)
6. [Rollback Procedures](#rollback-procedures)

---

## Pre-Deployment Verification

### 1.1 Environment Setup

**Prerequisites Checklist**:
- [ ] Python 3.11+ installed with virtual environment
- [ ] Neo4j 5.x accessible (local or remote)
- [ ] OpenAI API key configured
- [ ] Git repository cloned

**Steps**:
```bash
# 1. Clone repository (if not already done)
git clone <repository-url>
cd NRI_AI_Agent_Poc

# 2. Create and activate virtual environment (MANDATORY per Constitution Principle VI)
python3.11 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# or: .venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r services/mcp-server/requirements.txt
pip install -r apps/ui-streamlit/requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with actual credentials:
#   OPENAI_API_KEY=sk-proj-...
#   NEO4J_URI=bolt://localhost:7687
#   NEO4J_USER=neo4j
#   NEO4J_PASSWORD=<your-password>
#   MCP_SERVER_URL=http://localhost:8000
```

### 1.2 Code Quality Verification

**Run Linting** (Constitution Principle III):
```bash
# Format check
ruff format --check .

# Lint check
ruff check .

# Fix automatically (if needed)
ruff format .
ruff check --fix .
```

**Expected Output**: No errors or warnings

### 1.3 Unit Test Execution

**Run Full Test Suite**:
```bash
# MCP Server tests
cd services/mcp-server
PYTHONPATH=src:../../shared/lib pytest tests/unit -v --cov=src --cov-report=term-missing

# UI tests
cd ../../apps/ui-streamlit
pytest tests/ -v
```

**Success Criteria**:
- ✅ All tests pass (green)
- ✅ Code coverage ≥ 80% for critical paths
- ✅ No skipped tests (unless explicitly documented)

**Expected Coverage** (as of 2025-10-20):
- `knowledge/repository.py`: 95%+
- `knowledge/search_service.py`: 90%+
- `knowledge/promotion_repository.py`: 95%+
- `apis/batch_api.py`: 85%+
- `cli/promotion_cli.py`: 90%+

### 1.4 Accessibility Validation

**Automated Audit**:
```bash
cd apps/ui-streamlit
pytest tests/test_accessibility.py -v
```

**Manual Verification** (required per Constitution Principle I):
1. Start Streamlit UI: `streamlit run app.py`
2. Navigate with **keyboard only** (Tab, Enter, Escape)
3. Verify screen reader announcements (NVDA/VoiceOver)
4. Check color contrast with browser dev tools
5. Document results in `tests/accessibility-checklist.md`

**Reference**: `tests/accessibility-checklist.md` for detailed criteria

---

## Deployment Procedures

### 2.1 Neo4j Setup

**Start Neo4j** (Docker):
```bash
cd infra/neo4j
docker-compose up -d

# Verify Neo4j is running
docker-compose ps
# Expected: neo4j container STATUS = Up

# View logs
docker-compose logs -f neo4j
```

**Initialize Schema**:
```bash
cd ../../services/mcp-server
PYTHONPATH=src:../../shared/lib python scripts/init_neo4j_schema.py
```

**Verify Schema**:
```cypher
// Connect to Neo4j Browser: http://localhost:7474
// Run this query:
SHOW VECTOR INDEXES
// Expected: knowledge_embedding index with 1536 dimensions, cosine similarity
```

**Seed Test Data** (optional for demo):
```bash
PYTHONPATH=src:../../shared/lib python scripts/seed_users.py
```

### 2.2 MCP Server Deployment

**Development Mode**:
```bash
cd services/mcp-server
PYTHONPATH=src:../../shared/lib uvicorn src.main:app --reload --port 8000
```

**Production Mode**:
```bash
cd services/mcp-server
PYTHONPATH=src:../../shared/lib gunicorn src.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

**Health Check**:
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy", "neo4j": "connected"}
```

### 2.3 Streamlit UI Deployment

**Development Mode**:
```bash
cd apps/ui-streamlit
streamlit run app.py --server.port 8501
```

**Production Mode**:
```bash
streamlit run app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.enableCORS false \
  --server.enableXsrfProtection true
```

**Access URL**: `http://localhost:8501`

---

## Post-Deployment Validation

### 3.1 Smoke Tests

**US1: Knowledge Persistence**:
1. Open Streamlit UI: `http://localhost:8501`
2. Enter query: "Summarize best practices for customer support"
3. Click "送信" (Submit)
4. **Verify**:
   - ✅ Status message: "ナレッジを保存しました。"
   - ✅ Agent response displayed with Knowledge ID
   - ✅ References table shows provenance

**US2: Vector Search**:
1. After US1 query completes
2. **Verify** "検索結果" section appears automatically
3. **Verify** references table shows:
   - ✅ personal/team knowledge items
   - ✅ similarity scores
   - ✅ owner information (user-1, team-demo)
   - ✅ empty state message if no results: "参照情報はありません。"

**US3: Batch Promotion**:
```bash
# CLI test (dry-run)
cd services/mcp-server
PYTHONPATH=src:../../shared/lib python scripts/promote.py team-demo --dry-run

# Verify output includes:
# - "dry_run": true
# - promoted/skipped counts
# - knowledge IDs

# API test
curl -X POST "http://localhost:8000/api/batch/promote?team_id=team-demo&dry_run=true"

# Verify JSON response:
# - team_id: "team-demo"
# - dry_run: true
# - promoted_count, promoted_ids, skipped
```

### 3.2 Performance Validation

**Run Benchmark** (NF-005):
```bash
cd services/mcp-server
PYTHONPATH=src:../../shared/lib python scripts/benchmark_performance.py \
  --iterations 10 \
  --include-search \
  --output ../../docs/QA/benchmark-results.json

# Check results
cat ../../docs/QA/benchmark-results.json | jq '.summary | {
  save_avg_ms, save_p95_ms, search_avg_ms, search_p95_ms,
  save_target_ms, search_target_ms
}'
```

**Success Criteria**:
- ✅ `save_p95_ms` ≤ 2000ms (NF-005.1)
- ✅ `search_p95_ms` ≤ 1500ms (NF-005.2)

**Expected Results** (baseline):
- save_p95_ms: ~650ms (67.5% under budget)
- search_p95_ms: ~980ms (34.7% under budget)

### 3.3 Log Verification

**Check Structured Logs** (FR-007):
```bash
# View recent logs
tail -f services/mcp-server/logs/app.log

# Verify JSON structure
tail -1 services/mcp-server/logs/app.log | jq '.'

# Expected fields:
# - timestamp (ISO 8601)
# - level (INFO, WARNING, ERROR)
# - message
# - extra fields (user_id, team_id, knowledge_id, etc.)
```

---

## Operational Procedures

### 4.1 Monitoring

**Key Metrics to Track**:
1. **Latency**:
   - P95 save latency (target: ≤2000ms)
   - P95 search latency (target: ≤1500ms)
2. **Error Rates**:
   - OpenAI API failures (should trigger retry)
   - Neo4j connection failures
3. **Resource Usage**:
   - Neo4j memory (`dbms.memory.pagecache.size`)
   - MCP server CPU/memory
4. **Knowledge Base Size**:
   - Total Knowledge nodes
   - Personal vs Team distribution

**Neo4j Monitoring Queries**:
```cypher
// Total knowledge count
MATCH (k:Knowledge) RETURN count(k) AS total

// Personal vs Team distribution
MATCH (k:Knowledge)
RETURN k.type AS type, count(k) AS count

// Recent promotions
MATCH (k:Knowledge)-[:PROMOTED_TO]->(tk:Knowledge)
RETURN k.id, tk.id, tk.created_at
ORDER BY tk.created_at DESC
LIMIT 10
```

### 4.2 Backup Procedures

**Neo4j Backup** (Docker):
```bash
cd infra/neo4j

# Create backup
docker-compose exec neo4j neo4j-admin database dump neo4j \
  --to-path=/backups/neo4j-$(date +%Y%m%d-%H%M%S).dump

# Copy to host
docker cp neo4j:/backups ./backups/
```

**Application Logs Backup**:
```bash
# Archive logs (weekly)
tar -czf logs-backup-$(date +%Y%m%d).tar.gz services/mcp-server/logs/

# Move to archive directory
mv logs-backup-*.tar.gz backups/logs/
```

### 4.3 Batch Promotion Operations

**Manual Promotion Trigger**:
```bash
# Dry-run first (recommended)
PYTHONPATH=src:../../shared/lib python scripts/promote.py team-demo --dry-run

# Review output, then run live
PYTHONPATH=src:../../shared/lib python scripts/promote.py team-demo
```

**Scheduled Promotion** (optional):
```bash
# Add to crontab (daily at 2 AM)
0 2 * * * cd /path/to/NRI_AI_Agent_Poc/services/mcp-server && \
  PYTHONPATH=src:../../shared/lib python scripts/promote.py team-demo >> logs/promotion-cron.log 2>&1
```

---

## Troubleshooting

### 5.1 Common Issues

#### Issue: "ModuleNotFoundError: No module named 'config'"
**Cause**: PYTHONPATH not set correctly
**Solution**:
```bash
# Always run with PYTHONPATH
cd services/mcp-server
PYTHONPATH=src:../../shared/lib python <script>
```

#### Issue: "Couldn't connect to localhost:7687"
**Cause**: Neo4j not running
**Solution**:
```bash
cd infra/neo4j
docker-compose up -d
docker-compose ps  # Verify status
```

#### Issue: "OpenAI API rate limit exceeded"
**Cause**: Too many requests in short period
**Solution**:
- Wait for rate limit reset (usually 1 minute)
- Retry logic (FR-008) will handle automatically after 1s/2s/4s delays

#### Issue: "Vector index not found"
**Cause**: Schema not initialized
**Solution**:
```bash
cd services/mcp-server
PYTHONPATH=src:../../shared/lib python scripts/init_neo4j_schema.py
```

#### Issue: "Streamlit showing 'Connection error'"
**Cause**: MCP Server not running
**Solution**:
```bash
cd services/mcp-server
PYTHONPATH=src:../../shared/lib uvicorn src.main:app --port 8000
```

### 5.2 Diagnostic Commands

**Check all services**:
```bash
# Neo4j
docker ps | grep neo4j

# MCP Server
lsof -i :8000

# Streamlit
lsof -i :8501
```

**View logs**:
```bash
# Neo4j
docker-compose -f infra/neo4j/docker-compose.yml logs -f

# MCP Server
tail -f services/mcp-server/logs/app.log

# Streamlit (console output)
```

---

## Rollback Procedures

### 6.1 Code Rollback

**Git Revert**:
```bash
# Identify last good commit
git log --oneline

# Revert to specific commit
git revert <commit-hash>

# Or reset to previous version (destructive)
git reset --hard <commit-hash>
```

### 6.2 Database Rollback

**Restore Neo4j Backup**:
```bash
cd infra/neo4j

# Stop Neo4j
docker-compose down

# Restore from backup
docker-compose run --rm neo4j neo4j-admin database load neo4j \
  --from-path=/backups/neo4j-20251020-120000.dump \
  --overwrite-destination

# Restart
docker-compose up -d
```

### 6.3 Emergency Stop

**Stop All Services**:
```bash
# Stop Streamlit (Ctrl+C in terminal)

# Stop MCP Server (Ctrl+C or kill process)
lsof -ti :8000 | xargs kill -9

# Stop Neo4j
cd infra/neo4j
docker-compose down
```

---

## Success Criteria Summary

**Deployment Successful If**:
- ✅ All unit tests pass
- ✅ US1/US2/US3 smoke tests complete successfully
- ✅ Performance benchmarks meet NF-005 targets
- ✅ Accessibility validation passes (manual + automated)
- ✅ Logs show structured JSON format
- ✅ No critical errors in logs within first 15 minutes

**Go/No-Go Decision Checklist**:
- [ ] All pre-deployment verification passed
- [ ] Neo4j schema initialized successfully
- [ ] MCP Server health check returns 200
- [ ] Streamlit UI accessible and responsive
- [ ] US1/US2/US3 smoke tests validated
- [ ] Performance benchmarks within targets
- [ ] Accessibility compliance documented

---

## Contact & Escalation

**Primary Contact**: Development Team
**Secondary Contact**: DevOps Team
**Emergency Escalation**: Project Manager

**Issue Tracking**: GitHub Issues
**Incident Response**: Slack #ai-agent-incidents

---

**Document Status**: ✅ Complete
**Next Review**: 2025-11-20 (monthly)
**Change History**:
- 2025-10-20 v1.0: Initial runbook (根岸 + Claude)
