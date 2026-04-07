---
name: searxng-search
description: Search the web using SearXNG and extract web page content natively
author: Your Name
version: 0.1.0
tags:
  - search
  - web
  - searxng
  - extraction
requires_tools:
  - searxng_search
  - native_extract
provides_commands:
  - /searxng-search
---

# SearXNG Search Skill

## When to Use

Use this skill when the user asks to search the web and a SearXNG instance is
configured (via the `SEARXNG_URL` environment variable). SearXNG is a
privacy-respecting, self-hosted metasearch engine that aggregates results from
multiple search engines without tracking.

Also use the `native_extract` tool when you need to fetch and extract content
from specific URLs without relying on third-party extraction APIs.

## Procedure

### Searching with SearXNG

1. Call `searxng_search` with a `query` string.
2. Optionally set `limit` (1–20, default 5) to control result count.
3. Parse the returned JSON. Results are in `data.web` as an array of:
   - `title` — Page title
   - `url` — Page URL
   - `description` — Snippet/content summary
   - `position` — 1-based ranking position
4. If the tool returns `"success": false`, inform the user that SearXNG is not
   configured and suggest setting `SEARXNG_URL`.

### Extracting Web Pages

1. Call `native_extract` with a `urls` array (max 5 URLs).
2. Parse the returned JSON. Each entry contains:
   - `url` — The requested URL
   - `title` — Page title (may be empty)
   - `content` — Extracted content as markdown
   - `error` — `null` on success, error message on failure
3. If `html-to-markdown` is not installed, a basic HTML tag stripping fallback
   is used. Results may be less clean.

## Configuration

The plugin requires the `SEARXNG_URL` environment variable to be set. The URL
should include a `%s` placeholder for the search query:

```
SEARXNG_URL=https://searx.example.com/search?q=%s
```

Optional authentication via Bearer token:

```
SEARXNG_API_KEY=your-api-key
```

## Pitfalls

- **Missing SEARXNG_URL**: The `searxng_search` tool will return an error if
  the environment variable is not set. Check `"success": false` in the response.
- **URL template format**: The URL must contain `%s` as the query placeholder.
  Without it, the query will not be substituted correctly.
- **Rate limits**: SearXNG instances may have rate limits. Use reasonable
  `limit` values.
- **SSL errors**: The `native_extract` tool may fail with SSL errors on some
  Python configurations. The error message will indicate this.
- **HTML-to-markdown**: Without the `html-to-markdown` package, extracted
  content uses a crude regex fallback. Install it for cleaner results.
- **Max URLs**: `native_extract` silently caps at 5 URLs.

## Verification

To verify the plugin is working:

1. Set `SEARXNG_URL` to a valid SearXNG instance URL with `%s` placeholder.
2. Run Hermes and confirm `searxng_search` and `native_extract` appear in the
   available tools list.
3. Trigger a search query and confirm results are returned with title, URL,
   and description fields.
