# Quickstart: 上傳狀態鎖定與編輯器同步修復

## 修改範圍

僅修改 `app.py`，不新增檔案。

## 變更摘要

### 1. Session State 初始化
```python
# 新增到 key 清單
'uploading'
# 初始化
if st.session_state.uploading is None:
    st.session_state.uploading = False
```

### 2. is_busy 擴展
```python
# 原本
is_busy = st.session_state.summarizing
# 改為
is_busy = st.session_state.summarizing or st.session_state.uploading
```

### 3. 上傳按鈕改用 Rerun 模式
```python
if st.button("✅ 確認上傳 Notion", ...):
    st.session_state.summary = edited_summary
    st.session_state.key_points = edited_key_points
    st.session_state.uploading = True
    st.rerun()
```

### 4. 偵測 uploading 執行上傳
```python
# _show_summary_review() 底部
if st.session_state.uploading:
    _upload_to_notion(st.session_state.summary, st.session_state.key_points)
```

### 5. _upload_to_notion 加入狀態管理
```python
try:
    # ... 現有上傳邏輯 ...
    st.session_state.uploading = False
    st.rerun()
except Exception as e:
    st.session_state.upload_error = str(e)
    st.session_state.uploading = False
    st.rerun()
```

### 6. 錯誤顯示
```python
# _show_summary_review() 開頭
if 'upload_error' in st.session_state:
    st.error(f"❌ 上傳失敗：{st.session_state.upload_error}")
    del st.session_state['upload_error']
```

### 7. 批次取代 Bug Fix
```python
# 原本（bug）
current = st.session_state.get("transcript_editor", st.session_state.raw_transcript)
# 改為
editor_key = f"transcript_editor_v{st.session_state.editor_version}"
current = st.session_state.get(editor_key, st.session_state.raw_transcript)
```

### 8. 新增 disabled 的 Widget
- 版本選擇器 radio → `disabled=is_busy`
- 摘要編輯器 text_area → `disabled=is_busy`
- Highlights text_input → `disabled=is_busy`
- `_show_notion_page_selector()` 接受 `disabled` 參數

## 驗證

```bash
# 啟動應用
cd "meeting manager"
.\venv\Scripts\activate
streamlit run app.py

# 測試：上傳期間按鈕 disabled
# 測試：批次取代保留手動編輯
# 測試：版本切換後編輯器內容正確
```
