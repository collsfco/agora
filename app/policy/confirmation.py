import time
import uuid
import hashlib
import json
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class ActionTicket(BaseModel):
    action_id: str = Field(default_factory=lambda: f"act_{uuid.uuid4().hex[:8]}")
    tool: str
    arguments: Dict[str, Any]
    summary: str
    profile_id: str
    chat_id: int
    created_at: float = Field(default_factory=time.time)
    expires_at: float = Field(default_factory=lambda: time.time() + 300) # 5 min TTL
    args_hash: str = ""
    is_executed: bool = False

    def model_post_init(self, __context: Any) -> None:
        if not self.args_hash:
            canonical = json.dumps(self.arguments, sort_keys=True)
            self.args_hash = hashlib.sha256(canonical.encode()).hexdigest()[:12]

class ConfirmationManager:
    """Manages pending high-risk action tickets with TTL and idempotency."""
    def __init__(self):
        self._tickets: Dict[str, ActionTicket] = {}

    def create_ticket(
        self,
        tool: str,
        arguments: Dict[str, Any],
        summary: str,
        profile_id: str,
        chat_id: int,
        ttl_seconds: int = 300
    ) -> ActionTicket:
        ticket = ActionTicket(
            tool=tool,
            arguments=arguments,
            summary=summary,
            profile_id=profile_id,
            chat_id=chat_id,
            expires_at=time.time() + ttl_seconds
        )
        self._tickets[ticket.action_id] = ticket
        return ticket

    def validate_and_consume(self, action_id: str, profile_id: str) -> Optional[ActionTicket]:
        """
        Validates token existence, expiration, profile matching, and ensures single execution.
        """
        ticket = self._tickets.get(action_id)
        if not ticket:
            return None
        
        if ticket.is_executed:
            return None
        
        if time.time() > ticket.expires_at:
            del self._tickets[action_id]
            return None
        
        if ticket.profile_id != profile_id:
            return None
        
        # Mark as executed (idempotency guard)
        ticket.is_executed = True
        return ticket

confirmation_manager = ConfirmationManager()
