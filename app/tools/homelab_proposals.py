from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from agora_contracts.action import ActionProposal
from agora_contracts.envelope import ToolResult, ToolMeta

def homelab_propose_restart_container(container_name: str) -> ToolResult[ActionProposal]:
    """
    Proposes restarting a Docker container in the Homelab.
    Does NOT restart it directly. Emits an ActionProposal for Telegram user confirmation.
    """
    proposal = ActionProposal(
        action="homelab_restart_container",
        summary=f"Reiniciar el contenedor '{container_name}' en la infraestructura Homelab.",
        arguments={"container_name": container_name},
        impact=f"Interrupción momentánea del servicio alojado en '{container_name}' durante el reinicio.",
        requires_confirmation=True
    )
    return ToolResult(
        ok=True,
        meta=ToolMeta(source="agora_policy", tool="homelab_propose_restart_container", observed_at=datetime.now(timezone.utc)),
        data=proposal
    )

def home_propose_call_service(
    domain: str,
    service: str,
    service_data: Optional[Dict[str, Any]] = None
) -> ToolResult[ActionProposal]:
    """
    Proposes executing a Home Assistant service (e.g. light.turn_off, climate.set_temperature).
    Does NOT execute it directly. Emits an ActionProposal for Telegram user confirmation.
    """
    payload = service_data or {}
    proposal = ActionProposal(
        action="home_call_service",
        summary=f"Ejecutar servicio domótico '{domain}.{service}' con parámetros: {payload}.",
        arguments={"domain": domain, "service": service, "service_data": payload},
        impact="Cambio de estado físico en dispositivos del hogar.",
        requires_confirmation=True
    )
    return ToolResult(
        ok=True,
        meta=ToolMeta(source="agora_policy", tool="home_propose_call_service", observed_at=datetime.now(timezone.utc)),
        data=proposal
    )

def workshop_propose_add_inventory_item(
    name: str,
    location: str,
    quantity: int = 1,
    description: str = "",
    tags: Optional[List[str]] = None
) -> ToolResult[ActionProposal]:
    """
    Proposes registering a new item in Homebox inventory.
    Does NOT create it directly. Emits an ActionProposal for Telegram user confirmation.
    """
    proposal = ActionProposal(
        action="workshop_add_inventory_item",
        summary=f"Registrar '{name}' (x{quantity}) en ubicación '{location}' dentro de Homebox.",
        arguments={
            "name": name,
            "location": location,
            "quantity": quantity,
            "description": description,
            "tags": tags or []
        },
        impact="Crea un nuevo registro en la base de datos de Homebox.",
        requires_confirmation=True
    )
    return ToolResult(
        ok=True,
        meta=ToolMeta(source="agora_policy", tool="workshop_propose_add_inventory_item", observed_at=datetime.now(timezone.utc)),
        data=proposal
    )
