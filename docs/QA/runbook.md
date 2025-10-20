# QA Runbook – Crystal Intelligence PoC

## 1. Pre-flight Checklist
- 仮想環境 `.venv/` を有効化し `pip install -e ".[dev]"`
- Neo4j コンテナを `infra/neo4j/docker-compose.yml` で起動
- `.env` の OpenAI/Neo4j 設定を確認
- `benchmark_performance.py --iterations 1` で接続チェック

## 2. Test Matrix
| Suite | Command | Purpose |
|-------|---------|---------|
| Unit | `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest services/mcp-server/tests/unit` | ドメインロジック/ツール/API/CLI の回帰確認 |
| UI component | `pytest apps/ui-streamlit/tests` | Streamlit コンポーネントのレンダリング |
| Integration | `pytest services/mcp-server/tests/integration/test_query_sync.py` | クエリ保存パスの同期保証 |
| Accessibility | `pytest apps/ui-streamlit/tests/test_accessibility.py -k accessibility` | axe-core による自動監査 |
| Benchmark | `python services/mcp-server/scripts/benchmark_performance.py --include-search --output reports/perf-latest.json` | NF-005 達成状況の検証 |

## 3. Manual Verification
1. Streamlit UIでクエリ送信 → 応答、参照セクション、検索結果を確認。
2. `tests/accessibility-checklist.md` の該当行に手動チェック結果を追記。
3. `/api/batch/promote` を dry-run → 本番モードで実行し、Neo4j でチームナレッジ・PromotionAudit を照合。

## 4. Release Gate
- 全てのタスクが `specs/005-/tasks.md` で `[X]` になっていることをチェック
- `docs/requirements-compliance-analysis.md` の未解決項目が無いこと
- `docs/QA/performance-report.md` が最新日付で保存されていること
- axe-core レポートと手動チェックログを PR に添付

## 5. Incident Response
- バッチ失敗や検索エラーは `logs/app.log` の JSON ログで検知
- 緊急時は `services/mcp-server/scripts/promote.py TEAM_ID --dry-run` で再現→修正後に `--dry-run` 解除
- 再発防止策・対応時間を `docs/requirements-compliance-analysis.md` に追記
