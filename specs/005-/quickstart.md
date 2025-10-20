# Quickstart: Crystal Intelligence風ナレッジ統合システム PoC

## 1. 前提条件
- Python 3.11
- Docker / Docker Compose v2
- OpenAI APIキー（`OPENAI_API_KEY`）
- Neo4j用ローカルポート `7687`, `7474` が空いていること

## 2. 初期セットアップ
```bash
# リポジトリ直下で実行
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt  # poetry export 想定時は `poetry install`
cp .env.example .env
# .env 内でOpenAI/Neo4j/MCP URLなどを設定
```

## 3. インフラ起動
```bash
# Neo4j (vector plugin) をDocker Composeで起動
cd infra/neo4j
docker compose up -d
# 初回のみスキーマ初期化
poetry run python services/mcp-server/scripts/init_neo4j_schema.py
poetry run python services/mcp-server/scripts/seed_users.py
```

## 4. アプリケーション起動
```bash
# MCPサーバー
poetry run uvicorn services.mcp-server.src.main:app --reload

# 別ターミナルでStreamlit UI
cd apps/ui-streamlit
poetry run streamlit run app.py --server.port 8501
```

## 5. 動作確認
1. Streamlit UIからクエリを送信し、検索結果と参照ナレッジが表示されることを確認。
2. Neo4jブラウザで`MATCH (k:Knowledge) RETURN k LIMIT 10;`を実行し、保存済みナレッジを確認。
3. `poetry run python services/mcp-server/scripts/promote.py --dry-run`で昇格バッチを手動トリガー。

## 6. テスト & 品質ゲート
```bash
# Lint
poetry run ruff check .
poetry run black --check .

# Unit / integration tests
poetry run pytest
poetry run pytest -m unit

# Accessibility (axe-core)
poetry run pytest apps/ui-streamlit/tests/test_accessibility.py
# 手動チェック結果を tests/accessibility-checklist.md に記録

# 性能ベンチマーク
poetry run python services/mcp-server/scripts/benchmark_performance.py --report ./reports/perf-latest.json
```

## 7. ログと監査
- `logs/app.log` にJSONフォーマットでAPI・バッチ・リトライ結果が出力される。
- 障害発生時はSlack `#ai-agent-alert` チャンネルへ通知（`scripts/notify_incident.py`を利用）。

## 8. シャットダウン
```bash
# UI / MCP サーバー停止（Ctrl+C）
# Neo4j停止
cd infra/neo4j
docker compose down
```

## 9. 次のステップ
- `tests/accessibility-checklist.md` に各ストーリーの手動検証結果を反映。
- `reports/perf-latest.json` をSlackへ共有し、NF-005達成をレビュー。
- 追加のADRが必要な場合は `docs/adr/` に記載。
