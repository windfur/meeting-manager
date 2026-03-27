# 🎙️ 會議管理助手

上傳會議錄音 → 自動逐字稿 → AI 摘要 → 一鍵存入 Notion

---

## 專案結構

```
app.py              ← Streamlit 主介面（三步驟流程）
transcriber.py      ← OpenAI Whisper 逐字稿
summarizer.py       ← 兩階段 AI 摘要（Phase 1 結論分析 → Phase 2 正式摘要）
notion_uploader.py  ← Notion REST API 上傳
config.py           ← 環境變數 & 路徑設定

prompts/            ← AI Prompt 檔案（Markdown，方便閱讀和維護）
  ├── phase1_analysis.md       ← Phase 1：議題結論追蹤
  ├── phase2_system.md         ← Phase 2：角色定義 & 輸出格式（固定）
  └── phase2_default_style.md  ← Phase 2：預設摘要規範（使用者可覆蓋）

.env                ← API Keys（不進版控）
.env.template       ← .env 範本
.db_config.json     ← Notion Database ID（首次使用時自動產生）
summary_style.md    ← 個人摘要規範（不進版控，見下方說明）

output/             ← 每場會議的逐字稿 & 摘要
  └── YYYY-MM-DD_會議名稱/
      ├── transcript_raw.txt    ← 原始逐字稿
      └── summary_draft.md      ← AI 摘要草稿
```

---

## 快速開始

### 1. 首次安裝

雙擊 `setup.bat`，它會自動建立虛擬環境、安裝依賴、檢查 ffmpeg。

### 2. 設定 API Keys

```
copy .env.template .env
```

用記事本打開 `.env`，填入：

| 變數 | 說明 | 取得方式 |
|------|------|----------|
| `OPENAI_API_KEY` | OpenAI 金鑰 | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `NOTION_TOKEN` | Notion Integration Token | [notion.so/my-integrations](https://www.notion.so/my-integrations) |
| `NOTION_PARENT_PAGE_ID` | Notion 頁面 ID（網址最後那段） | 你的 Notion 頁面 URL |

> ⚠️ Notion Integration 建好後，需到 Notion 頁面 →「…」→「連結」→ 把 Integration 加進去，否則沒有權限。

### 3. 啟動

雙擊 `start.bat`，瀏覽器會自動開啟 http://localhost:8501

---

## 使用流程

```
Step 1 ─ 上傳音檔     支援 mp3/mp4/m4a/wav/ogg（最大 1GB）
  │
Step 2 ─ 審閱逐字稿    可用「批次取代」修正人名、術語辨識錯誤
  │
Step 3 ─ AI 產生摘要   兩階段分析，自動標記 ✅ 採納 / ⏳ 待確認 / ❌ 否決
  │
Step 4 ─ 審閱摘要      可直接在頁面上修改
  │
Step 5 ─ 上傳 Notion   一鍵存入知識庫
```

---

## 兩階段 AI 摘要原理

| 階段 | 做什麼 | 為什麼需要 |
|------|--------|------------|
| **Phase 1** | 追蹤每個議題的最終結論（✅/⏳/❌） | 防止 AI 搞混「有討論」和「有拍板」 |
| **Phase 2** | 根據 Phase 1 的結論產生正式摘要 | 確保結論標記準確，摘要結構完整 |

Phase 2 摘要由兩層 prompt 組成：
- **System Intro（不可改）**：角色定義、遵守 Phase 1 標記、KEY_POINTS/TAGS 輸出格式
- **摘要規範（可自訂）**：語言規則、寫作原則、結論標記、主題拆分、輸出格式 — 全部可覆蓋

---

## 自訂摘要規範

在 **Streamlit 左側欄 →「⚙️ 摘要規範設定」** 可以定義你自己的摘要規範。
規範存在 `summary_style.md`（不進版控），每次產生摘要時自動套用。

### 快速開始

1. 點 **「📋 產生規範範本」** — 系統填入結構化骨架
2. 照著改就好 — 每個 section 都有預填內容，改成你需要的
3. 按 **「💾 儲存」**

### 規範結構

範本包含以下 section，每個都可以自由修改：

| Section | 控制什麼 | 範例 |
|---------|---------|------|
| **語言規則** | 輸出語言、術語處理 | 「全英文撰寫」「日文輸出」 |
| **領域知識** | 團隊背景、縮寫、人名 | 「PM = Product Manager」「小明 = 後端工程師」 |
| **寫作原則** | 詳略程度、風格 | 「精簡為主，每案不超過 5 行」 |
| **結論標記準則** | ✅/⏳/❌ 判定方式 | 可調整判定嚴格度 |
| **主題拆分** | 拆分顆粒度 | 「以 JIRA ticket 為單位拆分」 |
| **輸出格式** | 摘要的骨架結構 | 完全自訂段落、欄位、排版 |

不需要的 section 可以刪掉，AI 會對未定義的部分自行判斷（建議至少保留「輸出格式」section）。

### 💡 用 ChatGPT 幫你寫

> 我有一個會議摘要工具，讓我用 Markdown 定義摘要規範。  
> 規範需要包含：語言規則、領域知識、寫作原則、結論標記準則、主題拆分、輸出格式。  
> 請根據以下需求幫我寫一份完整的摘要規範：  
> [你的需求，例如：我們是資安團隊，會議常討論 IAM policy、network ACL...]

### 注意事項

- 不需要重啟 Streamlit，下次「重新產生摘要」時自動套用
- 留空或清除 → 恢復預設規範

---

## 切換摘要模型

編輯 `.env` 中的 `OPENAI_LLM_MODEL`：

| 模型 | 費用 | 說明 |
|------|------|------|
| gpt-4.1-mini | ~$0.005/次 | **推薦**，性價比最佳 |
| gpt-4o | ~$0.03/次 | 強力推理 |
| gpt-4.1 | ~$0.025/次 | 最新最強 |

> ⚠️ 不建議使用 gpt-4o-mini，實測摘要品質不佳（會搞混採納/放棄的結論）。

---

## 常用指令

| 動作 | 操作 |
|------|------|
| 首次安裝 | 雙擊 `setup.bat` |
| 啟動 | 雙擊 `start.bat` |
| 重啟（卡住時） | 雙擊 `restart.bat` |
| 停止 | 在終端機按 `Ctrl+C` |

## 系統需求

- Windows 10/11
- Python 3.10+（安裝時勾選「Add Python to PATH」）
- OpenAI API Key（需要付費帳號，$5 起）
- Notion Integration Token
