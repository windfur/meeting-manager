import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
WHISPER_MODEL = os.getenv("OPENAI_WHISPER_MODEL", "whisper-1")
LLM_MODEL = os.getenv("OPENAI_LLM_MODEL", "gpt-4.1-mini")

# Notion
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_PARENT_PAGE_ID = os.getenv("NOTION_PARENT_PAGE_ID", "")
NOTION_TOKENS_FILE = BASE_DIR / ".notion_tokens.json"
NOTION_ACTIVE_FILE = BASE_DIR / ".notion_active_account"

# Audio
MAX_AUDIO_SIZE_MB = 25

# Summary style
SUMMARY_STYLE_FILE = BASE_DIR / "summary_style.md"


# ── Notion 多帳號管理 ──

def load_notion_tokens():
    """載入所有已儲存的 Notion tokens，回傳 [{label, token}]。"""
    tokens = []
    # .env 的 token 當作預設
    if NOTION_TOKEN:
        tokens.append({"label": "預設（.env）", "token": NOTION_TOKEN})
    # 額外儲存的 tokens
    if NOTION_TOKENS_FILE.exists():
        try:
            with open(NOTION_TOKENS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                for item in saved:
                    # 避免跟 .env 的重複
                    if item.get("token") != NOTION_TOKEN:
                        tokens.append(item)
        except (json.JSONDecodeError, KeyError):
            pass
    return tokens


def save_notion_token(label, token):
    """新增一組 Notion token。"""
    saved = []
    if NOTION_TOKENS_FILE.exists():
        try:
            with open(NOTION_TOKENS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
        except (json.JSONDecodeError, KeyError):
            pass
    # 避免重複
    saved = [t for t in saved if t.get("token") != token]
    saved.append({"label": label, "token": token})
    with open(NOTION_TOKENS_FILE, "w", encoding="utf-8") as f:
        json.dump(saved, f, ensure_ascii=False, indent=2)


def remove_notion_token(token):
    """移除一組 Notion token。"""
    if not NOTION_TOKENS_FILE.exists():
        return
    try:
        with open(NOTION_TOKENS_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
        saved = [t for t in saved if t.get("token") != token]
        with open(NOTION_TOKENS_FILE, "w", encoding="utf-8") as f:
            json.dump(saved, f, ensure_ascii=False, indent=2)
    except (json.JSONDecodeError, KeyError):
        pass


def save_active_notion_account(label):
    """記錄目前使用的 Notion 帳號 label。"""
    NOTION_ACTIVE_FILE.write_text(label, encoding="utf-8")


def load_active_notion_account():
    """讀取上次使用的 Notion 帳號 label，不存在則回傳 None。"""
    if NOTION_ACTIVE_FILE.exists():
        return NOTION_ACTIVE_FILE.read_text(encoding="utf-8").strip()
    return None
