# Feature Specification: 會議 Metadata 顯示與同步

**Feature Branch**: `002-metadata-edit-sync`  
**Created**: 2026-03-30  
**Status**: Draft  
**Input**: User description: "恢復歷史會議時在 UI 顯示標籤與參與者（可編輯），儲存草稿時同步回存標籤與參與者至 meeting_meta.json"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 恢復會議時顯示 Metadata (Priority: P1)

使用者從側邊欄歷史會議瀏覽器恢復一場舊會議後，在所有步驟（Step 1 逐字稿審閱、Step 2 摘要審閱、Step 3 上傳完成）都能看到該會議的標籤和參與者，且可以直接修改。

**Why this priority**: 恢復會議是最常見場景，使用者需要確認、修正歷史會議的 metadata 才能正確上傳 Notion。目前恢復後標籤和參與者完全不可見，使用者無法確認資料正確性。

**Independent Test**: 恢復任一有 metadata 的歷史會議，在 Step 1 和 Step 2 都確認標籤、參與者欄位正確顯示且可編輯。

**Acceptance Scenarios**:

1. **Given** 一場歷史會議有 tags=["專案A","進度"] 和 participants=["James","Frank"], **When** 使用者從側邊欄點選恢復該會議, **Then** 所有步驟頁面顯示可編輯的標籤欄位（預填 "專案A, 進度"）和參與者欄位（預填 "James, Frank"）
2. **Given** 一場歷史會議的 meeting_meta.json 中 tags 和 participants 為空陣列, **When** 使用者恢復該會議, **Then** 標籤和參與者欄位顯示為空白，使用者可自行填入
3. **Given** 使用者在 Step 1 修改標籤欄位內容, **When** 進入 Step 2, **Then** Step 2 顯示的標籤為 Step 1 修改後的值（跨步驟同步）

---

### User Story 2 - 儲存草稿時同步 Metadata (Priority: P1)

使用者在摘要審閱頁面編輯標籤和參與者後，按下「💾 儲存草稿」時，修改後的標籤和參與者會一併回存到 meeting_meta.json。

**Why this priority**: 與 US1 同等重要——顯示了卻不存，等於白改。使用者修改 metadata 後期望儲存時一併保存，否則下次恢復會遺失修改。

**Independent Test**: 恢復會議 → 修改標籤 → 儲存草稿 → 重新恢復同一場會議，確認標籤保留修改後的值。

**Acceptance Scenarios**:

1. **Given** 使用者已恢復歷史會議並修改標籤為 "新標籤A, 新標籤B", **When** 點擊「💾 儲存草稿」, **Then** meeting_meta.json 的 tags 更新為 ["新標籤A","新標籤B"]
2. **Given** 使用者已恢復歷史會議並清空參與者欄位, **When** 點擊「💾 儲存草稿」, **Then** meeting_meta.json 的 participants 更新為 []
3. **Given** 使用者已恢復歷史會議但未修改任何 metadata, **When** 點擊「💾 儲存草稿」, **Then** meeting_meta.json 的 tags 和 participants 維持原值不變

---

### User Story 3 - 新會議流程中 Metadata 貫穿所有步驟 (Priority: P2)

使用者在新會議流程中（Step 0 填入 metadata → Step 1 逐字稿 → Step 2 摘要），從 Step 1 開始每個步驟都能看到並修改先前填入的標籤和參與者。

**Why this priority**: 新會議流程目前只有 Step 0 能看到 metadata，進到 Step 1/2 後已不可見。使用者可能在審閱逐字稿或摘要時才發現需要修改標籤。

**Independent Test**: 建立新會議填入 tags → 走完轉錄 → Step 1 確認 tags 可見可改 → Step 2 確認同步。

**Acceptance Scenarios**:

1. **Given** 使用者在 Step 0 填入 tags=["週會"] 和 participants=["Aki"], **When** 進入 Step 1 逐字稿審閱, **Then** 標籤欄位預填 "週會"、參與者欄位預填 "Aki"
2. **Given** 使用者在 Step 1 修改標籤為 "週會, 緊急", **When** 進入 Step 2 摘要審閱, **Then** 標籤欄位預填 "週會, 緊急"
3. **Given** 使用者在 Step 2 修改標籤, **When** 點擊「💾 儲存草稿」, **Then** 修改後的標籤同步存入 meeting_meta.json

---

### Edge Cases

- 恢復的歷史會議沒有 meeting_meta.json 檔案時，標籤和參與者欄位應顯示為空白
- 標籤或參與者包含前後空白時，儲存時應自動 trim
- 標籤輸入包含連續逗號（如 "A,,B"）時，空值應被過濾
- 上傳 Notion 時使用的 tags 和 participants 應來自當前步驟的可編輯欄位（而非 Step 0 的舊值）

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 逐字稿審閱頁面（Step 1）和摘要審閱頁面（Step 2）都必須顯示可編輯的標籤和參與者輸入欄位，預填目前會議的已知值
- **FR-002**: 恢復歷史會議時，標籤和參與者必須從 meeting_meta.json 載入並顯示在所有步驟的輸入欄位中
- **FR-003**: 使用者按下「💾 儲存草稿」時，必須將當前步驟中的標籤和參與者同步寫入 meeting_meta.json
- **FR-004**: 使用者按下「✅ 確認上傳 Notion」時，必須使用當前步驟中最新的標籤和參與者值
- **FR-005**: 標籤和參與者欄位的格式為逗號分隔字串，儲存時需 trim 每個項目並過濾空值
- **FR-006**: 標籤和參與者的修改必須跨步驟同步——在 Step 1 修改後進入 Step 2 時必須反映最新值

### Key Entities

- **meeting_meta.json**: 會議的持久化 metadata 檔案，包含 meeting_name、date、tags（字串陣列）、participants（字串陣列）
- **session state tags/participants**: 執行期間的標籤與參與者資料，型別為字串陣列

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 恢復歷史會議後，使用者在任何步驟都能在 3 秒內確認該會議的標籤與參與者
- **SC-002**: 修改標籤後儲存草稿，再次恢復同一場會議，修改值 100% 保留
- **SC-003**: 從新會議流程進入 Step 1/Step 2 時，Step 0 填入的標籤和參與者 100% 可見可編輯

## Assumptions

- 標籤和參與者的 UI 呈現方式沿用現有 Step 0 的 text_input 風格（逗號分隔字串）
- metadata 欄位放在各步驟主內容上方（Step 1 逐字稿上方、Step 2 摘要編輯器上方），不影響現有排版
- 現有的 metadata 儲存機制已正確實作，只需在適當時機呼叫

## Clarifications

### Session 2026-03-30

- Q: 標籤和參與者只在 Step 2 顯示，還是貫穿所有步驟？ → A: 貫穿所有步驟（Step 1 逐字稿審閱 + Step 2 摘要審閱），跨步驟同步修改值
