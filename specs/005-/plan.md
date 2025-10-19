# Implementation Plan: Crystal Intelligence風ナレッジ統合システム PoC

**Branch**: `005-` | **Date**: 2025-10-18 | **Spec**: `/specs/005-/spec.md`
**Input**: Feature specification from `/specs/005-/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

StreamlitベースのUIとLangChain/LangGraphエージェントで収集した対話データを、Neo4jのベクトル＋グラフ基盤に同期保存し、手動トリガーの昇格バッチでチーム共有ナレッジを自動生成するPoCを3〜4週間で構築する。MCPサーバーを介して`file_search`/`web_search`/`query_team_knowledge`/`save_knowledge`ツールを統合し、参照ナレッジの表示とプロベナンス追跡を保証する。

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.11 (pyproject.toml管理、**必須**: 仮想環境 venv/virtualenv)
**Primary Dependencies**: Streamlit, LangChain 0.2+, LangGraph, OpenAI SDK, Neo4j Python Driver, python-dotenv, APScheduler (手動トリガー補助), pytest
**Storage**: Neo4j 5.x (Vector Index + Graph)、ローカルファイルシステム（入力ファイル）
**Testing**: pytest + pytest-asyncio、manual E2E checklist
**Target Platform**: Docker Compose上のローカル開発環境（Streamlit UI + MCP Server + Neo4jコンテナ）
**Environment Isolation**: Python仮想環境（`.venv/`）必須、依存関係はpyproject.tomlで固定バージョン管理  
**Project Type**: multi-service（`apps/ui` Streamlit、`services/mcp-server` Python、`infra/neo4j`）  
**Performance Goals**: Vector検索 Top-100 が < 1.5s / クエリ、保存処理が < 2s / 対話  
**Constraints**: PoC範囲でDocker Composeのみ、LLM/EmbeddingはOpenAI API、バックグラウンド処理は同期要求（レスポンス許容3s）、LLM失敗時は1/2/4秒のバックオフで最大3回再試行し`logs/app.log`へJSONロギング  
**Scale/Scope**: 最大5ユーザー・1日100往復、Neo4jデータ8kノード以下、PoC期間3〜4週間

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Accessibility** (Principle I): Streamlit UIは`axe-core`自動監査（CIの`accessibility`ジョブ）と手動キーボード／コントラストチェックを実施し、結果を`tests/accessibility-checklist.md`に記録したうえでPRへ添付。未解決の失敗はマージを禁止。アクセシビリティ責任者: プロダクトデザイナー（佐藤）。
- **Unit Testing** (Principle II): `apps/ui`はStreamlitロジックのモジュール関数をpytestでユニットテスト、`services/mcp-server`はツール実装別に成功/失敗/空結果をテスト。CIで`pytest -m unit`を必須実行。
- **Linting & Formatting** (Principle III): `ruff` + `black`（Python）、`prettier`（markdown）の設定をプロジェクトルートに配置し、プリプッシュフックで強制。例外申請はArchitectureレビューへ提出。
- **Security Remediation** (Principle IV): セキュリティ担当: システムアーキテクト（田中）。脆弱性検知時は1時間以内にSlack #ai-agent-alertへ共有し、24時間以内にHotfixブランチで修正→デプロイ。
- **Decision Records** (Principle V): `.specify/memory/constitution.md`と`specs/005-/spec.md`のRationale Logを最新化、追加の技術判断は`docs/adr/`にADR-001として記録予定。
- **Virtual Environment** (Principle VI): 全てのPython実行は仮想環境（`.venv/`）内で実施。README.mdに環境構築手順を記載し、CI/CDでも仮想環境を検証。依存関係はpyproject.tomlで厳密にバージョン固定。

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```
apps/
└── ui-streamlit/
    ├── app.py
    ├── components/
    └── tests/

services/
└── mcp-server/
    ├── src/
    │   ├── tools/
    │   ├── knowledge/
    │   └── apis/
    └── tests/

infra/
└── neo4j/
    └── docker-compose.yml

shared/
└── lib/
    └── embeddings/

tests/
├── unit/
├── integration/
└── accessibility/
```

**Structure Decision**: Streamlit UIとMCPサーバーを分離したPythonサービス構成とし、Neo4j・環境設定は`infra/`配下でDocker Compose管理。共通ロジックは`shared/lib`で再利用、テストはタイプ別ディレクトリを採用する。

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
