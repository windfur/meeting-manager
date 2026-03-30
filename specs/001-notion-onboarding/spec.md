# Feature Specification: Notion 帳號 Onboarding 優化

**Feature Branch**: `001-notion-onboarding`  
**Created**: 2026-03-30  
**Status**: Draft  
**Input**: User description: "Notion 帳號 Onboarding 優化 — 解除 Notion token 對啟動的阻塞，讓新使用者能透過側邊欄完成首次 token 設定"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 新使用者首次啟動 (Priority: P1)

一位新使用者首次安裝並啟動 app，尚未設定任何 Notion token（.env 與 .notion_tokens.json 皆無 token）。使用者能順利看到 app 介面與側邊欄，在左側「Notion 帳號」區塊新增第一組 token 後，即可開始使用主流程功能。

**Why this priority**: 這是整個 onboarding 流程的核心——如果新使用者連 UI 都進不去，就無法完成任何操作。解除啟動阻塞是所有後續功能的前提。

**Independent Test**: 可透過移除所有 Notion token 設定後啟動 app，驗證 UI 是否正常載入且側邊欄可操作。

**Acceptance Scenarios**:

1. **Given** .env 中無 NOTION_TOKEN 且 .notion_tokens.json 不存在或為空, **When** 使用者啟動 app, **Then** app 正常載入，UI 可見，不顯示「設定不完整」阻擋頁面
2. **Given** app 已啟動且無任何 Notion token, **When** 使用者查看側邊欄, **Then** 側邊欄完整顯示，包含歷史會議瀏覽器、Notion 帳號管理區塊和摘要偏好設定
3. **Given** app 已啟動且無任何 Notion token, **When** 使用者在側邊欄新增一組有效的 Notion token, **Then** 主流程功能解鎖，使用者可開始使用會議摘要上傳等完整功能
4. **Given** 無任何 Notion token, **When** 使用者查看側邊欄的歷史會議瀏覽器, **Then** 歷史會議瀏覽器正常顯示且可操作，不受 Notion token 缺失影響

---

### User Story 2 - 無 token 時主區域引導提示 (Priority: P2)

使用者啟動 app 後，主區域清楚告知需要先新增 Notion 帳號，並引導使用者至側邊欄操作。Notion 帳號管理區塊自動展開，降低操作門檻。

**Why this priority**: 清楚的引導能大幅減少使用者困惑，確保 onboarding 順暢完成。若無引導提示，使用者可能不知道下一步該做什麼。

**Independent Test**: 可在無 token 的狀態下啟動 app，驗證主區域提示文字和側邊欄展開狀態。

**Acceptance Scenarios**:

1. **Given** app 已啟動且無任何 Notion token, **When** 使用者查看主區域, **Then** 顯示提示訊息「👈 請先在左側『🔑 Notion 帳號』新增至少一組 Token，才能開始使用。」，主流程功能（音檔上傳、語音轉錄、AI 摘要、Notion 上傳）不可用
2. **Given** app 已啟動且無任何 Notion token, **When** 使用者查看側邊欄的 Notion 帳號區塊, **Then** 該 expander 為自動展開狀態
3. **Given** 使用者新增第一組 token 後頁面重新載入, **When** 使用者查看主區域, **Then** 引導提示消失，主流程功能正常顯示

---

### User Story 3 - Page selector 防護 (Priority: P3)

在使用者尚未選擇有效的 Notion 帳號（active token）時，Notion page selector 不會嘗試呼叫 API，而是顯示適當的提示訊息。

**Why this priority**: 這是防禦性設計，避免在無有效 token 的情況下觸發不必要的 API 錯誤，提升使用體驗的穩定性。

**Independent Test**: 可在 token 存在但尚未選擇 active token 的狀態下，觀察 page selector 的行為。

**Acceptance Scenarios**:

1. **Given** 使用者未設定或未選擇任何 active Notion token, **When** app 嘗試顯示 Notion page selector, **Then** 不發出任何 Notion API 呼叫，顯示提示訊息引導使用者先設定帳號
2. **Given** 使用者已選擇一組有效的 active Notion token, **When** app 顯示 Notion page selector, **Then** 正常呼叫 API 取得頁面列表供選擇

---

