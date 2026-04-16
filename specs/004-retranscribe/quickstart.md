# Quickstart: Retranscribe（重新轉錄）

## Change Summary

| 檔案 | 函數 | 變更類型 | 說明 |
|------|------|----------|------|
| `config.py` | 模組層級 | 新增常數 | `AUDIO_EXTENSIONS` set |
| `app.py` | `main()` | 修改 | session state 初始化新增 `retranscribing`、`audio_path` |
| `app.py` | `_find_audio_path()` | 新增函數 | 從 metadata 或 fallback 掃描定位音檔 |
| `app.py` | `_do_retranscribe()` | 新增函數 | 重新轉錄執行邏輯 |
| `app.py` | `_show_transcript_review()` | 修改 | 加入重新轉錄按鈕與 UI 狀態控制 |
| `app.py` | `_do_transcription()` | 修改 | 存 `audio_path` 到 session state |
| `app.py` | `_save_meeting_meta()` | 修改 | 讀寫 `audio_path` 欄位 |

## Implementation Details

### 1. `config.py` — 新增 AUDIO_EXTENSIONS

```python
# Audio
MAX_AUDIO_SIZE_MB = 25
AUDIO_EXTENSIONS = {'.mp3', '.mp4', '.wav', '.m4a', '.ogg', '.webm', '.mpeg', '.mpga'}
```

### 2. `app.py` — session state 初始化

在 `main()` 的 session state 初始化區塊新增：

```python
for key in ['raw_transcript', 'confirmed_transcript', 'summary',
            'summary_draft', 'key_points', 'output_dir', 'page_url',
            'step', 'meeting_name', 'date_str', 'tags', 'participants',
            'replace_pairs_count', 'editor_version', 'summarizing', 'uploading',
            'summary_version_idx', 'draft_base_version', 'notion_target_page',
            'notion_target_db', 'audio_path']:  # <-- 新增 audio_path
    if key not in st.session_state:
        st.session_state[key] = None

# 新增 retranscribing 初始化（與 summarizing、uploading 相同模式）
if 'retranscribing' not in st.session_state:
    st.session_state.retranscribing = False
```

### 3. `app.py` — `_find_audio_path(output_dir)` 新增函數

```python
def _find_audio_path(output_dir) -> str | None:
    """定位會議原始音檔。優先從 meeting_meta.json 讀取，fallback 掃描資料夾。"""
    output_dir = Path(output_dir)

    # 1. 嘗試從 meeting_meta.json 讀取
    meta_path = output_dir / "meeting_meta.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding='utf-8'))
            audio_path = meta.get("audio_path")
            if audio_path and Path(audio_path).exists():
                return audio_path
        except (json.JSONDecodeError, KeyError):
            pass

    # 2. Fallback: 掃描 output 資料夾中的音檔
    audio_files = [
        f for f in output_dir.iterdir()
        if f.is_file() and f.suffix.lower() in config.AUDIO_EXTENSIONS
    ]
    if len(audio_files) == 1:
        return str(audio_files[0])

    return None
```

### 4. `app.py` — `_do_retranscribe()` 新增函數

```python
def _do_retranscribe():
    """執行重新轉錄：呼叫 Whisper API，成功後覆蓋 transcript_raw.txt。"""
    from transcriber import transcribe

    audio_path = st.session_state.audio_path
    output_dir = Path(st.session_state.output_dir)

    status = st.status("重新轉錄中...", expanded=True)

    try:
        # 檢查音檔是否存在（防止在 retranscribing = True 後檔案被移除）
        if not audio_path or not Path(audio_path).exists():
            st.error(f"❌ 找不到原始音檔：{audio_path}，無法重新轉錄")
            return

        file_size_mb = Path(audio_path).stat().st_size / (1024 * 1024)
        if file_size_mb == 0:
            st.error("❌ 音檔大小為 0，無法轉錄")
            return

        status.write(f"📂 音檔：{Path(audio_path).name}（{file_size_mb:.1f} MB）")

        result = transcribe(
            audio_path,
            progress_callback=lambda msg: status.write(f"⏳ {msg}")
        )

        new_transcript = result['raw_text']

        # 成功後才覆蓋檔案（FR-007: 失敗時保留原稿）
        (output_dir / "transcript_raw.txt").write_text(new_transcript, encoding='utf-8')
        st.session_state.raw_transcript = new_transcript
        st.session_state.editor_version += 1

        status.update(label="✅ 重新轉錄完成", state="complete")
        status.write(f"共 {len(new_transcript):,} 字")

    except Exception as e:
        status.update(label="❌ 重新轉錄失敗", state="error")
        status.write(f"❌ {str(e)}")
        logger.error("重新轉錄失敗 | %s: %s", type(e).__name__, str(e), exc_info=True)

    finally:
        st.session_state.retranscribing = False
```

