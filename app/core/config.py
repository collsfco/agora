import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseModel):
    # Ollama
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")

    # Telegram Francisco
    telegram_bot_token_francisco: str = os.getenv("TELEGRAM_BOT_TOKEN_FRANCISCO", "")
    telegram_user_id_francisco: Optional[int] = (
        int(os.getenv("TELEGRAM_USER_ID_FRANCISCO")) if os.getenv("TELEGRAM_USER_ID_FRANCISCO") and os.getenv("TELEGRAM_USER_ID_FRANCISCO").isdigit() else None
    )

    # Telegram Esposa
    telegram_bot_token_esposa: str = os.getenv("TELEGRAM_BOT_TOKEN_ESPOSA", "")
    telegram_user_id_esposa: Optional[int] = (
        int(os.getenv("TELEGRAM_USER_ID_ESPOSA")) if os.getenv("TELEGRAM_USER_ID_ESPOSA") and os.getenv("TELEGRAM_USER_ID_ESPOSA").isdigit() else None
    )

    # Obsidian Vaults
    obsidian_vault_francisco: str = os.getenv("OBSIDIAN_VAULT_FRANCISCO", str(Path.home() / "ObsidianVaults" / "Francisco"))
    obsidian_vault_esposa: str = os.getenv("OBSIDIAN_VAULT_ESPOSA", str(Path.home() / "ObsidianVaults" / "Esposa"))

    # PulseHunter
    pulsehunter_api_url: str = os.getenv("PULSEHUNTER_API_URL", "http://localhost:8000/api/v1")
    pulsehunter_mcp_python: str = os.getenv("PULSEHUNTER_MCP_PYTHON", "/home/colls/github/pulse-hunter/backend/.venv/bin/python")
    pulsehunter_backend_dir: str = os.getenv("PULSEHUNTER_BACKEND_DIR", "/home/colls/github/pulse-hunter/backend")

    # Data paths
    checkpoints_db_path: str = os.getenv("CHECKPOINTS_DB_PATH", str(BASE_DIR / "data" / "checkpoints.sqlite"))
    engram_index_db_path: str = os.getenv("ENGRAM_INDEX_DB_PATH", str(BASE_DIR / "data" / "engram_index.db"))

settings = Settings()
