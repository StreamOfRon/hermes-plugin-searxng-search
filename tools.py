"""Tool handler implementations for the SearXNG plugin.

Each handler follows the contract:
    def handler(args: dict, **kwargs) -> str

- `args` is a dict of parsed input parameters
- Must return a JSON-encoded string (use json.dumps)
- Must not raise exceptions; catch and return error JSON instead
- Accept **kwargs for forward compatibility
"""

import json
import logging
import os
import urllib.parse

import httpx

logger = logging.getLogger(__name__)


def searxng_search_handler(args: dict, **kwargs) -> str:
    """Search using a SearXNG instance.

    SearXNG is a free, self-hosted metasearch engine. This implementation
    supports both public and authenticated instances.

    Args:
        args: Dict with 'query' (str) and optional 'limit' (int, default 5).
        **kwargs: Additional context (e.g., plugin context, logger).

    Returns:
        JSON string containing search results in standard format.
    """
    try:
        query = args.get("query", "")
        limit = args.get("limit", 5)

        url_template = os.getenv("SEARXNG_URL", "").strip()
        if not url_template:
            return json.dumps({
                "success": False,
                "error": (
                    "SearXNG backend selected but no URL configured. "
                    "Set SEARXNG_URL env var."
                ),
            })

        search_url = url_template.replace("%s", urllib.parse.quote_plus(query))

        headers = {"Accept": "application/json"}
        api_key = os.getenv("SEARXNG_API_KEY", "").strip()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        with httpx.Client(timeout=30.0) as client:
            resp = client.get(search_url, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        results = data.get("results", [])[:limit]
        normalized = [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "description": r.get("content", ""),
                "position": i + 1,
            }
            for i, r in enumerate(results)
        ]
        return json.dumps(
            {"success": True, "data": {"web": normalized}}, ensure_ascii=False
        )

    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
