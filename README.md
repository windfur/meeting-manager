# 🎙️ 會議管理助手

上傳會議錄音 → 自動逐字稿 → AI 摘要 → 一鍵存入 Notion

## 快速開始

### 1. 首次安裝

雙擊 `setup.bat`，它會自動：
- 建立 Python 虛擬環境
- 安裝所有依賴套件
- 檢查 ffmpeg（音檔處理必備）

### 2. 設定 API Keys

複製 `.env.template` 為 `.env`，填入你的金鑰：

```
copy .env.template .env
```

用記事本打開 `.env`，填入：
- **OPENAI_API_KEY** — 從 [OpenAI Platform](https://platform.openai.com/api-keys) 取得
- **NOTION_TOKEN** — 從 [Notion Integrations](https://www.notion.so/my-integrations) 建立 Integration 取得
- **NOTION_PARENT_PAGE_ID** — 你想存放會議紀錄的 Notion 頁面 ID（網址最後那段）

> ⚠️ Notion Integration 建好後，需要到你的 Notion 頁面按「...」→「連結」→ 把你的 Integration 加進去，否則會沒有權限。

### 3. 啟動

雙擊 `start.bat`，瀏覽器會自動開啟 http://localhost:8501

### 4. 使用流程

1. **上傳音檔** — 支援 mp3, mp4, m4a, wav, ogg 等格式（最大 1GB）
2. **審閱逐字稿** — 可用「批次取代」修正人名/術語辨識錯誤
3. **AI 產生摘要** — 兩階段分析，確保結論正確
4. **審閱摘要** — 可直接修改
5. **上傳 Notion** — 一鍵存入

## 常用指令

| 動作 | 操作 |
|------|------|
| 首次安裝 | 雙擊 `setup.bat` |
| 啟動 | 雙擊 `start.bat` |
| 重啟（卡住時） | 雙擊 `restart.bat` |
| 停止 | 在終端機按 `Ctrl+C` |

## 切換摘要模型

編輯 `.env` 中的 `OPENAI_LLM_MODEL`：

| 模型 | 費用 | 說明 |
|------|------|------|
| gpt-4.1-mini | ~$0.005/次 | **推薦**，性價比最佳 |
| gpt-4o | ~$0.03/次 | 強力推理 |
| gpt-4.1 | ~$0.025/次 | 最新最強 |

> ⚠️ 不建議使用 gpt-4o-mini，實測摘要品質不佳（會搞混採納/放棄的結論）。

## 系統需求

- Windows 10/11
- Python 3.10+（安裝時勾選「Add Python to PATH」）
- OpenAI API Key（需要付費帳號，$5 起）
- Notion Integration Token
