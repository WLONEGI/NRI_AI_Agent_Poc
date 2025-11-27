
## 1. 概要

### 1.1 背景

社内で利用する AI エージェント（ChatGPT）との対話の中には、手順やルール、設計方針など、後から再利用可能な「ナレッジ」が多く含まれている。
現状これらは会話ログの中に埋もれており、体系的に蓄積・検索して再利用する仕組みがない。

### 1.2 目的

本要件定義書は、以下を満たす **ローカル専用ナレッジメモリ MCP サーバ** の要件を定義する。

* ChatGPT から MCP 経由で呼び出し可能
* 会話の中から重要なナレッジだけを Markdown 形式で保存
* 保存済みナレッジをキーワードベースで検索・参照できる

### 1.3 コンセプト

* 仕組みの基本思想は Serena MCP の「メモリ機能」を模倣する

  * `write_memory / read_memory / list_memories / delete_memory` の API 群
  * その裏側で Markdown + YAML によるメモリファイルを管理
* Embedding（ベクトル埋め込み）は使わず、**完全ローカル + テキストファイルのみ**で実現する。

---

## 2. システム全体像

### 2.1 全体イメージ

* ChatGPT（MCP クライアント）から、ローカルで起動した MCP サーバへ接続する。
* MCP サーバは、ローカルディスク上の `<memory_root>` 配下にメモリファイル群を保持する。
* ChatGPT は、会話の中で重要だと判断したタイミングで `write_memory` を呼び、
  記憶を参照したいときに `search_memories` / `read_memory` を呼び出す。

### 2.2 利用シナリオ

1. **対話からのナレッジ保存**

   * ユーザと ChatGPT が業務の話をしている中で、
     LLM が「これは長期的に再利用すべき」と判断した場合のみ `write_memory` を呼ぶ。
   * 1 回の会話から複数のメモリ（例：`architecture`, `billing-flow` 等）を作成してよい。

2. **ナレッジ検索・参照**

   * ユーザの質問に回答する際、事前に `search_memories` で関連メモリを検索し、
     必要なものを `read_memory` で取得してから回答を生成する。

---

## 3. スコープ

### 3.1 対象範囲（本システムで実現するもの）

* ChatGPT から MCP 経由で呼び出せる **メモリ操作 API 群** の提供

  * メモリの作成・更新（write）
  * メモリの取得（read）
  * メモリ一覧の取得（list）
  * メモリ削除（delete）
  * メモリ全文検索（search）
* メモリの永続化

  * Markdown（`.md`）＋ YAML（front matter / index）による保存
* 検索機能

  * Embedding を利用しないキーワードベース全文検索
  * 日本語を主対象とした検索

### 3.2 非対象範囲（本フェーズでは扱わないもの）

* Web UI / GUI によるナレッジ閲覧・管理
* 認証・認可
* 既存ナレッジ基盤（Confluence / Notion 等）との統合
* ベクタ DB / Embedding モデルによる高精度セマンティック検索
* ネットワーク越しの共有サーバ（あくまでローカル前提）

---

## 4. 前提条件・制約

### 4.1 実行環境

* MCP クライアント: ChatGPT
* MCP サーバ:

  * MCP Python SDK（`mcp.server.fastmcp.FastMCP`）を使用
  * 通信方式: `stdio`（標準入出力）による接続
* OS:

  * macOS / Linux を優先サポート
* 言語／ランタイム:

  * Python 3.10 以上

### 4.2 ストレージ

* ローカルファイルシステムのみ使用
* ファイル形式:

  * ナレッジ本文: Markdown（`.md`）
  * インデックス・設定: YAML（`.yaml`）
* 文字コード: UTF-8

### 4.3 ネットワーク・セキュリティ

* 外部 API へのアクセスなし（完全ローカル完結）
* アプリケーションレベルの認証・認可は行わない
  → 利用者は当該マシンにログイン可能なユーザに限定

---

## 5. 機能要件

### 5.1 MCP サーバ本体

* サーバ名: `local-memory-store`（案）
* 起動:

  * ローカルコマンドとして実行し、ChatGPT から MCP サーバとして登録
* 機能:

  * MCP Tools として、以下のメモリ操作 API を提供する
    `write_memory`, `read_memory`, `list_memories`, `delete_memory`, `search_memories`

---

### 5.2 メモリ操作 API 詳細

#### 5.2.1 write_memory

**目的**
名前付きメモリの作成・更新（追記または上書き）を行う。

**入力項目（要求）**

* `memory_name`（string, 必須）

  * メモリを一意に識別するキー
