# Feature Specification: 上傳狀態鎖定與編輯器同步修復

**Feature Branch**: `001-upload-lock-and-editor-sync`
**Created**: 2026-03-30
**Status**: Draft

## Project Context

會議管理助手是一個 Streamlit 應用，流程為：

1. **上傳音檔** → 2. **審閱逐字稿**（可批次取代修正辨識錯誤） → 3. **AI 兩階段摘要**（Phase 1 議題結論追蹤 → Phase 2 結構化摘要） → 4. **審閱摘要**（可切換 AI 版本、編輯、儲存草稿） → 5. **一鍵上傳 Notion**

目前已支援：
- 多 Notion token 切換（個人/公司 workspace）
- 使用者自選目標頁面和資料庫
- 摘要版本歷史（summary_v1.md, v2.md...）+ 草稿持久化（summary_draft.md）
- 歷史會議瀏覽器（sidebar 掃描 output/ 恢復舊會議）
- 自訂摘要規範（summary_style.md），無自訂時使用 prompts/phase2_default_style.md 預設

### 技術架構
- Python 3.12 + Streamlit 1.55
- OpenAI API：Whisper（轉錄）+ gpt-4.1-mini（摘要）
- Notion REST API（httpx 直接呼叫）
- 本地儲存：output/{date}_{name}/ 目錄

### 已知問題（本 spec 要修復的）
1. 上傳 Notion 期間，UI 未鎖定 → 可重複點擊上傳、切換版本
2. 逐字稿批次取代讀取錯誤的 widget key → 使用者手動編輯會被覆蓋
3. 摘要產生期間，版本選擇器未 disabled → 可能導致狀態混亂

## Clarifications

### Session 2026-03-30

- Q: 上傳 Notion 執行模式：同步阻塞（sync）還是 rerun 模式？ → A: Option B — rerun 模式（與 summarize 一致，設 uploading=True 後 st.rerun()，讓 Streamlit 重繪時所有 widget 讀取 disabled 狀態）
- Q: 上傳失敗後錯誤訊息呈現方式？ → A: Option A — `uploading=False` → `st.rerun()` → 重繪時 `st.error()` 顯示錯誤（留到下次互動自動消失），所有按鈕立即恢復可操作

## User Scenarios & Testing

### User Story 1 - 上傳 Notion 時鎖定所有互動（Priority: P1）

使用者按下「確認上傳 Notion」後，所有版本選擇器、編輯器、按鈕都應該被鎖定，直到上傳完成或失敗。避免使用者在上傳過程中切換版本或重複點擊上傳。

**Why this priority**: 上傳期間切換版本或重複上傳可能導致資料不一致或 Notion 重複建立頁面。

**Independent Test**: 啟動上傳後，嘗試點擊任何按鈕或切換版本，應全部為 disabled 狀態。

**Acceptance Scenarios**:

1. **Given** 使用者在審閱摘要頁面, **When** 按下「確認上傳 Notion」, **Then** 版本選擇器（radio）、摘要編輯器（text_area）、Highlights 編輯器、儲存草稿按鈕、重新產生按鈕、回到逐字稿按鈕全部 disabled
2. **Given** 上傳成功, **When** 頁面跳轉到結果頁, **Then** 所有鎖定自動解除
3. **Given** 上傳失敗, **When** 顯示錯誤訊息, **Then** 所有按鈕恢復可操作狀態

---

### User Story 2 - 批次取代讀取正確的編輯器內容（Priority: P1）

使用者在逐字稿編輯器中手動修改文字後，點擊「套用取代」時，批次取代應該基於使用者目前在編輯器中看到的內容，而不是原始的 raw_transcript。

**Why this priority**: 目前有 bug — 批次取代會覆蓋使用者的手動編輯。

**Independent Test**: 在逐字稿編輯器中手動改幾個字，然後執行批次取代，確認手動修改仍保留。

**Acceptance Scenarios**:

1. **Given** 使用者在編輯器中把「Hello」改成「Hi」, **When** 執行批次取代將「World」→「Earth」, **Then** 編輯器內容為「Hi ... Earth」（兩個修改都保留）
2. **Given** 使用者未做任何手動編輯, **When** 執行批次取代, **Then** 正常運作與現在相同

---

### User Story 3 - 摘要產生期間鎖定版本選擇器（Priority: P2）

使用者按下「重新產生摘要」後，版本選擇器應該被鎖定，避免在 AI 產生摘要過程中切換版本導致狀態混亂。

**Why this priority**: 防止 AI 產生中切換版本導致結果覆蓋錯誤的版本狀態。

**Independent Test**: 按下重新產生後，嘗試切換版本 radio，應為 disabled。

**Acceptance Scenarios**:

1. **Given** 使用者按下「重新產生摘要」, **When** AI 正在產生中, **Then** 版本選擇器 radio disabled
2. **Given** AI 產生完成, **When** 新版本加入清單, **Then** 版本選擇器恢復可用，自動切到最新版

---

### Edge Cases

- 上傳中途網路中斷：`uploading=False` → `st.rerun()` → `st.error()` 顯示錯誤訊息，所有按鈕恢復可操作，使用者可重試
- 使用者在上傳中關閉瀏覽器：不需處理（Streamlit 會自動中斷 session）
- 批次取代的 old/new 欄位為空：按鈕已 disabled（現有邏輯）

## Requirements

### Functional Requirements

- **FR-001**: 新增 `uploading` session state 旗標（類似現有的 `summarizing`）
- **FR-002**: 上傳期間 `is_busy` 判斷改為 `summarizing or uploading`
- **FR-003**: 審閱摘要頁面所有互動 widget（radio、text_area、text_input、selectbox、button）必須加入 `disabled=is_busy` 參數
- **FR-004**: 批次取代改用版本化 widget key `transcript_editor_v{st.session_state.editor_version}` 而非靜態 key `"transcript_editor"`
- **FR-005**: 上傳採用 rerun 模式：按下上傳 → 設 `uploading=True` → `st.rerun()` → 重繪時偵測 `uploading` 執行實際上傳 → 完成後設 `uploading=False` → `st.rerun()`；失敗時額外存 `upload_error` 到 session_state

### Key Entities

- **session_state.uploading**: Boolean，上傳 Notion 期間為 True
- **is_busy**: 統一判斷 = `summarizing or uploading`

## Success Criteria

- **SC-001**: 上傳期間沒有任何按鈕可被連續點擊
- **SC-002**: 批次取代後，使用者手動編輯的內容 100% 保留
- **SC-003**: 版本切換後，編輯器內容 100% 與選擇的版本一致
- **SC-004**: 上傳失敗時，UI 在 3 秒內恢復為可操作狀態

## Non-Functional Requirements

- **NFR-001**: 不影響現有的摘要產生流程（Phase 1 + Phase 2）
- **NFR-002**: 不影響歷史會議瀏覽器的載入邏輯
- **NFR-003**: 維持所有 widget key 使用版本化模式（`widget_v{N}`），禁止靜態 key
- **NFR-004**: 所有變更需符合 constitution.md 定義的編輯器同步原則（第 VI 條）

## Assumptions

- Streamlit 的 `disabled` 參數對 radio/text_area/button 都有效
- 上傳 Notion 是同步操作（在 `st.status` 中執行），不需 async 處理
- 音檔最大 1GB（.env 中 maxUploadSize=1024），轉錄和摘要階段不受本 spec 影響
- 自訂摘要規範（summary_style.md）的存取不受本 spec 影響
- 多 Notion token 管理邏輯不受本 spec 影響（只影響上傳按鈕的 disabled 狀態）
