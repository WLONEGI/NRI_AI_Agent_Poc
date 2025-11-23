# PoC要件定義書テンプレ（MCPナレッジPoC）

> 本テンプレートは、AIエージェント対話から自動的に知識を捕捉・構造化し、Graph＋Vectorで検索・再利用する **MCPサーバ（AWSサーバーレス）** のPoC向け要件定義書です。**太字＝確定事項／_斜体＝TBD（決定待ち）** を推奨表記とします。必要に応じて章を増減してください。

---

## ドキュメント情報

* 文書タイトル：PoC要件定義書（MCPナレッジPoC）
* バージョン：v0.1（初稿）
* 作成日：YYYY-MM-DD
* 作成者：
* レビュー／承認：
* ステータス：ドラフト｜レビュー中｜承認済み
* 変更履歴：

  | 版   | 日付         | 変更内容 | 作成/変更者 |
  | --- | ---------- | ---- | ------ |
  | 0.1 | YYYY-MM-DD | 初版作成 |        |

---

## 1. 背景・目的

* 背景：社内AI活用の加速に伴い、**AI対話・ツール実行の過程で生まれるナレッジを自動で捕捉・管理**し、組織学習を促進する基盤が必要。
* 目的：**MCP接続のAIが社内情報に特化したコンテキストを活用**できるようにし、検索・再利用性を高める。
* 本PoCで検証する価値：

  * **B: 可視化UI（閲覧のみ）**でナレッジの可視確認が可能。
  * 検索再利用により**回答精度／コンテキスト一致の主観的改善**が体感できる。

## 2. スコープ

* 対象機能（含む）：取り込み、検索/再利用、閲覧UI（編集なし）、個人/チーム2層のアクセス制御。
* 対象外（PoC範囲外）：編集・承認ワークフロー、本番レベル監視/監査ログ、高可用構成、広域スケール試験。

## 3. ゴールと成功指標

* ゴール：**AI対話 → 自動知識化 → 検索/再利用 → 可視化UI（閲覧）**までのデモを成立。
* KPI/評価：

  * 主観評価での**精度/コンテキスト一致の改善**（5段階）。
  * PoCチーム**10名**が継続利用したいと感じるか。
  * 体感速度（検索→提示）に実用感があるか。

## 4. 想定ユーザー & 利用形態

* 利用者：**社内PoCチーム10名**
* クライアント：**MCP対応クライアント**（OpenAI／VS Code拡張／社内ツール）
* 利用言語：**日本語主体**

## 5. 全体アーキテクチャ（高レベル）

* 実装ランタイム：**AWS Lambda（サーバーレス）**
* MCPサーバ：**modelcontextprotocol/python-sdk 前提**
* フロント：SPA（S3+CloudFront）［閲覧専用］**Vite + React**
* 認証/認可：**Amazon Cognito（Auth Code + PKCE）**、Cognitoグループ/IdP属性でチーム付与
* ネットワーク：**ALB** → VPC内Lambda、**社内IP許可のAllowlist（172.26.138.0/24）**
* データ：**S3（原本）＋ OpenSearch Serverless（Vector）＋ Neptune Serverless（Graph）**
* リージョン：**ap-northeast-1**

```
[MCPクライアント] --HTTPS--> [ALB(OIDC/Cognito)]
                               |
                               v
                        [Lambda: API]
                           |      \
                       (/ingest)  (/query)
                           |         |
                   [前処理: PIIマスク/正規化]
                           |
                           v
                    [S3 原本(JSONL)]
                           |
                 [Step Functions：非同期]
                      |                 \
                      v                  v
            [埋め込み/チャンク → OpenSearch]   [NER/関係抽出 → Neptune]
                       \                /
                        \---->  [検索UI(閲覧のみ)]
```

## 6. 機能要件

### 6.1 取り込み（ingest）

* 対象：会話テキスト、**ツール呼び出し・結果**、添付（PDF/画像はTextractで抽出）
* PII前処理：**Comprehend（英/西）＋日本語はルールベース補完**
* 保存：S3に原本（JSON Lines）、メタ付与（speaker, sessionId, ts, scope など）
* 非同期パイプライン：チャンク/埋め込み、NER/関係抽出

