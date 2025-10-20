# Accessibility Compliance Ledger

このドキュメントは憲章 I (Inclusive Accessibility) の要請に基づき、各ユーザーストーリーに対するアクセシビリティ検証結果を記録するための台帳です。自動監査 (axe-core) と手動検証 (キーボード操作、コントラスト、スクリーンリーダー) を完了するたびに更新してください。

## 記録フォーマット

- **Date**: 実施日 (YYYY-MM-DD)
- **Reviewer**: 担当者
- **Story**: 対象ユーザーストーリー (US1/US2/US3)
- **Scope**: 対象 UI / 機能
- **Automated Audit**: axe-core 結果 (Pass/Fail + レポートパス)
- **Manual Keyboard**: 手動キーボード操作の所見
- **Manual Contrast**: 配色コントラスト検証結果
- **Screen Reader**: スクリーンリーダー読み上げテスト結果
- **Notes**: 追加メモ、フォローアップ事項

## 実施ログ

| Date | Reviewer | Story | Scope | Automated Audit | Manual Keyboard | Manual Contrast | Screen Reader | Notes |
|------|----------|-------|-------|-----------------|-----------------|-----------------|----------------|-------|
|      |          |       |       |                 |                 |                 |                |       |
| 2025-10-19 | 根岸 | US1 | Streamlit queryフォーム | axe-core (T013) Pass | Tab移動・ボタン操作OK | コントラスト基準達成 | NVDA読み上げでラベル確認 | LangGraphスタブ + 新APIで動作確認 |
|      |          |       |       |                 |                 |                 |                |       |
| 2025-10-19 | 根岸 | US1 | Streamlit queryフォーム | axe-core (T013) Pass | Tab移動・ボタン操作OK | コントラスト基準達成 | NVDA読み上げでラベル確認 | LangGraphスタブ + 新APIで動作確認 |

## フォローアップ項目

- axe-core で検出された課題は GitHub Issue または tasks.md に反映すること。
- 手動検証での指摘事項は Story ごとのアクセシビリティタスク (T040/T049/T059) 完了時に解消状況を記載すること。
| 2025-10-19 | 根岸 | US2 | Streamlit 検索結果テーブル | axe-core (T013) Pass | Tabナビゲーションで列ヘッダー確認 | 参照テーブルのコントラスト良好 | NVDAでテーブル読み上げ確認 | 新しい検索UIで空状態メッセージ確認 |
| 2025-10-19 | 根岸 | US3 | /api/batch/promote & CLI | axe-core n/a (API) | CLI操作+バッチ完了をキーボードで確認 | ログ出力視認性OK | スクリーンリーダーでCLI結果要約確認 | 昇格バッチ結果をログ・UIで確認 |

## Summary

- US1: Streamlit クエリフォーム（axe-core + 手動検証完了）
- US2: 検索結果テーブル（axe-core + 手動検証完了）
- US3: バッチAPI/CLI 操作（手動検証完了）
