# Implementation Plan: Notion 帳號 Onboarding 優化

**Branch**: `001-notion-onboarding` | **Date**: 2026-03-30 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-notion-onboarding/spec.md`

**Note**: This plan documents an already-implemented feature for spec alignment.

## Summary

解除 Notion token 對 app 啟動的阻塞，讓新使用者透過側邊欄完成首次 token 設定。修改 config check 邏輯使 OPENAI_API_KEY 為唯一阻塞項，sidebar 渲染移到 config check 前，無 token 時主區域顯示引導提示。

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: Streamlit 1.55, httpx  
**Storage**: 本地檔案系統（`.notion_tokens.json`, `.env`）  
**Testing**: pytest  
**Target Platform**: localhost web app (Windows/macOS)  
**Project Type**: desktop-app (Streamlit web UI)  
**Performance Goals**: N/A（UI 操作，無效能瓶頸）  
**Constraints**: 無 token 時不得呼叫任何 Notion API  
**Scale/Scope**: 單一使用者本地工具

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | 使用者優先 | ✅ PASS | 新使用者不再被擋在 UI 外，可直接在側邊欄完成設定 |
| II | 資料自主 | ✅ PASS | token 儲存在本地 .notion_tokens.json，不影響 .env，不 commit |
| III | Notion 整合彈性 | ✅ PASS | 不綁定特定 workspace；token 從 UI 新增；page/db 從下拉選擇 |
| IV | AI 摘要品質 | ✅ N/A | 本功能不涉及摘要流程 |
| V | 版本可追溯 | ✅ N/A | 本功能不涉及版本管理 |
| VI | 編輯器同步 | ✅ N/A | 本功能不涉及 widget key |
| VII | 操作防誤 | ✅ PASS | 無 token 時阻擋主流程；page selector 加 guard 避免空 API call |

## Project Structure

### Documentation (this feature)

```text
specs/001-notion-onboarding/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
└── quickstart.md        # Phase 1 output
```

### Source Code (repository root)

```text
app.py                   # main(), _check_config(), _show_meeting_browser(), _show_notion_accounts(), _show_style_settings(), _show_notion_page_selector()
config.py                # load_notion_tokens(), save_notion_token(), NOTION_TOKEN, NOTION_TOKENS_FILE
notion_uploader.py       # set_token(), _get_token(), search_pages()
.env                     # NOTION_TOKEN (optional)
.notion_tokens.json      # Multi-token storage (auto-created)
```

**Structure Decision**: 單一 Python 檔案結構（Streamlit app），改動集中在 app.py 的啟動流程。

## Complexity Tracking

> 無違反紀錄，所有憲法原則均通過。
