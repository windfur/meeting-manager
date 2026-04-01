# meeting manager Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-31

## Active Technologies
- Python 3.12 + Streamlit 1.55, httpx (001-notion-onboarding)
- 本地檔案系統（`.notion_tokens.json`, `.env`） (001-notion-onboarding)
- 本地檔案系統（`output/` 目錄、`meeting_meta.json`） (002-metadata-edit-sync)
- Python 3.12 + Streamlit 1.55, httpx (notion_uploader) (003-notion-account-history)
- 本地 JSON 檔案 (meeting_meta.json) (003-notion-account-history)
- Python 3.12 + Streamlit 1.55, OpenAI SDK (003-notion-account-history)
- 本地 JSON 檔案（`output/{date}_{name}/meeting_meta.json`） (003-notion-account-history)

- Python 3.12 + Streamlit 1.55 + streamlit, openai, httpx (Notion API) (main)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

cd src; pytest; ruff check .

## Code Style

Python 3.12 + Streamlit 1.55: Follow standard conventions

## Recent Changes
- 003-notion-account-history: Added Python 3.12 + Streamlit 1.55, OpenAI SDK
- 003-notion-account-history: Added Python 3.12 + Streamlit 1.55, httpx (notion_uploader)
- 003-notion-account-history: Added Python 3.12 + Streamlit 1.55, httpx


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
