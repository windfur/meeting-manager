# Feature Specification: 歷史會議帳號標記與篩選

**Feature Branch**: `003-notion-account-history`  
**Created**: 2026-03-31  
**Status**: Draft  
**Input**: User description: "現在系統支援多組 Notion 帳號（token），但歷史會議瀏覽器（sidebar）不知道哪場會議是由哪個帳號上傳的。需要在上傳時記錄帳號 label，在歷史瀏覽器中顯示帳號資訊並提供篩選功能。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 上傳時自動記錄帳號標記 (Priority: P1)

使用者選擇一個 Notion 帳號並上傳會議摘要後，系統自動在該會議的 metadata 中記錄上傳所用的帳號名稱（label）。使用者無需額外操作，記錄完全自動。

**Why this priority**: 這是所有後續功能的基礎——沒有帳號記錄，就無法在瀏覽器中顯示或篩選。且此功能對現有使用流程零干擾。

**Independent Test**: 可透過上傳一場會議後，檢查 meeting_meta.json 中是否包含正確的帳號 label 來驗證。

**Acceptance Scenarios**:

1. **Given** 使用者已選擇帳號「Alice」並完成摘要編輯，**When** 使用者點擊上傳到 Notion，**Then** meeting_meta.json 中新增欄位記錄帳號 label 為「Alice」
2. **Given** 使用者使用預設帳號（.env）上傳，**When** 上傳完成，**Then** meeting_meta.json 中記錄帳號 label 為「預設（.env）」
3. **Given** 使用者上傳失敗（Notion API 回傳錯誤），**When** 上傳未成功，**Then** meeting_meta.json 中不寫入帳號標記

---

### User Story 2 - 歷史會議顯示上傳帳號 (Priority: P2)

使用者在側邊欄的歷史會議瀏覽器中，可以一眼看出每場已上傳會議是由哪個帳號上傳的。未上傳的會議維持原有顯示方式不變。

**Why this priority**: 這是使用者最直接感受到的 UI 改善，讓多帳號環境下的會議歸屬一目了然。依賴 P1 的帳號記錄功能。

**Independent Test**: 可在有多場會議（分別由不同帳號上傳）的環境中，開啟歷史會議瀏覽器，確認每場會議旁顯示正確的帳號名稱。

**Acceptance Scenarios**:

1. **Given** 一場會議已由帳號「Alice」上傳，**When** 使用者開啟歷史會議瀏覽器，**Then** 該會議狀態顯示為「🟢已上傳（Alice）」
2. **Given** 一場會議已上傳但 metadata 中無帳號記錄（舊資料），**When** 使用者開啟歷史會議瀏覽器，**Then** 該會議狀態顯示為「🟢已上傳」（不顯示帳號，向下相容）
3. **Given** 一場會議尚未上傳（僅有草稿或逐字稿），**When** 使用者開啟歷史會議瀏覽器，**Then** 顯示方式不變（🟡草稿 或 🔵僅逐字稿）

---

### User Story 3 - 依帳號篩選歷史會議 (Priority: P3)

使用者可以在歷史會議瀏覽器中，依帳號篩選會議列表，快速找到特定帳號上傳的會議，或僅查看尚未上傳的會議。

**Why this priority**: 當會議數量多且帳號多時，篩選功能大幅提升查找效率。依賴 P1 與 P2。

**Independent Test**: 可在有多場會議（含不同帳號上傳與未上傳）的環境中，切換篩選條件，確認列表正確過濾。

**Acceptance Scenarios**:

1. **Given** 歷史中有 Alice 上傳 3 場、Bob 上傳 2 場、未上傳 4 場，**When** 使用者選擇篩選「Alice」，**Then** 列表僅顯示 Alice 上傳的 3 場會議
2. **Given** 同上環境，**When** 使用者選擇篩選「只看未上傳」，**Then** 列表僅顯示 4 場未上傳會議
3. **Given** 同上環境，**When** 使用者選擇「全部」（預設），**Then** 列表顯示所有 9 場會議
4. **Given** 使用者同時選擇了日期篩選與帳號篩選，**When** 兩個篩選條件同時生效，**Then** 列表僅顯示同時符合兩個條件的會議

---

### User Story 4 - 切換帳號自動篩選歷史會議 (Priority: P3)

使用者在側邊欄切換 Notion 帳號時，歷史會議瀏覽器的帳號篩選自動切換到對應帳號，讓使用者立即看到該帳號上傳的會議。若該帳號在歷史中無上傳記錄，篩選維持「全部」。

**Why this priority**: 與 US3 同屬篩選體驗優化。切換帳號後自動聚焦到該帳號的會議，減少手動操作。依賴 US3 的篩選機制。

**Independent Test**: 切換 Notion 帳號後，觀察歷史會議篩選 selectbox 是否自動跟著切換。

**Acceptance Scenarios**:

1. **Given** 使用者目前選擇帳號「Alice」，歷史中有 Alice 上傳的會議，**When** 使用者切換到帳號「Bob」，**Then** 歷史會議帳號篩選自動切換為「Bob」，列表僅顯示 Bob 上傳的會議
2. **Given** 使用者切換到帳號「Charlie」，但歷史中沒有 Charlie 上傳的會議，**When** 切換完成，**Then** 帳號篩選維持「全部」，不報錯
3. **Given** 使用者手動將帳號篩選改為「只看未上傳」，**When** 之後切換 Notion 帳號，**Then** 篩選被覆蓋為該帳號（若有歷史）或「全部」（若無歷史）

