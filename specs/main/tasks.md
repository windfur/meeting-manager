# Tasks: 上傳狀態鎖定與編輯器同步修復

**Input**: Design documents from `specs/main/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Session State 基礎)

**Purpose**: 新增 `uploading` 旗標並擴展 `is_busy` 判斷

- [X] T001 在 `app.py` 的 session state 初始化區新增 `uploading` 到 key 清單（~L23），並新增 `if st.session_state.uploading is None: st.session_state.uploading = False`（~L39 之後）

---

## Phase 2: Foundational (is_busy 擴展)

**Purpose**: 所有使用 `is_busy` 的位置都需要擴展為 `summarizing or uploading`，這是所有 User Story 的前提

**⚠️ CRITICAL**: 此 phase 完成前，US1/US2/US3 的 disabled 行為都不會生效

- [X] T002 在 `app.py` 的 `_show_summary_review()` 函式中，將 `is_busy = st.session_state.summarizing`（~L714）改為 `is_busy = st.session_state.summarizing or st.session_state.uploading`
- [X] T003 在 `app.py` 的逐字稿確認區中，將 `is_busy = st.session_state.summarizing`（~L604）改為 `is_busy = st.session_state.summarizing or st.session_state.uploading`

**Checkpoint**: `is_busy` 現在同時反映 summarizing 和 uploading 狀態

---

## Phase 3: User Story 1 — 上傳 Notion 時鎖定所有互動 (Priority: P1) 🎯 MVP

**Goal**: 按下上傳後所有 widget disabled，直到上傳完成/失敗

**Independent Test**: 在審閱摘要頁面按「確認上傳 Notion」，確認所有按鈕、radio、text_area 都變為 disabled，上傳完成或失敗後恢復

### Implementation for User Story 1

- [X] T004 [US1] 在 `app.py` 的 `_show_summary_review()` 開頭（~L711 之後），新增 upload_error 顯示邏輯：`if 'upload_error' in st.session_state: st.error(...); del st.session_state['upload_error']`
- [X] T005 [US1] 在 `app.py` 的上傳按鈕回調（~L776-778）中，改為 rerun 模式：儲存 edited_summary/edited_key_points 到 session_state → 設 `uploading=True` → `st.rerun()`（移除直接呼叫 `_upload_to_notion`）
- [X] T006 [US1] 在 `app.py` 的 `_show_summary_review()` 底部（`if is_busy: _do_summarize()` 區塊之前），新增 uploading 偵測：`if st.session_state.uploading: _upload_to_notion(st.session_state.summary, st.session_state.key_points)`
- [X] T007 [US1] 修改 `app.py` 的 `_upload_to_notion()` 函式（~L891）：在 try 成功路徑加入 `st.session_state.uploading = False`；在 except 區塊改為 `st.session_state.upload_error = str(e); st.session_state.uploading = False; st.rerun()`
- [X] T008 [P] [US1] 在 `app.py` 的版本選擇器 `st.radio`（~L722）加入 `disabled=is_busy` 參數
- [X] T009 [P] [US1] 在 `app.py` 的摘要編輯器 `st.text_area`（~L748）加入 `disabled=is_busy` 參數
- [X] T010 [P] [US1] 在 `app.py` 的 Highlights 編輯器 `st.text_input`（~L754）加入 `disabled=is_busy` 參數
- [X] T011 [US1] 修改 `app.py` 的 `_show_notion_page_selector()` 函式簽名（~L813），新增 `disabled=False` 參數，並將內部的 `st.selectbox`（頁面選擇 ~L840、資料庫選擇 ~L870）和重整按鈕加入 `disabled=disabled` 參數
- [X] T012 [US1] 在 `app.py` 呼叫 `_show_notion_page_selector()` 的位置（~L772），傳入 `disabled=is_busy`

**Checkpoint**: 上傳期間所有 widget disabled，成功跳轉結果頁，失敗顯示 st.error() 並恢復可操作

---

## Phase 4: User Story 2 — 批次取代讀取正確的編輯器內容 (Priority: P1)

**Goal**: 批次取代基於使用者目前編輯器中的內容，而非舊的靜態 key

**Independent Test**: 在逐字稿編輯器手動修改幾個字，執行批次取代，確認手動修改和取代結果都保留

### Implementation for User Story 2

- [X] T013 [US2] 修正 `app.py` 批次取代區（~L582）中的 widget key 讀取：將 `st.session_state.get("transcript_editor", st.session_state.raw_transcript)` 改為 `st.session_state.get(f"transcript_editor_v{st.session_state.editor_version}", st.session_state.raw_transcript)`

**Checkpoint**: 批次取代不再覆蓋使用者手動編輯的內容

---

## Phase 5: User Story 3 — 摘要產生期間鎖定版本選擇器 (Priority: P2)

**Goal**: 版本選擇器在 AI 產生摘要期間 disabled

**Independent Test**: 按「重新產生摘要」後嘗試切換版本 radio，應為 disabled 狀態

### Implementation for User Story 3

> **Note**: T008 已為版本選擇器加入 `disabled=is_busy`，而 `is_busy` 在 Phase 2 已擴展。因此 US3 在 Phase 2 + T008 完成後**自動滿足**。此處無額外任務。

**Checkpoint**: 摘要產生期間版本選擇器、編輯器、按鈕全部 disabled

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 驗證所有變更符合規範

- [X] T014 執行 `streamlit run app.py` 啟動應用，手動驗證 quickstart.md 中的三項測試場景
- [X] T015 執行 `pytest tests/` 確認現有測試未被破壞

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)        → 無依賴，立即開始
Phase 2 (Foundational) → 依賴 Phase 1（需要 uploading 旗標存在）
Phase 3 (US1)          → 依賴 Phase 2（需要 is_busy 擴展）
Phase 4 (US2)          → 依賴 Phase 1 僅（獨立於 US1）
Phase 5 (US3)          → 由 Phase 2 + T008 自動滿足
Phase 6 (Polish)       → 依賴 Phase 3, 4 完成
```

### User Story Dependencies

- **US1 (P1)**: 依賴 Phase 2 → 核心變更量最大
- **US2 (P1)**: 僅依賴 Phase 1 → 獨立 bug fix，可與 US1 平行
- **US3 (P2)**: 由 Phase 2 + T008 自動滿足 → 無額外工作

### Parallel Opportunities

- T008, T009, T010 可平行執行（不同 widget，互不影響）
- US2 (T013) 可與 US1 的任何 task 平行執行（修改不同區域的程式碼）

---

## Parallel Example: User Story 1

```bash
# 先完成依序任務：
T004 → T005 → T006 → T007

# 再平行執行 disabled 參數添加：
T008: 版本選擇器 radio disabled
T009: 摘要編輯器 text_area disabled
T010: Highlights text_input disabled

# 最後完成 Notion selector：
T011 → T012
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002-T003)
3. Complete Phase 3: User Story 1 (T004-T012)
4. **STOP and VALIDATE**: 手動測試上傳鎖定功能
5. Continue to Phase 4: User Story 2 (T013)
6. Phase 5 自動滿足
7. Complete Phase 6: Polish (T014-T015)
