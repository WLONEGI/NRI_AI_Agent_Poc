0. 目的と基本方針

目的：

社内で発生する教訓・ノウハウ・事例を自動的にカード化（構造化）し蓄積・検索可能にする。

AIエージェントの利用過程でユーザー操作なしにナレッジが溜まる仕組みをPoCで実現する。

方針：

MCPサーバは「蓄積」と「検索」の最小機能のみを提供（1Tool / 1Resource）。

埋め込みはローカル（オンプレ）で実施。

Graph＋Vector＋全文（BM25）のハイブリッド検索構成。

PoC目的のため監視・本番セキュリティ・承認フローは除外。

1. 全体構成

クライアント（MCP対応AIエージェント）

Tool: store_knowledge

Resource: knowledge://search

Auto Capture Middleware（自動カード化ミドルウェア）を内蔵

サーバ（MCP Server）

FastMCP（Python / mcp-python-sdk）

内部モジュール：API Layer, Ingest Core, Search Core, Applicability Match, Embedding Cache

データ層

Graph DB（Neo4jまたはMemgraph）

Vector / BM25 Index

Local Embedding Service（FastAPI + sentence-transformers）

2. MCPサーバ 公開インターフェース

Tool: store_knowledge(text_blob, scope, tags[], type?)

役割：自由記述をCard構造に抽出・正規化して保存

出力：card_id, normalized_fields, quality, embedding_model, version

Resource: knowledge://search?q=&scope=&k=&filters=&quality=&locale=&visibility=

役割：ハイブリッド検索（Vector × BM25 × Graph）

出力：cards[]（score, warnings, explanations）

3. 内部モジュール構成
🟩 蓄積系（store_knowledge）

API Layer

Tool呼び出しをIngest Coreへルーティング

Ingest Core

抽出・正規化（LLM温度0）

Schema検証（必須項目: title, situation, action）

欠損補完（fallback rule）

content_hash計算とUpsert処理

Embedding Service

ローカルFastAPIサービス（POST /embed）

モデル例：multilingual-e5-base

Embedding Cache

LRUキャッシュ、キー＝(text, model)

Graph DB

ノード：:Card

リレーション：:SUPPORTS, :CONTRADICTS, :CANDIDATE_SUPPORTS, :CANDIDATE_CONTRADICTS

Indexes

Vector index：Card.embedding

Fulltext index：title, situation, action, outcome

🟥 検索系（knowledge://search）

API Layer

Resource呼び出しをSearch Coreへルーティング

Search Core

Vector TopK + BM25 TopKを統合

scope/tags/type/locale/visibility/qualityでフィルタ

1-hopグラフ拡張（SUPPORTS/CONTRADICTS）

再ランク：
score = W_SIM*sim + W_FIT*fit + W_SUP*support - W_CON*contradict

Applicability Match

applicability / anti_applicability とクエリ条件の一致スコアを計算

Graph DB

SUPPORTS/CONTRADICTS関係の1-hop探索

Indexes

Vector索引（近似検索）

Fulltext索引（BM25）

Embedding Service

クエリのベクトル化

Logging / Metrics

処理時間・モデル・スコア内訳を構造化出力

4. データモデル（Card構造）
Card {
  id: string,
  title: string,
  type: 'lesson'|'guideline'|'pitfall'|'case-study'|'faq',
  situation: string,
  action: string,
  outcome: string,
  applicability: string[],
  anti_applicability?: string[],
  rationale?: string,
  tags?: string[],
  scope: 'personal'|'team'|'org',
  visibility?: 'public'|'restricted',
  quality: 'draft'|'verified',
  locale?: string,
  evidence?: {source: string, quote?: string}[],
  embedding_model: string,
  embedding_dim: number,
  content_hash: string,
  embedding: number[],
  created_at, updated_at, version
}

5. 蓄積（store_knowledge）処理フロー

受信：text_blob, scope, tags, type

正規化：改行統一、記号除去、PIIマスク

抽出：LLM温度0でtitle, situation, action, outcome等を抽出

Schema検証：欠損をnull許容、型・列挙値検証

content_hash生成・Upsert（既存→version++）

埋め込み生成（キャッシュ優先）

Graph登録（:Cardノード作成）

SUPPORTS/CONTRADICTS候補生成（CANDIDATE_*として）

応答返却（card_id, normalized_fields）

6. 検索（knowledge://search）処理フロー

クエリ埋め込み生成（ローカルEMB）

Vector TopK（k=32）＋BM25 TopK（k=32）収集

結果統合→重複除去

scope, tags, type, locale, quality, visibilityでフィルタ

1-hopグラフ拡張（SUPPORTS, CONTRADICTS）

適用条件一致度（fit）算出

再ランク計算

環境変数調整可：
W_SIM=0.5, W_FIT=0.25, W_SUP=0.15, W_CON=0.10

反例（CONTRADICTS）があればwarnings[]に追加

出力：cards[score, highlights, warnings, explanations]