* `content_markdown`（string, 必須）

  * メモリ本文（Markdown）。front matter を含まない想定（front matter はサーバ側で生成）
* `tags`（list[string], 任意）

  * 自由タグ（0 個以上）
* `source_session_id`（string, 任意）

  * 生成元となった ChatGPT セッションの ID
* `source_user_id`（string, 任意）

  * 利用ユーザ識別子
* `append`（bool, 任意・デフォルト: false）

  * true: 既存メモリがあれば末尾に追記
  * false: 既存メモリがあれば本文を上書き

**出力項目（要求）**

* `memory_name`
* `path`（メモリファイルのパス）
* `created`（新規作成かどうかのフラグ）
* `updated_at`

**動作要件**

1. `memory_name` に対応するファイルパスを決定する。
2. 対応する Markdown ファイルが存在する場合：

   * `append=false` の場合：本文を置き換え、`updated_at` 更新
   * `append=true` の場合：本文末尾に追記し、`updated_at` 更新
3. 存在しない場合：

   * 新規に Markdown ファイルを作成し、`created_at` / `updated_at` を設定
4. front matter にメタ情報（memory_name, title, tags, source 等）を付与・更新する。
5. `index.yaml` にメタ情報（memory_name, title, path, tags等）を登録・更新する。
6. 異常時にはエラーコード・メッセージを返す。

---

#### 5.2.2 read_memory

**目的**
指定した `memory_name` のメモリを取得する。

**入力項目**

* `memory_name`（string, 必須）

**出力項目**

* `memory_name`
* `metadata`

  * `title`
  * `created_at`
  * `updated_at`
  * `tags`
  * `source`（session_id, user_id など）
* `content_markdown`

  * front matter を含む Markdown 全文、または本文のみ（仕様としてどちらかに統一）

**動作要件**

1. `index.yaml` から `memory_name` に対応するファイルパスを取得。
2. 対応ファイルの存在を確認し、内容を読み込む。
3. front matter と本文をパースし、出力形式に整形する。
4. `memory_name` に対応するメモリが存在しない場合、適切なエラーを返す。

---

#### 5.2.3 list_memories

**目的**
保存済みメモリの一覧を取得する。

**入力項目**

* `prefix`（string, 任意）

  * `memory_name` のプレフィクスでフィルタ
* `tag_filter`（list[string], 任意）

  * 指定タグを含むメモリのみ返す
* `limit`（int, 任意・デフォルト: 50）

**出力項目**

メモリごとのメタ情報のリスト：

* `memory_name`
* `title`
* `created_at`
* `updated_at`
* `tags`

**動作要件**

1. `index.yaml` の全項目をロード。
2. `prefix` 指定がある場合、`memory_name` を前方一致でフィルタ。
3. `tag_filter` 指定がある場合、すべての指定タグを含むメモリのみ返す（AND 条件想定）。
4. `limit` 件まで返却。

---

#### 5.2.4 delete_memory

**目的**
指定メモリを削除する。

**入力項目**

* `memory_name`（string, 必須）

**出力項目**

* `memory_name`
* `deleted`（bool）
* `message`（任意の補足）

**動作要件**

1. `memory_name` に対応するファイルの存在を確認。
2. サーバとしての方針を以下から選択（要決定）：

   * 物理削除：Markdown ファイルを削除し、`index.yaml` からも削除
   * 論理削除：front matter に `deleted: true` を追加し、`index.yaml` にも削除フラグをセット
3. 削除済みメモリは `search_memories` や `list_memories` の結果から除外する。

---

#### 5.2.5 search_memories

**目的**
Embedding を使わず、キーワードベースでメモリを全文検索し、関連度の高いメモリを返す。

**入力項目**

* `query`（string, 必須）
* `top_k`（int, 任意・デフォルト: 5）
* `tag_filter`（list[string], 任意）

**出力項目**

類似度順に並んだメモリ情報のリスト：

* `memory_name`
* `title`
* `score`（0〜1 目安）
* `tags`
* `snippet`（本文の一部抜粋）

**動作要件**

1. `query` をトークン化（日本語を含むので簡易ルール or 形態素解析）。
2. `index.yaml` をもとに対象メモリを列挙。

   * `tag_filter` 指定があれば、それを満たすメモリのみ検索対象。
3. 各メモリについて：

   * Markdown ファイルを読み込み、タイトル・見出し・本文をトークン化。
   * クエリトークンとのマッチ数を元にスコアを算出。

     * タイトル命中 > 見出し命中 > 本文命中 のように重みづけ。