### User Story 4 - OPENAI_API_KEY 缺失仍阻擋啟動 (Priority: P2)

config 檢查仍然驗證 OPENAI_API_KEY 是否設定。當此 key 缺失時，app 應阻擋主流程並顯示明確的錯誤訊息，但側邊欄仍應可見。

**Why this priority**: OPENAI_API_KEY 是核心功能（摘要生成）的必要條件，缺失時的行為需要明確定義，與 Notion token 的處理邏輯區隔開來。

**Independent Test**: 可移除 OPENAI_API_KEY 後啟動 app，驗證阻擋行為和錯誤訊息。

**Acceptance Scenarios**:

1. **Given** .env 中無 OPENAI_API_KEY, **When** 使用者啟動 app, **Then** 主區域顯示設定不完整的錯誤訊息
2. **Given** .env 中無 OPENAI_API_KEY, **When** 使用者查看側邊欄, **Then** 側邊欄仍然完整顯示，使用者可管理 Notion 帳號和摘要偏好

---

### Edge Cases

- 使用者新增了一組無效的 Notion token（格式錯誤或已過期），系統如何回應？預期：token 儲存成功但在後續 API 呼叫時顯示錯誤提示，不影響 app 啟動
- .notion_tokens.json 檔案存在但內容為空陣列或格式損壞時，app 應能正常啟動，視為無 token 狀態
- 使用者同時缺少 OPENAI_API_KEY 和 Notion token 時，兩種提示應各自呈現，不互相覆蓋
- 使用者刪除所有已儲存的 Notion token 後，app 應回到「無 token」狀態，主區域重新顯示引導提示

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 啟動檢查（config check）不得因 Notion token 缺失而阻擋 app 載入，僅 OPENAI_API_KEY 缺失時阻擋主流程
- **FR-002**: 側邊欄（包含歷史會議瀏覽器、Notion 帳號管理、摘要偏好設定）在任何情況下都必須可見可操作，即使 config check 未通過或 Notion token 缺失
- **FR-003**: 當無任何 Notion token 時，主區域必須顯示明確的引導提示，告知使用者需先新增 token，並阻止進入主流程
- **FR-004**: 當無任何 Notion token 時，側邊欄的 Notion 帳號 expander 必須自動展開
- **FR-005**: Notion page selector 在無有效 active token 時，必須顯示提示訊息而非嘗試呼叫 Notion API
- **FR-006**: 使用者透過側邊欄新增 token 後，頁面重新載入即解鎖主流程，無需手動重啟 app
- **FR-007**: token 儲存機制支援 .env 和 .notion_tokens.json 兩種來源，系統自動偵測可用的 token
- **FR-008**: 歷史會議瀏覽器（meeting browser）為純本地操作，不依賴 Notion token，必須在 Notion token 檢查之前渲染，確保無 token 時仍可瀏覽歷史會議

### Key Entities

- **Notion Token**: 使用者的 Notion Integration token，用於存取 Notion API。可來自 .env（NOTION_TOKEN）或 .notion_tokens.json（多帳號儲存）。具有名稱標籤和有效性狀態。
- **Active Notion Token**: 使用者目前選定使用的 Notion token，用於 page selector 和上傳功能。
- **Config Check 狀態**: 記錄各項必要設定（OPENAI_API_KEY 等）的檢查結果，決定主流程是否可用。Notion token 不列入此檢查。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 新使用者在無任何 Notion token 的情況下，能在 10 秒內看到完整的 app 介面（含側邊欄）
- **SC-002**: 新使用者從首次啟動到成功新增第一組 Notion token 並解鎖主流程，整個流程可在 2 分鐘內完成
- **SC-003**: 100% 的無 token 啟動情境下，主區域顯示引導提示且不出現未預期的錯誤訊息
- **SC-004**: 無有效 active token 時，page selector 不產生任何 API 呼叫錯誤

## Assumptions

- 使用者已正確安裝 app 及其依賴套件（requirements.txt）
- OPENAI_API_KEY 仍為主流程的必要條件，其檢查行為不受本功能影響
- token 的有效性驗證（是否能成功呼叫 Notion API）不在啟動階段進行，僅在實際使用時驗證
- 現有的 token 讀取與儲存機制維持不變
- 此功能為已實作功能的文件補齊，不涉及新的設計決策
