import os
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.core.config import settings

VAULT_BASE = Path.home() / "ObsidianVaults"

def get_db_connection() -> sqlite3.Connection:
    """Abre conexión a la base de datos SQLite de Engram y asegura las tablas FTS5."""
    db_path = Path(settings.engram_index_db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Tabla relacional principal
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            principal_id TEXT NOT NULL,
            category TEXT NOT NULL,
            relative_path TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(principal_id, relative_path)
        )
    """)

    # Tabla virtual FTS5 para búsqueda de texto completo ultrarrápida
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
            entry_id UNINDEXED,
            principal_id,
            category,
            title,
            content,
            tokenize = 'porter unicode61'
        )
    """)
    conn.commit()
    return conn

def reindex_all_vaults() -> Dict[str, int]:
    """Reconstruye el índice completo de Engram desde las carpetas de Obsidian."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Limpiar índice existente
    cursor.execute("DELETE FROM memory_fts")
    cursor.execute("DELETE FROM memory_entries")
    conn.commit()

    stats = {"principal_a": 0, "principal_b": 0, "shared": 0}

    vault_mappings = [
        ("principal_a", Path(settings.obsidian_vault_principal_a)),
        ("principal_b", Path(settings.obsidian_vault_principal_b)),
        ("shared", VAULT_BASE / "Compartido"),
    ]

    for principal_id, vault_path in vault_mappings:
        if not vault_path.exists():
            continue

        for root, _, files in os.walk(vault_path):
            for file in files:
                if file.endswith(".md"):
                    full_path = Path(root) / file
                    rel_path = str(full_path.relative_to(vault_path))
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            raw_text = f.read()

                        # Extraer título y contenido
                        title = file.replace(".md", "").replace("_", " ").title()
                        category = Path(rel_path).parent.name if Path(rel_path).parent.name else "general"

                        cursor.execute("""
                            INSERT INTO memory_entries (principal_id, category, relative_path, title, content)
                            VALUES (?, ?, ?, ?, ?)
                        """, (principal_id, category, rel_path, title, raw_text))

                        entry_id = cursor.lastrowid

                        cursor.execute("""
                            INSERT INTO memory_fts (entry_id, principal_id, category, title, content)
                            VALUES (?, ?, ?, ?, ?)
                        """, (entry_id, principal_id, category, title, raw_text))

                        stats[principal_id] += 1
                    except Exception as e:
                        print(f"Error indexando {full_path}: {e}")

    conn.commit()
    conn.close()
    return stats

def search_memory(principal_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Busca en la memoria aplicando el aislamiento estricto de principal_id."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Escapar comillas dobles para FTS5 seguro
    safe_query = query.replace('"', '""').strip()
    if not safe_query:
        conn.close()
        return []

    # Consulta con aislamiento: solo ve su principal_id o 'shared'
    allowed_principals = (principal_id, "shared")

    try:
        cursor.execute("""
            SELECT entry_id, principal_id, category, title, snippet(memory_fts, 4, '<b>', '</b>', '...', 20) as snippet, content
            FROM memory_fts
            WHERE principal_id IN (?, ?) AND memory_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (allowed_principals[0], allowed_principals[1], safe_query, limit))

        rows = cursor.fetchall()
        results = [
            {
                "principal_id": row["principal_id"],
                "category": row["category"],
                "title": row["title"],
                "snippet": row["snippet"],
                "preview": row["content"][:300]
            }
            for row in rows
        ]
        conn.close()
        return results
    except Exception as e:
        print(f"Error en búsqueda FTS5 ({query}): {e}")
        conn.close()
        return []
