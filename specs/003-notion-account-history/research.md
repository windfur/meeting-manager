# Research: 歷史會議帳號標記與篩選

## R1: 帳號 label 寫入時機與位置

**Decision**: 在 `_upload_to_notion()` 成功取得 `page_url` 後、呼叫 `st.rerun()` 前，將帳號 label 寫入 `meeting_meta.json` 的 `uploaded_by` 欄位。

**Rationale**:
- `_upload_to_notion()` 已在成功路徑中呼叫 `_save_meeting_meta()` 寫入 metadata，但此時尚未包含帳號資訊
- 帳號 label 只能在上傳**成功**後寫入（FR-002 要求失敗不寫入）
- 現有的 try/except 結構天然分離成功與失敗路徑——成功時執行 `st.session_state.page_url = page_url`，失敗時進入 except
- 最小侵入方式：在成功路徑中修改 `_save_meeting_meta()` 使其可接受 `uploaded_by` 參數；或在成功後單獨追加寫入 JSON

**Alternatives considered**:
- 在 `_save_meeting_meta()` 自動從 session state 讀取帳號資訊 → 拒絕：`_save_meeting_meta()` 也被儲存草稿流程呼叫，草稿階段不應記錄帳號
- 在 `notion_uploader.upload_meeting()` 裡寫入 → 拒絕：uploader 不應耦合本地 metadata 檔案

## R2: `_save_meeting_meta()` 修改策略

**Decision**: 新增 `uploaded_by` 參數（預設 `None`），當非 `None` 時寫入 JSON。

**Rationale**:
- 將帳號寫入邏輯與一般 metadata 儲存合併，避免額外的 JSON 讀寫操作
- `uploaded_by=None` 保持現有呼叫處（儲存草稿）的行為不變
- 重新上傳時傳入新帳號 label 即自動覆蓋（FR-003）

**Alternatives considered**:
- 新增獨立函數 `_save_upload_account()` → 拒絕：額外的 JSON 讀-改-寫，且與 `_save_meeting_meta()` 寫入同一檔案，存在覆蓋風險
- 在 session state 加上 `uploaded_by` 由 `_save_meeting_meta()` 自動讀取 → 拒絕：session state 中的 `uploaded_by` 語意不清（是當前帳號還是上次上傳帳號？），易出錯

## R3: `_scan_meetings()` 讀取帳號資訊

**Decision**: 在 `_scan_meetings()` 中讀取每個會議資料夾的 `meeting_meta.json`，提取 `uploaded_by` 欄位加入回傳的 dict。

**Rationale**:
- `_scan_meetings()` 已遍歷所有 output/ 子資料夾，額外讀取 JSON 開銷極小（本地 I/O、< 200 個檔案）
- 讀取後將 `uploaded_by` 值附加到每個 meeting dict，供 `_show_meeting_browser()` 使用
- JSON 缺失或損壞時 `uploaded_by` 為 `None`，向下相容（FR-005）

**Alternatives considered**:
- 在 `_show_meeting_browser()` 逐一讀取 → 拒絕：職責分離不佳，`_scan_meetings()` 應負責所有資料收集
- 快取 metadata → 拒絕：本地 I/O 延遲可忽略，Streamlit 每次 rerun 都會重掃，無需快取

## R4: 帳號篩選 UI 設計

**Decision**: 在 `_show_meeting_browser()` 的日期篩選下方新增 `st.selectbox`，選項為：「全部」、「只看未上傳」、加上歷史會議中出現過的帳號 label（去重、排序）。

**Rationale**:
- spec FR-006 明確要求三類選項：全部、只看未上傳、各帳號名稱
- selectbox 與現有日期篩選一致的 UI 模式，使用者無學習成本
- 帳號清單從 `_scan_meetings()` 回傳的 `uploaded_by` 動態收集（FR-006 要求來自歷史資料而非帳號設定）
- 篩選與日期篩選為 AND 邏輯（FR-007）

**Alternatives considered**:
- multiselect 選擇多帳號 → 拒絕：spec 只要求單選，且 SC-002 要求 2 次點擊內完成篩選
- radio button → 拒絕：選項數量不固定（帳號可多可少），selectbox 更節省空間

## R5: 狀態文字格式

**Decision**: 已上傳且有帳號記錄：`🟢已上傳（{label}）`；已上傳但無帳號記錄：`🟢已上傳`。

**Rationale**:
- 直接遵循 spec FR-004、FR-005 的格式定義
- 在 `_show_meeting_browser()` 的 label 組裝邏輯中，根據 `uploaded_by` 是否存在決定後綴
- 現有 `_scan_meetings()` 的 `status_text` 欄位可直接附加帳號資訊

## R6: 帳號 label 取得方式

**Decision**: 從 `config.load_notion_tokens()` 取得 tokens 列表，以 `st.session_state.notion_token_idx` 索引取得對應 label。

**Rationale**:
- `_show_notion_accounts()` 已將 `notion_token_idx` 存入 session state
- `tokens[idx]["label"]` 即為使用者在 UI 上看到的帳號名稱
- 預設帳號（.env）的 label 為 `"預設（.env）"`，由 `load_notion_tokens()` 自動產生

**Alternatives considered**:
- 在 session state 中新增 `active_notion_label` → 拒絕：增加需同步的 state，且 `tokens[idx]["label"]` 已可直接取得
- 從 token 值反查 label → 拒絕：不必要的間接層