4. スコア順にソートし、上位 `top_k` 件を返す。
5. 一定件数以上のメモリが存在する場合、性能のためにキャッシュ等の検討余地あり（将来拡張）。

---

## 6. データ要件

### 6.1 ディレクトリ構造

```text
<memory_root>/
  memories/
    YYYY/
      MM/
        YYYYMMDD-<slug>.md
  index.yaml
  config.yaml
  logs/
    memory-mcp.log
```

* `<memory_root>` は設定ファイルまたは環境変数から指定。
* 日付単位のディレクトリ分割（`YYYY/MM/`）でファイル数を分散。

### 6.2 メモリファイル構造（Markdown）

```markdown
---
memory_name: "billing-flow"
title: "請求処理ワークフローの確定版"
created_at: "2025-11-24T09:15:00+09:00"
updated_at: "2025-11-24T09:20:00+09:00"
source:
  type: "chat"
  agent: "chatgpt"
  session_id: "abc123"
  user_id: "u001"
tags:
  - "経理"
  - "請求処理"
importance: "normal"
version: 1
---

## 要約

...

## 詳細

...
```

* `tags` は自由タグのみ。
* `importance` は将来の検索スコア補正などに利用可能。

### 6.3 インデックスファイル（index.yaml）

```yaml
items:
  - memory_name: "architecture"
    title: "システム全体構成の概要"
    path: "memories/2025/11/20251124-architecture.md"
    created_at: "2025-11-24T09:00:00+09:00"
    updated_at: "2025-11-24T09:10:00+09:00"
    tags: ["システム構成"]
  - memory_name: "billing-flow"
    title: "請求処理ワークフローの確定版"
    path: "memories/2025/11/20251124-billing-flow.md"
    created_at: "2025-11-24T09:15:00+09:00"
    updated_at: "2025-11-24T09:20:00+09:00"
    tags: ["経理", "請求処理"]
```

* 書き換え時は一時ファイルに出力 → アトミックリネームで上書きし、破損を防止。
* `deleted` フラグを導入する場合はここに記録。

### 6.4 設定ファイル（config.yaml）

* `<memory_root>` パス（省略可能、デフォルトは実行ディレクトリ配下）
* ログ出力先
* 検索実装に関するパラメータ（必要であれば）

  * トークナイザ種別
  * タイトル・本文への重み

---

## 7. 非機能要件

### 7.1 性能

* 想定規模

  * メモリ件数: 数千件程度
  * 同時利用: 1 ユーザ〜少数（ローカル用途）
* 目標レスポンス

  * `write_memory`: 通常 1 秒以内
  * `read_memory`: 通常 0.5 秒以内
  * `search_memories`: 数千件規模で 1〜2 秒以内

### 7.2 可用性・信頼性

* ローカルツールとして利用するため 24x7 高可用性は要求しない。
* ただし以下は担保する：

  * index.yaml / メモリファイルの更新時にアトミックな書き換えで破損を防止
  * 例外発生時にファイルが中途半端な状態にならないよう配慮

### 7.3 セキュリティ

* アプリケーションレベルの認証・認可なし。
* 保存されるメモリ内容に機密情報・個人情報が含まれうることを明示し、
  PC のログイン制御・ディスク暗号化等は運用ルールで対応。

### 7.4 拡張性

* 将来の拡張を想定した設計とする：

  * 内部の検索実装を Embedding + ベクタ検索に差し替え可能
  * index.yaml を別ストレージ（RDB など）に移行可能
  * HTTP ベースの MCP トランスポートへの変更（オプション）

### 7.5 運用・ログ

* ログ出力

  * 出力先ディレクトリ: `<memory_root>/logs/`
  * ログファイル: `memory-mcp.log`
  * 記録内容:

    * ツール呼び出し（ツール名、開始・終了時刻、処理時間）
    * `write_memory` 呼び出し件数・メモリ名
    * エラー時のスタックトレース
* バックアップ

  * `<memory_root>` 以下を OS 側のバックアップ対象とする（Git 管理も可）

---

## 8. ChatGPT との連携要件（概要）

* ChatGPT 側の MCP 設定に、当 MCP サーバの起動コマンドを登録する。
* システムプロンプト（ガイドライン）の例：

  * 長期的に役立つ知識がまとまった場合のみ `write_memory` を使用すること。
  * 回答の前に、必要に応じて `search_memories` を行い、関連メモリを利用すること。
  * 1 つの会話から複数のメモリを作成してよいこと。

---
