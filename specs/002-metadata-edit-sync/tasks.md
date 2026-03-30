# Tasks: 會議 Metadata 顯示與同步

**Input**: Design documents from `/specs/002-metadata-edit-sync/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Tests**: 未明確要求測試，本檔不含測試任務。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Project initialization

> N/A — 既有專案，無需初始化。所有變更集中在 `app.py` 單一檔案。

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 新增共用 helper 與 session state 初始化，所有 User Story 都依賴此階段

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T001 Add `_parse_comma_list()` helper function in app.py (after existing helper functions, before `_show_transcript_review()`)
- [X] T002 Add `meta_tags_input` and `meta_participants_input` to session state initialization block in app.py main()

**Checkpoint**: Foundational ready — User Story implementation can now begin

---

## Phase 3: User Story 1 — 恢復會議時顯示 Metadata (Priority: P1) 🎯 MVP

**Goal**: 使用者從側邊欄恢復歷史會議後，在 Step 1（逐字稿審閱）和 Step 2（摘要審閱）都能看到並編輯該會議的標籤與參與者

**Independent Test**: 恢復任一有 metadata 的歷史會議 → Step 1 和 Step 2 都顯示標籤、參與者欄位且可編輯 → 在 Step 1 修改後進入 Step 2 確認同步

### Implementation for User Story 1

- [X] T003 [US1] Update `_resume_meeting()` to set `st.session_state.meta_tags_input` and `st.session_state.meta_participants_input` from loaded tags/participants in app.py
- [X] T004 [US1] Add tags and participants `st.text_input` fields (key=`meta_tags_input`/`meta_participants_input`) to `_show_transcript_review()` header area in app.py
- [X] T005 [US1] Add tags and participants `st.text_input` fields (key=`meta_tags_input`/`meta_participants_input`) to `_show_summary_review()` header area in app.py
- [X] T006 [US1] Update "確認逐字稿，產生摘要" handler to parse `meta_tags_input`/`meta_participants_input` via `_parse_comma_list()` into `session_state.tags`/`session_state.participants`, and sync `meta_tags_input` after auto_tags fallback in app.py

**Checkpoint**: 恢復歷史會議 → Step 1/2 metadata 可見可編輯，跨步驟同步正確

---

## Phase 4: User Story 2 — 儲存草稿時同步 Metadata (Priority: P1)

**Goal**: 使用者修改標籤/參與者後，按「💾 儲存草稿」時同步回存至 meeting_meta.json；上傳 Notion 時使用最新值

**Independent Test**: 恢復會議 → 修改標籤 → 儲存草稿 → 重新恢復同一場會議 → 確認標籤保留修改後的值

### Implementation for User Story 2

- [X] T007 [US2] Update "💾 儲存草稿" handler to parse `meta_tags_input`/`meta_participants_input` via `_parse_comma_list()` into `session_state.tags`/`session_state.participants` and call `_save_meeting_meta()` in app.py
- [X] T008 [US2] Update "✅ 確認上傳" handler to parse `meta_tags_input`/`meta_participants_input` via `_parse_comma_list()` into `session_state.tags`/`session_state.participants` before calling `_upload_to_notion()` in app.py

**Checkpoint**: 修改 metadata → 儲存草稿 → 重新恢復 → 修改值 100% 保留；上傳 Notion 使用最新值

---

## Phase 5: User Story 3 — 新會議流程中 Metadata 貫穿所有步驟 (Priority: P2)

**Goal**: 使用者在新會議 Step 0 填入的標籤/參與者，在進入 Step 1/2 後依然可見可編輯

**Independent Test**: 建立新會議填入 tags → 走完轉錄 → Step 1 確認 tags 可見可改 → Step 2 確認同步

### Implementation for User Story 3

- [X] T009 [US3] Update "🚀 開始轉錄" handler to set `st.session_state.meta_tags_input` and `st.session_state.meta_participants_input` from parsed Step 0 input values in app.py

**Checkpoint**: 新會議 Step 0 填入 metadata → Step 1/2 正確預填並可編輯

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 驗證邊界情況與整體品質

- [X] T010 Validate disabled state for metadata fields during transcription and upload operations in app.py (Constitution VII 操作防誤)
- [X] T011 Run quickstart.md verification steps and validate edge cases (trim, empty values, consecutive commas) in app.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: N/A
- **Foundational (Phase 2)**: No dependencies — can start immediately. BLOCKS all user stories.
- **US1 (Phase 3)**: Depends on Foundational (Phase 2) completion
- **US2 (Phase 4)**: Depends on Foundational (Phase 2) completion. Logically follows US1 (metadata fields must exist before save handler can reference them)
- **US3 (Phase 5)**: Depends on Phase 3 (US1) — metadata fields in Step 1/2 must already exist
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational — No dependencies on other stories
- **User Story 2 (P1)**: Depends on US1 (T004/T005 metadata fields must exist for save handler to parse)
- **User Story 3 (P2)**: Depends on US1 (T004/T005 metadata fields must exist to display Step 0 values)

### Within Each User Story

- T003 (resume) before T004/T005 (fields) — restored values must populate session state before rendering
- T004/T005 (fields) before T006 (step transition sync) — fields must exist before transition handler can parse them
- T007/T008 (save/upload handlers) are independent of each other within US2

### Parallel Opportunities

Within this feature, parallelism is limited because all changes are in `app.py`. However:

- T001 and T002 (Foundational) touch non-overlapping sections and can be applied sequentially in one pass
- T004 and T005 (metadata fields in Step 1 vs Step 2) touch different functions — logical parallelism
- T007 and T008 (save vs upload handlers) touch different handlers — logical parallelism

---

## Parallel Example: User Story 1

```
# T003 first (sets up resume values):
Task: Update _resume_meeting() to set meta_tags_input/meta_participants_input

# T004 and T005 (different functions, no cross-dependency):
Task: Add metadata fields to _show_transcript_review()
Task: Add metadata fields to _show_summary_review()

# T006 last (depends on T004/T005 fields existing):
Task: Update step transition handler to sync metadata
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: Foundational (T001–T002)
2. Complete Phase 3: User Story 1 (T003–T006)
3. **STOP and VALIDATE**: 恢復歷史會議，確認 Step 1/2 metadata 顯示正確、跨步驟同步正常
4. Can deploy/demo: 使用者已可看到並編輯 metadata

### Incremental Delivery

1. Foundational (T001–T002) → helper + session state ready
2. US1 (T003–T006) → 恢復會議 metadata 可見可改 (MVP!)
3. US2 (T007–T008) → 草稿儲存 + Notion 上傳使用最新 metadata
4. US3 (T009) → 新會議流程 metadata 貫穿
5. Polish (T010–T011) → 邊界驗證 + disabled 狀態
6. Each story adds value without breaking previous stories

---

## Notes

- 所有變更集中在 `app.py` 單一檔案
- `_save_meeting_meta()` 函數本身不需修改，已正確從 session_state 讀取 tags/participants
- Widget key 使用固定值（非版本化），因 metadata 不存在外部強制覆蓋場景（Research R2）
- Tags 優先序不變：使用者輸入 > AI auto_tags > 磁碟載入（Research R4）
- Commit after each phase or logical group
