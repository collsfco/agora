from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# ==============================================================================
# HOMELAB DOCKER & SYSTEM CONTRACTS
# ==============================================================================

class ContainerSummary(BaseModel):
    name: str = Field(description="Nombre legible del contenedor Docker")
    status: str = Field(description="running | exited | restarting")
    uptime: str = Field(description="Tiempo de actividad o estado")

class SystemStatusOutput(BaseModel):
    cpu_load: str = Field(description="Carga de CPU o load average")
    ram_usage: str = Field(description="Memoria usada / total")
    disk_usage: str = Field(description="Porcentaje de disco usado")
    total_containers: int
    running_containers: int
    failed_containers: List[str] = Field(default_factory=list, description="Contenedores con estado != running")
    items: List[ContainerSummary] = Field(max_length=15, description="Lista resumida de contenedores")

class DockerRestartInput(BaseModel):
    container_name: str = Field(description="Nombre exacto del contenedor a reiniciar")
    reason: str = Field(description="Motivo justificado del reinicio")

class DockerRestartOutput(BaseModel):
    container_name: str
    success: bool
    requires_human_approval: bool = False
    message: str

# ==============================================================================
# PULSEHUNTER MCP CONTRACTS (Output Budgeting: max 300 tokens)
# ==============================================================================

class JobItemCompact(BaseModel):
    id: int
    title: str
    company: str
    country: str
    is_remote: bool
    url: str
    top_skills: List[str] = Field(default_factory=list, max_length=4)

class PulseHunterJobsOutput(BaseModel):
    total_found: int
    returned_count: int
    jobs: List[JobItemCompact] = Field(max_length=5, description="Máximo 5 ofertas por consulta para proteger contexto")

class PulseHunterAlertInput(BaseModel):
    name: str = Field(description="Título descriptivo de la alerta")
    role: str = Field(description="Puesto o tecnología (ej. PHP, React, DevOps)")
    country: str = Field(default="European Union", description="País o región")
    is_remote: bool = Field(default=True, description="Si es 100% teletrabajo")
    interval_minutes: int = Field(default=60, description="Frecuencia en minutos")

# ==============================================================================
# MEMORY & OBSIDIAN CONTRACTS
# ==============================================================================

class MemoryFactInput(BaseModel):
    category: str = Field(description="perfil | decisiones | proyectos | general")
    fact_statement: str = Field(description="Hecho atómico claro y conciso en una frase")
    importance_score: float = Field(ge=0.0, le=1.0, description="Relevancia a largo plazo (0.0 a 1.0)")

class MemorySearchOutput(BaseModel):
    query: str
    total_matches: int
    results: List[Dict[str, str]] = Field(max_length=5, description="Extractos relevantes encontrados en las notas")
