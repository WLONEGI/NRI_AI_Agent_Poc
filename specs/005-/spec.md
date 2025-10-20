# Feature Specification: Crystal Intelligence風ナレッジ統合システム PoC

**Feature Branch**: `005-`  
**Created**: 2025-10-17  
**Status**: Draft  
**Input**: User description: "AIエージェントの業務利用過程で取得した情報を自動的にナレッジ化し、階層的に蓄積・共有するシステムのPoC実装"

## Clarifications

### Session 2025-10-17

- Q: 環境変数・シークレットの管理方式は？ → A: `.env.example`をコミットし、`python-dotenv`で`OPENAI_API_KEY`などをロードする。
- Q: ベクトル類似度をどのように実装する？ → A: Neo4jのVector Indexを作成し、コサイン類似度のTop-K検索で近似最近傍探索する。
- Q: 出典リンク表示はどう提供する？ → A: 応答下部に参照ナレッジ一覧を表示し、Neo4jクエリログで取得を追跡する。

### Session 2025-10-19

- Q: ユーザーストーリー2のアクセシビリティ受け入れ基準は？ → A: 検索結果一覧に対し、キーボード操作・コントラスト・スクリーンリーダー確認を実施し、`tests/accessibility-checklist.md`へ手動チェック結果を追記する。
- Q: ユニットテストおよび回帰テストの責任者は誰か？ → A: 開発リードの根岸が全ユニットテストと回帰の責任者を担い、機能担当者が個別テストを実装する。

### Session 2025-10-20

- Q: FR-009とL165のTop-K設定に矛盾がある。K=100を固定値とするか調整可能とするか？ → A: Keep K=100 fixed (remove adjustability claim from L165) - simplest for PoC
- Q: FR-007の昇格閾値（類似度0.75、貢献者3名、カバレッジ50%）の根拠は？ → A: Experimental PoC parameters requiring post-deployment validation
- Q: NF-003のNeo4j監査ログ統合のトリガーは？ → A: After PoC validation phase completes
- Q: ユーザー・チーム定義YAMLファイルの配置場所は？ → A: infra/users_teams.yaml
- Q: 複雑なファイルフォーマット（画像等）のアクセシビリティ検証範囲は？ → A: Defer complex format accessibility to post-PoC phase

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 自動ナレッジ蓄積と可観測性 (Priority: P1)

エージェントがStreamlit UI経由の対話のたびに、クエリ・応答・ツール実行結果・データソースを自動的に収集し、Neo4jに個人ナレッジとして保存する。

**Why this priority**: PoCの最小価値は、対話内容から即時にナレッジ化できることを証明する点にあるため。

**Independent Test**: `save_knowledge`を中心としたコア保存ロジックのユニットテストと、手動E2EシナリオでNeo4jのプロベナンスを確認する。

**Acceptance Scenarios**:

1. **Given** ユーザーがStreamlit UIで質問しファイル検索ツールを利用した場合、 **When** LangChainエージェントが応答を生成し保存処理まで同期的に実行すると、 **Then** ユーザーの個人ナレッジとしてクエリ内容・応答・ツール履歴・データソースがNeo4jに保存され、キーボード操作とコントラスト検証の結果が確認できる。
2. **Given** 保存処理が同期で実行される場合、 **When** APIレスポンスが成功を返すと、 **Then** Neo4j上で`Knowledge`ノードにベクトル埋め込みと`SYNTHESIZED_FROM`リレーションが作成され、レスポンス内で保存完了が確認できる。

### User Story 2 - 個人・チームナレッジ検索 (Priority: P2)

ユーザーが検索クエリを入力すると、個人ナレッジと所属チームナレッジを横断して関連情報を取得し、プロベナンス付きで表示する。

**Why this priority**: 個人とチーム双方のナレッジ活用がPoCのビジネス価値を証明するため。

**Independent Test**: Neo4jに仕込んだテストデータを用いた検索関数のユニットテストと、手動UI操作による結果確認を組み合わせる。

**Acceptance Scenarios**:

1. **Given** 1人のユーザーに個人ナレッジが存在しチームナレッジは空である場合、 **When** 検索クエリを送信すると、 **Then** 個人ナレッジのみが検索結果に含まれアクセス制御違反が発生しない。
2. **Given** 同一チーム内の複数ユーザーに類似テーマのナレッジが存在する場合、 **When** 検索クエリを送信すると、 **Then** チームナレッジと個人ナレッジの両方が類似度順に返り、各項目に`ATTRIBUTED_TO`ユーザー情報が付与されている。
3. **Given** 検索結果一覧がStreamlit UIで表示される場合、 **When** キーボード操作・スクリーンリーダー読み上げ・WCAGコントラスト比チェックを実施すると、 **Then** すべて成功し、結果が`tests/accessibility-checklist.md`に追記されている。

