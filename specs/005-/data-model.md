# Data Model: Crystal Intelligence風ナレッジ統合システム PoC

## Entity Overview

| Entity | Description | Identifier | Key Relationships |
|--------|-------------|------------|-------------------|
| User | PoC参加ユーザー。所属チームとアクセス制御に利用。 | `user_id` (string, UUID or slug) | `User`-[:MEMBER_OF]->`Team`, `User`-[:AUTHORED]->`Knowledge`, `User`-[:ISSUED]->`Query` |
| Team | アクセス制御単位のチーム。 | `team_id` (string) | `Team`-[:HAS_MEMBER]->`User`, `Team`-[:OWNS]->`Knowledge` |
| Query | Streamlit UI経由で送信されたクエリとメタ情報。 | `query_id` (string) | `Query`-[:INITIATED_BY]->`User`, `Query`-[:RESULTED_IN]->`AgentExecution` |
| AgentExecution | LangChain/LangGraphエージェントの実行セッション。 | `execution_id` (string) | `AgentExecution`-[:TRIGGERED_BY]->`Query`, `AgentExecution`-[:USED_TOOL]->`ToolExecution` |
| ToolExecution | MCPツール呼び出し記録。 | `tool_execution_id` (string) | `ToolExecution`-[:DERIVES_FROM]->`AgentExecution`, `ToolExecution`-[:READ_FROM]->`DataSource` |
| DataSource | ファイルやWebなど取得元。 | `data_source_id` (string) | `DataSource`-[:FEEDS]->`ExtractedContent` |
| ExtractedContent | 抽出・要約内容。 | `content_id` (string) | `ExtractedContent`-[:SYNTHESIZED_TO]->`Knowledge` |
| Knowledge | 個人/チームナレッジノード。 | `knowledge_id` (string) | `Knowledge`-[:CAPTURED_FROM]->`Query`, `Knowledge`-[:ATTRIBUTED_TO]->`User`, `Knowledge`-[:PROMOTED_FROM]->`Knowledge` |

## Detailed Schemas

### User
- `user_id`: string (primary key)
- `name`: string
- `email`: string (optional, PoCでは任意)
- `team_id`: string (FK to Team)
- `role`: enum {"individual", "team_admin"} (default individual)
- Audit: `created_at`, `updated_at`

Constraints:
- `user_id` unique、`team_id`必須。
- 削除は非サポート（PoCでは論理削除せず）。

### Team
- `team_id`: string (primary key)
- `name`: string
- `description`: string (optional)

Constraints:
- `team_id` unique。
- チーム削除は不可。

### Query
- `query_id`: string (primary key)
- `user_id`: string (FK to User)
- `text`: text
- `submitted_at`: datetime (timezone-aware)
- `channel`: enum {"streamlit"}（将来拡張用）

Constraints:
- `user_id`存在必須。
- `text`1文字以上。

### AgentExecution
- `execution_id`: string (primary key)
- `query_id`: string (FK)
- `model_name`: string
- `started_at`: datetime
- `ended_at`: datetime
- `status`: enum {"success","failed","partial"}
- `latency_ms`: integer

Constraints:
- `ended_at >= started_at`
- `latency_ms`自動計算。

### ToolExecution
- `tool_execution_id`: string (primary key)
- `execution_id`: string (FK)
- `tool_name`: enum {"file_search","web_search","query_team_knowledge","save_knowledge"}
- `input_payload`: json
- `output_payload`: json
- `started_at`: datetime
- `ended_at`: datetime
- `status`: enum {"success","failed"}

Constraints:
- `ended_at >= started_at`
- `tool_name`は列挙内。

### DataSource
- `data_source_id`: string (primary key)
- `origin_type`: enum {"file","web","knowledge"}
- `uri`: string (file path / URL / knowledge id)
- `owner_team_id`: string (optional)
- `metadata`: map<string,string>

Constraints:
- `origin_type`に応じて`uri`フォーマットを検証。

### ExtractedContent
- `content_id`: string (primary key)
- `summary`: text
- `facts`: list<string>
- `confidence`: float (0-1)
- `data_source_id`: string (FK)

Constraints:
- `confidence`範囲: 0.0 ≤ x ≤ 1.0。

### Knowledge
- `knowledge_id`: string (primary key)
- `level`: enum {"personal","team"}
- `owner_user_id`: string (FK to User, personal時必須)
- `owner_team_id`: string (FK to Team, team時必須)
- `title`: string
- `content`: text
- `category`: string
- `embedding`: float[512]
- `similarity_threshold`: float (昇格判定時の記録)
- `vector_created_at`: datetime
- `access_tags`: list<string>
- `created_at`: datetime

Constraints:
- `level=personal`なら`owner_user_id`必須、`owner_team_id`任意。
- `level=team`なら`owner_team_id`必須、`owner_user_id`任意。
- `embedding`必須。生成失敗時はNULL許容とし、再計算フラグを付与。

### Promotion Audit (Log)
- `promotion_id`: string (primary key)
- `source_knowledge_ids`: list<string>
- `target_knowledge_id`: string (FK)
- `executed_by`: string (user id or "batch")
- `executed_at`: datetime
- `similarity_score`: float
- `contributors`: list<string>
- `team_coverage_ratio`: float (0-1)
- `status`: enum {"promoted","skipped"}
- `reason`: string (skip時)

## Relationships Graph Summary

```
(User)-[:MEMBER_OF]->(Team)
(User)-[:ISSUED]->(Query)-[:RESULTED_IN]->(AgentExecution)-[:USED_TOOL]->(ToolExecution)-[:READ_FROM]->(DataSource)
(DataSource)-[:FEEDS]->(ExtractedContent)-[:SYNTHESIZED_TO]->(Knowledge)
(Knowledge)-[:CAPTURED_FROM]->(Query)
(Knowledge)-[:ATTRIBUTED_TO]->(User)
(Knowledge personal)-[:PROMOTED_TO]->(Knowledge team)
(PromotionAudit)-[:CREATED]->(Knowledge team)
```

## Validation & Indexes
- Neo4j constraints:
  - `CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE`
  - 同様に`Team`, `Query`, `AgentExecution`, `ToolExecution`, `Knowledge`にユニーク制約。
  - `CALL db.index.vector.createNodeIndex("knowledge_embedding", "Knowledge", "embedding", 512, "cosine")`
- Appレイヤー検証:
  - `content`長は最大10,000文字。
  - `facts`リストは10件以内。
  - 昇格判定時に`contributors`重複禁止。

## State Transitions
- Knowledge
  - `personal:draft`（保存直後）→`personal:active`（保存成功）→`team:promoted`（昇格バッチ実行）
  - 失敗時は`personal:retry_pending`でバックオフ再実行。
- PromotionAudit
  - `created` → `notified` （Slack通知済み）

## Data Volume Assumptions
- 1日最大100クエリ、ToolExecutionはクエリあたり最大5件。
- 個人ナレッジはユーザーあたり最大300件、チームナレッジは50件程度。
- 埋め込みベクトル数はPoC期間中に8kノード以下。