### 6.2 検索/再利用（query）

* Vector近傍検索（OpenSearch）で候補抽出
* Graph近傍（Neptune）で関連補完（任意）
* MCPへはコンテキスト（snippet＋docId）を返却、UIは詳細閲覧可能

### 6.3 可視化UI（閲覧のみ）

* 検索フォーム、結果一覧、スニペット/メタ、原文ビュー
* 簡易グラフビュー（**react-force-graph採用**、読み取り専用）

### 6.4 アクセス制御（2層）

* スコープ：**個人知識／チーム知識**
* 公開：**本人操作で即時**／チーム横断アクセスは不可
* グループ割当：**Cognitoグループ/IdP属性を自動反映**

## 7. インターフェース仕様

### 7.1 MCPツール（Tool）

* `search_knowledge`

  * 入力：`{ q, topK, scope:"personal|team", filters? }`
  * 出力：`{ hits:[{docId, snippet, score, meta}], relatedGraph? }`
* `capture_interaction`

  * 入力：`{ sessionId, speaker, text?, toolCall?, toolResult?, scope, metadata? }`
  * 出力：`{ status:"accepted", docId }`
* `promote_to_team`

  * 入力：`{ docId }` → 出力：`{ status:"ok" }`
* （任意）`get_graph_neighbors`

  * 入力：`{ entity, hops=1 }` → 出力：`{ nodes, edges }`

> ※ Toolは**可変パラメータのアクション**、大きな本文は **MCP Resource** で公開（例：`kb://doc/{id}`）。

### 7.2 REST API（ALB経由, JWT必須）

| Method | Path     | 説明                 | 主なパラメータ                                           |
| ------ | -------- | ------------------ | ------------------------------------------------- |
| POST   | /ingest  | 取り込み受理（非同期処理起動）    | sessionId, speaker, text/toolCalls/results, scope |
| POST   | /query   | 検索（Vector±Graph補完） | q, topK, scope, filters                           |
| POST   | /promote | 個人→チーム公開           | docId                                             |

**Auth**：Authorization: Bearer <JWT>（Cognito発行）。JWK検証、`sub`/`groups` をスコープ判定に利用。

#### 7.2.1 リクエスト/レスポンス例（サンプル）

```jsonc
// POST /query (request)
{
  "q": "運用フロー",
  "topK": 8,
  "scope": "team",
  "filters": {"toolType": "jira"}
}
```

```jsonc
// /query (response)
{
  "hits": [
    {"docId": "doc_123", "snippet": "…", "score": 0.82, "meta": {"sessionId": "s1", "ts": "2025-11-01T09:00:00Z"}}
  ],
  "relatedGraph": {"nodes": [], "edges": []}
}
```

## 8. データ要件

### 8.1 スキーマ（最小）

* **S3 原本（JSON Lines）**

  ```jsonc
  {"docId":"…","ownerId":"u1","teamId":"t1","scope":"personal|team",
   "text":"…","lang":"ja","piiMasked":true,
   "toolCall":{…},"toolResult":{…},
   "sessionId":"…","createdAt":"…"}
  ```
* **OpenSearch（index: knowledge_chunks）**

  * `id, ownerId, teamId, scope, text, embedding(vector), sessionId, toolType, ts`
* **Neptune（Property Graph）**

  * Node：`Entity(type,name,normName)`, `Doc(id,kind)`
  * Edge：`MENTIONS(Doc→Entity)`, `RELATES(Entity↔Entity,relType)`, `DERIVED_FROM`

### 8.2 埋め込みモデル

* **Amazon Bedrock** を使用（日本語対応優先）

### 8.3 PIIマスキング

* 方式：**Comprehend（英/西）＋日本語は正規表現/辞書で補完**
* 対象：氏名/メール/電話/住所/社員ID など基本PII
* 可逆性：**不可逆マスク**を基本（原文はS3原本で暗号化保存）

### 8.4 データ保持・ライフサイクル

* 保持期間：**90日**（S3 Lifecycle設定で自動削除）／削除方針：PoC終了時に全消去

