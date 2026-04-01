# Data Model: 歷史會議帳號標記與篩選

## meeting_meta.json Schema

```json
{
  "meeting_name": "string",
  "date": "YYYY-MM-DD",
  "tags": ["string"],
  "participants": ["string"],
  "uploaded_by": "string | null (新增欄位)"
}
```

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `meeting_name` | str | ✅ | 會議名稱 |
| `date` | str | ✅ | 會議日期（YYYY-MM-DD） |
| `tags` | list[str] | ✅ | 標籤 |
| `participants` | list[str] | ✅ | 參與者 |
| `uploaded_by` | str \| null | ❌ | **新增**。上傳成功時記錄帳號 label，未上傳或上傳失敗時不存在或為 null |

**向下相容**: 舊的 meeting_meta.json 無 `uploaded_by` 欄位，`dict.get("uploaded_by")` 回傳 `None`，顯示邏輯退化為 `🟢已上傳`。

## `_scan_meetings()` 回傳結構變更

```python
# 現有欄位（不變）
{
    "path": Path,
    "date": str,
    "name": str,
    "status": str,         # "🟢" | "🟡" | "🔵"
    "status_text": str,    # "已上傳" | "草稿" | "僅逐字稿"
    "has_transcript": bool,
    "has_draft": bool,
    "has_uploaded": bool,
    "ver_count": int,
}

# 新增欄位
{
    "uploaded_by": str | None,  # 帳號 label 或 None
}
```

## State Flow

```
[上傳流程]
_upload_to_notion()
    │
    ├─ try 區塊內：
    │   ├─ _save_meeting_meta(output_dir)               # 寫入基本 metadata
    │   ├─ upload_meeting(...) → page_url                # 上傳到 Notion
    │   ├─ 成功 →
    │   │   ├─ 取得 account_label = tokens[notion_token_idx]["label"]
    │   │   ├─ _save_meeting_meta(output_dir, uploaded_by=account_label)  # 覆寫 metadata 含帳號
    │   │   └─ st.session_state.page_url = page_url
    │   │
    │   └─ 失敗（exception）→ 不寫入 uploaded_by
    │
    ▼

[歷史瀏覽流程]
_scan_meetings()
    │
    ├─ 遍歷 output/ 子資料夾
    │   ├─ 讀取 meeting_meta.json
    │   ├─ uploaded_by = meta.get("uploaded_by")
    │   └─ 附加到 meeting dict
    │
    ▼
_show_meeting_browser()
    │
    ├─ 收集所有 uploaded_by 值 → 帳號選項清單
    ├─ 顯示帳號篩選 selectbox
    │   └─ 選項：["全部", "只看未上傳", "Alice", "Bob", ...]
    ├─ 套用帳號篩選（AND 日期篩選）
    └─ 顯示會議列表
        └─ label = "🟢已上傳（Alice）" | "🟢已上傳" | "🟡草稿" | "🔵僅逐字稿"
```

## Changed Behaviors

| Function | Before | After |
|----------|--------|-------|
| `_save_meeting_meta()` | 寫入 meeting_name, date, tags, participants | 新增可選 `uploaded_by` 參數，非 None 時寫入 JSON |
| `_upload_to_notion()` | 上傳成功後不記錄帳號 | 上傳成功後取得帳號 label，再呼叫 `_save_meeting_meta(uploaded_by=label)` |
| `_scan_meetings()` | 不讀取 meeting_meta.json | 讀取 meeting_meta.json 取得 `uploaded_by`，附加到回傳 dict |
| `_show_meeting_browser()` | 僅日期篩選，狀態無帳號資訊 | 新增帳號篩選 selectbox，已上傳會議在 label 中顯示帳號 |

## Widget Key Design

| Widget | Key | 說明 |
|--------|-----|------|
| 帳號篩選 | `meeting_browser_account` | 側邊欄帳號篩選 selectbox |

## Session State Changes

> 無新增 session state 變數。帳號篩選 selectbox 使用 Streamlit widget key 自動管理。

## Filtering Logic

```python
# 帳號篩選邏輯（虛擬碼）
if selected_account == "全部":
    pass  # 不過濾
elif selected_account == "只看未上傳":
    meetings = [m for m in meetings if not m["has_uploaded"]]
else:
    # 選擇特定帳號 → 僅顯示該帳號上傳的會議
    meetings = [m for m in meetings if m["uploaded_by"] == selected_account]
```
