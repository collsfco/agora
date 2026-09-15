from typing import Any, Literal, TypedDict, Optional
from langchain_core.messages import BaseMessage

Domain = Literal["homelab", "home", "workshop", "pulsehunter", "knowledge", "weather_web", "general"]
Risk = Literal["none", "read", "write", "destructive"]

class Evidence(TypedDict):
    source: str
    tool: str
    observed_at: str
    cache_status: Literal["miss", "hit", "bypassed"]
    data: dict[str, Any]

class PendingAction(TypedDict):
    action_id: str
    tool: str
    arguments: dict[str, Any]
    summary: str
    profile_id: str
    chat_id: int
    expires_at: str

class AgoraState(TypedDict, total=False):
    profile_id: Literal["principal_a", "principal_b"]
    chat_id: int
    thread_id: str
    user_message: str
    response_language: Literal["es", "en"]
    domain: Domain
    risk: Risk
    requires_fresh_data: bool
    allowed_tools: list[str]
    evidence: list[Evidence]
    tool_call_count: int
    pending_action: Optional[PendingAction]
    confirmed_action_id: Optional[str]
    final_answer: str
    messages: list[BaseMessage]