### 5. `app.py` — `_show_transcript_review()` 修改

在逐字稿 text_area 上方（批次取代區之前或之後）新增重新轉錄按鈕：

```python
def _show_transcript_review():
    # ... 現有 metadata 欄位與批次取代 ...

    # --- 重新轉錄 ---
    is_busy = st.session_state.summarizing or st.session_state.uploading or st.session_state.retranscribing
    audio_path = _find_audio_path(st.session_state.output_dir)
    no_audio = audio_path is None

    retranscribe_col, _ = st.columns([1, 3])
    with retranscribe_col:
        btn_label = "⏳ 重新轉錄中..." if st.session_state.retranscribing else "🔄 重新轉錄"
        if st.button(btn_label, disabled=is_busy or no_audio):
            st.session_state.retranscribing = True
            st.session_state.audio_path = audio_path
            st.rerun()
    if no_audio:
        st.caption("⚠️ 找不到原始音檔，無法重新轉錄")

    # --- 重新轉錄執行（在 rerun cycle 中當 retranscribing=True 時觸發）---
    if st.session_state.retranscribing:
        _do_retranscribe()
        st.rerun()

    # ... 現有的 text_area 與確認按鈕 ...
    # 注意：is_busy 條件需同步更新到確認按鈕和前往摘要按鈕的 disabled
```

### 6. `app.py` — `_do_transcription()` 修改

在儲存音檔後、呼叫 `_save_meeting_meta()` 前，存 `audio_path` 到 session state：

```python
# 在兩個分支（首次轉錄、已有逐字稿）中都要設定：
st.session_state.audio_path = str(audio_path)
```

### 7. `app.py` — `_save_meeting_meta()` 修改

在 `meta` dict 建構後、寫入前，加入 `audio_path` 欄位處理：

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

    # 保留 audio_path
    if st.session_state.get("audio_path"):
        meta["audio_path"] = st.session_state.audio_path

    # 保留既有欄位（uploaded_by, audio_path）
    meta_path = output_dir / "meeting_meta.json"
    if meta_path.exists():
        try:
            existing = json.loads(meta_path.read_text(encoding='utf-8'))
            if uploaded_by is None and "uploaded_by" in existing:
                meta["uploaded_by"] = existing["uploaded_by"]
            if "audio_path" not in meta and "audio_path" in existing:
                meta["audio_path"] = existing["audio_path"]
        except (json.JSONDecodeError, KeyError):
            pass

    meta_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8'
    )
```

## Verification Steps

### 手動測試

1. **新會議首次轉錄**：上傳音檔 → 轉錄完成 → 檢查 `meeting_meta.json` 是否包含 `audio_path`
2. **重新轉錄（正常）**：在 Step 1 頁面點擊「🔄 重新轉錄」→ 確認逐字稿更新、按鈕 disabled 期間其他按鈕不可用
3. **音檔遺失**：手動修改 `audio_path` 指向不存在路徑 → 按鈕應為 disabled + 顯示「找不到原始音檔」
4. **舊會議 fallback**：從歷史選擇一場有音檔但無 `audio_path` 欄位的會議 → 按鈕應可用（fallback 掃描到音檔）
5. **API 失敗**：斷網或 API key 無效時點擊重新轉錄 → 應顯示錯誤訊息，原逐字稿不受影響

### Edge Cases

- 空音檔（0 bytes）→ 顯示錯誤
- Output 資料夾有多個音檔 → 按鈕 disabled（fallback 不確定選哪個）
- 轉錄進行中頁面刷新 → Streamlit session state 重置，`retranscribing` 回到 False