### User Story 3 - 自動昇格バッチ処理 (Priority: P3)

定期バッチが個人ナレッジを集約し、類似性と貢献者数の閾値を満たすエントリを自動でチームナレッジへ昇格させる。

**Why this priority**: 集約アルゴリズムの妥当性確認がPoC成功判定の核心となるため。

**Independent Test**: 類似度計算関数のユニットテストを実施し、手動トリガーで実行されるバッチスクリプトの結果をNeo4j上で確認する。

**Acceptance Scenarios**:

1. **Given** 類似度0.75以上・貢献者3名・対象チームメンバーの50%以上が関与するナレッジが存在する場合、 **When** バッチ処理を手動で実行すると、 **Then** 新しいチームナレッジノードが作成され元の個人ナレッジは維持される。
2. **Given** 類似度0.72で条件を満たさない複数ナレッジがある場合、 **When** バッチが実行されると、 **Then** 昇格は行われず、監査ログに理由が記録される。
3. **Given** 昇格結果を確認するストリームリットUIコンポーネント（もしくは提供する視覚化）が表示される場合、 **When** キーボード操作・スクリーンリーダー読み上げ・WCAGコントラスト比チェックを行うと、 **Then** いずれも成功し、手動チェック結果が`tests/accessibility-checklist.md`に記録されている。

## Edge Cases

- LLM APIが一時的に失敗した場合は指数バックオフ付きリトライを行い、最大試行回数超過時には処理を保留してログに残す。
- ツールが空の結果を返した場合でもプロベナンスは記録し、抽出コンテンツが空であってもナレッジ抽出を試行した事実を保存する。
- 類似したナレッジが多数生成された場合でも削除や統合は行わず、昇格ロジックに委ねる。
- ローカルファイルに画像や複雑なフォーマットが含まれる場合の詳細なアクセシビリティ対応（代替テキスト・ARIAラベル・セマンティックマークアップ）はPoC範囲外とし、PoC検証後のフェーズで実装する。PoC期間中はテキストベースのファイル処理に限定する。
- 埋め込み生成が失敗した場合はナレッジ本体を保存し、埋め込みフィールドを空値のまま保持して後続バッチで再試行可能とする。検索処理は埋め込み欠損のナレッジを結果から除外し、欠損発生を監査ログへ記録する。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムはStreamlit UIから受信したユーザークエリとAI応答を、対話完了ごとにNeo4jへ個人ナレッジとして保存しなければならない。
- **FR-002**: LangChain/LangGraphエージェントはMCPプロトコルを通じて`file_search`、`web_search`、`query_team_knowledge`ツールにアクセスできなければならない。
- **FR-003**: `save_knowledge`ツールはクエリ、応答、ツール実行トレース、データソースのメタデータおよびベクトル埋め込みを含むレコードを生成し、Query→AgentExecution→ToolExecution→DataSource→ExtractedContent→Knowledge の6ノードとリレーションが欠損なく保存されなければならない。
- **FR-004**: Neo4jグラフはUser、Team、Query、AgentExecution、DataSource、ToolExecution、ExtractedContent、Knowledgeノードと定義済みリレーションを作成・更新できなければならない。
- **FR-005**: 検索機能はユーザーの個人ナレッジと所属チームナレッジを統合し、ベクトル類似度で順位付けした結果とその出典を返さなければならない。
- **FR-006**: Streamlit UIはWCAG 2.1 AA成功基準を満たすよう実装し、axe-coreによる自動監査と手動キーボード／コントラストチェックの結果を`tests/accessibility-checklist.md`に記録しなければならない。
- **FR-007**: 自動昇格バッチは手動トリガーまたは簡易スケジューラで実行され、類似度0.75以上・貢献者3名以上・チーム構成員の50%以上という条件を満たすナレッジのみをチームレベルへ昇格させなければならない。
- **FR-008**: LLM API障害発生時は1秒・2秒・4秒の指数バックオフで最大3回再試行し、すべて失敗した場合は障害内容と手動再実行の必要性を`logs/app.log`（JSON形式）へ記録しなければならない。
- **FR-009**: ベクトル検索はNeo4jのVector Indexと`db.index.vector.queryNodes()`を用い、コサイン類似度のTop-K（K=100）検索で近似最近傍を取得し、アクセス制御フィルタのみ適用して全100件を返さなければならない（追加の類似度閾値フィルタは行わない）。

### Non-Functional Simplifications

