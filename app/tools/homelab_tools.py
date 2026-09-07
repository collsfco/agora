import subprocess
import shutil
import docker
from typing import Dict, Any, List
from app.schemas.tools_contracts import SystemStatusOutput, ContainerSummary, DockerRestartOutput

# Contenedores críticos cuyo reinicio desatendido está estrictamente bloqueado
PROTECTED_CONTAINERS = {"traefik", "vaultwarden", "homeassistant", "postgres", "agora_core"}

def get_docker_client():
    try:
        return docker.from_env()
    except Exception:
        return None

def get_system_status_compact() -> Dict[str, Any]:
    """Obtiene el estado de CPU, RAM, Disco y contenedores Docker con Output Budgeting estricto."""
    total, used, free = shutil.disk_usage("/")
    disk_pct = f"{round((used / total) * 100, 1)}%"

    try:
        load_avg = subprocess.check_output(["uptime"]).decode("utf-8").strip()
    except Exception:
        load_avg = "N/A"

    try:
        mem_raw = subprocess.check_output(["free", "-h"]).decode("utf-8").split("\n")[1].split()
        ram_usage = f"{mem_raw[2]} / {mem_raw[1]}"
    except Exception:
        ram_usage = "N/A"

    client = get_docker_client()
    containers_summary: List[ContainerSummary] = []
    failed: List[str] = []
    total_c = 0
    running_c = 0

    if client:
        try:
            c_list = client.containers.list(all=True)
            total_c = len(c_list)
            for c in c_list[:15]:
                st = c.status.lower()
                if st == "running":
                    running_c += 1
                else:
                    failed.append(c.name)
                
                containers_summary.append(ContainerSummary(
                    name=c.name,
                    status=c.status,
                    uptime=c.attrs.get("State", {}).get("Status", "N/A")
                ))
        except Exception as e:
            failed.append(f"Error Docker: {e}")

    out = SystemStatusOutput(
        cpu_load=load_avg,
        ram_usage=ram_usage,
        disk_usage=disk_pct,
        total_containers=total_c,
        running_containers=running_c,
        failed_containers=failed,
        items=containers_summary
    )
    return out.model_dump()

def restart_docker_container_safe(container_name: str, is_human_confirmed: bool = False) -> Dict[str, Any]:
    """Reinicia un contenedor aplicando la política Human-in-the-Loop para servicios protegidos."""
    c_clean = container_name.lower().strip()
    
    if c_clean in PROTECTED_CONTAINERS and not is_human_confirmed:
        return DockerRestartOutput(
            container_name=container_name,
            success=False,
            requires_human_approval=True,
            message=f"⚠️ El contenedor '{container_name}' es crítico. Requiere confirmación humana en Telegram antes de reiniciar."
        ).model_dump()

    client = get_docker_client()
    if not client:
        return DockerRestartOutput(
            container_name=container_name,
            success=False,
            requires_human_approval=False,
            message="No se pudo conectar al daemon de Docker."
        ).model_dump()

    try:
        container = client.containers.get(container_name)
        container.restart()
        return DockerRestartOutput(
            container_name=container_name,
            success=True,
            requires_human_approval=False,
            message=f"✅ Contenedor '{container_name}' reiniciado correctamente."
        ).model_dump()
    except Exception as e:
        return DockerRestartOutput(
            container_name=container_name,
            success=False,
            requires_human_approval=False,
            message=f"❌ Error al reiniciar contenedor: {e}"
        ).model_dump()
