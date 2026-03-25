import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
DB_CONFIG_FILE = BASE_DIR / ".db_config.json"

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
WHISPER_MODEL = os.getenv("OPENAI_WHISPER_MODEL", "whisper-1")
LLM_MODEL = os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini")

# Notion
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_PARENT_PAGE_ID = os.getenv("NOTION_PARENT_PAGE_ID", "")

# Audio
MAX_AUDIO_SIZE_MB = 25


def get_db_id():
    if DB_CONFIG_FILE.exists():
        try:
            with open(DB_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("database_id")
        except (json.JSONDecodeError, KeyError):
            return None
    return None


def save_db_id(db_id):
    with open(DB_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"database_id": db_id}, f)
