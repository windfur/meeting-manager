# Implementation Plan: Retranscribe（重新轉錄）

**Branch**: `004-retranscribe` | **Date**: 2026-04-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-retranscribe/spec.md`

## Summary

在 Step 1 逐字稿審閱頁面新增「重新轉錄」按鈕，讓使用者點擊後重新呼叫 Whisper API 轉錄，覆蓋 `transcript_raw.txt` 並即時更新頁面。音檔路徑優先從 `meeting_meta.json` 的 `audio_path` 讀取，fallback 掃描 output 資料夾。首次轉錄時自動儲存 `audio_path` 至 metadata。全部變更集中在 `app.py` 和 `config.py`，重用現有 `transcriber.transcribe()` 管道。

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: Streamlit 1.55, OpenAI SDK（Whisper API）  
**Storage**: 本地檔案系統（`output/{date}_{name}/` 目錄，JSON + txt）  
**Testing**: pytest（`tests/` 目錄）  
**Target Platform**: Windows / macOS（本地桌面應用）  
**Project Type**: desktop-app（Streamlit 單頁應用）  
**Performance Goals**: N/A — 本地使用，轉錄時間取決於音檔長度與 Whisper API  
**Constraints**: Streamlit widget key 版本化限制；轉錄期間全頁按鈕 disabled（FR-005）  
**Scale/Scope**: 單人 / 小團隊使用，< 200 場會議

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 狀態 | 說明 |
|------|------|------|
| I. 使用者優先 | ✅ | 一鍵重新轉錄，操作直覺 |
| II. 資料自主 | ✅ | 資料存本地 output/，無新增敏感資料 |
| III. Notion 整合彈性 | ✅ | 不涉及 Notion |
| IV. AI 摘要品質 | ✅ | 不修改摘要流程 |
| V. 版本可追溯 | ✅ | 覆蓋 transcript_raw.txt（spec 明確說明不保留逐字稿歷史） |
| VI. 編輯器同步 | ✅ | 轉錄完成後遞增 `editor_version` 強制 text_area 刷新 |
| VII. 操作防誤 | ✅ | 轉錄期間 disable 所有按鈕（FR-005），API 失敗保留原稿（FR-007） |

**Pre-Phase 0 Gate**: 通過，無 violations。

**Post-Phase 1 Re-check**: 設計未引入新依賴、僅修改 `app.py` 的 2 個既有函數 + 新增 2 個 helper、向下相容舊 metadata。通過。

## Project Structure

### Documentation (this feature)

```text
specs/004-retranscribe/
├── plan.md              # This file
├── research.md          # Phase 0: 研究決策
├── data-model.md        # Phase 1: meeting_meta.json schema 變更
├── quickstart.md        # Phase 1: 實作細節與驗證步驟
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
app.py                   # 主應用 — 修改 _show_transcript_review()、_save_meeting_meta()、_do_transcription()；新增 _find_audio_path()、_do_retranscribe()
transcriber.py           # 轉錄邏輯 — 不修改（重用 transcribe()）
config.py                # 設定檔 — 新增 AUDIO_EXTENSIONS 常數
output/                  # 會議資料目錄（meeting_meta.json、transcript_raw.txt 在此）
```

**Structure Decision**: 主要變更集中在 `app.py`，新增兩個函數（`_find_audio_path` 音檔定位、`_do_retranscribe` 重新轉錄流程）。`config.py` 僅新增一個常數。無需新增模組或資料夾。

## Complexity Tracking

> 無 Constitution violations — 本節留空。
# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]  
**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]  
**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]  
**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]  
**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]
**Project Type**: [e.g., library/cli/web-service/mobile-app/compiler/desktop-app or NEEDS CLARIFICATION]  
**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]  
**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]  
**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Gates determined based on constitution file]

## Project Structure

### Documentation (this feature)

```text
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

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
