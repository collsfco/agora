import json
from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from app.agents.factory import get_base_llm
from app.tools.homelab_tools import get_system_status_compact, restart_docker_container_safe
from app.tools.pulsehunter_client import fetch_pulsehunter_jobs, create_pulsehunter_search_alert, fetch_pulsehunter_housing
from app.tools.engram_fts5 import search_memory
from app.tools.obsidian_io import write_markdown_fact
from app.tools.web_search_tool import search_internet

TOOLS_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "get_system_status",
            "description": "Obtiene el estado general de salud del Homelab (CPU, RAM, Disco y contenedores Docker).",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "restart_docker_container",
            "description": "Reinicia un contenedor Docker en el Homelab. Los protegidos requieren aprobación previa.",
            "parameters": {
                "type": "object",
                "properties": {
                    "container_name": {"type": "string", "description": "Nombre exacto del contenedor"}
                },
                "required": ["container_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_pulsehunter_jobs",
            "description": "Consulta y filtra ofertas de empleo tech en la base de datos de PulseHunter.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": "Tecnología, rol o palabra clave (ej: React, PHP, Python, Frontend)"},
                    "country": {"type": "string", "description": "País o región (ej: Ireland, Spain, European Union)"},
                    "is_remote": {"type": "boolean", "description": "True para 100% remoto, False para presencial/híbrido"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_pulsehunter_housing",
            "description": "Consulta viviendas y pisos en alquiler en Irlanda (Dublin, etc.) en PulseHunter.",
            "parameters": {
                "type": "object",
                "properties": {
                    "county": {"type": "string", "description": "Condado o ciudad (ej: Dublin, Cork, Galway)"},
                    "max_price": {"type": "number", "description": "Precio máximo mensual en euros (ej: 1800)"},
                    "min_bedrooms": {"type": "integer", "description": "Número mínimo de habitaciones (ej: 2)"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Busca en Internet en tiempo real noticias, clima, documentación técnica o datos de actualidad.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Términos exactos de búsqueda en Internet"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_pulsehunter_alert",
            "description": "Crea una alerta de empleo recurrente en PulseHunter.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Nombre de la alerta"},
                    "role": {"type": "string", "description": "Tecnología o rol (PHP, React, etc.)"},
                    "country": {"type": "string", "description": "País o región"}
                },
                "required": ["name", "role"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_user_memory",
            "description": "Busca notas, decisiones, CV o hechos en la bóveda de Obsidian del usuario activo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Palabra clave o frase a buscar"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_memory_fact",
            "description": "Guarda una nota o hecho relevante en la bóveda de Obsidian del usuario.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Título de la nota"},
                    "content": {"type": "string", "description": "Contenido en Markdown"},
                    "category": {"type": "string", "description": "01_Informes_Mercado, 02_Memoria, 01_Notas"}
                },
                "required": ["title", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_message_to_peer_principal",
            "description": "Envía un mensaje o recordatorio al otro Principal autorizado en el sistema.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Mensaje o recordatorio a transmitir"}
                },
                "required": ["message"]
            }
        }
    }
]

PRINCIPAL_A_PROMPT = """Eres el Copiloto Técnico de Principal A (Ágora Supervisor).
Tu misión es gestionar su Homelab, ofertas de empleo y vivienda con PulseHunter, su memoria en Obsidian y consultar información en Internet cuando se requiera.
Tu tono es directo, profesional, técnico y conciso.
Responde siempre en español y utiliza las herramientas para fundamentar tus respuestas con datos reales.
- Si te preguntan por el clima, noticias o datos externos, usa search_web.
- Si te preguntan por casas o alquileres, usa get_pulsehunter_housing.
- Si te preguntan por ofertas de empleo, usa get_pulsehunter_jobs."""

PRINCIPAL_B_PROMPT = """Eres el Asistente Personal de Principal B (Ágora Supervisor).
Tu misión es asistir con notas diarias, consultas generales, recordatorios, clima e información en Internet.
Tu tono es amable, servicial, conciso y conversacional.
No uses jerga de programación a menos que sea explícitamente necesario."""

