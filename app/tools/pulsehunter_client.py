import json
import httpx
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.schemas.tools_contracts import JobItemCompact, PulseHunterJobsOutput

async def fetch_pulsehunter_jobs(
    search: Optional[str] = None,
    country: Optional[str] = None,
    is_remote: Optional[bool] = None,
    limit: int = 5
) -> Dict[str, Any]:
    """Consulta la API de PulseHunter permitiendo búsqueda semántica por keyword/tecnología y país."""
    url = f"{settings.pulsehunter_api_url}/jobs/"
    params: Dict[str, Any] = {"limit": limit}
    
    if search:
        params["search"] = search
    if country:
        params["country"] = country
    if is_remote is not None:
        params["is_remote"] = is_remote
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(url, params=params)
            if res.status_code != 200:
                return {"error": f"PulseHunter API respondió con código {res.status_code}"}
            
            data = res.json()
            raw_items = data.get("items", [])
            
            compact_jobs: List[JobItemCompact] = []
            for item in raw_items[:limit]:
                skills = item.get("skills_extracted") or []
                if isinstance(skills, str):
                    try:
                        skills = json.loads(skills)
                    except Exception:
                        skills = []
                
                compact_jobs.append(JobItemCompact(
                    id=item.get("id"),
                    title=item.get("title", "Desconocido"),
                    company=item.get("company", "Empresa Confidencial"),
                    country=item.get("country") or country or "Desconocido",
                    is_remote=item.get("is_remote", False),
                    url=item.get("job_url") or item.get("url", ""),
                    top_skills=skills[:4]
                ))
            
            out = PulseHunterJobsOutput(
                total_found=data.get("total", len(raw_items)),
                returned_count=len(compact_jobs),
                jobs=compact_jobs
            )
            return out.model_dump()
    except Exception as e:
        return {"error": f"Error conectando con PulseHunter: {e}"}

async def create_pulsehunter_search_alert(name: str, role: str, country: str = "European Union", is_remote: bool = True, interval_min: int = 60) -> str:
    """Crea una alerta de rastreo recurrente en PulseHunter."""
    url = f"{settings.pulsehunter_api_url}/alerts/"
    payload = {
        "name": name,
        "alert_type": "job",
        "interval_minutes": interval_min,
        "query_params": {
            "role": role,
            "country": country,
            "is_remote": is_remote,
            "hours_old": 72,
            "results_wanted": 25
        }
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(url, json=payload)
            if res.status_code in (200, 201):
                return f"✅ Alerta '{name}' para {role} en {country} programada cada {interval_min}m."
            return f"❌ Error creando alerta ({res.status_code}): {res.text}"
    except Exception as e:
        return f"Error en PulseHunter: {e}"
