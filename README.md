# 🎙️ 會議管理助手

上傳會議錄音 → 自動逐字稿 → AI 摘要 → 審閱修改 → 一鍵存入 Notion

---

## 專案結構

```
app.py              ← Streamlit 主介面（五步驟流程）
transcriber.py      ← OpenAI Whisper 逐字稿（大檔案自動分段）
summarizer.py       ← 兩階段 AI 摘要（Phase 1 結論分析 → Phase 2 正式摘要）
notion_uploader.py  ← Notion REST API 上傳（批量分頁、自動建表）
config.py           ← 環境變數 & 路徑設定（多帳號 token 管理）

prompts/            ← AI Prompt 檔案（Markdown，方便閱讀和維護）
  ├── phase1_analysis.md       ← Phase 1：議題結論追蹤
  ├── phase2_system.md         ← Phase 2：角色定義 & 輸出格式（固定）
  └── phase2_default_style.md  ← Phase 2：預設摘要規範（使用者可覆蓋）

.env                ← API Keys（不進版控）
.env.template       ← .env 範本
.notion_tokens.json ← 多帳號 Notion Token 儲存（不進版控，自動產生）
summary_style.md    ← 個人摘要規範（不進版控，見下方說明）

output/             ← 每場會議的完整記錄
  └── YYYY-MM-DD_會議名稱/
      ├── transcript_raw.txt    ← 原始逐字稿
      ├── summary_v1.md         ← AI 摘要版本 1
      ├── summary_v2.md         ← AI 摘要版本 2（重新產生時遞增）
      ├── summary_draft.md      ← 使用者編輯草稿
      ├── summary.md            ← 最終上傳版
      ├── meeting_meta.json     ← 會議資訊（名稱、日期、標籤、參與者）
      └── {audio_file}          ← 原音檔
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

| 變數 | 說明 | 必填 | 取得方式 |
|------|------|------|----------|
| `OPENAI_API_KEY` | OpenAI 金鑰 | ✅ | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |

> **Notion Token 不需要寫在 .env 裡。** 啟動後直接在側邊欄「🔑 Notion 帳號」新增即可。
> 
> 如果你偏好寫在 .env，也可以填入 `NOTION_TOKEN`，系統會自動讀取並顯示為「預設（.env）」帳號。

### 3. 啟動

雙擊 `start.bat`，瀏覽器會自動開啟 http://localhost:8501

#### 首次啟動流程

1. 啟動後，側邊欄「🔑 Notion 帳號」會自動展開
2. 輸入 Notion Integration Token 和標籤（例如「公司」），點「➕ 新增」
3. 主流程解鎖，即可開始使用

> ⚠️ Notion Integration 建好後，需到 Notion 頁面 →「…」→「連結」→ 把 Integration 加進去，否則搜尋不到頁面。

---

## 使用流程

```
Step 0 ─ 上傳音檔         支援 mp3/mp4/m4a/wav/ogg/webm/mpeg/mpga（最大 1GB）
  │                       填寫會議名稱、日期、標籤、參與者
  │
Step 1 ─ 審閱逐字稿       可用「批次取代」修正人名、術語辨識錯誤
  │                       確認後自動進入摘要
  │
Step 2 ─ AI 產生摘要       兩階段分析，自動標記 ✅ 採納 / ⏳ 待確認 / ❌ 否決
  │                       支援版本歷史（每次重新產生都保留前版）
  │
Step 3 ─ 審閱摘要          可直接在頁面上修改，對照逐字稿檢查
  │                       選擇 Notion 上傳頁面和資料庫
  │
Step 4 ─ 上傳 Notion       一鍵存入知識庫，顯示頁面連結
```

---

## 側邊欄功能

### 🔑 Notion 帳號管理

支援多個 Notion workspace 的 Token 管理：

- **新增帳號**：輸入標籤 + Token，點「➕ 新增」
- **切換帳號**：Radio 按鈕快速切換，切換時自動重新載入頁面清單
- **刪除帳號**：UI 新增的帳號可移除，.env 的預設帳號不可刪
- Token 儲存在本地 `.notion_tokens.json`（不進版控）

### 📂 歷史會議瀏覽器

瀏覽和恢復過去的會議記錄：

- 自動掃描 `output/` 資料夾列出所有歷史會議
- 狀態標記：🟢 已上傳 Notion ｜ 🟡 有摘要草稿 ｜ 🔵 僅逐字稿
- 支援按日期篩選
- 點擊任何會議即可恢復進度，繼續編輯或重新產生摘要
- **純本地操作**，不需要 Notion Token 也能瀏覽

### ⚙️ 摘要規範設定

自訂 AI 摘要的風格和格式（詳見下方「自訂摘要規範」）。

---

## 摘要版本管理

每次 AI 產生摘要都會自動保存為新版本：

```
summary_v1.md   ← 第一次產生
summary_v2.md   ← 重新產生（前版仍保留）
summary_draft.md ← 使用者手動編輯的草稿，標記基於哪個 AI 版本
```

- 兩個以上版本時，頁面顯示版本選擇器可切換查看
- 草稿獨立於 AI 版本，不會被覆蓋
- 上傳 Notion 時使用的是你編輯區的內容

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

## Notion 上傳

### 頁面與資料庫選擇

上傳時有兩層選擇：

1. **選擇頁面** — 列出 Integration 有權限存取的所有 Notion 頁面
2. **選擇資料庫** — 列出該頁面下的資料庫，或選「➕ 自動建立新資料庫」

> `NOTION_PARENT_PAGE_ID`（.env 選填）可設定預設頁面，省去每次手動選擇。

### Integration 設定

1. 到 [notion.so/my-integrations](https://www.notion.so/my-integrations) 建立一個 Internal Integration
2. 複製 Integration Token
3. 到你要上傳的 Notion 頁面 → 「…」 → 「連結」 → 加入該 Integration
4. 在 app 側邊欄「🔑 Notion 帳號」新增此 Token

---

## 切換摘要模型

編輯 `.env` 中的 `OPENAI_LLM_MODEL`：

| 模型 | 費用 | 說明 |
|------|------|------|
| gpt-4.1-mini | ~$0.005/次 | **預設推薦**，性價比最佳 |
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
- ffmpeg（`setup.bat` 會自動安裝）
- OpenAI API Key（需要付費帳號，$5 起）
- Notion Integration Token（在 app 內新增即可）
