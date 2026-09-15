from typing import List, Dict, Any
from app.agents.loader import load_yaml_config

TOOL_REGISTRY = load_yaml_config("tool_registry.yaml").get("tools", {})

def get_allowed_tools_for_domain(
    domain: str,
    profile_id: str = "principal_a",
    include_write: bool = False
) -> List[str]:
    """
    Returns filtered list of tool names for a specific domain, profile and risk level.
    Ensures maximum 3-5 relevant tools are exposed to the model per turn.
    """
    allowed = []
    for tool_name, meta in TOOL_REGISTRY.items():
        tool_domain = meta.get("domain")
        allowed_profiles = meta.get("profiles", [])
        risk = meta.get("risk", "read")
        workers = meta.get("visibility", {}).get("workers", [])

        if (tool_domain == domain or domain in workers) and profile_id in allowed_profiles:
            if include_write or risk == "read":
                allowed.append(tool_name)
    return allowed

def get_tool_descriptions(tool_names: List[str]) -> str:
    """Formats markdown tool descriptions for prompt injection."""
    descriptions = []
    for name in TOOL_REGISTRY.keys():
        if name in tool_names:
            meta = TOOL_REGISTRY.get(name, {})
            desc = meta.get("description", "")
            risk = meta.get("risk", "read")
            confirm = meta.get("confirmation_required", False)
            confirm_str = " (Requires Confirmation Token)" if confirm else ""
            descriptions.append(f"- `{name}` [{risk.upper()}]{confirm_str}: {desc}")
    return "\n".join(descriptions)
