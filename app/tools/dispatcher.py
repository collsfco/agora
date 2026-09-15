import json
import logging
from typing import Dict, Any
from app.tools.homelab_client import (
    fetch_homelab_overview,
    fetch_stack_containers,
    fetch_container_logs,
    fetch_uptime_status,
    query_workshop_filaments,
    search_workshop_inventory,
    fetch_crowdsec_alerts,
    fetch_home_summary,
    fetch_entity_state,
    fetch_all_home_entities,
    execute_container_restart,
    execute_home_service,
    execute_add_inventory_item
)
from app.tools.homelab_proposals import (
    homelab_propose_restart_container,
    home_propose_call_service,
    workshop_propose_add_inventory_item
)
from app.tools.pulsehunter.read_tools import (
    pulsehunter_search_jobs,
    pulsehunter_search_housing,
    pulsehunter_list_alerts
)
from app.tools.pulsehunter.proposal_tools import (
    pulsehunter_propose_create_alert,
    pulsehunter_propose_delete_alert
)
from app.tools.weather_tool import get_current_weather
from app.tools.web_search_tool import search_internet
from app.tools.engram_fts5 import search_memory
from app.tools.obsidian_io import write_markdown_fact

logger = logging.getLogger("agora.dispatcher")

async def execute_tool(name: str, args: Dict[str, Any], profile_id: str = "principal_a") -> str:
    """Unified tool executor for LangGraph and Supervisor."""
    logger.info(f"🛠️ [DISPATCHER] Executing tool: {name} with args: {args}")
    try:
        # 1. Homelab & Workshop
        if name in ("homelab_get_resource_overview", "get_homelab_overview"):
            res = await fetch_homelab_overview()
            return json.dumps(res, ensure_ascii=False)
        elif name in ("homelab_list_containers", "list_homelab_containers"):
            res = await fetch_stack_containers(args.get("stack_name"))
            return json.dumps(res, ensure_ascii=False)
        elif name in ("homelab_get_service_status", "get_homelab_logs"):
            res = await fetch_container_logs(args.get("service") or args.get("container_name", ""), int(args.get("tail", 30)))
            return json.dumps({"service": args.get("service") or args.get("container_name"), "logs": res}, ensure_ascii=False)
        elif name in ("homelab_get_uptime_status", "get_uptime_status"):
            res = await fetch_uptime_status()
            return json.dumps(res, ensure_ascii=False)
        elif name in ("homelab_get_crowdsec_alerts", "get_crowdsec_alerts"):
            res = await fetch_crowdsec_alerts()
            return json.dumps(res, ensure_ascii=False)
        elif name == "homelab_propose_restart_container":
            res = homelab_propose_restart_container(container_name=args.get("container_name", ""))
            return res.model_dump_json()

        # Workshop
        elif name in ("workshop_search_filaments", "query_workshop_filaments"):
            res = await query_workshop_filaments(material=args.get("material"), color=args.get("color"))
            return json.dumps(res, ensure_ascii=False)
        elif name in ("workshop_search_inventory", "search_workshop_inventory"):
            res = await search_workshop_inventory(query=args.get("query", ""))
            return json.dumps(res, ensure_ascii=False)
        elif name == "workshop_propose_add_inventory_item":
            res = workshop_propose_add_inventory_item(
                name=args.get("name", ""),
                location=args.get("location", ""),
                quantity=int(args.get("quantity", 1)),
                description=args.get("description", ""),
                tags=args.get("tags")
            )
            return res.model_dump_json()

        # 2. PulseHunter
        elif name in ("pulsehunter_search_jobs", "get_pulsehunter_jobs"):
            alert_id_val = int(args["alert_id"]) if args.get("alert_id") is not None else None
            res = await pulsehunter_search_jobs(
                search=args.get("search"),
                alert_id=alert_id_val,
                country=args.get("country"),
                is_remote=args.get("is_remote"),
                sort_by=args.get("sort_by", "last_seen_desc"),
                limit=int(args.get("limit", 5)),
                owner_id=profile_id
            )
            return res.model_dump_json()
        elif name in ("pulsehunter_search_housing", "get_pulsehunter_housing"):
            res = await pulsehunter_search_housing(
                county=args.get("county"),
                listing_type=args.get("listing_type", "rent"),
                max_price=args.get("max_price"),
                min_bedrooms=args.get("min_bedrooms"),
                limit=int(args.get("limit", 5)),
                owner_id=profile_id
            )
            return res.model_dump_json()
        elif name in ("pulsehunter_list_alerts", "list_pulsehunter_alerts"):
            res = await pulsehunter_list_alerts(owner_id=profile_id)
            return res.model_dump_json()
        elif name == "pulsehunter_propose_create_alert":
            res = pulsehunter_propose_create_alert(
                name=args.get("name", "Alert"),
                role=args.get("role", "Developer"),
                country=args.get("country"),
                is_remote=bool(args.get("is_remote", True)),
                interval_minutes=int(args.get("interval_minutes", 60))
            )
            return res.model_dump_json()
        elif name == "pulsehunter_propose_delete_alert":
            res = pulsehunter_propose_delete_alert(alert_id=int(args.get("alert_id", 0)))
            return res.model_dump_json()

        # 3. Home Assistant
        elif name in ("home_get_summary", "get_home_status"):
            res = await fetch_home_summary()
            return json.dumps(res, ensure_ascii=False)
        elif name in ("home_get_entity_state", "get_entity_state"):
            res = await fetch_entity_state(args.get("entity_id", ""))
            return json.dumps(res, ensure_ascii=False)
        elif name in ("home_list_entities", "list_home_entities"):
            res = await fetch_all_home_entities(domain=args.get("domain"))
            return json.dumps(res, ensure_ascii=False)
        elif name == "home_propose_call_service":
            res = home_propose_call_service(
                domain=args.get("domain", ""),
                service=args.get("service", ""),
                service_data=args.get("service_data")
            )
            return res.model_dump_json()

        # 4. Weather & Web
        elif name in ("get_weather_forecast", "get_weather", "get_current_weather"):
            loc = args.get("location") or args.get("city") or "Solares"
            res = await get_current_weather(loc)
            return json.dumps(res, ensure_ascii=False)
        elif name in ("web_search", "search_internet"):
            res = await search_internet(args.get("query", ""))
            return json.dumps(res, ensure_ascii=False)

        # 5. Knowledge & Memory
        elif name in ("memory_search_notes", "search_memory"):
            res = await search_memory(args.get("query", ""), profile_id=profile_id)
            return json.dumps(res, ensure_ascii=False)
        elif name in ("memory_write_note", "write_markdown_fact"):
            res = await write_markdown_fact(args.get("fact", ""), args.get("category", "General"), profile_id=profile_id)
            return json.dumps(res, ensure_ascii=False)

        else:
            return json.dumps({"ok": False, "error": f"Tool '{name}' not found in dispatcher"})
    except Exception as e:
        logger.exception(f"Error executing tool {name}")
        return json.dumps({"ok": False, "error": str(e)})
