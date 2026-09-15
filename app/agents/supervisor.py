def parse_raw_tool_calls(text: str) -> List[Dict[str, Any]]:
    results = []
    if not text:
        return results
    for i, ch in enumerate(text):
        if ch == '{':
            for j in range(len(text), i + 1, -1):
                chunk = text[i:j].strip()
                if chunk.endswith('}'):
                    try:
                        d = json.loads(chunk)
                        if isinstance(d, dict) and ('name' in d or 'tool' in d):
                            name = d.get('name', d.get('tool'))
                            args = d.get('arguments', d.get('args', {}))
                            results.append({'name': name, 'args': args, 'id': name})
                            break
                    except Exception:
                        pass
            if results:
                break
    return results

import json
from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from app.agents.factory import get_base_llm
from app.tools.homelab_tools import get_system_status_compact, restart_docker_container_safe
from app.tools.homelab_client import (
    fetch_homelab_overview,
    fetch_stack_containers,
    fetch_container_logs,
    fetch_all_home_entities, fetch_home_summary,
    fetch_entity_state,
    search_workshop_inventory,
    query_workshop_filaments,
    fetch_crowdsec_alerts,
    execute_container_restart,
    execute_home_service,
    execute_add_inventory_item
)
from app.tools.pulsehunter_client import (
    fetch_pulsehunter_jobs,
    create_pulsehunter_search_alert,
    fetch_pulsehunter_housing,
    list_pulsehunter_alerts,
    trigger_pulsehunter_alert_execution,
    delete_pulsehunter_alert
)
from app.tools.engram_fts5 import search_memory
from app.tools.obsidian_io import write_markdown_fact
from app.tools.web_search_tool import search_internet
from app.tools.weather_tool import get_current_weather

