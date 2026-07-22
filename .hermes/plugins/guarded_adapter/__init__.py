"""guarded_adapter plugin — Scope enforcement adapter for ADT governance.

Provides two tools:
  - guarded_write: Write files within authorized scope only
  - guarded_repo_actions: Git/GitHub actions within authorized scope only

Both tools validate through gate.py before execution, ensuring:
  - No repository/base/branch drift
  - Action type is authorized
  - Path is within plan.write_scope and authorized_write_scope
  - Authorization binding is valid
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def register(ctx: Any) -> None:
    """Register the guarded_adapter tools with the Hermes plugin system.

    Args:
        ctx: PluginContext from hermes_cli.plugins.
    """
    from .tools.guarded_write import (
        GUARDED_WRITE_SCHEMA,
        guarded_write_handler,
    )
    from .tools.guarded_repo_actions import (
        GUARDED_REPO_ACTIONS_SCHEMA,
        guarded_repo_actions_handler,
    )

    # Register guarded_write tool
    ctx.register_tool(
        name="guarded_write",
        toolset="guarded_adapter",
        schema=GUARDED_WRITE_SCHEMA,
        handler=guarded_write_handler,
        description=(
            "Write content to a file within the authorized write scope. "
            "Validates through the ADT scope enforcement gate before writing. "
            "Returns BLOCKED with ATTEMPTED_SCOPE_VIOLATION if the path is "
            "outside authorized scope."
        ),
        emoji="🔒",
    )

    # Register guarded_repo_actions tool
    ctx.register_tool(
        name="guarded_repo_actions",
        toolset="guarded_adapter",
        schema=GUARDED_REPO_ACTIONS_SCHEMA,
        handler=guarded_repo_actions_handler,
        description=(
            "Perform repository actions within authorized scope. Actions: "
            "git_add_authorized_paths, git_commit, git_push_authorized_branch, "
            "create_draft_pr, read_repository_state. No free command strings. "
            "All commands are structurally built — no shell injection possible."
        ),
        emoji="🛡️",
    )

    logger.info("guarded_adapter plugin registered: guarded_write, guarded_repo_actions")
