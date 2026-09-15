from typing import Optional
from agora_contracts.pulsehunter import JobSearchInput, JobSearchOutput, HousingSearchInput, HousingSearchOutput
from agora_contracts.envelope import ToolResult
from app.integrations.pulsehunter import pulsehunter_client

async def pulsehunter_search_jobs(
    search: Optional[str] = None,
    country: Optional[str] = None,
    is_remote: Optional[bool] = None,
    limit: int = 5,
    owner_id: Optional[str] = None
) -> ToolResult[JobSearchOutput]:
    """
    Searches recent job vacancies by keyword, country or remote status.
    Returns compact results with salary, company, top skills, and link.
    Read-only. Does not create alerts or apply to jobs.
    """
    input_data = JobSearchInput(search=search, country=country, is_remote=is_remote, limit=limit)
    return await pulsehunter_client.search_jobs(input_data, owner_id=owner_id)

async def pulsehunter_search_housing(
    county: Optional[str] = None,
    listing_type: str = "rent",
    max_price: Optional[float] = None,
    min_bedrooms: Optional[int] = None,
    limit: int = 5,
    owner_id: Optional[str] = None
) -> ToolResult[HousingSearchOutput]:
    """
    Searches rental or sale housing properties by county, price limit and bedroom count.
    Returns property listings with numeric prices, bedroom counts, and source URLs.
    Read-only.
    """
    input_data = HousingSearchInput(county=county, listing_type=listing_type, max_price=max_price, min_bedrooms=min_bedrooms, limit=limit)
    return await pulsehunter_client.search_housing(input_data, owner_id=owner_id)

async def pulsehunter_list_alerts(owner_id: Optional[str] = None) -> ToolResult:
    """Lists active job and housing tracking alerts in PulseHunter. Read-only."""
    return await pulsehunter_client.list_alerts(owner_id=owner_id)
