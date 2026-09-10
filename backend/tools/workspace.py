"""
Workspace-scoped file tools.

Every function here MUST validate that the resolved path stays inside
WORKSPACE_ROOT before doing anything with it. This is the sandbox boundary -
nothing in this file should ever be able to read, write, or list anything
outside backend/config.py's WORKSPACE_ROOT, no matter what path is requested.
"""

import os
from backend.config import WORKSPACE_ROOT


def _resolve_safe_path(relative_path: str) -> str:
    """
    Resolves a user-supplied relative path against WORKSPACE_ROOT and
    verifies the result is still inside WORKSPACE_ROOT.

    Raises PermissionError if the path would escape the workspace.
    Returns the safe, absolute path if it's valid.
    """
    # Join first, then resolve fully (this collapses any ".." segments,
    # symlinks, etc. into the real final destination).
    candidate = os.path.join(WORKSPACE_ROOT, relative_path)
    resolved = os.path.realpath(candidate)

    # os.path.realpath(WORKSPACE_ROOT) ensures we compare against the
    # same fully-resolved form, in case WORKSPACE_ROOT itself contains
    # symlinks (unlikely here, but cheap to be correct about).
    safe_root = os.path.realpath(WORKSPACE_ROOT)

    if not resolved.startswith(safe_root):
        raise PermissionError(
            f"Path '{relative_path}' resolves outside the workspace and is not allowed."
        )

    return resolved


def list_workspace(subpath: str = "") -> list[str]:
    """Lists files and folders inside the workspace, optionally within a subfolder."""
    target = _resolve_safe_path(subpath)

    if not os.path.isdir(target):
        raise FileNotFoundError(f"'{subpath}' is not a directory in the workspace.")

    return os.listdir(target)


def read_file(path: str) -> str:
    """Reads and returns the full text content of a file inside the workspace."""
    target = _resolve_safe_path(path)

    if not os.path.isfile(target):
        raise FileNotFoundError(f"'{path}' does not exist in the workspace.")

    with open(target, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path: str, content: str) -> str:
    """Creates or overwrites a file inside the workspace with the given content."""
    target = _resolve_safe_path(path)

    # Ensure parent directories exist (e.g. writing to "notes/new/file.txt"
    # when "new/" doesn't exist yet).
    os.makedirs(os.path.dirname(target), exist_ok=True)

    with open(target, "w", encoding="utf-8") as f:
        f.write(content)

    return f"Wrote {len(content)} characters to '{path}'."


def append_file(path: str, content: str) -> str:
    """Appends content to an existing file inside the workspace (creates it if missing)."""
    target = _resolve_safe_path(path)

    os.makedirs(os.path.dirname(target), exist_ok=True)

    with open(target, "a", encoding="utf-8") as f:
        f.write(content)

    return f"Appended {len(content)} characters to '{path}'."