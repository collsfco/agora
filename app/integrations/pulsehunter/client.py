import httpx
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from agora_contracts.envelope import ToolResult, ToolMeta, ToolError
from agora_contracts.pulsehunter import (
    JobSearchInput,
    JobSearchOutput,
    JobItemCompact,
    HousingSearchInput,
    HousingSearchOutput,
    HousingItemCompact,
)
from app.core.config import settings

logger = logging.getLogger("agora.pulsehunter_client")

class PulseHunterClient:
    """Client for Pulse Hunter API implementing agora-contracts."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.pulsehunter_api_url).rstrip("/")
        self.timeout = 15.0

    async def search_jobs(self, input_data: JobSearchInput, owner_id: Optional[str] = None) -> ToolResult[JobSearchOutput]:
        params: Dict[str, Any] = {"limit": input_data.limit}
        if input_data.search:
            params["search"] = input_data.search
        if input_data.alert_id:
            params["alert_id"] = input_data.alert_id
        if input_data.country:
            params["country"] = input_data.country
        if input_data.is_remote is not None:
            params["is_remote"] = str(input_data.is_remote).lower()
        if input_data.sort_by:
            params["sort_by"] = input_data.sort_by
        if owner_id:
            params["owner_id"] = owner_id

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(f"{self.base_url}/jobs/", params=params, follow_redirects=True)
                if res.status_code != 200:
                    return ToolResult(
                        ok=False,
                        meta=ToolMeta(source="pulsehunter_api", tool="pulsehunter_search_jobs"),
                        error=ToolError(code=f"HTTP_{res.status_code}", message=f"PulseHunter API returned {res.status_code}", retryable=True, http_status=res.status_code)
                    )
                raw_data = res.json()
                if isinstance(raw_data, list):
                    items = raw_data
                    total_count = len(raw_data)
                elif isinstance(raw_data, dict):
                    items = raw_data.get("items", [])
                    total_count = raw_data.get("total", len(items))
                else:
                    items = []
                    total_count = 0

                compact_jobs = []
                for item in items[:input_data.limit]:
                    skills = item.get("skills_extracted", [])
                    if not skills:
                        skills = item.get("skills", [])
                    if isinstance(skills, str):
                        skills = [s.strip() for s in skills.split(",") if s.strip()]
                    raw = item.get("raw_data") or {}
                    company_name = item.get("company")
                    if not company_name or company_name.lower() in ("unknown", "unknown company"):
                        company_name = raw.get("company") or raw.get("company_name") or item.get("company") or "Unknown"

                    job_link = raw.get("job_url_direct") or raw.get("job_url") or item.get("url")

                    compact_jobs.append(JobItemCompact(
                        id=item.get("id", 0),
                        title=item.get("title", "Untitled Job"),
                        company=company_name,
                        location=item.get("location", "Remote"),
                        is_remote=bool(item.get("is_remote", False)),
                        salary_range=item.get("salary") or item.get("salary_range"),
                        skills=skills[:4],
                        url=job_link,
                        published_at=item.get("date_posted") or item.get("published_at") or item.get("first_seen_at")
                    ))
                
                output = JobSearchOutput(
                    total_found=total_count,
                    returned_count=len(compact_jobs),
                    jobs=compact_jobs
                )
                return ToolResult(
                    ok=True,
                    meta=ToolMeta(source="pulsehunter_api", tool="pulsehunter_search_jobs", observed_at=datetime.now(timezone.utc)),
                    data=output
                )
        except Exception as e:
            logger.exception("PulseHunter job search failed")
            return ToolResult(
                ok=False,
                meta=ToolMeta(source="pulsehunter_api", tool="pulsehunter_search_jobs"),
                error=ToolError(code="UPSTREAM_UNAVAILABLE", message=f"PulseHunter is unavailable: {str(e)}", retryable=True)
            )

    async def search_housing(self, input_data: HousingSearchInput, owner_id: Optional[str] = None) -> ToolResult[HousingSearchOutput]:
        params: Dict[str, Any] = {"limit": input_data.limit, "listing_type": input_data.listing_type}
        if input_data.county:
            params["county"] = input_data.county
        if input_data.max_price:
            params["max_price"] = input_data.max_price
        if input_data.min_bedrooms is not None:
            params["min_bedrooms"] = input_data.min_bedrooms
        if owner_id:
            params["owner_id"] = owner_id

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(f"{self.base_url}/housing/", params=params, follow_redirects=True)
                if res.status_code != 200:
                    return ToolResult(
                        ok=False,
                        meta=ToolMeta(source="pulsehunter_api", tool="pulsehunter_search_housing"),
                        error=ToolError(code=f"HTTP_{res.status_code}", message=f"PulseHunter Housing API returned {res.status_code}", retryable=True, http_status=res.status_code)
                    )
                raw_data = res.json()
                if isinstance(raw_data, list):
                    items = raw_data
                    total_count = len(raw_data)
                elif isinstance(raw_data, dict):
                    items = raw_data.get("items", [])
                    total_count = raw_data.get("total", len(items))
                else:
                    items = []
                    total_count = 0

                properties = []
                for item in items[:input_data.limit]:
                    price_val = item.get("current_price") or item.get("price_monthly") or item.get("price") or item.get("initial_price")
                    try:
                        price_num = float(price_val) if price_val is not None else None
                    except (ValueError, TypeError):
                        price_num = None
                    
                    properties.append(HousingItemCompact(
                        id=item.get("id", ""),
                        title=item.get("title") or item.get("address", "Property"),
                        price=price_num,
                        currency="EUR",
                        price_period="month" if input_data.listing_type == "rent" else "sale",
                        bedrooms=item.get("bedrooms"),
                        county=item.get("county"),
                        url=item.get("url"),
                        source=item.get("source", "daft")
                    ))
                output = HousingSearchOutput(
                    total_found=total_count,
                    properties=properties
                )
                return ToolResult(
                    ok=True,
                    meta=ToolMeta(source="pulsehunter_api", tool="pulsehunter_search_housing", observed_at=datetime.now(timezone.utc)),
                    data=output
                )
        except Exception as e:
            logger.exception("PulseHunter housing search failed")
            return ToolResult(
                ok=False,
                meta=ToolMeta(source="pulsehunter_api", tool="pulsehunter_search_housing"),
                error=ToolError(code="UPSTREAM_UNAVAILABLE", message=f"PulseHunter housing service unavailable: {str(e)}", retryable=True)
            )

    async def list_alerts(self, owner_id: Optional[str] = None) -> ToolResult[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(f"{self.base_url}/alerts/", follow_redirects=True)
                if res.status_code == 200:
                    raw = res.json()
                    if isinstance(raw, list):
                        alerts = raw
                    elif isinstance(raw, dict):
                        alerts = raw.get("items", [])
                    else:
                        alerts = []
                    return ToolResult(
                        ok=True,
                        meta=ToolMeta(source="pulsehunter_api", tool="pulsehunter_list_alerts", observed_at=datetime.now(timezone.utc)),
                        data={"total_alerts": len(alerts), "alerts": alerts}
                    )
                return ToolResult(
                    ok=False,
                    meta=ToolMeta(source="pulsehunter_api", tool="pulsehunter_list_alerts"),
                    error=ToolError(code=f"HTTP_{res.status_code}", message=f"PulseHunter Alerts API returned {res.status_code}")
                )
        except Exception as e:
            return ToolResult(
                ok=False,
                meta=ToolMeta(source="pulsehunter_api", tool="pulsehunter_list_alerts"),
                error=ToolError(code="UPSTREAM_UNAVAILABLE", message=str(e), retryable=True)
            )

pulsehunter_client = PulseHunterClient()