- **NF-001**: PoC期間中はナレッジ保存を同期処理で実行し、応答終了までに保存を完了させる。
- **NF-002**: バッチ処理は手動トリガー可能なスクリプトまたはエンドポイントとして実装し、APSchedulerによる自動実行はオプション扱いとする。
- **NF-003**: 監査ログはPython `logging`モジュールのファイルハンドラを用いて永続化する。PoC検証フェーズ完了後、Neo4j監査ログノードへの統合を検討する。
- **NF-004**: 環境変数は`.env`ファイルで管理し、`.env.example`をコミットして`python-dotenv`で`OPENAI_API_KEY`、`NEO4J_URI`、`NEO4J_USER`、`NEO4J_PASSWORD`、`MCP_SERVER_URL`をロードする。
- **NF-005**: ベクトル検索APIエンドポイントは埋め込み生成とNeo4jクエリを含むエンドツーエンドでTop-100取得を1.5秒以内、ナレッジ保存は対話完了からNeo4j永続化完了まで2秒以内で完了しなければならない。

### Key Entities *(include if feature involves data)*

- **User**: PoC参加者を表し、所属チームと識別子を保持する。
- **Team**: ユーザーをグルーピングし、アクセス制御の単位となる。
- **Query**: ユーザー入力テキストとタイムスタンプを保持する対話イベント。
- **AgentExecution**: LLMモデル、開始・終了時刻、ステータスを含むエージェント実行情報。
- **DataSource**: ファイル・Web・既存ナレッジなど取得元のメタデータとコンテンツを保持する。
- **ToolExecution**: ツール名、入力、処理時間を保持する実行ログ。
- **ExtractedContent**: LLMが抽出した要約、主要ファクト、信頼度を保持する。
- **Knowledge**: 階層レベル（personal/team）、コンテンツ、カテゴリ、ベクトル埋め込み、所有者、信頼度を保有するナレッジノード。

## Rationale Log *(mandatory)*

- **Business Logic Decisions**: 2階層（個人→チーム）構造は最短期間で業務適用可否を検証するための最小構成であり、昇格条件を完全自動にすることで運用コストと主観的判断を排除する。
- **Promotion Thresholds**: FR-007の類似度0.75、貢献者3名以上、チーム構成員50%以上という閾値は、実験的なPoC開始値であり、実運用データを基に検証・調整を行う前提で設定している。本番展開時には利用パターン分析に基づく最適化が必要となる。
- **Non-Functional Requirements**: PoCでは同期保存・簡易ログ・手動バッチを採用して実装負荷を抑えつつ、将来的な拡張（非同期化、APScheduler、Neo4j監査ログ）に向けた拡張ポイントを確保する。

## 環境変数とシークレット管理

- `.env.example`をリポジトリに含め、必要なキーとデフォルト値のダミーを共有する。
- 実際の`.env`は`.gitignore`で除外し、開発者ごとにローカル作成する。
- `python-dotenv`を用いてアプリ起動時に環境変数をロードする。
- 必須環境変数:

```env
OPENAI_API_KEY=sk-xxx
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
MCP_SERVER_URL=http://localhost:3000
```

## テスト方針

- コアロジック（ナレッジ保存、検索、類似度計算）はpytestによるユニットテストを実施し、主要な成功/失敗パターンをカバーする。
- E2E検証は手動シナリオまたは簡易スクリプトで実行し、結果を検証シートに記録してトレーサビリティを確保する。
- アクセシビリティはキーボード操作とコントラストの手動チェックリストで確認し、未達項目は将来対応として残す。

## Success Criteria *(mandatory)*

- **SC-001**: 3名のユーザーが同テーマでAI利用した後、各自の個人ナレッジがNeo4jに生成され、プロベナンスが欠落していないこと。
- **SC-002**: 手動トリガーで実行したバッチ処理後、条件を満たすナレッジが自動的にチームナレッジへ昇格し、元データが保持されていること。
- **SC-003**: 4人目のユーザーが質問した際にチームナレッジを参照して回答を提供でき、「参照したナレッジ」セクションでID・要約・所有者・作成日時が表示されNeo4jログから参照履歴を確認できること。
- **SC-004**: axe-coreレポートとキーボード／コントラストの手動チェックリストが`tests/accessibility-checklist.md`に更新され、Pull Requestへ添付されていること。

## 技術アーキテクチャ概要

- ユーザーはStreamlit UIからクエリを送信し、LangChain/LangGraphエージェントが応答を生成する。
- エージェントはMCPプロトコル経由でカスタムMCPサーバーと通信し、`file_search`、`web_search`、`query_team_knowledge`、`save_knowledge`などのツールを利用する。
- MCPサーバーはNeo4jベースのKnowledge Engineと連携し、ベクトル＋グラフ検索を提供する。
- 実行環境はDocker Compose上で構築し、LLMにはGPT-5-mini、埋め込みにはOpenAI `text-embedding-3`を使用する。

