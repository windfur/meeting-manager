# Research: 上傳狀態鎖定與編輯器同步修復

## R1: Streamlit Rerun 模式 — 現有 summarize 模式分析

**Decision**: 上傳採用與 summarize 完全相同的 rerun 模式

**Rationale**: 專案已有成熟的 rerun 模式實現（`summarizing` 旗標），上傳功能應複製相同 pattern 以確保一致性。

**現有模式流程**（app.py L616 → L641-694 → L804-806）：
1. 按鈕 callback 設 `st.session_state.summarizing = True` + `st.rerun()`
2. 重繪時 `is_busy = st.session_state.summarizing` → 所有 widget 讀取 disabled
3. 頁面底部檢測 `if is_busy: _do_summarize(); st.rerun()`
4. `_do_summarize()` 在 try/except 中執行實際工作
5. 成功/失敗都設 `summarizing = False`
6. 失敗時存 `st.session_state.summarize_error = str(e)`，下一次重繪用 `st.error()` 顯示

**上傳應用方式**：
- 新旗標: `uploading` (初始化 False)
- 統一判斷: `is_busy = summarizing or uploading`
- 錯誤存: `st.session_state.upload_error = str(e)`
- 重繪顯示: `st.error()` → 下次互動自動消失

**Alternatives considered**: 
- 同步阻塞模式（直接在 button callback 中執行上傳）→ 拒絕：按鈕回調期間 Streamlit 不會重繪，widget 無法顯示 disabled 狀態

## R2: 批次取代的 Widget Key Bug

**Decision**: 使用 `edited_transcript` 變數而非 `st.session_state.get("transcript_editor")`

**Rationale**: 目前 widget key 是 `transcript_editor_v{N}`（版本化 key），但批次取代程式碼卻讀取靜態 key `"transcript_editor"`（不存在）。

**現有 bug 位置**: app.py L582
```python
current = st.session_state.get("transcript_editor", st.session_state.raw_transcript)
```

**修正方式**: 批次取代按鈕的位置在 `edited_transcript = st.text_area(...)` **之前**（L557-598 vs L600），因此無法直接使用 `edited_transcript` 變數。

**解法**（兩個可行方案）:
1. 讀取正確的版本化 key: `st.session_state.get(f"transcript_editor_v{st.session_state.editor_version}", st.session_state.raw_transcript)` 
2. 將批次取代區移到 text_area 之後

**選擇方案 1**：不需要改動 UI 佈局，風險最小。

**Alternatives considered**: 
- 移動 UI 順序 → 拒絕：改變使用者介面佈局，不在 spec scope 內

## R3: Streamlit `disabled` 參數支援度

**Decision**: `disabled` 參數對 `st.radio`, `st.text_area`, `st.button`, `st.text_input`, `st.selectbox` 均有效

**Rationale**: Streamlit 1.55 所有互動 widget 都支援 `disabled` 參數（Boolean），設為 True 時 widget 呈灰色且不可點擊。

**新增需 disabled 的 widget**:
- 版本選擇器 `st.radio`（app.py ~L722）→ 加 `disabled=is_busy`
- 摘要編輯器 `st.text_area`（~L748）→ 加 `disabled=is_busy`
- Highlights 編輯器 `st.text_input`（~L754）→ 加 `disabled=is_busy`
- Notion 頁面/資料庫選擇器（~L840, L870）→ 加 `disabled=is_busy`（需傳入參數）

## R4: 錯誤顯示機制

**Decision**: 採用與 `summarize_error` 相同的模式 — session_state 暫存 + `st.error()` 顯示 + 自動清除

**Rationale**: 已有成熟模式（app.py L711-713），保持一致。

**實作**:
```python
# 上傳失敗時（在 _upload_to_notion 內）:
st.session_state.upload_error = str(e)
st.session_state.uploading = False

# 重繪時（在 _show_summary_review 開頭）:
if 'upload_error' in st.session_state:
    st.error(f"❌ 上傳失敗：{st.session_state.upload_error}")
    del st.session_state['upload_error']
```
