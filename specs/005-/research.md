# Research Log: Crystal Intelligence風ナレッジ統合システム PoC

## R1. 性能計測とベンチマーク戦略
- **Decision**: `services/mcp-server/scripts/benchmark_performance.py`でベクトル検索Top-100および同期保存処理を計測し、CIフラグ付きで週次手動実行する。計測はNeo4jサンプルデータ（>=1kノード）とOpenAI埋め込みモックを使用し、p95指標をSlackに共有する。
- **Rationale**: NF-005の1.5秒/2秒目標を客観的に検証し、PoC期間中に性能退行を即時発見できる。
- **Alternatives considered**: `pytest-benchmark`統合（計測粒度は良いがセットアップが複雑）、本番相当負荷テストツール（PoC範囲外と判断）。

## R2. アクセシビリティ検証フロー
- **Decision**: axe-core自動監査はCIジョブでPull Requestごとに実施し、手動チェック（キーボード操作、コントラスト比、スクリーンリーダー読み上げ）はStory 1/2/3完了時およびリリース前に根岸が実施して`tests/accessibility-checklist.md`へ記録する。
- **Rationale**: 憲章Iの「ストーリーごとのアクセシビリティ基準とテストのトレーサビリティ」を満たし、PoCでも実運用に近い確認を提供する。
- **Alternatives considered**: 自動ツールのみで完結（手動確認欠如で憲章違反）、専門業者への委託（PoCスコープ外・コスト過大）。

## R3. Neo4jベクトル + グラフ統合パターン
- **Decision**: Knowledgeノードに512次元埋め込みを保持し、`Knowledge.embedding`へNeo4j Vector Index（cosine）を作成。Top-100検索後にCypherでチーム/個人アクセス制御フィルタを適用し、Graphトラバースでプロベナンスを補完する。
- **Rationale**: LangChainのRetrievalパターンとNeo4j公式ベストプラクティスに整合し、PoC期間の性能要件を満たしやすい。
- **Alternatives considered**: 外部ベクターストア（Pinecone）とのハイブリッド構成（新規依存が増えPoCスコープを超過）、完全Graphベース検索（高コスト）。

## R4. ログ監査と障害対応
- **Decision**: `logs/app.log`へJSON構造で主要イベント（API呼び出し、ツール実行、バッチ昇格結果、リトライ失敗）を出力し、日次でローテーション。重大障害はSlack通知スクリプト経由で共有する。
- **Rationale**: 憲章IVの迅速なセキュリティ/障害対応を支援し、PoCの観測性を確保できる。
- **Alternatives considered**: Neo4jへ直接監査ログを保存（PoCではオーバーヘッド）、クラウドログサービス（導入コスト・環境構築が重い）。
