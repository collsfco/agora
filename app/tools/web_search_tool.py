import logging
from typing import Dict, Any, List
from ddgs import DDGS

logger = logging.getLogger(__name__)

def search_internet(query: str, max_results: int = 4) -> Dict[str, Any]:
    """Realiza una búsqueda en Internet para obtener información en tiempo real."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            
            clean_results = []
            for r in results:
                clean_results.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "url": r.get("href", "")
                })
            
            return {
                "query": query,
                "total_results": len(clean_results),
                "results": clean_results
            }
    except Exception as e:
        logger.error(f"Error realizando búsqueda web para '{query}': {e}")
        return {
            "query": query,
            "error": f"No se pudo consultar Internet: {e}",
            "results": []
        }
