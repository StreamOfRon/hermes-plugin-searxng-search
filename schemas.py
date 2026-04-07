"""Tool schema definitions for the SearXNG plugin."""

SEARXNG_SEARCH_SCHEMA = {
    "name": "searxng_search",
    "description": (
        "Search the web using a SearXNG instance. SearXNG is a free, "
        "self-hosted metasearch engine that aggregates results from multiple "
        "search engines. Configure via SEARXNG_URL environment variable."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to look up",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return (default: 5)",
                "default": 5,
                "minimum": 1,
                "maximum": 20,
            },
        },
        "required": ["query"],
    },
}
