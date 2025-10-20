Crystal Intelligence風ナレッジ統合システム PoC仕様書
1. プロジェクト概要
目的: AIエージェントの業務利用過程で取得した情報を自動的にナレッジ化し、階層的に蓄積・共有するシステムのPoC実装
検証項目: 技術的実現可能性とアーキテクチャの妥当性
期間: 3-4週間（Phase3まで完全実装）
2. システムアーキテクチャ
User (Streamlit UI)
    ↓
LangChain/LangGraph Agent
    ↓ (MCP Protocol)
MCP Server
    ├→ Tools (file_search, web_search, query_knowledge)
    └→ Knowledge Engine
        └→ Neo4j (Vector + Graph)
3. 技術スタック
レイヤー技術UIStreamlitAIエージェントLangChain/LangGraphLLMGPT-5-mini埋め込みOpenAI text-embedding-3MCPカスタムMCPサーバーデータベースNeo4j (Docker)環境Docker Compose (ローカル)
4. 機能要件
4.1 データソース

ローカルファイル（テキスト、CSV等）
Web検索
内部ナレッジベース（Neo4j既存データ）

4.2 ナレッジ蓄積

トリガー: AI応答完了の直後（1往復ごと）
処理: 非同期バックグラウンド実行
入力データ:

ユーザークエリ
AI応答
実行トレース（ツール呼び出し履歴）
データソース（メタデータ + 実際の内容）
抽出コンテンツ（LLMによる解析結果）



4.3 階層構造

2階層: 個人ナレッジ → チームナレッジ
アクセス制御: 個人ナレッジは本人のみ、チームナレッジはチーム全員
検索時: 検索クエリベースで、自分の個人 + チームナレッジを参照

4.4 自動昇格（集約処理）

方式: 類似度ベースの完全自動
実行: 定期バッチ処理（例: 1日1回）
判定基準:

ベクトル類似度: 0.75以上
最小貢献者数: 3名以上
カバレッジ: チームの50%以上



4.5 エラーハンドリング

LLM API失敗: リトライ
ナレッジ抽出が空: ユーザー指示を基にAIが独自判断で行動
重複ナレッジ: 別々に保存（統合は自動昇格時）
データリセット: 不要（間違いも含め全て残す）

5. データモデル（Neo4jグラフ構造）
5.1 ノードタイプ
cypher// ユーザー・組織
(:User {id, name, team_id})
(:Team {id, name})

// クエリ・実行
(:Query {id, text, user_id, timestamp})
(:AgentExecution {id, query_id, agent_model, status, started_at, completed_at})

// データソース（PROV Entity）
(:DataSource {id, type, path/url, content_type, raw_content, metadata, retrieved_at})

// ツール実行（PROV Activity）
(:ToolExecution {id, tool_name, input_query, execution_time_ms, timestamp})

// 抽出コンテンツ
(:ExtractedContent {id, source_id, content_type, summary, key_facts, extraction_method, confidence, extracted_at})

// ナレッジ
(:Knowledge {
  id, type, content, category, 
  hierarchy_level, owner_id, confidence, 
  embedding, created_at
})
5.2 リレーション（PROV準拠）
cypher(:User)-[:ASKED]->(:Query)
(:Query)-[:TRIGGERED]->(:AgentExecution)
(:AgentExecution)-[:USED {step_number, reasoning}]->(:ToolExecution)
(:DataSource)-[:WAS_GENERATED_BY]->(:ToolExecution)
(:ExtractedContent)-[:DERIVED_FROM {extraction_prompt, llm_model}]->(:DataSource)
(:Knowledge)-[:SYNTHESIZED_FROM {synthesis_method}]->(:ExtractedContent)
(:Knowledge)-[:ATTRIBUTED_TO]->(:User)
(:Knowledge)-[:SIMILAR_TO {similarity_score, compared_at}]->(:Knowledge)
```

## 6. 処理フロー

### 6.1 リアルタイムナレッジ蓄積
```
1. ユーザー入力
2. LangChain Agentが処理
   ├→ MCP Tool: file_search → DataSource取得
   ├→ MCP Tool: web_search → DataSource取得
   └→ MCP Tool: query_knowledge → 既存ナレッジ参照
3. AIが情報統合・ナレッジ抽出（Agent内部処理）
4. AI応答をユーザーに表示
5. MCP Tool: save_knowledge → Neo4jに保存
   - プロベナンス完全記録
   - ベクトル埋め込み生成
```

### 6.2 定期バッチ処理（自動昇格）
```
1. 個人ナレッジをチームごとに収集
2. ベクトル類似度を計算
3. 類似度 > 0.75 かつ 3名以上が保持
4. チームナレッジとして新規作成
5. 元の個人ナレッジは保持（削除しない）
7. MCPサーバーツール定義
ツール名説明入力出力file_searchローカルファイル検索query, file_types{path, content, metadata}web_searchWeb検索・取得query{url, content, metadata}query_team_knowledge既存ナレッジ検索query, user_id[{knowledge}, ...]save_knowledgeナレッジ保存{knowledge, provenance}{id, status}
8. ユーザー・チーム管理

方式: YAMLファイルでハードコード
例:

yamlusers:
  - id: user1
    name: 田中太郎
    team: team_sales
  - id: user2
    name: 佐藤花子
    team: team_sales

teams:
  - id: team_sales
    name: 営業チーム
9. 成功基準
シナリオ:

3人のユーザーが同じトピックでAI利用
各自に個人ナレッジが蓄積
定期バッチ実行
チームナレッジが自動生成
4人目が質問 → チームナレッジを参照して回答

達成条件: 上記が動作すればPoC成功
10. スコープ外

❌ 3階層以上（部・会社レベル）
❌ 高度なアクセス制御（ロールベース等）
❌ UIの作り込み
❌ 本番環境向けスケーラビリティ
❌ 詳細なモニタリング・ログ
❌ ナレッジの削除・編集機能

11. 実装フェーズ
Phase 1 (1週目): 基本実装

ローカルファイル検索
簡易トレーシング（ツール名と結果のみ）

Phase 2 (2週目): 拡張

Web検索統合
詳細トレーシング（推論過程含む）

Phase 3 (3週目): 完成

複数データソース統合
完全自動集約処理
矛盾検出・解決