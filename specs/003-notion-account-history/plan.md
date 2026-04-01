# Implementation Plan: 歷史會議帳號標記與篩選

**Branch**: `003-notion-account-history` | **Date**: 2026-03-31 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-notion-account-history/spec.md`

## Summary

多帳號 Notion 環境下，上傳會議時自動在 `meeting_meta.json` 記錄帳號 label（`uploaded_by` 欄位），在側邊欄歷史會議瀏覽器顯示帳號資訊並提供帳號篩選 selectbox。全部修改集中在 `app.py` 的 4 個既有函數，不新增檔案。

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: Streamlit 1.55, OpenAI SDK  
**Storage**: 本地 JSON 檔案（`output/{date}_{name}/meeting_meta.json`）  
**Testing**: pytest（`tests/` 目錄）  
**Target Platform**: Windows / macOS（本地桌面應用）  
**Project Type**: desktop-app（Streamlit 單頁應用）  
**Performance Goals**: N/A — 本地使用，< 200 個會議資料夾  
**Constraints**: Streamlit widget key 限制（不可在 widget 實例化後修改同名 session state key）  
**Scale/Scope**: 單人 / 小團隊使用，< 200 場會議

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution 尚未定義具體原則（模板狀態）— 無 gate violations。通過。

**Post-Phase 1 Re-check**: 設計未引入新依賴、未新增檔案、僅修改 4 個既有函數、向下相容舊 metadata。通過。

## Project Structure

### Documentation (this feature)

```text
specs/003-notion-account-history/
├── plan.md              # This file
├── research.md          # Phase 0: 6 項研究決策
├── data-model.md        # Phase 1: meeting_meta.json schema + state flow
├── quickstart.md        # Phase 1: 實作細節與驗證步驟
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
app.py                   # 主應用 — 修改 5 個函數（含 sidebar 順序調整）
config.py                # 帳號管理 — 新增 save/load_active_notion_account()
notion_uploader.py       # Notion API — 不修改
output/                  # 會議資料目錄（meeting_meta.json 在此）
tests/                   # 測試目錄
```

**Structure Decision**: 主要變更集中在 `app.py`，`config.py` 僅新增帳號持久化讀寫函數。無需新增模組或資料夾。

## Complexity Tracking

> 無 Constitution violations — 本節留空。