7. AIエージェント（自動カード化ミドルウェア）
7.1 目的

ユーザーが特別な操作をせず、AIエージェントの利用過程（会話・タスク実行）から自動的にナレッジを登録。

7.2 監視ポイント（イベントフック）

タスク完了（完了報告・成果物出力時）

成果確定（文書生成・設計・振り返り確定時）

エラー解決（失敗→成功の学習イベント）

過去カードの再利用（SUPPORTS候補生成）

7.3 自動登録フロー

エージェントがイベントを検出

inputs, steps, outputs, errors から教訓文を自動要約

適格判定（内容長・具体性・重複・安全性）

条件を満たせば store_knowledge を自動呼び出し

成功時は構造化ログ出力

7.4 登録抑制ルール

文字数 < 400 文字 → 登録しない

同一content_hashが7日以内に存在 → 登録スキップ

固有名詞/数値比率 < 5% → 除外（抽象的すぎる）

機密語検出時 → 除外

1ユーザーあたり1日3カードまで（AUTO_CAPTURE_MAX_PER_DAY）

7.5 自動登録パラメータ
環境変数	デフォルト	説明
AUTO_CAPTURE_ENABLED	true	自動カード化ON/OFF
AUTO_CAPTURE_SCOPE_DEFAULT	team	既定スコープ
AUTO_CAPTURE_VISIBILITY_DEFAULT	restricted	共有範囲
AUTO_CAPTURE_MIN_SUMMARY_CHARS	400	要約最小長
AUTO_CAPTURE_MAX_PER_DAY	3	登録上限/日
8. Graphと関係データ仕様

ノード

(:Card {id, title, embedding, tags, ...})

関係

(:Card)-[:SUPPORTS {strength: float}]->(:Card)

(:Card)-[:CONTRADICTS {strength: float}]->(:Card)

(:Card)-[:CANDIDATE_SUPPORTS]->(:Card)（PoCでは候補）

(:Card)-[:CANDIDATE_CONTRADICTS]->(:Card)（PoCでは候補）

関係生成

新カード登録時、近傍TopNから自動候補生成

強度（strength）＝cosine類似度閾値（例：0.6以上）

9. 検索スコアリング式
score = W_SIM*similarity
      + W_FIT*fit_score
      + W_SUP*support_strength
      - W_CON*contradict_strength


各重みは環境変数で設定可能。

CONTRADICTS存在時は warnings[] に要約付きメッセージ。

score < 0.4 は非表示、0.4–0.6 は low_confidence=true。

10. キャッシュ仕様

Embedding Cache

キー：(content_hash, model)

LRUキャッシュ上限：10,000件

TTL：永続（手動クリア）

Search Result Cache

キー：(q, filters, model, weights)

TTL：60秒

重量級クエリの負荷を軽減

11. デプロイ構成

Docker Composeサービス：

embed：FastAPI + sentence-transformers

graph：Neo4j 5.x（APOC有効）

mcp-server：FastMCPアプリケーション

環境変数設定例：

EMBED_PROVIDER=local
EMBED_ENDPOINT=http://embed:8090/embed
EMBED_MODEL=multilingual-e5-base
GRAPH_URI=bolt://graph:7687
GRAPH_USER=neo4j
GRAPH_PASS=test
SEARCH_W_SIM=0.5
SEARCH_W_FIT=0.25
SEARCH_W_SUP=0.15
SEARCH_W_CON=0.10
AUTO_CAPTURE_ENABLED=true

12. 非機能要件
項目	目標値
p95応答時間（初回）	≤ 1.5s
p95応答時間（キャッシュヒット）	≤ 0.8s
同時処理耐性	10並列まで安定
抽出必須フィールド充足率	≥ 95%
type推定F1スコア	≥ 0.8
検索Recall@10	≥ 0.6
反例警告提示率	≥ 80%
埋め込みキャッシュヒット率	≥ 70%
13. ロギング・トレーサビリティ

構造化ログ形式（JSON Lines）：

ts, req_id, actor_id, op, elapsed_ms, model, quality, version, auto_capture

出力先：/logs/app.log

再現性確保項目：

embedding_model, embedding_dim, weights(W_SIM..W_CON), content_hash

14. テスト計画（受入）
テスト項目	検証内容	合格基準
抽出精度	title/situation/action/outcome抽出	90%以上正確
重複排除	同一文書登録時version++	OK
自動蓄積	AIエージェントから自動登録	3件/日上限内
反例警告	CONTRADICTS付きカードでwarning出力	表示あり
検索精度	Recall@10 ≥ 0.6	合格
性能	p95 ≤ 1.5s	合格
ログ整合	全処理でreq_id一貫	合格
15. 成果物（PoC Deliverables）

MCPサーバ実装（mcp-knowledge）

AIエージェント自動蓄積モジュール（auto_capture_middleware）

seed_cards.jsonl（初期カードセット）

evaluation.py（Recall/MRR測定）

verify-searchスクリプト（自動評価）

構造化ログテンプレート＋分析Notebook