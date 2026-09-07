from typing import List, Callable, Any
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from app.core.config import settings

def get_base_llm(temperature: float = 0.0) -> ChatOllama:
    """Devuelve la instancia tipada de ChatOllama configurada con la GPU local."""
    return ChatOllama(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        temperature=temperature
    )

def build_worker_agent(name: str, system_prompt: str, tools: List[Any]):
    """Fábrica estándar para construir sub-agentes ReAct con límites de pasos."""
    llm = get_base_llm(temperature=0.0)
    return create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
        name=name
    )
