from typing import Optional
from agora_contracts.action import ActionProposal
from agora_contracts.envelope import ToolResult, ToolMeta
from datetime import datetime, timezone

def pulsehunter_propose_create_alert(
    name: str,
    role: str,
    country: Optional[str] = None,
    is_remote: bool = True,
    interval_minutes: int = 60
) -> ToolResult[ActionProposal]:
    """
    Proposes creating a new recurring job alert in PulseHunter.
    Does NOT create the alert directly. Generates a structured proposal for Telegram confirmation.
    """
    target_region = country if country else "cualquier region"
    proposal = ActionProposal(
        action="pulsehunter_create_alert",
        summary=f"Crear alerta de empleo recurrente para {role} en {target_region} cada {interval_minutes}m.",
        arguments={
            "name": name,
            "role": role,
            "country": country,
            "is_remote": is_remote,
            "interval_minutes": interval_minutes
        },
        impact="Crea una tarea periodica de scraping en la base de datos de PulseHunter.",
        requires_confirmation=True
    )
    return ToolResult(
        ok=True,
        meta=ToolMeta(source="agora_policy", tool="pulsehunter_propose_create_alert", observed_at=datetime.now(timezone.utc)),
        data=proposal
    )

def pulsehunter_propose_delete_alert(alert_id: int) -> ToolResult[ActionProposal]:
    """
    Proposes permanently deleting a job alert from PulseHunter.
    Does NOT delete the alert directly. Generates a structured proposal for Telegram confirmation.
    """
    proposal = ActionProposal(
        action="pulsehunter_delete_alert",
        summary=f"Eliminar permanentemente la alerta de empleo #{alert_id}.",
        arguments={"alert_id": alert_id},
        impact="Eliminacion destructiva de la alerta y su historial en la base de datos.",
        requires_confirmation=True
    )
    return ToolResult(
        ok=True,
        meta=ToolMeta(source="agora_policy", tool="pulsehunter_propose_delete_alert", observed_at=datetime.now(timezone.utc)),
        data=proposal
    )
