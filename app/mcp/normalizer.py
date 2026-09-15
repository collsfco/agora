from datetime import datetime, timezone
from typing import Any, Dict, Optional, Literal
from pydantic import BaseModel, Field

class NormalizedToolResult(BaseModel):
    ok: bool = True
    source: str
    tool: str
    observed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    cache_status: Literal["miss", "hit", "bypassed"] = "miss"
    data: Dict[str, Any]
    warnings: list[str] = []
    error: Optional[str] = None

def build_normalized_response(
    source: str,
    tool: str,
    data: Dict[str, Any],
    ok: bool = True,
    cache_status: Literal["miss", "hit", "bypassed"] = "miss",
    error: Optional[str] = None
) -> Dict[str, Any]:
    """Helper to return clean serializable normalized response dictionary."""
    res = NormalizedToolResult(
        ok=ok,
        source=source,
        tool=tool,
        observed_at=datetime.now(timezone.utc).isoformat(),
        cache_status=cache_status,
        data=data,
        error=error
    )
    return res.model_dump()
