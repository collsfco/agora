import os
from pathlib import Path
import yaml
from typing import Dict, Any

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
CONFIG_DIR = Path(__file__).resolve().parent / "config"


def load_prompt_file(relative_path: str) -> str:
    """Loads a markdown prompt file from the prompts directory."""
    path = PROMPTS_DIR / relative_path
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def load_yaml_config(filename: str) -> Dict[str, Any]:
    """Loads a YAML configuration file from the config directory."""
    path = CONFIG_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_system_prompt(
    worker_name: str,
    profile_id: str = "principal_a",
    available_tools_description: str = ""
) -> str:
    """
    Composes a modular system prompt for a specific worker and user profile.
    Combines: identity + language + safety + grounding + profile + worker prompt + tools.
    """
    parts = [
        load_prompt_file("global/identity.md"),
        load_prompt_file("global/language.md"),
        load_prompt_file("global/safety.md"),
        load_prompt_file("global/grounding.md"),
        load_prompt_file(f"profiles/{profile_id}.md"),
        load_prompt_file(f"workers/{worker_name}.md"),
    ]

    if available_tools_description:
        parts.append(f"## Tools Available For This Turn\n{available_tools_description}")

    return "\n\n---\n\n".join(parts)
