# Research: Retranscribe（重新轉錄）

## R1: 音檔路徑定位策略

**Decision**: 定義 `_find_audio_path(output_dir)` 函數，依序：(1) 讀取 `meeting_meta.json` 的 `audio_path` 欄位 → (2) fallback 掃描 output 資料夾中的音檔（依 `AUDIO_EXTENSIONS` 篩選）→ 找到唯一檔案則回傳，否則回傳 `None`。

**Rationale**:
- `audio_path` 是首次轉錄時儲存的絕對路徑，最可靠（FR-002）
- 舊會議沒有 `audio_path`，需要 fallback 掃描（Assumptions 明確說明）
- 掃描時只取 `output_dir` 內匹配 `AUDIO_EXTENSIONS` 的檔案，排除 transcript/summary/metadata 等
- 若掃描到多個音檔，不自動選擇（避免誤判），回傳 `None` 並提示用戶

**Alternatives considered**:
- 只依賴 `audio_path`，不做 fallback → 拒絕：舊會議無此欄位，無法使用重新轉錄功能
- 掃描到多個音檔時取最大的 → 拒絕：無法保證正確性，違反操作防誤原則

## R2: audio_path 欄位寫入時機

**Decision**: 在 `_do_transcription()` 儲存音檔到 output 後、呼叫 `_save_meeting_meta()` 前，將 `audio_path` 存入 `st.session_state`，由 `_save_meeting_meta()` 自動寫入 JSON。

**Rationale**:
- `_do_transcription()` 已知音檔的完整路徑（`audio_path = output_dir / f"{safe_name}{audio_ext}"`）
- 寫入時機在轉錄成功之前（只要音檔存在即記錄），確保即使轉錄失敗也能保留路徑
- `_save_meeting_meta()` 已在 `_do_transcription()` 尾端呼叫，只需讓它額外讀取 session state 中的 `audio_path`

**Alternatives considered**:
- 在 `_save_meeting_meta()` 中新增 `audio_path` 參數 → 拒絕：已有 `uploaded_by` 參數，參數持續增加會難以維護。改用從 session state 讀取更統一
- 在 `_find_audio_path()` 找到 fallback 音檔時自動補寫 `audio_path` → 拒絕：`_find_audio_path()` 應為純查詢函數，不應有寫入副作用

## R3: 重新轉錄的狀態管理

**Decision**: 新增 `st.session_state.retranscribing` 布林值，控制轉錄期間的 UI 狀態（disable 按鈕、顯示進度）。與現有的 `summarizing` 和 `uploading` 模式一致。

**Rationale**:
- 現有架構已用 `summarizing` 和 `uploading` 控制 busy 狀態，`retranscribing` 沿用相同模式
- `_show_transcript_review()` 已有 `is_busy = st.session_state.summarizing or st.session_state.uploading`，新增 `retranscribing` 到這個聯集即可（FR-005）
- 轉錄完成後 `retranscribing = False`，更新 `raw_transcript` 和 `editor_version`，`st.rerun()` 刷新UI

**Alternatives considered**:
- 重用 `summarizing` 旗標 → 拒絕：語意不符，且 `_do_summarize()` 會被錯誤觸發
- 不用旗標，直接在按鈕 callback 中同步執行 → 拒絕：Streamlit 的 rerun 機制需要旗標來延遲執行，且需跨 rerun 維持 disabled 狀態

## R4: 轉錄失敗時的安全機制

**Decision**: 在呼叫 `transcribe()` 之前不動 `transcript_raw.txt`。轉錄成功後才覆蓋檔案。失敗時顯示 `st.error()` 並保留原始內容。

**Rationale**:
- FR-007 明確要求 API 失敗時不損毀原有逐字稿
- 實作方式：`transcribe()` 回傳 `result['raw_text']` 後，才寫入檔案和更新 session state
- 異常發生在 `transcribe()` 內部時，`try/except` 捕獲後直接顯示錯誤，原檔案完全不被觸及
- 這與 `_do_transcription()` 中首次轉錄的模式一致

**Alternatives considered**:
- 先備份 transcript_raw.txt → 拒絕：過度設計，只要不在轉錄成功前覆蓋即可
- 寫入暫存檔再 rename → 拒絕：本地單人使用場景無需這種防護

## R5: 重新轉錄按鈕的 disabled 條件

**Decision**: 以下任一條件成立時 disable「重新轉錄」按鈕：(1) `_find_audio_path()` 回傳 `None`（音檔不存在）；(2) `retranscribing` / `summarizing` / `uploading` 為 True。音檔不存在時附帶 caption 提示「找不到原始音檔」。

**Rationale**:
- FR-006 要求音檔不存在時 disabled 並提示
- FR-005 要求轉錄期間 disable 其他按鈕（反向亦然：其他操作進行中也不應允許轉錄）
- 在 `_show_transcript_review()` 渲染按鈕前呼叫 `_find_audio_path()`，根據結果設定 `disabled` 屬性

**Alternatives considered**:
- 按鈕始終可點，點擊後才檢查 → 拒絕：FR-006 明確要求 disabled 狀態，UX 更好

## R6: AUDIO_EXTENSIONS 常數位置

**Decision**: 在 `config.py` 新增 `AUDIO_EXTENSIONS = {'.mp3', '.mp4', '.wav', '.m4a', '.ogg', '.webm', '.mpeg', '.mpga'}` 常數。

**Rationale**:
- `app.py` 的 `file_uploader` 已列出 `['mp3', 'mp4', 'wav', 'm4a', 'ogg', 'webm', 'mpeg', 'mpga']`，需保持一致
- 集中到 `config.py` 避免 fallback 掃描與上傳介面的副檔名清單不同步
- 使用 set 而非 list，方便 `.suffix in AUDIO_EXTENSIONS` 查詢

**Alternatives considered**:
- 直接在 `_find_audio_path()` 硬編碼 → 拒絕：與 `file_uploader` 列表重複，日後新增格式易遺漏
