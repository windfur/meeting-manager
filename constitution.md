# Meeting Manager Constitution

## Core Principles

### I. 使用者優先
所有功能設計以「簡化會議流程」為核心目標。UI 操作必須直覺、步驟明確，不需要技術背景即可使用。

### II. 資料自主
- 使用者的錄音、逐字稿、摘要等資料全部存在本地 `output/` 目錄
- Notion token、帳號資訊等敏感資料嚴禁 commit 到 Git
- .env、.notion_tokens.json 必須在 .gitignore 中
- 任何模板檔案（.env.template）只能放佔位符，不能有真正的密鑰

### III. Notion 整合彈性
- 不得綁定特定的 Notion workspace 或帳號
- 支援多 Notion token 切換（個人、公司等不同 workspace）
- 使用者可自由選擇上傳目標頁面和資料庫
- NOTION_PARENT_PAGE_ID 為選填，非必要設定

### IV. AI 摘要品質
- 兩階段摘要流程（Phase 1: 議題結論追蹤 → Phase 2: 結構化摘要）
- 支援使用者自定義摘要規範（summary_style.md），無自定義時使用預設規範
- Prompt 檔案集中管理於 `prompts/` 資料夾
- 摘要內容必須以 Markdown 格式輸出

### V. 版本可追溯
- AI 每次產生的摘要存為 `summary_v{N}.md`
- 使用者草稿存為 `summary_draft.md`，包含 base version 標記
- 歷史會議可隨時恢復、繼續編輯
- 上傳 Notion 的最終版存為 `summary.md`

### VI. 編輯器同步（嚴格要求）
- Streamlit text_area/text_input 必須使用版本化 key（如 `widget_v{N}`）
- 任何狀態變更（版本切換、AI 重新產生、批次取代）必須遞增 widget 版本號
- 禁止使用 `del st.session_state[key]` 方式「清除」widget

### VII. 操作防誤
- 上傳 Notion 期間，版本選擇器和上傳按鈕必須 disabled
- 摘要產生期間，所有互動元素必須 disabled
- 破壞性操作（刪除帳號、覆蓋檔案）需要確認或防呆

## Tech Stack

- **語言**: Python 3.12+
- **前端**: Streamlit
- **AI**: OpenAI API (gpt-4.1-mini)，可在 .env 切換模型
- **語音轉錄**: OpenAI Whisper API
- **Notion API**: httpx 直接呼叫 REST API
- **儲存**: 本地檔案系統 (`output/` 目錄)

## Development Guidelines

- 回覆語言一律使用**繁體中文**
- 檔案使用 UTF-8 編碼
- Python 套件管理使用 `requirements.txt`
- 本地開發使用 venv 虛擬環境
- Git repo: github.com/windfur/meeting-manager

## Governance

- Constitution 為最高層級開發準則，所有 feature spec 和 PR 必須符合
- 變更需更新版本號和日期

**Version**: 1.0.0 | **Ratified**: 2026-03-30 | **Last Amended**: 2026-03-30
