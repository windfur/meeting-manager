# Implementation Plan: 上傳狀態鎖定與編輯器同步修復

**Branch**: `main` | **Date**: 2026-03-30 | **Spec**: [specs/main/spec.md](specs/main/spec.md)
**Input**: Feature specification from `specs/main/spec.md`

## Summary

修復三個 UI 同步問題：(1) 上傳 Notion 期間鎖定所有互動元素（採 rerun 模式），(2) 批次取代讀取正確的 widget 值，(3) 摘要產生期間 disabled 版本選擇器。主要修改集中在 `app.py`，新增 `uploading` session state 旗標，統一 `is_busy` 判斷邏輯。

## Technical Context

**Language/Version**: Python 3.12 + Streamlit 1.55  
**Primary Dependencies**: streamlit, openai, httpx (Notion API)  
**Storage**: 本地檔案系統 (`output/{date}_{name}/`)  
**Testing**: pytest (`tests/test_summary_style.py`)  
**Target Platform**: Windows 桌面（localhost:8501）  
**Project Type**: desktop-app (Streamlit web UI)  
**Performance Goals**: N/A（單人使用）  
**Constraints**: 上傳失敗後 UI 需在 3 秒內恢復  
**Scale/Scope**: 單一使用者，單一 `app.py` 主檔（~960 行）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | 使用者優先 | ✅ PASS | 本功能目標即為改善使用者體驗 |
| II | 資料自主 | ✅ PASS | 無新增外部資料傳輸 |
| III | Notion 整合彈性 | ✅ PASS | 不改變 Notion 上傳邏輯，僅加鎖 |
| IV | AI 摘要品質 | ✅ PASS | 不影響摘要產生流程 |
| V | 版本可追溯 | ✅ PASS | 不影響版本儲存機制 |
| VI | 編輯器同步 | ✅ PASS | 修復批次取代 bug + 維持版本化 key |
| VII | 操作防誤 | ✅ PASS | 新增上傳鎖定正是此原則的實現 |

**Gate Result**: ✅ ALL PASS — 無違規，可進入 Phase 0。

## Project Structure

### Documentation (this feature)

```text
specs/main/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
└── quickstart.md        # Phase 1 output
```

### Source Code (repository root)

```text
app.py                   # 主要修改目標（~960 行 Streamlit 應用）
config.py                # 設定管理（不修改）
transcriber.py           # 語音轉錄（不修改）
summarizer.py            # AI 摘要（不修改）
notion_uploader.py       # Notion 上傳（不修改）
tests/
└── test_summary_style.py
```

**Structure Decision**: 單檔案專案，所有變更集中在 `app.py`。不需要新增檔案或目錄。

## Complexity Tracking

> 無違規，此 section 不適用。
