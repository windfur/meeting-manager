# Tasks: 歷史會議帳號標記與篩選

**Input**: Design documents from `/specs/003-notion-account-history/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Tests**: 本功能規格未要求自動化測試，不產生測試任務。

**Organization**: 依 User Story 分組。所有變更集中在 `app.py`（單檔修改模式），無新增檔案。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: 建立功能分支

- [X] T001 建立 git branch `003-notion-account-history` 並切換

---

## Phase 2: User Story 1 — 上傳時自動記錄帳號標記 (Priority: P1) 🎯 MVP

**Goal**: 使用者上傳會議至 Notion 後，系統自動在 meeting_meta.json 記錄上傳帳號 label。上傳失敗不寫入，重新上傳覆蓋為最新帳號。

**Independent Test**: 上傳一場會議後，開啟 `output/{date}_{name}/meeting_meta.json` 確認包含 `"uploaded_by": "{label}"`。

### Implementation for User Story 1

- [X] T002 [US1] 修改 `_save_meeting_meta()` 新增 `uploaded_by` 參數，非 None 時寫入 JSON；草稿儲存時保留既有 `uploaded_by` 值 in `app.py`
- [X] T003 [US1] 修改 `_upload_to_notion()` 成功路徑：從 `config.load_notion_tokens()` + `st.session_state.notion_token_idx` 取得帳號 label，呼叫 `_save_meeting_meta(output_dir, uploaded_by=account_label)` in `app.py`

**Checkpoint**: 上傳會議後 meeting_meta.json 出現 `uploaded_by` 欄位，上傳失敗則無此欄位。可獨立驗證。

---

## Phase 3: User Story 2 — 歷史會議顯示上傳帳號 (Priority: P2)

**Goal**: 歷史會議瀏覽器中，已上傳且有帳號記錄的會議顯示為「🟢已上傳（{label}）」，舊資料向下相容顯示「🟢已上傳」。

**Independent Test**: 在有多場不同帳號上傳會議的環境中，開啟歷史瀏覽器確認每場會議正確顯示帳號名稱。

### Implementation for User Story 2

- [X] T004 [US2] 修改 `_scan_meetings()` 讀取每個會議資料夾的 `meeting_meta.json`，提取 `uploaded_by` 欄位並附加至回傳 dict；JSON 缺失或損壞時 `uploaded_by` 為 None in `app.py`
- [X] T005 [US2] 修改 `_scan_meetings()` 中 status_text 邏輯：已上傳且 `uploaded_by` 非 None 時 status_text 為 `已上傳（{uploaded_by}）` in `app.py`
- [X] T006 [US2] 修改 `_show_meeting_browser()` 會議列表 label 組裝邏輯，使用含帳號資訊的 status_text in `app.py`

**Checkpoint**: 歷史瀏覽器中已上傳會議顯示帳號 label，舊會議顯示「🟢已上傳」無報錯。可獨立驗證。

---

## Phase 4: User Story 3 — 依帳號篩選歷史會議 (Priority: P3)

**Goal**: 使用者可在歷史會議瀏覽器中依帳號篩選（全部 / 只看未上傳 / 特定帳號），與日期篩選為 AND 邏輯。

**Independent Test**: 切換帳號篩選 selectbox，確認列表正確過濾；同時使用日期篩選與帳號篩選，確認 AND 邏輯正確。

### Implementation for User Story 3

- [X] T007 [US3] 在 `_show_meeting_browser()` 收集所有 `uploaded_by` 值建立帳號選項清單（去重、排序），新增帳號篩選 `st.selectbox` (key=`meeting_browser_account`) 於日期篩選下方 in `app.py`
- [X] T008 [US3] 在 `_show_meeting_browser()` 實作帳號篩選邏輯：「全部」不篩選、「只看未上傳」篩 `not has_uploaded`、特定帳號篩 `uploaded_by == selected`，與日期篩選 AND 組合 in `app.py`

**Checkpoint**: 篩選功能完整運作，全部 / 只看未上傳 / 特定帳號皆正確過濾，AND 日期篩選。可獨立驗證。

---

## Phase 4b: User Story 4 — 切換帳號自動篩選歷史會議 (Priority: P3)

**Goal**: 使用者切換 Notion 帳號時，歷史會議瀏覽器的帳號篩選自動切換到對應帳號。若該帳號無歷史記錄則退化為「全部」。

**Independent Test**: 切換 Notion 帳號後，觀察歷史會議帳號篩選 selectbox 是否自動跟隨。

### Implementation for User Story 4

- [X] T011 [US4] 在 `_show_notion_accounts()` 切換帳號時設定 `st.session_state._pending_browser_account = labels[selected_idx]` in `app.py`
- [X] T012 [US4] 在 `_show_meeting_browser()` 建立帳號篩選 selectbox 前，讀取 `_pending_browser_account`；若該值存在於選項中則設為 default index，否則退化為「全部」(index=0) in `app.py`

**Checkpoint**: 切換帳號後歷史會議篩選自動跟隨；帳號無歷史時篩選為「全部」。可獨立驗證。

---

## Phase 4c: User Story 5 — 帳號選擇持久化 (Priority: P3)

**Goal**: 使用者切換帳號後，下次啟動應用時自動還原上次選擇的帳號。

**Independent Test**: 選擇帳號 B → 重啟應用 → 確認帳號仍停在 B。

### Implementation for User Story 5

- [X] T013 [US5] 在 `config.py` 新增 `save_active_notion_account(label)` 和 `load_active_notion_account()` 函數，讀寫 `.notion_active_account` 檔案
- [X] T014 [US5] 修改 `_show_notion_accounts()` 啟動時從磁碟還原帳號選擇（`load_active_notion_account()`）；切換帳號時存檔（`save_active_notion_account()`） in `app.py`
- [X] T015 [US5] 在 `.gitignore` 新增 `.notion_active_account`

**Checkpoint**: 重啟應用後帳號選擇不 reset。可獨立驗證。

---

## Phase 4d: Bug Fix — Sidebar 渲染順序

- [X] T016 調整 sidebar 呼叫順序為 `_show_notion_accounts()` → `_show_meeting_browser()` → `_show_style_settings()`，確保切換帳號的 pending 值在同一次 rerun 內被歷史會議篩選消費（FR-010 timing fix）in `app.py`

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: 向下相容驗證與最終確認

- [X] T009 執行 quickstart.md 驗證步驟（10 項），確認所有場景通過
- [X] T010 確認舊 meeting_meta.json（無 `uploaded_by`）向下相容：歷史瀏覽器正常顯示、不報錯

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 無依賴 — 立即開始
- **US1 (Phase 2)**: 依賴 Setup — T002 → T003（順序執行）
- **US2 (Phase 3)**: 依賴 US1 完成（需 `uploaded_by` 欄位存在）— T004 → T005 → T006（順序執行）
- **US3 (Phase 4)**: 依賴 US2 完成（需 scan 回傳 `uploaded_by`）— T007 → T008（順序執行）
- **Polish (Phase 5)**: 依賴所有 User Story 完成

### User Story Dependencies

- **US1 (P1)**: 無外部依賴，可在 Setup 後開始
- **US2 (P2)**: 依賴 US1（需讀取 `uploaded_by` 欄位）
- **US3 (P3)**: 依賴 US2（需 `uploaded_by` 在 scan 結果中）

### Parallel Opportunities

本功能所有變更集中在 `app.py` 單一檔案，且 User Story 間有資料依賴，因此**無平行執行機會**。建議依 P1 → P2 → P3 順序實作。

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup（建立分支）
2. Complete Phase 2: US1（帳號記錄）
3. **STOP and VALIDATE**: 上傳會議，檢查 meeting_meta.json 中 `uploaded_by` 欄位
4. Continue Phase 3: US2（瀏覽器顯示）
5. Continue Phase 4: US3（帳號篩選）
6. Complete Phase 5: Polish（驗證所有場景）
