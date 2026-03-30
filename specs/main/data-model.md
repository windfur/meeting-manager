# Data Model: 上傳狀態鎖定與編輯器同步修復

## Session State 變更

### 新增欄位

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `uploading` | `bool` | `False` | 上傳 Notion 期間為 True |
| `upload_error` | `str \| None` | 不初始化 | 上傳失敗時暫存錯誤訊息，顯示後刪除 |

### 現有欄位（行為變更）

| Field | Change |
|-------|--------|
| `summarizing` | 不變，但 `is_busy` 判斷擴展為 `summarizing or uploading` |

### 衍生屬性

| Name | Formula | Used By |
|------|---------|---------|
| `is_busy` | `st.session_state.summarizing or st.session_state.uploading` | 所有 `disabled=` 參數 |

## State Machine: Upload Flow

```
IDLE (uploading=False)
  │
  ├── [按下「確認上傳 Notion」]
  │     ├── 儲存 edited_summary/edited_key_points 到 session_state
  │     ├── uploading = True
  │     └── st.rerun()
  │
  ▼
UPLOADING (uploading=True, is_busy=True)
  │  → 所有 widget disabled
  │  → _show_summary_review() 底部偵測 uploading → 執行 _upload_to_notion()
  │
  ├── [上傳成功]
  │     ├── uploading = False
  │     ├── step = 3
  │     └── st.rerun() → 跳到結果頁
  │
  └── [上傳失敗]
        ├── upload_error = str(e)
        ├── uploading = False
        └── st.rerun() → 重繪顯示 st.error()，按鈕恢復
```

## 影響範圍

### 需修改的 Widget（disabled 狀態）

| Widget | Location | Current `disabled` | New `disabled` |
|--------|----------|-------------------|----------------|
| 版本選擇器 radio | ~L722 | 無 | `disabled=is_busy` |
| 摘要編輯器 text_area | ~L748 | 無 | `disabled=is_busy` |
| Highlights text_input | ~L754 | 無 | `disabled=is_busy` |
| 上傳 Notion 按鈕 | ~L775 | `is_busy or not target` | 不變（已包含） |
| 儲存草稿按鈕 | ~L781 | `is_busy` | 不變（已包含） |
| 重新產生按鈕 | ~L795 | `is_busy` | 不變（已包含） |
| 回到逐字稿按鈕 | ~L799 | `is_busy` | 不變（已包含） |
| Notion 頁面 selectbox | ~L840 | 無 | `disabled=is_busy`（需傳參數） |
| Notion 資料庫 selectbox | ~L870 | 無 | `disabled=is_busy`（需傳參數） |

### 需修改的函式

| Function | Change |
|----------|--------|
| `main()` 初始化區 | 新增 `uploading` 到初始化 |
| `_show_summary_review()` | `is_busy` 擴展、新增 upload_error 顯示、底部新增 uploading 偵測 |
| `_upload_to_notion()` | 改為 rerun 模式：try/except 中設 `uploading=False` + `st.rerun()` |
| `_show_notion_page_selector()` | 接受 `disabled` 參數 |
| 批次取代邏輯 | 修正 widget key 讀取 |
