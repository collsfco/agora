import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class PrincipalProfileConfig(BaseModel):
    user_id: Optional[int] = None
    bot_token: str = ""
    vault_path: str = ""

class Settings(BaseModel):
    # Ollama
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")

    # Principal A (Primary User Profile)
    telegram_bot_token_principal_a: str = os.getenv("TELEGRAM_BOT_TOKEN_PRINCIPAL_A", "")
    telegram_user_id_principal_a: Optional[int] = (
        int(os.getenv("TELEGRAM_USER_ID_PRINCIPAL_A")) if os.getenv("TELEGRAM_USER_ID_PRINCIPAL_A") and os.getenv("TELEGRAM_USER_ID_PRINCIPAL_A").isdigit() else None
    )
    obsidian_vault_principal_a: str = os.getenv("OBSIDIAN_VAULT_PRINCIPAL_A", str(Path.home() / "ObsidianVaults" / "PrincipalA"))

    # Principal B (Secondary User Profile)
    telegram_bot_token_principal_b: str = os.getenv("TELEGRAM_BOT_TOKEN_PRINCIPAL_B", "")
    telegram_user_id_principal_b: Optional[int] = (
        int(os.getenv("TELEGRAM_USER_ID_PRINCIPAL_B")) if os.getenv("TELEGRAM_USER_ID_PRINCIPAL_B") and os.getenv("TELEGRAM_USER_ID_PRINCIPAL_B").isdigit() else None
    )
    obsidian_vault_principal_b: str = os.getenv("OBSIDIAN_VAULT_PRINCIPAL_B", str(Path.home() / "ObsidianVaults" / "PrincipalB"))

    # PulseHunter Local MCP Service
    pulsehunter_api_url: str = os.getenv("PULSEHUNTER_API_URL", "http://localhost:8000/api/v1")
    pulsehunter_mcp_python: str = os.getenv("PULSEHUNTER_MCP_PYTHON", "/home/colls/github/pulse-hunter/backend/.venv/bin/python")
    pulsehunter_backend_dir: str = os.getenv("PULSEHUNTER_BACKEND_DIR", "/home/colls/github/pulse-hunter/backend")

    # Data paths
    checkpoints_db_path: str = os.getenv("CHECKPOINTS_DB_PATH", str(BASE_DIR / "data" / "checkpoints.sqlite"))
    engram_index_db_path: str = os.getenv("ENGRAM_INDEX_DB_PATH", str(BASE_DIR / "data" / "engram_index.db"))

settings = Settings()
