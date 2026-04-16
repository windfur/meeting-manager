# Feature Specification: Retranscribe（重新轉錄）

**Feature Branch**: `004-retranscribe`  
**Created**: 2026-04-14  
**Status**: Draft  
**Input**: 在逐字稿審閱頁面新增「重新轉錄」按鈕，讓使用者可用原始音檔重新呼叫 Whisper API 產生逐字稿，覆蓋現有的 transcript_raw.txt。

## User Scenarios & Testing

### User Story 1 - 使用新設定重新轉錄當前會議（Priority: P1）

使用者在逐字稿審閱頁面（Step 1）發現轉錄品質不佳（例如簡繁體混用），調整了 Whisper 參數或 prompt 後，點擊「重新轉錄」按鈕用新設定重新產生逐字稿。

**Why this priority**: 這是功能的核心價值——允許使用者迭代轉錄品質。

**Independent Test**: 開啟任一會議的 Step 1 頁面，點擊重新轉錄按鈕，確認逐字稿內容被更新。

**Acceptance Scenarios**:

1. **Given** 使用者在 Step 1 審閱頁面，且 meeting_meta.json 中 audio_path 指向有效音檔，**When** 使用者點擊「重新轉錄」按鈕，**Then** 系統呼叫 Whisper API 重新轉錄，完成後 transcript_raw.txt 被覆蓋，頁面上的逐字稿顯示區域即時更新為新內容。
2. **Given** 重新轉錄正在執行中，**When** 使用者嘗試點擊其他操作按鈕，**Then** 這些按鈕處於 disabled 狀態，無法觸發操作。
3. **Given** 重新轉錄成功完成，**When** 系統恢復正常狀態，**Then** 所有按鈕恢復可操作，並顯示成功訊息。

---

### User Story 2 - 音檔遺失時的錯誤處理（Priority: P1）

使用者從歷史會議載入一場舊會議，點擊「重新轉錄」，但原始音檔已被刪除或移動。

**Why this priority**: 錯誤處理是功能完整性的必要條件，與核心功能同等重要。

**Independent Test**: 手動修改 meeting_meta.json 中的 audio_path 指向不存在的路徑，點擊重新轉錄按鈕。

**Acceptance Scenarios**:

1. **Given** 使用者在 Step 1 審閱頁面，且 audio_path 指向不存在的檔案，**When** 使用者點擊「重新轉錄」，**Then** 系統顯示明確的錯誤訊息（例如「找不到原始音檔：[路徑]，無法重新轉錄」），不修改現有逐字稿。
2. **Given** meeting_meta.json 中不存在 audio_path 欄位，且 output 資料夾中也找不到音檔，**When** 使用者在 Step 1 頁面，**Then** 「重新轉錄」按鈕顯示為 disabled，附帶提示「找不到原始音檔」。

### Edge Cases

- 重新轉錄過程中網路中斷或 Whisper API 回傳錯誤時，應保留原有 transcript_raw.txt 不被損毀，並顯示錯誤訊息。
- 音檔檔案存在但格式損壞或大小為 0 時，應顯示適當錯誤。
- 使用者在轉錄進行中關閉瀏覽器或切換頁面時，轉錄流程的行為由 Streamlit session 管理（不在此 spec 範圍內進行特殊處理）。

## Requirements

### Functional Requirements

- **FR-001**: 系統 MUST 在 Step 1 逐字稿審閱頁面提供「重新轉錄」按鈕。
- **FR-002**: 點擊重新轉錄時，系統 MUST 先從 meeting_meta.json 讀取 audio_path；若該欄位不存在，則 fallback 掃描 output 資料夾中的音檔（mp3/mp4/wav/m4a/ogg/webm），找到唯一音檔後驗證其存在再執行轉錄。
- **FR-002a**: 新會議首次轉錄完成後，系統 MUST 將 audio_path 存入 meeting_meta.json，供後續重新轉錄使用。
- **FR-003**: 重新轉錄 MUST 使用當前的 Whisper 參數與 prompt 設定（與首次轉錄相同的管道）。
- **FR-004**: 轉錄完成後，系統 MUST 覆蓋現有 transcript_raw.txt 並即時更新頁面顯示。
- **FR-005**: 重新轉錄期間，系統 MUST disable 頁面上的其他操作按鈕，防止衝突操作。
- **FR-006**: 音檔不存在或 audio_path 缺失時，系統 MUST 顯示明確的錯誤訊息，不修改現有逐字稿。
- **FR-007**: 轉錄 API 呼叫失敗時，系統 MUST 保留原有 transcript_raw.txt 不受影響，並顯示錯誤訊息。

## Success Criteria

### Measurable Outcomes

- **SC-001**: 使用者可在 3 次點擊以內完成重新轉錄操作（進入會議 → Step 1 → 點擊按鈕）。
- **SC-002**: 音檔遺失時，100% 的情況下顯示可理解的錯誤訊息而非系統崩潰。
- **SC-003**: 轉錄失敗時，100% 的情況下保留原有逐字稿內容不受損。
- **SC-004**: 重新轉錄完成後，頁面自動顯示新逐字稿，無需使用者手動重新整理。

## Assumptions

- 新會議的 meeting_meta.json 會包含 audio_path 欄位；舊會議可能沒有此欄位，系統透過掃描 output 資料夾中的音檔作為 fallback。
- 現有的 transcriber.py 中的轉錄邏輯可被重用，不需要從頭實作 Whisper API 呼叫。
- 重新轉錄不需保留舊版逐字稿的歷史紀錄（覆蓋即可）。
- Whisper API 的參數和 prompt 設定來自現有的 config 機制，此功能不新增設定介面。
