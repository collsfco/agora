import os
import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from app.core.config import settings

VAULT_BASE = Path.home() / "ObsidianVaults"

def get_vault_path_for_principal(principal_id: str) -> Path:
    """Devuelve la ruta absoluta de la bóveda correspondiente al principal activo."""
    if principal_id == "principal_a":
        return Path(settings.obsidian_vault_principal_a)
    elif principal_id == "principal_b":
        return Path(settings.obsidian_vault_principal_b)
    elif principal_id == "shared":
        return VAULT_BASE / "Compartido"
    else:
        raise ValueError(f"Principal ID '{principal_id}' desconocido.")

def read_markdown_file(principal_id: str, relative_path: str) -> Optional[str]:
    """Lee un archivo Markdown respetando el aislamiento de bóvedas."""
    vault = get_vault_path_for_principal(principal_id)
    file_path = vault / relative_path

    # Si no está en su bóveda privada, probar en la compartida
    if not file_path.exists():
        shared_path = (VAULT_BASE / "Compartido") / relative_path
        if shared_path.exists():
            file_path = shared_path
        else:
            return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error leyendo archivo {file_path}: {e}")
        return None

def write_markdown_fact(principal_id: str, category: str, title: str, content: str) -> str:
    """Escribe un hecho o nota estructurada en la bóveda del principal correspondiente."""
    vault = get_vault_path_for_principal(principal_id)
    target_dir = vault / category
    target_dir.mkdir(parents=True, exist_ok=True)

    clean_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    file_path = target_dir / f"{clean_title}.md"

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"---\nprincipal_id: {principal_id}\ncategoria: {category}\nfecha: {timestamp}\n---\n\n"
    body = f"# {title}\n\n{content}\n"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(header + body)

    return str(file_path.relative_to(vault))