TOOLS_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "get_homelab_overview",
            "description": "Obtiene el resumen de salud de los 5 stacks del Homelab (CPU, RAM, Temp SoC de la Raspberry Pi y estado de contenedores).",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_homelab_containers",
            "description": "Lista los contenedores Docker del Homelab y su estado (running, exited). Opcionalmente filtra por stack (01-infrastructure, 02-automation, 03-workshop, 04-utilities, 05-media).",
            "parameters": {
                "type": "object",
                "properties": {
                    "stack_name": {"type": "string", "description": "Nombre opcional del stack (ej. '01-infrastructure', '02-automation')"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_homelab_logs",
            "description": "Obtiene las últimas líneas de logs de un contenedor del Homelab para diagnosticar errores (ej: traefik, crowdsec, n8n, homeassistant).",
            "parameters": {
                "type": "object",
                "properties": {
                    "container_name": {"type": "string", "description": "Nombre exacto del contenedor (ej. 'traefik', 'crowdsec')"},
                    "tail": {"type": "integer", "description": "Número de líneas (por defecto 50)"}
                },
                "required": ["container_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_home_status",
            "description": "Consulta el estado general del hogar desde Home Assistant (temperaturas de estancias, luces encendidas, puertas/ventanas abiertas).",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_workshop_inventory",
            "description": "Busca repuestos, componentes electrónicos y herramientas en el inventario de Homebox del taller.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Término de búsqueda (ej: 'fuente 12v', 'esp32', 'relé')"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_workshop_filaments",
            "description": "Consulta el stock de bobinas de filamento 3D disponibles en Spoolman.",
            "parameters": {
                "type": "object",
                "properties": {
                    "material": {"type": "string", "description": "Material (ej: 'PLA', 'PETG', 'ABS')"},
                    "color": {"type": "string", "description": "Color o tonalidad"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_crowdsec_alerts",
            "description": "Consulta las alertas de seguridad y las IPs bloqueadas recientemente por CrowdSec en el firewall del Homelab.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "restart_homelab_container",
            "description": "Reinicia un contenedor Docker en el Homelab. Requiere confirmación previa en Telegram.",
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
            "description": "Consulta ofertas de alquiler y vivienda disponibles en la base de datos de PulseHunter.",
            "parameters": {
                "type": "object",
                "properties": {
                    "county": {"type": "string", "description": "Condado o ciudad (ej: Dublin, Cork, Galway)"},
                    "max_price": {"type": "number", "description": "Precio máximo mensual"},
                    "min_bedrooms": {"type": "integer", "description": "Número mínimo de habitaciones"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_pulsehunter_alerts",
            "description": "Lista todas las alertas de búsqueda activas registradas en PulseHunter.",
            "parameters": {
                "type": "object",
                "properties": {
                    "alert_type": {"type": "string", "description": "Tipo de alerta: 'jobs' o 'housing'"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_pulsehunter_alert",
            "description": "Crea una nueva alerta periódica de empleo o vivienda en PulseHunter.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Nombre identificativo de la alerta"},
                    "role": {"type": "string", "description": "Puesto o tecnología (ej: React Senior Developer)"},
                    "country": {"type": "string", "description": "País o región (ej: Ireland)"}
                },
                "required": ["name", "role"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_pulsehunter_alert",
            "description": "Ejecuta inmediatamente una alerta de PulseHunter para rastrear ofertas frescas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "alert_id": {"type": "integer", "description": "ID numérico de la alerta"}
                },
                "required": ["alert_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_pulsehunter_alert",
            "description": "Elimina una alerta de búsqueda de PulseHunter por su ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "alert_id": {"type": "integer", "description": "ID numérico de la alerta a eliminar"}
                },
                "required": ["alert_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Obtiene el pronóstico del tiempo actual y temperatura exacta de una ciudad.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "Ciudad o región (ej: Santander, Madrid, Dublin)"}
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Busca información actualizada en tiempo real en Internet (DuckDuckGo).",
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

PRINCIPAL_A_PROMPT = """

REGLAS IMPORTANTES DE HERRAMIENTAS:
1. SI EL USUARIO TE PREGUNTA POR DATOS DE DOMÓTICA, TEMPERATURAS, LUCES O DOCKER, LLAMA DIRECTAMENTE A LAS HERRAMIENTAS CORRESPONDIENTES SIN PREGUNTAR AL USUARIO SI QUIERES QUE LAS LLAMES.
2. Si te preguntan por filamentos, impresiones 3D, bobinas o impresión, consulta SIEMPRE 'query_workshop_filaments' en Spoolman.
3. Si te preguntan por componentes, teclados, herraminentas, repuestos o stock del taller, consulta SIEMPRE 'search_workshop_inventory' en Homebox.
4. Para encender o apagar luces o interruptores, usa 'call_home_service' con el domain (ej. 'light'), service (ej. 'turn_on' o 'turn_off') y service_data con el entity_id exacto (ej. {'entity_id': 'light.0xa4c138389c2f1ecc'}).
5. BÚSQUEDA EN HOMEBOX ('search_workshop_inventory'): Traduce SIEMPRE la consulta del usuario al inglés antes de llamar a la herramienta (ej. 'ventilador 12V' -> 'fan 12v', 'teclado' -> 'keyboard', 'fuente' -> 'power supply'). Muestra SIEMPRE la ubicación jerárquica exacta devuelta (ej. 'Office > 3D printer cabinet > Shelf 0'). NUNCA te inventes componentes, marcas o ubicaciones si la herramienta no los devuelve.
Eres el Copiloto Técnico de Principal A (Ágora Supervisor).
Tu misión es gestionar su Homelab en la Raspberry Pi 4, ofertas de empleo y vivienda con PulseHunter, su memoria en Obsidian, inventario del taller y consultar datos en Internet.
Tu tono es directo, profesional, técnico y conciso.
Responde siempre en español y utiliza las herramientas para fundamentar tus respuestas con datos reales.
- Si te preguntan por el estado del Homelab, stacks o contenedores, usa get_homelab_overview o list_homelab_containers.
- Si te preguntan por logs o errores en Docker, usa get_homelab_logs.
- Si te preguntan por la casa o domótica, usa get_home_status.
- Si te preguntan por inventario, repuestos o filamentos 3D, usa search_workshop_inventory o query_workshop_filaments.
- Si te preguntan por seguridad o CrowdSec, usa get_crowdsec_alerts.
- Si te preguntan por el clima o temperatura, usa SIEMPRE get_weather.
- Si te preguntan por casas o alquileres, usa get_pulsehunter_housing.
- Si te preguntan por ofertas de empleo, usa get_pulsehunter_jobs."""

PRINCIPAL_B_PROMPT = """

REGLAS IMPORTANTES DE HERRAMIENTAS:
1. SI EL USUARIO TE PREGUNTA POR DATOS DE DOMÓTICA, TEMPERATURAS, LUCES O DOCKER, LLAMA DIRECTAMENTE A LAS HERRAMIENTAS CORRESPONDIENTES SIN PREGUNTAR AL USUARIO SI QUIERES QUE LAS LLAMES.
2. Si te preguntan por filamentos, impresiones 3D, bobinas o impresión, consulta SIEMPRE 'query_workshop_filaments' en Spoolman.
3. Si te preguntan por componentes, teclados, herraminentas, repuestos o stock del taller, consulta SIEMPRE 'search_workshop_inventory' en Homebox.
4. Para encender o apagar luces o interruptores, usa 'call_home_service' con el domain (ej. 'light'), service (ej. 'turn_on' o 'turn_off') y service_data con el entity_id exacto (ej. {'entity_id': 'light.0xa4c138389c2f1ecc'}).
5. BÚSQUEDA EN HOMEBOX ('search_workshop_inventory'): Traduce SIEMPRE la consulta del usuario al inglés antes de llamar a la herramienta (ej. 'ventilador 12V' -> 'fan 12v', 'teclado' -> 'keyboard', 'fuente' -> 'power supply'). Muestra SIEMPRE la ubicación jerárquica exacta devuelta (ej. 'Office > 3D printer cabinet > Shelf 0'). NUNCA te inventes componentes, marcas o ubicaciones si la herramienta no los devuelve.
Eres el Asistente Personal de Principal B (Ágora Supervisor).
Tu misión es asistir con notas diarias, consultas generales, recordatorios, clima, estado del hogar e información en Internet.
Tu tono es amable, servicial, conciso y conversacional."""

async def execute_tool_call(name: str, args: dict, principal_id: str, peer_notifier: Optional[Any] = None) -> str:
    """Despacha la ejecución de herramientas inyectando el principal_id activo."""
    # ── Homelab Tools ──────────────────────────────────────────
    if name == "get_homelab_overview":
        res = await fetch_homelab_overview()
        # Fallback local si el MCP no está levantado
        if res.get("status") == "unavailable":
            res = get_system_status_compact()
        return json.dumps(res, ensure_ascii=False)
    
    elif name == "list_homelab_containers":
        s_name = args.get("stack_name")
        res = await fetch_stack_containers(stack_name=s_name)
        return json.dumps(res, ensure_ascii=False)

    elif name == "get_homelab_logs":
        c_name = args.get("container_name", "")
        tail = args.get("tail", 50)
        res = await fetch_container_logs(container_name=c_name, tail=tail)
        return json.dumps(res, ensure_ascii=False)

    elif name == "get_home_status":
        res = await fetch_home_summary()
        return json.dumps(res, ensure_ascii=False)

    elif name == "search_workshop_inventory":
        q = args.get("query", "")
        res = await search_workshop_inventory(query=q)
        return json.dumps(res, ensure_ascii=False)

    elif name == "query_workshop_filaments":
        mat = args.get("material")
        col = args.get("color")
        res = await query_workshop_filaments(material=mat, color=col)
        return json.dumps(res, ensure_ascii=False)

    elif name == "get_crowdsec_alerts":
        res = await fetch_crowdsec_alerts()
        return json.dumps(res, ensure_ascii=False)

    elif name == "restart_homelab_container":
        c_name = args.get("container_name", "")
        res = await execute_container_restart(c_name)
        return json.dumps(res, ensure_ascii=False)

    # ── PulseHunter Tools ──────────────────────────────────────
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

    elif name == "list_pulsehunter_alerts":
        a_type = args.get("alert_type")
        res = await list_pulsehunter_alerts(alert_type=a_type)
        return json.dumps(res, ensure_ascii=False)

    elif name == "trigger_pulsehunter_alert":
        a_id = args.get("alert_id")
        return await trigger_pulsehunter_alert_execution(alert_id=int(a_id))

    elif name == "delete_pulsehunter_alert":
        a_id = args.get("alert_id")
        return await delete_pulsehunter_alert(alert_id=int(a_id))

    elif name == "create_pulsehunter_alert":
        name_a = args.get("name", "Alerta")
        role = args.get("role", "Developer")
        country = args.get("country", "European Union")
        return await create_pulsehunter_search_alert(name=name_a, role=role, country=country)

    # ── Utilidades Generales & Memoria ─────────────────────────
    elif name == "get_weather":
        loc = args.get("location", "Santander")
        res = await get_current_weather(city_or_region=loc)
        return json.dumps(res, ensure_ascii=False)

    elif name == "search_web":
        q = args.get("query", "")
        res = search_internet(query=q)
        return json.dumps(res, ensure_ascii=False)
        
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


    # Robust Tool Calling Handler (handles native tool_calls and text tool calls from Qwen/Ollama)
    tool_calls = []
    if hasattr(ai_msg, "tool_calls") and ai_msg.tool_calls:
        tool_calls = ai_msg.tool_calls
    else:
        tool_calls = parse_raw_tool_calls(ai_msg.content)

    if tool_calls:
        for tool_call in tool_calls:
            t_name = tool_call["name"]
            t_args = tool_call.get("args", {})
            t_id = tool_call.get("id", t_name)

            tool_result = await execute_tool_call(t_name, t_args, principal_id, peer_notifier)
            messages.append(ToolMessage(content=tool_result, tool_call_id=t_id, name=t_name))

        final_ai = await llm.ainvoke(messages)
        return final_ai.content

    return ai_msg.content

