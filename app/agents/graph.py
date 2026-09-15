import json
from typing import List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from app.agents.state import AgoraState, Evidence
from app.agents.router import pre_route_user_message, detect_response_language
from app.policy.tool_policy import get_allowed_tools_for_domain, get_tool_descriptions
from app.agents.loader import build_system_prompt, load_yaml_config
from app.agents.factory import get_base_llm

AGENTS_CONFIG = load_yaml_config("agents.yaml").get("agents", {})
MAX_TOOL_ROUNDS = 4

async def run_agora_graph_turn(
    user_message: str,
    profile_id: str = "principal_a",
    conversation_history: List[Dict[str, Any]] = None,
    tool_executor_fn = None
) -> Dict[str, Any]:
    """
    Executes a complete StateGraph turn following the Phase 2 & Phase 3 specification:
    1. Pre-routes intent (0ms determinism).
    2. Filters allowed tools to 1-4.
    3. Executes multi-step tool calls (up to 4 rounds).
    4. Enforces 'Evidence Verifier' (requires_fresh_data check).
    """
    # 1. Routing & Language
    response_lang = detect_response_language(user_message)
    domain, requires_fresh = pre_route_user_message(user_message)

    # 2. Tool Filter Policy
    allowed_tool_names = get_allowed_tools_for_domain(domain, profile_id)
    tool_descriptions = get_tool_descriptions(allowed_tool_names)

    # 3. Modular System Prompt Assembly
    worker_name = domain if domain in ["homelab", "home", "workshop", "pulsehunter", "weather_web", "knowledge"] else "homelab"
    system_prompt = build_system_prompt(worker_name, profile_id, tool_descriptions)

    # 4. LLM & Tools setup
    agent_cfg = AGENTS_CONFIG.get(worker_name, {})
    temp = agent_cfg.get("temperature", 0.0)
    llm = get_base_llm(temperature=temp)

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
    for _ in range(MAX_TOOL_ROUNDS):
        ai_msg = await llm.ainvoke(messages)
        messages.append(ai_msg)

        tool_calls = getattr(ai_msg, "tool_calls", []) or []
        if not tool_calls:
            # 6. Evidence Verifier Check
            if requires_fresh and not evidence_collected:
                return {
                    "final_answer": "⚠️ No se ha podido verificar el estado actual en tiempo real ya que no se obtuvo evidencia de las herramientas.",
                    "domain": domain,
                    "evidence": [],
                    "requires_fresh_data": True
                }
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

            if t_name not in allowed_tool_names:
                res_str = json.dumps({"ok": False, "error": f"Herramienta '{t_name}' no autorizada para el dominio {domain}."})
            elif tool_executor_fn:
                res_str = await tool_executor_fn(t_name, t_args, profile_id)
                evidence_collected.append({
                    "source": domain,
                    "tool": t_name,
                    "observed_at": "",
                    "cache_status": "miss",
                    "data": {"args": t_args}
                })
            else:
                res_str = json.dumps({"ok": True, "message": "Tool execution simulated."})
                evidence_collected.append({
                    "source": domain,
                    "tool": t_name,
                    "observed_at": "",
                    "cache_status": "miss",
                    "data": {"simulated": True}
                })

            messages.append(ToolMessage(content=res_str, tool_call_id=t_id, name=t_name))

    return {
        "final_answer": "Se alcanzó el límite máximo de iteraciones de herramientas.",
        "domain": domain,
        "evidence": evidence_collected,
        "requires_fresh_data": requires_fresh
    }
