"""SearXNG plugin — register entry point."""

import logging
import shutil
from pathlib import Path

from . import schemas
from . import tools

logger = logging.getLogger(__name__)


def _install_skill() -> None:
    """Copy our skill to ~/.hermes/skills/ on first load."""
    try:
        from hermes_cli.config import get_hermes_home

        dest = get_hermes_home() / "skills" / "searxng-search" / "SKILL.md"
    except Exception:
        dest = Path.home() / ".hermes" / "skills" / "searxng-search" / "SKILL.md"

    if dest.exists():
        return

    source = Path(__file__).parent / "skill" / "SKILL.md"
    if source.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)


def register(ctx):
    """Register all tools and hooks with the plugin context."""
    ctx.register_tool(
        name=schemas.SEARXNG_SEARCH_SCHEMA["name"],
        toolset="searxng_search",
        schema=schemas.SEARXNG_SEARCH_SCHEMA,
        handler=tools.searxng_search_handler,
    )

    _install_skill()
