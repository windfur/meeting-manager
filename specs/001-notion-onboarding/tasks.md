# Tasks: Notion 帳號 Onboarding 優化

**Input**: Design documents from `/specs/001-notion-onboarding/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md
**Status**: 已實作（文件補齊用）

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: 無需額外的 setup — 所有改動在既有檔案上進行

> 本功能不新增任何檔案或依賴套件，跳過此階段。

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 修改 main() 啟動流程和 config check，這是所有 user story 的前提

**⚠️ CRITICAL**: 渲染順序調整必須先完成，否則 sidebar 不會在 config check 失敗時顯示

- [x] T001 移動 session state 初始化和全部 sidebar 渲染（含 `_show_meeting_browser()`、`_show_notion_accounts()`、`_show_style_settings()`）至 config check 和 Notion token check 之前，確保無 token 時所有 sidebar 元件仍可見，在 app.py main()
- [x] T002 修改 `_check_config()` 移除 Notion token 檢查，只保留 OPENAI_API_KEY 驗證，在 app.py `_check_config()` 函數
- [x] T003 在 main() 中 `_check_config()` 之後新增獨立的 Notion token 檢查：`if not config.load_notion_tokens()` 顯示 `st.info("👈 請先在左側『🔑 Notion 帳號』新增至少一組 Token，才能開始使用。")` 引導提示並 return，在 app.py main()（涵蓋 FR-003 + US2 引導提示）

**Checkpoint**: 啟動流程重構完成 — config check 不再阻擋 sidebar，Notion token 有獨立檢查含引導提示

---

## Phase 3: User Story 1 - 新使用者首次啟動 (Priority: P1) 🎯 MVP

**Goal**: 新使用者無 Notion token 也能看到完整 UI 和側邊欄，新增 token 後解鎖主流程

**Independent Test**: 移除所有 Notion token 設定後啟動 app，驗證 UI 正常載入且側邊欄可操作

> US1 的核心功能已由 Phase 2 的 T001-T003 完成（sidebar 永遠可見 + token 缺失不阻擋啟動）。
> 以下為 US1 專屬的使用者體驗優化。

- [x] T004 [US1/US4] 驗證 sidebar 渲染獨立於 config check：(a) 無 Notion token 時 sidebar 可見可操作、meeting browser 正常瀏覽歷史會議 [FR-008]、新增 token 後 rerun 即解鎖主流程（FR-006）；(b) 無 OPENAI_API_KEY 時主區域顯示 st.error、sidebar 仍完整可見可操作，在 app.py main()

**Checkpoint**: US1+US4 可獨立驗證 — sidebar 在任何 config 狀態下皆可見

---

## Phase 4: User Story 2 - 無 token 時主區域引導提示 (Priority: P2)

**Goal**: 清楚告知新使用者需要新增 Notion 帳號，降低操作門檻

**Independent Test**: 無 token 啟動 app，驗證主區域提示文字和 expander 展開狀態

> 引導提示文字已由 T003 涵蓋，本 Phase 只處理 expander 展開。

- [x] T005 [US2] 修改 `_show_notion_accounts()` 的 expander 從 `expanded=False` 改為 `expanded=not tokens`，在 app.py `_show_notion_accounts()` 函數

**Checkpoint**: US2 可獨立驗證 — 無 token 時 expander 自動展開 + 主區域顯示引導提示（T003）

---

## Phase 5: User Story 3 - Page selector 防護 (Priority: P3)

**Goal**: 無 active token 時 page selector 不呼叫 API，顯示友善提示

**Independent Test**: 在 token 存在但 active token 為空的狀態下觀察 page selector 行為

- [x] T006 [US3] 在 `_show_notion_page_selector()` 開頭加入 guard：`if not st.session_state.get("active_notion_token")` 時顯示提示並 return，在 app.py `_show_notion_page_selector()` 函數

**Checkpoint**: US3 可獨立驗證 — 無 active token 時 page selector 不發 API request、顯示提示

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 最終驗證和清理

- [x] T007 執行 quickstart.md 驗證步驟（5 步驟完整走一遍）
- [x] T008 [P] 確認 .notion_tokens.json 在 .gitignore 中

> **隱式滿足的需求**：
> - FR-006（rerun 解鎖）：由 `_show_notion_accounts()` 中既有的 `st.rerun()` 機制滿足，T004 驗證
> - FR-007（雙來源 token）：由 `config.load_notion_tokens()` 既有邏輯滿足，非本 feature 新增

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 2)**: 無前置依賴 — 直接修改 app.py
- **US1+US4 (Phase 3)**: 依賴 Phase 2 完成
- **US2 (Phase 4)**: 依賴 Phase 2 完成，可與 Phase 3 並行
- **US3 (Phase 5)**: 依賴 Phase 2 完成，可與其他 US 並行
- **Polish (Phase 6)**: 依賴所有 US 完成

### User Story Dependencies

- **US1+US4 (P1/P2)**: 核心功能由 Phase 2 覆蓋，Phase 3 合併驗證
- **US2 (P2)**: 獨立於其他 US，只改 expander（引導提示已合併至 T003）
- **US3 (P3)**: 獨立於其他 US，只改 page selector

### Parallel Opportunities

- Phase 3/4/5 可全部並行（不同功能區域）
- T007 和 T008（Polish）可並行

---

## Implementation Strategy

### MVP Scope

**User Story 1（Phase 2 + Phase 3）**即為 MVP：

- 修改 main() 渲染順序 + config check 邏輯 → 新使用者能進入 UI
- 新增 Notion token 後主流程解鎖

### Incremental Delivery

1. **MVP**: Phase 2 + US1 → 新使用者可以用了
2. **UX 優化**: US2 → 引導提示 + expander 自動展開
3. **完整性**: US3 + US4 → 防禦性設計 + edge case 覆蓋
4. **收尾**: Polish → 驗證 + 確認 gitignore