## 参照ナレッジ表示

- AI応答の下部に「参照したナレッジ」セクションを設け、Top-K検索で得た結果を並べる。
- 各ナレッジ項目にはID、要約（先頭100文字）、所有者表示（チームナレッジは「チーム共有」ラベル）、作成日時へのリンクを含める。
- 表示と同時にNeo4jクエリログを保存し、どのナレッジが回答生成に利用されたか検証できるようにする。

## データソースと蓄積フロー

1. Streamlit UIからユーザークエリを受け取る。
2. LangChainエージェントが必要に応じてファイル検索、Web検索、既存ナレッジ検索ツールを呼び出す。
3. AI応答がユーザーに返却された直後、同期処理として`save_knowledge`ツールを実行しNeo4jへ保存する。
4. 保存時にQuery→AgentExecution→ToolExecution→DataSource→ExtractedContent→Knowledgeのプロベナンスチェーンを完全に記録する。

## ベクトル類似度と検索実装

- Neo4jのVector Indexを`CREATE VECTOR INDEX`で`Knowledge.embedding`に作成し、アップサート時に常に最新化する。
- 近似最近傍探索は`db.index.vector.queryNodes()`で実行し、コサイン類似度を使用する。
- Top-K値は100に固定し、PoC期間中は変更しない（FR-009準拠）。
- 全件比較は避け、Vector Index検索結果をGraphリレーションフィルタで絞り込む二段階構成とする。

## 定期バッチ（自動昇格）フロー

1. 手動トリガー（CLIまたは管理API呼び出し）でバッチ処理を開始する。
2. 個人ナレッジをチーム単位で収集しベクトル類似度を計算、しきい値0.75以上のグルーピングを抽出する。
3. 貢献者が3名以上、チームメンバーの50%以上をカバーしているグループのみチームナレッジに昇格させる。
4. 昇格結果は`SIMILAR_TO`や`synthesis_method`属性でトレーサビリティを確保し、元の個人ナレッジは保持する。
5. 将来的な自動化を想定したAPScheduler設定はオプションとして別ファイルで管理する。
6. すでにチームナレッジへ昇格済みのエントリは、後続バッチで閾値を下回っても降格や削除は行わず、昇格履歴と理由を保持する。

## 監査ログとモニタリング

- Python標準の`logging`モジュールでファイル出力を構成し、LLM/API障害や昇格結果を記録する。
- ログローテーションはPoC期間中は手動で対応し、必要に応じて将来のNeo4j連携を検討する。
- 重要イベントについては`INFO`以上のレベルで出力し、失敗時は`ERROR`ログに再試行予定を併記する。

## MCPサーバーツール仕様

| ツール名 | 説明 | 入力 | 出力 |
|----------|------|------|------|
| file_search | ローカルファイルからテキストやCSVを検索 | `query`, `file_types` | `{path, content, metadata}` |
| web_search | Web検索結果の取得 | `query` | `{url, content, metadata}` |
| query_team_knowledge | Neo4jの個人・チームナレッジを横断検索 | `query`, `user_id` | `[{knowledge}, ...]` |
| save_knowledge | ナレッジとプロベナンスを保存 | `{knowledge, provenance}` | `{id, status}` |

## ユーザー・チーム管理

- `infra/users_teams.yaml`でユーザーとチームを定義し、PoC範囲ではハードコードで管理する。
- 例:

```yaml
users:
  - id: user1
    name: 田中太郎
    team: team_sales
  - id: user2
    name: 佐藤花子
    team: team_sales

teams:
  - id: team_sales
    name: 営業チーム
```

## 実装フェーズ計画

- **Phase 1 (1週目)**: ローカルファイル検索と簡易トレーシングを実装し、個人ナレッジ保存のエンドツーエンド動作を確認する。
- **Phase 2 (2週目)**: Web検索統合と詳細トレーシング（推論過程含む）を実装し、チーム検索機能を完成させる。
- **Phase 3a (3週目)**: 複数データソース統合と自動昇格処理を完成させ、手動バッチトリガーでPoC成功シナリオを検証する。
- **Phase 3b (オプション)**: 矛盾検出・解決ロジックを試作し、時間が許せばPoCデモに組み込む。

## スコープ外

- 3階層以上のナレッジ構造や複雑なロールベースアクセス制御。
- エンタープライズ想定のスケーラビリティチューニング。
- UIのビジュアル作り込みや細かなカスタマイズ。
- ナレッジの削除・編集機能および詳細なモニタリング。
