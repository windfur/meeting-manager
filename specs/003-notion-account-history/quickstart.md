# Quickstart: 歷史會議帳號標記與篩選

## Change Summary

| 檔案 | 函數 | 變更類型 | 說明 |
|------|------|----------|------|
| `app.py` | `_save_meeting_meta()` | 修改 | 新增 `uploaded_by` 參數，非 None 時寫入 meeting_meta.json |
| `app.py` | `_upload_to_notion()` | 修改 | 上傳成功後取得帳號 label，呼叫 `_save_meeting_meta(uploaded_by=label)` |
| `app.py` | `_scan_meetings()` | 修改 | 讀取 meeting_meta.json 取得 `uploaded_by`，附加至回傳 dict |
| `app.py` | `_show_meeting_browser()` | 修改 | 新增帳號篩選 selectbox、已上傳會議 label 顯示帳號 |

## Implementation Details

### 1. `_save_meeting_meta()` — 新增 uploaded_by 參數

```python
def _save_meeting_meta(output_dir, uploaded_by=None):
    output_dir = Path(output_dir)
    meta = {
        "meeting_name": st.session_state.meeting_name,
        "date": st.session_state.date_str,
        "tags": st.session_state.tags or [],
        "participants": st.session_state.participants or [],
    }
    if uploaded_by is not None:
        meta["uploaded_by"] = uploaded_by
    # 保留既有的 uploaded_by（重新儲存草稿時不覆蓋）
    meta_path = output_dir / "meeting_meta.json"
    if uploaded_by is None and meta_path.exists():
        try:
            existing = json.loads(meta_path.read_text(encoding='utf-8'))
            if "uploaded_by" in existing:
                meta["uploaded_by"] = existing["uploaded_by"]
        except (json.JSONDecodeError, KeyError):
            pass
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
```

### 2. `_upload_to_notion()` — 成功後記錄帳號

```python
# 在 page_url = upload_meeting(...) 成功後：
tokens = config.load_notion_tokens()
token_idx = st.session_state.get("notion_token_idx", 0)
account_label = tokens[token_idx]["label"] if token_idx < len(tokens) else None
_save_meeting_meta(output_dir, uploaded_by=account_label)
```

### 3. `_scan_meetings()` — 讀取帳號資訊

```python
# 在建構 meeting dict 時，讀取 meeting_meta.json：
uploaded_by = None
meta_path = d / "meeting_meta.json"
if meta_path.exists():
    try:
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        uploaded_by = meta.get("uploaded_by")
    except (json.JSONDecodeError, KeyError):
        pass

# 已上傳且有帳號：更新 status_text
if has_uploaded and uploaded_by:
    status_text = f"已上傳（{uploaded_by}）"

meetings.append({
    ...,
    "uploaded_by": uploaded_by,
})
```

### 4. `_show_meeting_browser()` — 帳號篩選與顯示

```python
# 收集帳號選項（從歷史資料）
account_labels = sorted(set(
    m["uploaded_by"] for m in meetings if m["uploaded_by"]
))
account_options = ["全部", "只看未上傳"] + account_labels

selected_account = st.selectbox(
    "依帳號篩選",
    account_options,
    key="meeting_browser_account",
    label_visibility="collapsed",
)

# 篩選邏輯（在日期篩選之後）
if selected_account == "只看未上傳":
    meetings = [m for m in meetings if not m["has_uploaded"]]
elif selected_account not in ("全部",):
    meetings = [m for m in meetings if m["uploaded_by"] == selected_account]
```

## Verification Steps

1. 啟動 app → 選擇帳號「Alice」→ 上傳一場會議
2. 檢查 `output/{date}_{name}/meeting_meta.json` → 確認 `"uploaded_by": "Alice"`
3. 上傳失敗場景 → 確認 meeting_meta.json 無 `uploaded_by` 欄位
4. 開啟歷史會議瀏覽器 → 確認該會議顯示為「🟢已上傳（Alice）」
5. 舊會議（無 `uploaded_by`）→ 確認顯示為「🟢已上傳」
6. 未上傳會議 → 確認顯示為「🟡草稿」或「🔵僅逐字稿」
7. 帳號篩選 selectbox → 選「Alice」→ 僅顯示 Alice 上傳的會議
8. 帳號篩選 selectbox → 選「只看未上傳」→ 僅顯示未上傳會議
9. 同時使用日期篩選 + 帳號篩選 → 確認 AND 邏輯正確
10. 重新上傳同一場會議（用 Bob）→ 確認 `uploaded_by` 更新為 "Bob"

## Key Implementation Notes

- `uploaded_by` 為純文字，不依賴帳號是否仍存在（帳號刪除後歷史記錄不受影響）
- 篩選帳號清單從歷史會議動態收集，不從 `config.load_notion_tokens()` 取得
- `_save_meeting_meta()` 預設保留既有 `uploaded_by`（儲存草稿時不覆蓋上傳帳號記錄）
- 帳號篩選 selectbox key 為 `meeting_browser_account`，Streamlit 自動管理狀態
