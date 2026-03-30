# Data Model: 會議 Metadata 顯示與同步

## State Flow

```
[Step 0] 使用者填入 tags/participants
    │
    ├─ 按「🚀 開始轉錄」
    │   └─ session_state.tags = parsed_list
    │   └─ session_state.participants = parsed_list
    │
    ▼
[Step 1] 逐字稿審閱
    │
    ├─ 顯示 metadata 欄位（tags_input, participants_input）
    │   └─ 預填 session_state.tags → ", ".join()
    │   └─ key="meta_tags_input" / "meta_participants_input"
    │
    ├─ 使用者修改 → Streamlit 自動更新 session_state.meta_tags_input
    │
    ├─ 按「✅ 確認逐字稿，產生摘要」
    │   └─ 解析 meta_tags_input → session_state.tags
    │   └─ 解析 meta_participants_input → session_state.participants
    │
    ▼
[Step 2] 摘要審閱
    │
    ├─ 顯示 metadata 欄位（同 Step 1 的 key，自動保持同步）
    │
    ├─ 按「💾 儲存草稿」
    │   └─ 解析 meta_tags_input → session_state.tags
    │   └─ 呼叫 _save_meeting_meta() → 寫入 meeting_meta.json
    │
    ├─ 按「✅ 確認上傳 Notion」
    │   └─ 解析 meta_tags_input → session_state.tags
    │   └─ _upload_to_notion() → 使用最新 tags/participants
    │
    ▼
[meeting_meta.json] 持久化
    │
    └─ 恢復會議時 _resume_meeting()
        └─ 讀取 tags/participants → session_state.tags
        └─ Step 1/2 顯示欄位預填
```

## Changed Behaviors

| Function | Before | After |
|----------|--------|-------|
| `_show_transcript_review()` | 無 metadata 欄位 | Step header 下方新增標籤 + 參與者 text_input |
| `_show_summary_review()` | 無 metadata 欄位 | Step header 下方新增標籤 + 參與者 text_input |
| 「💾 儲存草稿」handler | 只存 summary_draft.md | 額外解析 tags/participants 並呼叫 `_save_meeting_meta()` |
| 「✅ 確認上傳」handler | 使用 session_state.tags（可能過時） | 先解析最新 text_input 值再上傳 |

## New Helper

```python
def _parse_comma_list(text: str) -> list[str]:
    """將逗號分隔字串解析為 list，自動 trim 並過濾空值。"""
    return [item.strip() for item in text.split(',') if item.strip()] if text else []
```

## Widget Key Design

| Widget | Key | Scope |
|--------|-----|-------|
| 標籤輸入 | `meta_tags_input` | 跨 Step 1/2 共用 |
| 參與者輸入 | `meta_participants_input` | 跨 Step 1/2 共用 |

## Session State Changes

| Key | Type | 新增/修改 | 說明 |
|-----|------|----------|------|
| `meta_tags_input` | str | 新增 | text_input 的綁定值（逗號分隔字串） |
| `meta_participants_input` | str | 新增 | text_input 的綁定值（逗號分隔字串） |
| `tags` | list[str] | 不變 | 解析後的標籤 list（保持向後相容） |
| `participants` | list[str] | 不變 | 解析後的參與者 list（保持向後相容） |
