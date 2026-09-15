import re
from typing import Dict, Any, Tuple
from app.agents.loader import load_yaml_config

ROUTING_RULES = load_yaml_config("routing_rules.yaml")

def detect_response_language(text: str) -> str:
    """Detects user language for response targeting ('es' or 'en'). Defaults to 'es'."""
    spanish_indicators = [
        "qué", "cómo", "cuál", "cuántos", "cuántas", "dónde", "está", "tengo", 
        "por favor", "hola", "gracias", "piso", "pisos", "casas", "empleo", "empleos",
        "muestra", "los", "las", "del", "servidor", "contenedores", "filamentos"
    ]
    text_lower = text.lower()
    if any(w in text_lower for w in spanish_indicators):
        return "es"
    
    english_indicators = [
        "what", "how", "where", "which", "who", "is", "are", "do", "does",
        "please", "hello", "thanks", "weather", "container", "containers", "job", "jobs"
    ]
    if any(w in text_lower for w in english_indicators):
        return "en"
    
    return "es"

def pre_route_user_message(user_message: str) -> Tuple[str, bool]:
    """
    Deterministic zero-token pre-router.
    Matches keywords against routing_rules.yaml.
    Distinguishes purely theoretical/conceptual questions from operational queries.
    """
    text_lower = user_message.lower()

    # Purely conceptual/comparative queries bypass tool execution
    conceptual_patterns = ["qué ventajas tiene", "qué es un ", "explica qué es", "diferencia entre", "how does zfs work"]
    if any(p in text_lower for p in conceptual_patterns):
        return "general", False

    domains = ROUTING_RULES.get("domains", {})
    for domain_name, rules in domains.items():
        keywords = rules.get("keywords", [])
        for kw in keywords:
            if kw.lower() in text_lower:
                requires_fresh = domain_name != "general"
                return domain_name, requires_fresh

    return "general", False