async def execute_tool_call(name: str, args: dict, principal_id: str, peer_notifier: Optional[Any] = None) -> str:
    """Despacha la ejecución de herramientas inyectando el principal_id activo."""
    if name == "get_system_status":
        res = get_system_status_compact()
        return json.dumps(res, ensure_ascii=False)
    
    elif name == "restart_docker_container":
        c_name = args.get("container_name", "")
        res = restart_docker_container_safe(c_name)
        return json.dumps(res, ensure_ascii=False)
        
    elif name == "get_pulsehunter_jobs":
        search = args.get("search")
        country = args.get("country")
        is_rem = args.get("is_remote")
        res = await fetch_pulsehunter_jobs(search=search, country=country, is_remote=is_rem)
        return json.dumps(res, ensure_ascii=False)

    elif name == "get_pulsehunter_housing":
        county = args.get("county", "Dublin")
        max_p = args.get("max_price")
        min_b = args.get("min_bedrooms")
        res = await fetch_pulsehunter_housing(county=county, max_price=max_p, min_bedrooms=min_b)
        return json.dumps(res, ensure_ascii=False)

    elif name == "search_web":
        q = args.get("query", "")
        res = search_internet(query=q)
        return json.dumps(res, ensure_ascii=False)
        
    elif name == "create_pulsehunter_alert":
        name_a = args.get("name", "Alerta")
        role = args.get("role", "Developer")
        country = args.get("country", "European Union")
        return await create_pulsehunter_search_alert(name=name_a, role=role, country=country)
        
    elif name == "search_user_memory":
        query = args.get("query", "")
        res = search_memory(principal_id=principal_id, query=query)
        return json.dumps(res, ensure_ascii=False)
        
    elif name == "save_memory_fact":
        title = args.get("title", "Nota")
        content = args.get("content", "")
        cat = args.get("category", "02_Memoria")
        rel_path = write_markdown_fact(principal_id=principal_id, category=cat, title=title, content=content)
        return f"✅ Nota guardada en tu bóveda privada: {rel_path}"

    elif name == "send_message_to_peer_principal":
        msg = args.get("message", "")
        target_peer = "principal_b" if principal_id == "principal_a" else "principal_a"
        if peer_notifier:
            await peer_notifier(target_peer, msg)
            return f"✅ Mensaje enviado al canal de {target_peer.upper()} exitosamente: '{msg}'"
        return f"📩 Mensaje encolado para {target_peer.upper()}: '{msg}'"
        
    return f"Herramienta '{name}' desconocida."

async def run_principal_turn(
    user_message: str,
    principal_id: str = "principal_a",
    conversation_history: List[Dict[str, Any]] = None,
    peer_notifier: Optional[Any] = None
) -> str:
    """Ejecuta un turno completo de razonamiento y ejecución de tools para el Principal especificado."""
    system_prompt = PRINCIPAL_A_PROMPT if principal_id == "principal_a" else PRINCIPAL_B_PROMPT
    llm = get_base_llm(temperature=0.0).bind_tools(TOOLS_DEFINITION)

    messages = [SystemMessage(content=system_prompt)]
    if conversation_history:
        for m in conversation_history:
            if m.get("role") == "user":
                messages.append(HumanMessage(content=m["content"]))
            elif m.get("role") == "assistant":
                messages.append(AIMessage(content=m["content"]))

    messages.append(HumanMessage(content=user_message))

    # Primer pase: LLM decide si llama herramientas
    ai_msg = await llm.ainvoke(messages)
    messages.append(ai_msg)

    # Si hay llamadas a herramientas, ejecutarlas
    if hasattr(ai_msg, "tool_calls") and ai_msg.tool_calls:
        for tool_call in ai_msg.tool_calls:
            t_name = tool_call["name"]
            t_args = tool_call["args"]
            t_id = tool_call.get("id", t_name)

            tool_result = await execute_tool_call(t_name, t_args, principal_id, peer_notifier)
            messages.append(ToolMessage(content=tool_result, tool_call_id=t_id, name=t_name))

        # Segundo pase: Síntesis final de respuesta
        final_ai = await llm.ainvoke(messages)
        return final_ai.content

    return ai_msg.content
