import sys
import json
from app.tools.engram_fts5 import reindex_all_vaults, search_memory
from app.tools.obsidian_io import write_markdown_fact, read_markdown_file

def main():
    if len(sys.argv) < 2:
        print("Uso: python cli.py [reindex | search <principal_id> <query> | test-write]")
        return

    cmd = sys.argv[1]

    if cmd == "reindex":
        print("🔄 Reindexando todas las bóvedas de Obsidian...")
        stats = reindex_all_vaults()
        print(f"✅ Reindexación completada en milisegundos: {stats}")

    elif cmd == "search":
        if len(sys.argv) < 4:
            print("Uso: python cli.py search <principal_a|principal_b> <query>")
            return
        p_id = sys.argv[2]
        query = " ".join(sys.argv[3:])
        print(f"🔍 Buscando '{query}' para el perfil '{p_id}' (con filtro de aislamiento)...")
        results = search_memory(p_id, query)
        print(f"Encontrados {len(results)} resultados:")
        for r in results:
            print(f"- [{r['principal_id'].upper()}] {r['title']} ({r['category']}): {r['snippet']}")

    elif cmd == "test-write":
        print("✍️ Probando escritura de hecho estructurado...")
        path = write_markdown_fact(
            principal_id="principal_a",
            category="02_Memoria",
            title="Decision Arquitectura Agora",
            content="Se acordó utilizar SQLite FTS5 como motor Engram para indexación sub-milisegundo de Obsidian."
        )
        print(f"✅ Nota escrita en: {path}")
        reindex_all_vaults()

if __name__ == "__main__":
    main()
