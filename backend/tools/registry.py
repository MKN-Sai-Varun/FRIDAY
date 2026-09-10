"""
Central policy engine for all tool calls FRIDAY can make.

No tool should ever be called directly from anywhere else in the codebase.
Every tool call must go through execute_tool(), which checks the
permission tier BEFORE the underlying function is ever invoked.

Tiers:
    always     - runs immediately, no restrictions (read-only, harmless)
    workspace  - runs immediately, but the tool itself must enforce that
                 any path stays inside WORKSPACE_ROOT
    confirm    - does NOT run immediately. Returns a "pending" result
                 instead, which the frontend must explicitly approve
                 before execute_tool runs it for real.
    forbidden  - never runs, under any circumstances.
"""

# Stores pending confirmations, keyed by a unique confirmation id.
# Structure: { confirmation_id: {"name": str, "args": dict, "session_id": str} }
pending_confirmations: dict[str, dict] = {}

# The actual registry. Each entry maps a tool name to its tier and its handler function.
# No real tools yet today - we register one fake/stub tool to prove the logic works.
TOOL_REGISTRY: dict[str, dict] = {}


def register_tool(name: str, tier: str, handler):
    """
    Adds a tool to the registry. Called once per tool, at import time,
    from wherever that tool is actually defined.
    """
    valid_tiers = {"always", "workspace", "confirm", "forbidden"}
    if tier not in valid_tiers:
        raise ValueError(f"Invalid tier '{tier}' for tool '{name}'. Must be one of {valid_tiers}.")

    TOOL_REGISTRY[name] = {"tier": tier, "handler": handler}


def execute_tool(name: str, args: dict, session_id: str) -> dict:
    """
    The single entrypoint for running any tool. Everything else in the
    codebase must call this instead of calling a tool function directly.

    Returns a dict describing what happened:
        {"status": "success", "result": ...}
        {"status": "error", "message": ...}
        {"status": "pending_confirmation", "confirmation_id": ...}
        {"status": "refused", "message": ...}
    """
    if name not in TOOL_REGISTRY:
        return {"status": "error", "message": f"Unknown tool: '{name}'"}

    entry = TOOL_REGISTRY[name]
    tier = entry["tier"]
    handler = entry["handler"]

    if tier == "forbidden":
        return {"status": "refused", "message": f"Tool '{name}' is forbidden and cannot be run."}

    if tier == "confirm":
        import uuid
        confirmation_id = str(uuid.uuid4())
        pending_confirmations[confirmation_id] = {
            "name": name,
            "args": args,
            "session_id": session_id,
        }
        return {
            "status": "pending_confirmation",
            "confirmation_id": confirmation_id,
            "message": f"Tool '{name}' requires confirmation before running.",
        }

    # tier is "always" or "workspace" - run it now.
    try:
        result = handler(**args)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def confirm_pending(confirmation_id: str, approved: bool) -> dict:
    """
    Called when the user approves or denies a pending confirmation.
    If approved, actually runs the tool now. If denied, discards it.
    """
    if confirmation_id not in pending_confirmations:
        return {"status": "error", "message": "No such pending confirmation, or it already expired."}

    pending = pending_confirmations.pop(confirmation_id)

    if not approved:
        return {"status": "denied", "message": f"Tool '{pending['name']}' was denied by the user."}

    entry = TOOL_REGISTRY.get(pending["name"])
    if entry is None:
        return {"status": "error", "message": f"Tool '{pending['name']}' no longer exists."}

    try:
        result = entry["handler"](**pending["args"])
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}