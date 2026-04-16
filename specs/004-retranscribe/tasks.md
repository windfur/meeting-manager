# Tasks: Retranscribe（重新轉錄）

**Input**: Design documents from `/specs/004-retranscribe/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: 新增共用常數

- [x] T001 Add `AUDIO_EXTENSIONS` constant set in config.py（值：`{'.mp3', '.mp4', '.wav', '.m4a', '.ogg', '.webm', '.mpeg', '.mpga'}`，放在 `MAX_AUDIO_SIZE_MB` 附近）

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: audio_path 持久化基礎設施與 session state 初始化，所有 User Story 的前置條件

**⚠️ CRITICAL**: US1/US2 都依賴這些變更，必須先完成

- [x] T002 Add `retranscribing` (bool, default `False`) and `audio_path` (default `None`) to session state initialization in app.py `main()`
- [x] T003 Modify `_save_meeting_meta()` in app.py to read `audio_path` from `st.session_state` and persist to meeting_meta.json；同時保留既有 JSON 中的 `audio_path` 避免被覆蓋（參考 quickstart.md §7）
- [x] T004 Modify `_do_transcription()` in app.py to save `audio_path` to `st.session_state.audio_path` after storing audio file to output_dir, before calling `_save_meeting_meta()`（參考 quickstart.md §6）。⚗️ **注意**：`has_existing` 分支（~L574）和新轉錄分支都要設定 `audio_path`，因為兩條路徑都會產生/使用音檔路徑
- [x] T005 Create `_find_audio_path(output_dir)` utility function in app.py — 優先讀取 meeting_meta.json 的 `audio_path` 欄位，fallback 掃描 output_dir 內符合 `config.AUDIO_EXTENSIONS` 的音檔；恰好 1 個回傳路徑，0 個或多個回傳 `None`（參考 quickstart.md §3、research.md R1）

**Checkpoint**: audio_path 持久化與定位機制就緒，可開始實作 User Story

---

## Phase 3: User Story 1 — 使用新設定重新轉錄當前會議 (Priority: P1) 🎯 MVP

**Goal**: 使用者在 Step 1 頁面點擊「重新轉錄」按鈕，系統重新呼叫 Whisper API 產生逐字稿，覆蓋 transcript_raw.txt 並即時更新頁面。

**Independent Test**: 開啟任一會議的 Step 1 頁面，點擊重新轉錄按鈕，確認逐字稿內容被更新、spinner 顯示、完成後按鈕恢復。

### Implementation for User Story 1

- [x] T006 [US1] Create `_do_retranscribe()` function in app.py — 呼叫 `transcribe(audio_path, progress_callback)`，成功後覆蓋 `transcript_raw.txt`、更新 `st.session_state.raw_transcript`、遞增 `editor_version`；API 失敗時 `st.error()` 並保留原稿不受影響（FR-007）；finally 區塊設定 `retranscribing = False`（參考 quickstart.md §4）
- [x] T007 [US1] Add retranscribe button and trigger logic in `_show_transcript_review()` in app.py — 新增 `is_busy` 條件包含 `retranscribing`；渲染「🔄 重新轉錄」按鈕（轉錄中顯示「⏳ 重新轉錄中...」）；點擊後設定 `retranscribing=True` + `audio_path` 並 `st.rerun()`；偵測 `retranscribing==True` 時呼叫 `_do_retranscribe()` 再 `st.rerun()`（參考 quickstart.md §5）
- [x] T008 [US1] Update all existing button `disabled` conditions in `_show_transcript_review()` in app.py to include `retranscribing` in `is_busy` check（確認按鈕、前往摘要按鈕等既有按鈕的 disabled 邏輯同步更新）。⚗️ **注意**：除了主要的 `is_busy`（~L695），還有 `is_busy_meta`（~L635，metadata 欄位的 disabled）也要加入 `retranscribing`

**Checkpoint**: 核心重新轉錄功能可用——有音檔的會議可成功重新轉錄

---

## Phase 4: User Story 2 — 音檔遺失時的錯誤處理 (Priority: P1)

**Goal**: 音檔不存在或無法定位時，系統顯示明確錯誤訊息，不修改現有逐字稿，按鈕顯示 disabled。

**Independent Test**: 手動修改 meeting_meta.json 中 `audio_path` 指向不存在的路徑，或刪除 `audio_path` 欄位且資料夾無音檔，開啟 Step 1 頁面確認按鈕 disabled 且有提示文字。

### Implementation for User Story 2

- [x] T009 [US2] Add disabled state and caption for missing audio in `_show_transcript_review()` in app.py — 當 `_find_audio_path()` 回傳 `None` 時 retranscribe 按鈕設為 `disabled=True`，下方顯示 `st.caption("⚠️ 找不到原始音檔，無法重新轉錄")`（FR-006、research.md R5）
- [x] T010 [US2] Add audio file validation guards at top of `_do_retranscribe()` in app.py — 檢查 `audio_path` 為 `None` 或檔案不存在時 `st.error("❌ 找不到原始音檔：{path}，無法重新轉錄")` 並 return；檔案大小為 0 時 `st.error("❌ 音檔大小為 0，無法轉錄")` 並 return（edge case from spec.md）

**Checkpoint**: 所有路徑（有音檔 / 無音檔 / API 失敗）均有明確的使用者回饋

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: 驗證與收尾

- [x] T011 Run quickstart.md verification steps — 驗證新會議轉錄後 meeting_meta.json 含 `audio_path`、舊會議 fallback 掃描正常、重新轉錄成功覆蓋逐字稿、音檔遺失時 disabled + 提示、API 失敗保留原稿
- [x] T012 Validate edge cases — 多音檔資料夾回傳 None、metadata JSON 損壞時 fallback 正常、`editor_version` 遞增使 text_area 刷新

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 無依賴，可立即開始
- **Foundational (Phase 2)**: 依賴 Phase 1（`AUDIO_EXTENSIONS` 常數）— **阻塞所有 User Story**
- **US1 (Phase 3)**: 依賴 Phase 2 完成
- **US2 (Phase 4)**: 依賴 Phase 2 完成；與 US1 可並行但建議先完成 US1（US2 的驗證需要按鈕存在）
- **Polish (Phase 5)**: 依賴 US1 + US2 完成

### User Story Dependencies

- **User Story 1 (P1)**: Phase 2 完成後可開始 — 不依賴 US2
- **User Story 2 (P1)**: Phase 2 完成後可開始 — 建議 US1 先完成（按鈕基礎架構在 T007）

### Within Each User Story

- US1: T006（_do_retranscribe）→ T007（按鈕 + trigger）→ T008（is_busy 同步）
- US2: T009（disabled + caption）→ T010（validation guards）

### Parallel Opportunities

- T003、T004、T005 修改 app.py 不同函數，邏輯獨立但同一檔案，建議依序執行
- T006 與 T009 分別建立/修改不同函數，但都在 app.py，建議依 US 順序執行
- 此功能規模小（2 檔案、~12 個 task），並行收益有限，建議線性執行 Phase 1→2→3→4→5

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup（config.py 常數）
2. Complete Phase 2: Foundational（session state + metadata + find_audio）
3. Complete Phase 3: User Story 1（重新轉錄核心流程）
4. **STOP and VALIDATE**: 測試有音檔的會議能否成功重新轉錄
5. 功能即可使用

### Incremental Delivery

1. Phase 1 + 2 → 基礎設施就緒
2. + User Story 1 → 核心功能可用（MVP）
3. + User Story 2 → 錯誤處理完善
4. + Polish → 全面驗證

---

## Notes

- 所有變更集中在 `config.py`（1 個常數）和 `app.py`（2 個新函數 + 3 個既有函數修改 + session state 初始化）
- `transcriber.py` 不需修改，重用現有 `transcribe()` 管道
- 詳細實作程式碼參考 `quickstart.md` 各章節
- Commit 建議：Phase 1+2 一個 commit、US1 一個 commit、US2 一個 commit
