# Data Model: Notion 帳號 Onboarding 優化

**Date**: 2026-03-30

## State Changes

本功能不新增任何 session state 欄位或檔案格式，僅改變**既有狀態的檢查時機和渲染順序**。

### Main Flow State Machine

```
App Start
    │
    ├─ Init session state (sidebar 元件需要)
    │
    ├─ Render sidebar (always, 不受任何 check 阻塞)
    │   ├─ _show_meeting_browser()   ← 純本地操作，最常用放最上
    │   ├─ _show_notion_accounts()
    │   └─ _show_style_settings()
    │
    ├─ _check_config()
    │   ├─ OPENAI_API_KEY missing → st.error() → return (BLOCKED)
    │   └─ OPENAI_API_KEY present → continue
    │
    ├─ Notion token check
    │   ├─ No tokens → st.info("請先新增") → return (GUIDED BLOCK)
    │   └─ Has tokens → continue to main flow
    │
    └─ Normal app flow (upload, transcribe, summarize, upload to Notion)
```

### Existing Entities (unchanged)

| Entity | Source | Description |
|--------|--------|-------------|
| `config.NOTION_TOKEN` | `.env` | 從 .env 讀取的預設 token（可為空） |
| `config.NOTION_TOKENS_FILE` | `.notion_tokens.json` | 多帳號 token 儲存檔 |
| `config.load_notion_tokens()` | config.py | 合併 .env + .json 的 token 清單 |
| `st.session_state.active_notion_token` | runtime | 目前選定使用的 token |
| `st.session_state.notion_token_idx` | runtime | 目前選定的 token index |

### Changed Behaviors

| Function | Before | After |
|----------|--------|-------|
| `_check_config()` | 檢查 OPENAI_API_KEY + NOTION_TOKEN，任一缺失都 return False | 只檢查 OPENAI_API_KEY |
| `main()` 渲染順序 | config check → sidebar → ... | session state init → sidebar（含 meeting browser）→ config check → token check → ... |
| `_show_notion_accounts()` expander | `expanded=False` 固定 | `expanded=not tokens` 動態 |
| `_show_notion_page_selector()` | 直接呼叫 API | 先檢查 active_notion_token，無則顯示提示 |
