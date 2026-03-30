# Implementation Plan: 會議 Metadata 顯示與同步

**Branch**: `002-metadata-edit-sync` | **Date**: 2026-03-30 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-metadata-edit-sync/spec.md`

## Summary

在 Step 1（逐字稿審閱）和 Step 2（摘要審閱）頁面新增可編輯的標籤與參與者輸入欄位，預填來自 session state 的值。使用者修改後跨步驟同步，儲存草稿與上傳 Notion 時同步回存 meeting_meta.json。

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: Streamlit 1.55, httpx  
**Storage**: 本地檔案系統（`output/` 目錄、`meeting_meta.json`）  
**Testing**: pytest（`tests/test_summary_style.py` 已有）  
**Target Platform**: localhost Streamlit web app (Windows/macOS)  
**Project Type**: desktop-app (Streamlit web UI)  
**Performance Goals**: UI 渲染 < 100ms，無新 API 呼叫  
**Constraints**: 純前端 UI 變更 + 本地檔案寫入，無外部服務依賴  
**Scale/Scope**: 單人使用，本地工具

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. 使用者優先 | ✅ PASS | metadata 貫穿所有步驟，操作更直覺 |
| II. 資料自主 | ✅ PASS | 資料僅寫入本地 output/ 目錄，不涉及敏感資料 |
| III. Notion 整合彈性 | ✅ PASS | 不影響 Notion token 管理，上傳時使用最新 tags |
| IV. AI 摘要品質 | ✅ PASS | 不影響摘要產生邏輯，auto_tags 覆寫邏輯不變 |
| V. 版本可追溯 | ✅ PASS | metadata 變更透過 meeting_meta.json 持久化 |
| VI. 編輯器同步 | ⚠️ WATCH | 新增 text_input 需遵守版本化 key 規則，跨步驟同步需正確更新 session state |
| VII. 操作防誤 | ✅ PASS | 上傳/摘要產生期間 metadata 欄位也需 disabled |

**Gate Result**: ✅ PASS — 所有原則通過，VI 需特別注意 widget key 版本化。

## Project Structure

### Documentation (this feature)

```text
specs/002-metadata-edit-sync/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
app.py                   # main(), _show_transcript_review(), _show_summary_review(), _upload_to_notion(), _save_meeting_meta()
config.py                # load_notion_tokens(), NOTION_TOKENS_FILE
notion_uploader.py       # upload_meeting()
```

**Structure Decision**: 所有變更集中在 app.py 單一檔案，涉及 3 個函數的修改。

## Complexity Tracking

> No violations — no complexity justification needed.