---

### User Story 5 - 帳號選擇持久化 (Priority: P3)

使用者切換 Notion 帳號後，下次啟動應用時系統自動還原上次選擇的帳號，而非每次都重置到第一個帳號。

**Why this priority**: 多帳號環境下每次重啟都要重新選擇帳號是不必要的操作成本。依賴現有帳號管理機制。

**Independent Test**: 選擇帳號 B → 重啟應用 → 確認帳號仍停在 B。

**Acceptance Scenarios**:

1. **Given** 使用者切換到帳號「Bob」，**When** 重啟應用（重新開啟瀏覽器或重啟 Streamlit），**Then** 帳號自動選擇「Bob」
2. **Given** 上次選擇的帳號已被刪除，**When** 啟動應用，**Then** 自動退化為第一個帳號，不報錯
3. **Given** 尚未切換過帳號（首次使用），**When** 啟動應用，**Then** 預設選擇第一個帳號

---

### Edge Cases

- 舊的 meeting_meta.json 沒有帳號欄位時，系統向下相容，將其視為「無帳號記錄」的已上傳會議
- 帳號被刪除後，該帳號上傳的歷史會議仍保留帳號 label 記錄（label 是純文字，不依賴帳號是否仍存在）
- 同一場會議重新上傳（覆蓋）時，帳號標記更新為最新一次上傳所用的帳號
- 篩選下拉選項中的帳號清單，應來自歷史會議中實際出現的帳號（而非當前設定中的帳號列表），以避免顯示從未使用過的帳號
- meeting_meta.json 損壞或缺失時，該會議仍可顯示，狀態回退為無帳號資訊
- 切換 Notion 帳號時，若該帳號 label 不在歷史篩選選項中，篩選退化為「全部」而非報錯

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系統在成功上傳會議摘要至 Notion 後，MUST 在 meeting_meta.json 中記錄上傳所用帳號的 label
- **FR-002**: 系統 MUST 在上傳失敗時不寫入帳號標記
- **FR-003**: 重新上傳（覆蓋）時，系統 MUST 將帳號標記更新為最新上傳所用帳號
- **FR-004**: 歷史會議瀏覽器中，已上傳且有帳號記錄的會議 MUST 在狀態中顯示帳號 label（格式：🟢已上傳（{label}））
- **FR-005**: 歷史會議瀏覽器中，已上傳但無帳號記錄的舊會議 MUST 僅顯示「🟢已上傳」，不報錯
- **FR-006**: 歷史會議瀏覽器 MUST 提供帳號篩選功能，選項包含：全部、只看未上傳、以及歷史中出現過的各帳號名稱
- **FR-007**: 帳號篩選 MUST 與現有日期篩選可同時使用（AND 邏輯）
- **FR-008**: 未上傳的會議 MUST 在所有帳號篩選條件下可見（選擇「全部」時），僅在選擇特定帳號時被隱藏
- **FR-009**: 帳號 label 為純文字記錄，MUST NOT 依賴帳號是否仍存在於系統設定中
- **FR-010**: 使用者在側邊欄切換 Notion 帳號時，歷史會議的帳號篩選 MUST 自動切換到對應帳號；若該帳號在歷史篩選選項中不存在，MUST 退化為「全部」
- **FR-011**: 使用者切換 Notion 帳號後，系統 MUST 將選擇持久化到磁碟，下次啟動時自動還原；若該帳號已不存在，MUST 退化為第一個帳號

### Key Entities

- **會議 Metadata（meeting_meta.json）**: 每場會議的描述資訊，新增帳號標記欄位。現有屬性：meeting_name、date、tags、participants；新增：上傳帳號 label
- **Notion 帳號**: 由 label（顯示名稱）與 token 組成的一組認證資訊，存在於系統設定中。帳號可被新增或移除，但已記錄在歷史會議中的 label 不受影響
- **歷史會議列表**: 由掃描 output/ 資料夾產生的會議清單，包含日期、名稱、狀態、版本數等資訊，新增帳號標記與篩選能力

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 使用者上傳會議後，可在 5 秒內於歷史瀏覽器中確認該會議的上傳帳號
- **SC-002**: 使用者可在 2 次點擊內從歷史會議列表中篩選出特定帳號的所有會議；切換帳號時 0 次點擊自動篩選
- **SC-003**: 舊有會議（無帳號標記）100% 正常顯示，不因功能新增而出現錯誤或資訊遺失
- **SC-004**: 篩選為「只看未上傳」時，列表準確顯示所有未上傳會議，無遺漏或誤判

## Assumptions

- 每場會議僅記錄最後一次上傳的帳號（不記錄上傳歷史）
- 帳號 label 在系統中是唯一的（由現有 config.py 的帳號管理邏輯保證）
- 不需要「強制綁定會議歸屬」的概念——僅記錄上傳事實
- 篩選下拉的帳號清單，從歷史會議的 metadata 動態收集，不依賴當前帳號設定
- 現有的日期篩選功能保持不變，帳號篩選為新增的獨立篩選維度
