"""
🔌 Homelab MCP Client para Ágora
--------------------------------
Conector HTTP / SSE asíncrono para comunicarse con el servidor Homelab MCP (en Raspberry Pi 4 o local).
Diseñado para no bloquear y con tolerancia total a fallos (Graceful Degradation).
"""

import json
import httpx
from typing import Dict, Any, List, Optional
from app.core.config import settings

def get_base_url() -> str:
    return settings.homelab_mcp_url.rstrip("/")

# ==============================================================================
# 📊 HERRAMIENTAS DE LECTURA & DIAGNÓSTICO (FASE 1)
# ==============================================================================

async def fetch_homelab_overview() -> Dict[str, Any]:
    """Obtiene el resumen de salud de los 5 stacks y métricas de CPU/RAM/Temp de la Raspberry Pi."""
    url = f"{get_base_url()}/get_homelab_overview"
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            res = await client.get(url)
            if res.status_code == 200:
                return res.json() if isinstance(res.json(), dict) else {"raw": res.text}
            return {"status": "error", "code": res.status_code, "message": res.text}
    except Exception as e:
        return {"status": "unavailable", "message": f"Homelab MCP no alcanzable en {get_base_url()}: {str(e)}"}


async def fetch_stack_containers(stack_name: Optional[str] = None) -> Dict[str, Any]:
    """Lista los contenedores Docker y su estado (filtrable por stack: '01-infrastructure', etc.)."""
    url = f"{get_base_url()}/list_containers"
    params = {"stack_name": stack_name} if stack_name else {}
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            res = await client.get(url, params=params)
            if res.status_code == 200:
                return res.json() if isinstance(res.json(), dict) else {"raw": res.text}
            return {"status": "error", "code": res.status_code, "message": res.text}
    except Exception as e:
        return {"status": "unavailable", "message": str(e)}


async def fetch_container_logs(container_name: str, tail: int = 50) -> Dict[str, Any]:
    """Obtiene las últimas líneas de logs de un contenedor para diagnóstico."""
    url = f"{get_base_url()}/get_container_logs"
    params = {"container_name": container_name, "tail": tail}
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            res = await client.get(url, params=params)
            if res.status_code == 200:
                return {"container": container_name, "logs": res.text}
            return {"status": "error", "code": res.status_code, "message": res.text}
    except Exception as e:
        return {"status": "unavailable", "message": str(e)}


async def fetch_home_summary() -> Dict[str, Any]:
    """Consulta temperaturas, luces encendidas y puertas abiertas en Home Assistant."""
    url = f"{get_base_url()}/get_home_summary"
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            res = await client.get(url)
            if res.status_code == 200:
                return res.json() if isinstance(res.json(), dict) else {"raw": res.text}
            return {"status": "error", "code": res.status_code, "message": res.text}
    except Exception as e:
        return {"status": "unavailable", "message": str(e)}


async def fetch_entity_state(entity_id: str) -> Dict[str, Any]:
    """Consulta el estado detallado de un sensor o entidad en Home Assistant."""
    url = f"{get_base_url()}/get_entity_state"
    params = {"entity_id": entity_id}
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            res = await client.get(url, params=params)
            if res.status_code == 200:
                return res.json() if isinstance(res.json(), dict) else {"raw": res.text}
            return {"status": "error", "code": res.status_code}
    except Exception as e:
        return {"status": "unavailable", "message": str(e)}


async def search_workshop_inventory(query: str) -> Dict[str, Any]:
    """Busca repuestos, herramientas y componentes electrónicos en Homebox."""
    url = f"{get_base_url()}/search_inventory"
    params = {"query": query}
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            res = await client.get(url, params=params)
            if res.status_code == 200:
                return res.json() if isinstance(res.json(), dict) else {"raw": res.text}
            return {"status": "error", "code": res.status_code}
    except Exception as e:
        return {"status": "unavailable", "message": str(e)}


async def query_workshop_filaments(material: Optional[str] = None, color: Optional[str] = None) -> Dict[str, Any]:
    """Consulta bobinas de filamento 3D disponibles en Spoolman."""
    url = f"{get_base_url()}/query_filaments"
    params = {}
    if material:
        params["material"] = material
    if color:
        params["color"] = color
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            res = await client.get(url, params=params)
            if res.status_code == 200:
                return res.json() if isinstance(res.json(), dict) else {"raw": res.text}
            return {"status": "error", "code": res.status_code}
    except Exception as e:
        return {"status": "unavailable", "message": str(e)}


async def fetch_crowdsec_alerts() -> Dict[str, Any]:
    """Consulta alertas recientes y estado de CrowdSec."""
    url = f"{get_base_url()}/get_crowdsec_status"
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            res = await client.get(url)
            if res.status_code == 200:
                return res.json() if isinstance(res.json(), dict) else {"raw": res.text}
            return {"status": "error", "code": res.status_code}
    except Exception as e:
        return {"status": "unavailable", "message": str(e)}


# ==============================================================================
# ⚡ HERRAMIENTAS DE ACCIÓN & CONTROL (FASE 2)
# ==============================================================================

async def execute_container_restart(container_name: str, is_human_confirmed: bool = False) -> Dict[str, Any]:
    """Reinicia un contenedor en el Homelab mediante el MCP."""
    if not is_human_confirmed:
        return {
            "status": "requires_approval",
            "container_name": container_name,
            "message": f"⚠️ Reiniciar '{container_name}' requiere confirmación humana interactiva en Telegram."
        }
    
    url = f"{get_base_url()}/restart_container"
    payload = {"container_name": container_name}
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            res = await client.post(url, json=payload)
            return res.json() if res.status_code == 200 else {"status": "error", "code": res.status_code}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def execute_home_service(domain: str, service: str, service_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Ejecuta un servicio domótico en Home Assistant."""
    url = f"{get_base_url()}/call_home_service"
    payload = {"domain": domain, "service": service, "service_data": service_data or {}}
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            res = await client.post(url, json=payload)
            return res.json() if res.status_code == 200 else {"status": "error", "code": res.status_code}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def execute_add_inventory_item(
    name: str,
    location: str,
    quantity: int = 1,
    description: str = "",
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Registra un nuevo ítem en Homebox."""
    url = f"{get_base_url()}/add_inventory_item"
    payload = {
        "name": name,
        "location": location,
        "quantity": quantity,
        "description": description,
        "tags": tags or []
    }
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            res = await client.post(url, json=payload)
            return res.json() if res.status_code == 200 else {"status": "error", "code": res.status_code}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def fetch_all_home_entities(domain: Optional[str] = None) -> Dict[str, Any]:
    """Lista todos los dispositivos y entidades de Home Assistant (luces, sensores, switches, etc.)."""
    url = f"{get_base_url()}/list_home_entities"
    params = {"domain": domain} if domain else {}
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            res = await client.get(url, params=params)
            if res.status_code == 200:
                return res.json() if isinstance(res.json(), dict) else {"raw": res.text}
            return {"status": "error", "code": res.status_code, "message": res.text}
    except Exception as e:
        return {"status": "unavailable", "message": str(e)}
