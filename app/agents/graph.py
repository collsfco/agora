import json
import logging
from typing import List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from app.agents.state import AgoraState, Evidence
from app.agents.router import pre_route_user_message, detect_response_language
from app.policy.tool_policy import get_allowed_tools_for_domain, get_tool_descriptions
from app.agents.loader import build_system_prompt, load_yaml_config
from app.agents.factory import get_base_llm

logger = logging.getLogger("agora.graph")
AGENTS_CONFIG = load_yaml_config("agents.yaml").get("agents", {})
TOOL_REGISTRY = load_yaml_config("tool_registry.yaml").get("tools", {})
MAX_TOOL_ROUNDS = 4

def get_tool_schemas_for_domain(tool_names: List[str]) -> List[Dict[str, Any]]:
    """Generates OpenAI-compatible function calling schemas filtered for the active domain."""
    schemas = []
    for name in tool_names:
        meta = TOOL_REGISTRY.get(name, {})
        desc = meta.get("description", "")

        properties: Dict[str, Any] = {}
        required: List[str] = []

        # Workshop
        if name in ("workshop_search_filaments", "query_workshop_filaments"):
            properties = {
                "material": {"type": "string", "description": "Material filter (e.g. PLA, PETG, TPU, PLA+)"},
                "color": {"type": "string", "description": "Color name (e.g. Red, Yellow, Blue, Black)"}
            }
        elif name in ("workshop_search_inventory", "search_workshop_inventory"):
            properties = {
                "query": {"type": "string", "description": "Keyword or component in English (e.g. keyboard, fan, power supply)"}
            }
            required = ["query"]
        elif name in ("workshop_propose_add_inventory_item",):
            properties = {
                "name": {"type": "string", "description": "Item or tool name"},
                "location": {"type": "string", "description": "Physical shelf/box location"},
                "quantity": {"type": "integer", "description": "Quantity count"},
                "description": {"type": "string", "description": "Brief notes or specs"}
            }
            required = ["name", "location"]

        # PulseHunter
        elif name in ("pulsehunter_search_jobs", "get_pulsehunter_jobs"):
            properties = {
                "search": {"type": "string", "description": "Job title or technology (e.g. PHP, Python, React)"},
                "country": {"type": "string", "description": "Country or European Union (leave null if not specified)"},
                "is_remote": {"type": "boolean", "description": "Whether the job is remote"},
                "limit": {"type": "integer", "description": "Max results (set 1 if user asks for latest, or N)"}
            }
        elif name in ("pulsehunter_search_housing", "get_pulsehunter_housing"):
            properties = {
                "county": {"type": "string", "description": "County or city (e.g. Dublin)"},
                "listing_type": {"type": "string", "enum": ["rent", "sale"]},
                "max_price": {"type": "number", "description": "Max price in EUR"},
                "min_bedrooms": {"type": "integer", "description": "Min bedrooms"},
                "limit": {"type": "integer", "description": "Max results (set 1 if user asks for latest, or N)"}
            }
        elif name in ("pulsehunter_propose_create_alert",):
            properties = {
                "name": {"type": "string", "description": "Alert title"},
                "role": {"type": "string", "description": "Target job role or tech stack"},
                "country": {"type": "string", "description": "Target country or region"},
                "is_remote": {"type": "boolean", "description": "Whether alert is remote only"},
                "interval_minutes": {"type": "integer", "description": "Scraping frequency in minutes"}
            }
            required = ["name", "role"]
        elif name in ("pulsehunter_propose_delete_alert",):
            properties = {
                "alert_id": {"type": "integer", "description": "ID of the alert to delete"}
            }
            required = ["alert_id"]

        # Weather & Web
        elif name in ("get_weather_forecast", "get_weather", "get_current_weather"):
            properties = {
                "location": {"type": "string", "description": "City or town name (e.g. Solares, Santander, Dublin)"}
            }
        elif name in ("web_search",):
            properties = {
                "query": {"type": "string", "description": "Search query keywords"}
            }
            required = ["query"]

        # Home Assistant
        elif name in ("home_get_entity_state", "get_entity_state"):
            properties = {
                "entity_id": {"type": "string", "description": "Home Assistant entity ID (e.g. sensor.temperatura_salon, climate.termostato)"}
            }
            required = ["entity_id"]
        elif name in ("home_list_entities", "list_home_entities"):
            properties = {
                "domain": {"type": "string", "description": "Domain filter (e.g. light, switch, climate, sensor)"}
            }
        elif name in ("home_propose_call_service",):
            properties = {
                "domain": {"type": "string", "description": "Service domain (e.g. light, switch, climate)"},
                "service": {"type": "string", "description": "Service action (e.g. turn_off, turn_on, set_temperature)"},
                "service_data": {"type": "object", "description": "Additional parameters like entity_id or temperature"}
            }
            required = ["domain", "service"]

        # Homelab
        elif name in ("homelab_list_containers", "list_homelab_containers"):
            properties = {
                "stack_name": {"type": "string", "description": "Stack name to filter (optional)"}
            }
        elif name in ("homelab_get_service_status", "get_homelab_logs"):
            properties = {
                "service": {"type": "string", "description": "Monitored container name (e.g. immich, traefik)"},
                "tail": {"type": "integer", "description": "Number of log lines"}
            }
        elif name in ("homelab_propose_restart_container",):
            properties = {
                "container_name": {"type": "string", "description": "Name of the Docker container to restart"}
            }
            required = ["container_name"]

        # Knowledge & Memory
        elif name in ("memory_search_notes", "search_memory"):
            properties = {
                "query": {"type": "string", "description": "Search query for Obsidian vault"}
            }
            required = ["query"]
        elif name in ("memory_write_note", "write_markdown_fact"):
            properties = {
                "fact": {"type": "string", "description": "Note content or fact to save in Markdown"},
                "category": {"type": "string", "description": "Category or topic folder"}
            }
            required = ["fact"]

        schemas.append({
            "type": "function",
            "function": {
                "name": name,
                "description": desc,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        })
    return schemas

async def run_agora_graph_turn(
    user_message: str,
    profile_id: str = "principal_a",
    conversation_history: List[Dict[str, Any]] = None,
    tool_executor_fn = None
) -> Dict[str, Any]:
    # 1. Routing & Language Detection
    response_lang = detect_response_language(user_message)
    domain, requires_fresh = pre_route_user_message(user_message)
    logger.info(f"🧭 [GRAPH] Routed to domain: '{domain}' (freshness_required={requires_fresh}, lang={response_lang})")

    # 2. Tool Filter Policy (Progressive Disclosure: 1-4 tools)
    allowed_tool_names = get_allowed_tools_for_domain(domain, profile_id)
    tool_descriptions = get_tool_descriptions(allowed_tool_names)
    tool_schemas = get_tool_schemas_for_domain(allowed_tool_names)

    # 3. Modular System Prompt Assembly
    worker_name = domain if domain in ["homelab", "home", "workshop", "pulsehunter", "weather_web", "knowledge", "general"] else "general"
    system_prompt = build_system_prompt(worker_name, profile_id, tool_descriptions)

    # Inject explicit language enforcement constraint
    lang_instruction = "IMPORTANT: You MUST write your ENTIRE final response strictly in SPANISH (español)." if response_lang == "es" else "IMPORTANT: You MUST write your ENTIRE final response strictly in ENGLISH."
    system_prompt = f"{system_prompt}\n\n---\n\n## Mandatory Language Constraint\n{lang_instruction}"

    # 4. LLM binding with ONLY allowed tools for this domain
    agent_cfg = AGENTS_CONFIG.get(worker_name, {})
    temp = agent_cfg.get("temperature", 0.0)
    base_llm = get_base_llm(temperature=temp)
    llm = base_llm.bind_tools(tool_schemas) if tool_schemas else base_llm

    messages = [SystemMessage(content=system_prompt)]
    if conversation_history:
        for m in conversation_history:
            if m.get("role") == "user":
                messages.append(HumanMessage(content=m["content"]))
            elif m.get("role") == "assistant":
                messages.append(AIMessage(content=m["content"]))
    messages.append(HumanMessage(content=user_message))

    evidence_collected: List[Evidence] = []
    
    # 5. Multi-Step Execution Loop
    for round_idx in range(MAX_TOOL_ROUNDS):
        ai_msg = await llm.ainvoke(messages)
        messages.append(ai_msg)

        tool_calls = getattr(ai_msg, "tool_calls", []) or []
        if not tool_calls:
            # 6. Evidence Verifier Check
            if requires_fresh and not evidence_collected and round_idx == 0:
                logger.warning(f"⚠️ [VERIFIER] Question in domain '{domain}' required live evidence but model did not call tools.")
            return {
                "final_answer": ai_msg.content,
                "domain": domain,
                "evidence": evidence_collected,
                "requires_fresh_data": requires_fresh
            }

        # Execute returned tools
        for tc in tool_calls:
            t_name = tc["name"]
            t_args = tc.get("args", {})
            t_id = tc.get("id", t_name)
            logger.info(f"🛠️ [GRAPH] Model called tool: '{t_name}' with args: {t_args}")

            if t_name not in allowed_tool_names:
                res_str = json.dumps({"ok": False, "error": f"Herramienta '{t_name}' no autorizada para el dominio {domain}."})
            elif tool_executor_fn:
                res_str = await tool_executor_fn(t_name, t_args, profile_id)
                evidence_collected.append({
                    "source": domain,
                    "tool": t_name,
                    "observed_at": "",
                    "cache_status": "miss",
                    "data": {"raw": res_str[:500]}
                })
            else:
                res_str = json.dumps({"ok": True, "message": "Tool execution simulated."})

            messages.append(ToolMessage(content=res_str, tool_call_id=t_id, name=t_name))

    return {
        "final_answer": "Se alcanzó el límite de llamadas a herramientas.",
        "domain": domain,
        "evidence": evidence_collected,
        "requires_fresh_data": requires_fresh
    }