## 9. セキュリティ/プライバシー

* 認証：**Cognito（Auth Code + PKCE）**
* 認可：JWT `sub`/`groups` で個人/チームを判定
* ネットワーク：**社内IP Allowlist（172.26.138.0/24）**、VPC内通信
* 暗号化：S3/Neptune/OpenSearch は **KMS暗号化**
* 監査：CloudWatch最小限の監査ログ（PoC範囲）

## 10. 非機能要件

* パフォーマンス：**~10 rps** 目安、Lambdaタイムアウト短め、重処理は非同期
* 可用性：単AZ可（PoC）
* 観測性：最低限のメトリクス/ログ（詳細基盤は対象外）
* コスト：**月5万円以内**（最小キャパで開始、データ量を抑制）

## 11. 運用・環境

* 環境：Dev / PoC（単一でも可）
* 開発：**ローカル環境からAWSリソースへの接続（ハイブリッド開発）を許容**
* デプロイ：IaC（**AWS CDK / TypeScript**）
* リリース：**All-at-once（一括更新）**
* バックアップ：S3バージョニング、Neptune/OSはスナップショット（最小）

## 12. テスト/検証計画

* 機能テスト：取り込み→検索→閲覧のE2E
* 評価テスト：**前後比較（10名×3タスク）**／5段階主観評価
* セキュリティテスト：認証・スコープ越境の無いこと
* 性能テスト：軽負荷（~10 rps）

## 13. リスク・制約・前提

* 日本語PIIの検出精度（ルール補完）
* OpenSearch/Neptuneの固定コスト（容量/設定最小で運用）
* OAuthトークン取得フロー：**ローカル補助スクリプト（auth-helper）により、ブラウザ認証→設定ファイル自動更新を行い、ユーザ負担を最小化する**

## 14. 変更管理・課題管理

* 変更申請：テンプレ（影響範囲・ロールバック手順含む）
* 課題トラッキング：Jira/Issues 等（リンク *TBD*）
* **決定事項（クリティカル解消）**：

  1. **社内IP帯 CIDR**：172.26.138.0/24（ALB Allowlistに設定）
  2. **IdP連携**：Cognito単独（User Pool）
  3. **埋め込みモデル**：Amazon Bedrock
  4. **添付取り込み**：Textractをパイプラインに組み込み
  5. **保持期間（TTL）**：90日（S3 Lifecycleで自動削除）

## 15. 受け入れ基準（Acceptance Criteria）

* [ ] MCPクライアントからの取り込みが成功し、S3原本に保存される
* [ ] ベクトル検索で意図した候補が **topK** 内に表示される
* [ ] UIでスニペット/原文/メタが閲覧できる
* [ ] （任意）グラフビューで主要関係が1ホップ表示される
* [ ] 個人/チームのスコープが期待どおりに制御される
* [ ] 主観評価で**利用者の半数以上（5名以上）が『検索精度が向上した』と回答すること**

## 付録A：APIスキーマ雛形

```jsonc
{
  "paths": {
    "/ingest": {"post": {"requestBody": {"content": {"application/json": {"schema": {"type": "object"}}}}}},
    "/query": {"post": {"requestBody": {"content": {"application/json": {"schema": {"type": "object"}}}}}},
    "/promote": {"post": {"requestBody": {"content": {"application/json": {"schema": {"type": "object"}}}}}}
  }
}
```

## 付録B：MCP Tool 定義雛形（JSON Schema）

```jsonc
{
  "name": "search_knowledge",
  "description": "Vector+Graphでナレッジ検索",
  "input_schema": {
    "type": "object",
    "properties": {
      "q": {"type": "string"},
      "topK": {"type": "integer", "default": 8},
      "scope": {"type": "string", "enum": ["personal", "team"]},
      "filters": {"type": "object"}
    },
    "required": ["q", "scope"]
  }
}
```

## 付録C：用語集（抜粋）

* MCP（Model Context Protocol）：AIクライアントとツール/リソースを接続するプロトコル
* Vector検索：埋め込みベクトルによる近傍検索
* Graph：エンティティと関係をノード・エッジで表現
* スコープ：個人/チームのアクセス境界
