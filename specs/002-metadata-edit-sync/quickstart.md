# Quickstart: 會議 Metadata 顯示與同步

## Change Summary

| 檔案 | 變更類型 | 說明 |
|------|----------|------|
| `app.py` `_show_transcript_review()` | 修改 | Step 1 新增 metadata 欄位 |
| `app.py` `_show_summary_review()` | 修改 | Step 2 新增 metadata 欄位 |
| `app.py` 「💾 儲存草稿」handler | 修改 | 解析最新 tags/participants 並呼叫 `_save_meeting_meta()` |
| `app.py` 「✅ 確認上傳」handler | 修改 | 上傳前解析最新 tags/participants |
| `app.py` `_resume_meeting()` | 修改 | 設定 `meta_tags_input` / `meta_participants_input` session state |
| `app.py` helper | 新增 | `_parse_comma_list()` 解析逗號分隔字串 |
| `app.py` main() session init | 修改 | 新增 `meta_tags_input`、`meta_participants_input` 初始化 |

## Verification Steps

1. 啟動 app → 上傳音檔、填入標籤 "測試A, 測試B"、參與者 "Aki" → 開始轉錄
2. Step 1（逐字稿審閱）→ 確認標籤欄位顯示 "測試A, 測試B"、參與者欄位顯示 "Aki"
3. 在 Step 1 修改標籤為 "測試A, 測試B, 新增C" → 確認逐字稿 → 進入 Step 2
4. Step 2 → 確認標籤欄位顯示 "測試A, 測試B, 新增C"（跨步驟同步）
5. 修改參與者為 "Aki, Bob" → 點擊「💾 儲存草稿」
6. 檢查 output/ 資料夾內 meeting_meta.json → 確認 participants 為 ["Aki","Bob"]
7. 從側邊欄歷史會議恢復該會議 → 確認標籤和參與者預填正確
8. 修改標籤 → 上傳 Notion → 確認 Notion page 的 Tags 屬性使用最新值

## Key Implementation Notes

- metadata 欄位使用共用 key（`meta_tags_input` / `meta_participants_input`），跨 Step 1/2 自動同步
- 現有 `_save_meeting_meta()` 函數不需修改，只需在儲存前確保 session_state.tags 已從 text_input 更新
- 恢復會議時 `_resume_meeting()` 需設定 `meta_tags_input` = ", ".join(tags)
- 新增 `_parse_comma_list()` helper 統一解析邏輯，取代現有各處重複的 list comprehension
