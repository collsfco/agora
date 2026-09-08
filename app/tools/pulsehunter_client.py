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

async def fetch_pulsehunter_housing(
    county: Optional[str] = "Dublin",
    max_price: Optional[float] = None,
    min_bedrooms: Optional[int] = None,
    listing_type: str = "rent",
    limit: int = 5
) -> Dict[str, Any]:
    """Consulta la API de PulseHunter para obtener propiedades en alquiler o venta."""
    url = f"{settings.pulsehunter_api_url}/housing/"
    params: Dict[str, Any] = {
        "listing_type": listing_type,
        "limit": limit
    }
    if county:
        params["county"] = county
    if max_price is not None:
        params["max_price"] = max_price
    if min_bedrooms is not None:
        params["bedrooms"] = min_bedrooms

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(url, params=params)
            if res.status_code != 200:
                return {"error": f"PulseHunter Housing API respondió con código {res.status_code}"}
            
            data = res.json()
            raw_items = data.get("items", [])
            
            properties = []
            for item in raw_items[:limit]:
                properties.append({
                    "id": item.get("id"),
                    "title": item.get("title") or item.get("address", "Propiedad"),
                    "price_per_month": f"€{item.get('price_monthly') or item.get('price', 'N/A')}",
                    "bedrooms": item.get("bedrooms", "N/A"),
                    "county": item.get("county", county),
                    "url": item.get("url", ""),
                    "source": item.get("source", "daft")
                })
            
            return {
                "total_found": data.get("total", len(raw_items)),
                "returned_count": len(properties),
                "properties": properties
            }
    except Exception as e:
        return {"error": f"Error conectando con PulseHunter Housing: {e}"}

async def list_pulsehunter_alerts(alert_type: Optional[str] = None) -> Dict[str, Any]:
    """Lista todas las alertas activas de empleo o vivienda configuradas en PulseHunter."""
    url = f"{settings.pulsehunter_api_url}/alerts/"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(url)
            if res.status_code != 200:
                return {"error": f"Error listando alertas ({res.status_code}): {res.text}"}
            
            raw_alerts = res.json()
            if alert_type:
                raw_alerts = [a for a in raw_alerts if a.get("alert_type") == alert_type]
                
            clean_alerts = []
            for a in raw_alerts:
                clean_alerts.append({
                    "id": a.get("id"),
                    "name": a.get("name"),
                    "type": a.get("alert_type"),
                    "is_active": a.get("is_active"),
                    "interval_minutes": a.get("interval_minutes"),
                    "last_run": a.get("last_run_at") or "Nunca",
                    "params": a.get("query_params")
                })
            return {"total_alerts": len(clean_alerts), "alerts": clean_alerts}
    except Exception as e:
        return {"error": f"Error conectando con PulseHunter: {e}"}

async def trigger_pulsehunter_alert_execution(alert_id: int) -> str:
    """Dispara la ejecución inmediata del scraper para una alerta específica."""
    url = f"{settings.pulsehunter_api_url}/alerts/{alert_id}/run"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(url)
            if res.status_code in (200, 202):
                return f"✅ Alerta ID {alert_id} ejecutada bajo demanda con éxito. El scraper está buscando nuevas vacantes/viviendas en segundo plano."
            return f"❌ Error ejecutando alerta ({res.status_code}): {res.text}"
    except Exception as e:
        return f"Error ejecutando alerta en PulseHunter: {e}"

async def delete_pulsehunter_alert(alert_id: int) -> str:
    """Elimina permanentemente una alerta de rastreo de PulseHunter."""
    url = f"{settings.pulsehunter_api_url}/alerts/{alert_id}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.delete(url)
            if res.status_code in (200, 204):
                return f"✅ Alerta ID {alert_id} eliminada correctamente de PulseHunter."
            return f"❌ Error eliminando alerta ({res.status_code}): {res.text}"
    except Exception as e:
        return f"Error eliminando alerta: {e}"
