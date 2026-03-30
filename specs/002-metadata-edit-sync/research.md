# Research: 會議 Metadata 顯示與同步

## R1: Streamlit text_input 跨步驟同步策略

**Decision**: 使用 session state 作為 metadata 的 single source of truth。每個步驟的 text_input 讀取 session state 值作為預設值，修改後立即寫回 session state。

**Rationale**:
- Streamlit 的 text_input `value` 參數只在首次渲染生效，之後 widget 自行管理狀態
- 使用 `key` 參數讓 Streamlit 自動綁定 session_state，避免手動管理
- 跨步驟切換時，session state 天然保持值——不需要額外同步機制

**Alternatives considered**:
- 每個步驟維護獨立的 tags/participants 變數 → 拒絕：需要手動同步，容易出錯
- 使用 callback on_change → 拒絕：增加複雜度，session state 直接綁定已足夠

## R2: Widget key 設計（遵守 Constitution VI）

**Decision**: metadata 輸入欄位使用固定 key（如 `meta_tags_input`、`meta_participants_input`），不需要版本化 key。

**Rationale**:
- Constitution VI 要求版本化 key 是針對「狀態變更需要強制重設 widget」的場景（如版本切換、AI 重新產生）
- metadata 欄位的值由使用者直接輸入，不存在「外部強制覆蓋」的場景
- 恢復歷史會議時已經透過 rerun 重新渲染，widget 會自動讀取新的 session state 值

**Alternatives considered**:
- 使用版本化 key（`meta_tags_v{N}`）→ 拒絕：metadata 不存在版本切換場景，過度工程化

## R3: 草稿儲存時 metadata 同步時機

**Decision**: 在「💾 儲存草稿」按鈕的 handler 中，先解析 text_input 的值更新 session state，再呼叫 `_save_meeting_meta()`。

**Rationale**:
- `_save_meeting_meta()` 已實作完整，從 session state 讀取 tags/participants 並寫入 meeting_meta.json
- 只需確保在呼叫前，session state 中的值是最新的（來自 text_input widget）
- Streamlit 的 widget 透過 key 自動綁定後，session state 已是最新值，不需要額外解析步驟

**Alternatives considered**:
- 新增獨立的 metadata 儲存函數 → 拒絕：`_save_meeting_meta()` 已完善，無需重複
- 自動儲存（on_change callback）→ 拒絕：增加磁碟 I/O，且與現有「手動儲存」設計不一致

## R4: Tags 來源優先序

**Decision**: 維持現有優先序不變：
1. 使用者在 UI 輸入的 tags（Step 0 或任何步驟的 metadata 欄位）
2. AI auto_tags（僅在使用者未填任何 tag 時回補）
3. 從磁碟 meeting_meta.json 載入（恢復會議時）

**Rationale**: 現有的 auto_tags 覆寫邏輯（`if not st.session_state.tags and auto_tags`）已正確處理。metadata 欄位在 Step 1 就顯示後，使用者更容易在 AI 產生摘要前就填好 tags，減少 auto_tags 介入的需要。

## R5: text_input 預填值與 session state 綁定

**Decision**: 使用 Streamlit 的 key-based 雙向綁定。具體做法：
- text_input 指定 `key="meta_tags_input"`
- 在渲染前將 session state 的 list 轉為逗號分隔字串設入 `st.session_state.meta_tags_input`
- 使用者修改後 Streamlit 自動更新 `st.session_state.meta_tags_input`
- 儲存/上傳時從 `st.session_state.meta_tags_input` 解析回 list

**Rationale**: 避免 value 參數與 key 參數衝突（Streamlit 不允許同時使用），利用 key 的自動綁定機制最省事。
