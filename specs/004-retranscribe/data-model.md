# Data Model: Retranscribe（重新轉錄）

## meeting_meta.json Schema

```json
{
  "meeting_name": "string",
  "date": "YYYY-MM-DD",
  "tags": ["string"],
  "participants": ["string"],
  "uploaded_by": "string | null",
  "audio_path": "string | null (新增欄位)"
}
```

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `meeting_name` | str | ✅ | 會議名稱 |
| `date` | str | ✅ | 會議日期（YYYY-MM-DD） |
| `tags` | list[str] | ✅ | 標籤 |
| `participants` | list[str] | ✅ | 參與者 |
| `uploaded_by` | str \| null | ❌ | 上傳 Notion 時記錄帳號 label（003 新增） |
| `audio_path` | str \| null | ❌ | **新增**。原始音檔的絕對路徑，首次轉錄時寫入 |

**向下相容**: 舊的 meeting_meta.json 無 `audio_path` 欄位，`dict.get("audio_path")` 回傳 `None`，系統自動 fallback 掃描 output 資料夾中的音檔。

## Session State 變更

```python
# 新增 key
st.session_state.retranscribing: bool  # 重新轉錄進行中旗標，預設 False
st.session_state.audio_path: str | None  # 當前會議的音檔路徑
```

## config.py 新增常數

```python
AUDIO_EXTENSIONS = {'.mp3', '.mp4', '.wav', '.m4a', '.ogg', '.webm', '.mpeg', '.mpga'}
```

## State Flow

```
[重新轉錄流程]

_show_transcript_review()
    │
    ├─ audio_path = _find_audio_path(output_dir)
    │   ├─ 讀取 meeting_meta.json → audio_path 欄位
    │   ├─ 若 audio_path 存在且檔案存在 → 回傳
    │   ├─ 否則 fallback 掃描 output_dir 內音檔
    │   │   ├─ 恰好 1 個 → 回傳該路徑
    │   │   └─ 0 個或 > 1 個 → 回傳 None
    │   └─ 回傳 None（音檔不存在）
    │
    ├─ audio_path is None:
    │   └─ 按鈕 disabled + caption「找不到原始音檔」
    │
    ├─ audio_path 有效:
    │   └─ 按鈕可點擊
    │       │
    │       └─ 使用者點擊「🔄 重新轉錄」
    │           ├─ st.session_state.retranscribing = True
    │           ├─ st.session_state.audio_path = audio_path
    │           └─ st.rerun()
    │
    ├─ retranscribing == True:
    │   └─ _do_retranscribe()
    │       ├─ try:
    │       │   ├─ transcribe(audio_path, progress_callback)
    │       │   ├─ 成功 → 覆蓋 transcript_raw.txt
    │       │   ├─ 更新 st.session_state.raw_transcript
    │       │   ├─ 遞增 editor_version
    │       │   └─ st.toast("✅ 重新轉錄完成")
    │       ├─ except:
    │       │   └─ st.error("轉錄失敗：{錯誤訊息}")
    │       │       （原 transcript_raw.txt 不受影響）
    │       └─ finally:
    │           ├─ retranscribing = False
    │           └─ st.rerun()
    │
    └─ 所有按鈕 disabled 條件：
        is_busy = summarizing or uploading or retranscribing


[首次轉錄 — audio_path 寫入]

_do_transcription()
    │
    ├─ 儲存音檔到 output_dir → 得到 audio_path
    ├─ st.session_state.audio_path = str(audio_path)
    ├─ transcribe(audio_path) → transcript_raw.txt
    └─ _save_meeting_meta(output_dir)
        └─ 自動從 st.session_state.audio_path 讀取並寫入 JSON
```

## 檔案影響矩陣

| 檔案 | 函數 / 區域 | 變更類型 | 說明 |
|------|-------------|----------|------|
| `config.py` | 模組層級 | 新增 | `AUDIO_EXTENSIONS` 常數 |
| `app.py` | `main()` init 區 | 修改 | 新增 `retranscribing`、`audio_path` 到 session state 初始化 |
| `app.py` | `_find_audio_path()` | 新增 | 音檔路徑定位函數 |
| `app.py` | `_do_retranscribe()` | 新增 | 重新轉錄執行流程 |
| `app.py` | `_show_transcript_review()` | 修改 | 新增重新轉錄按鈕 + disabled 邏輯 + 呼叫 `_do_retranscribe()` |
| `app.py` | `_do_transcription()` | 修改 | 儲存 `audio_path` 到 session state |
| `app.py` | `_save_meeting_meta()` | 修改 | 讀取並保留 `audio_path` 欄位 |
