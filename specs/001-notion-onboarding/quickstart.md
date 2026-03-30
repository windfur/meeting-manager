# Quickstart: Notion 帳號 Onboarding 優化

**Date**: 2026-03-30

## 變更摘要

| 檔案 | 改動 |
|------|------|
| `app.py` main() 前段 | session state 初始化移到 sidebar 之前 |
| `app.py` main() sidebar 區塊 | sidebar 渲染（含 meeting browser）移到 `_check_config()` 之前 |
| `app.py` L20-26 | config check 後新增獨立的 Notion token 檢查 |
| `app.py` `_check_config()` | 移除 Notion token 檢查，只保留 OPENAI_API_KEY |
| `app.py` `_show_notion_accounts()` | expander `expanded=not tokens` 動態展開 |
| `app.py` `_show_notion_page_selector()` | 加入 active_notion_token guard |

## 驗證步驟

1. 註解掉 `.env` 中的 `NOTION_TOKEN` 和 `NOTION_PARENT_PAGE_ID`
2. 確認 `.notion_tokens.json` 不存在或為空
3. 啟動 app → 應看到主區域引導提示、側邊欄歷史會議瀏覽器在最上方、Notion 帳號 expander 自動展開
4. 在側邊欄新增 token → 頁面重新載入後主流程解鎖
5. 恢復 `.env` Notion 設定 → 預設帳號出現在列表中
