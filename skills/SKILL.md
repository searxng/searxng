---
name: searxng
description: Web search using SearXNG meta search engine. Use this skill when the user wants to search the web, find information online, look up documentation, research topics, or get current information from the internet. Triggers include "search for", "look up", "find information about", "web search", "google", "search online", or any request requiring up-to-date information not available in the current context.
---

# SearXNG Web Search

Perform web searches using SearXNG, a privacy-respecting meta search engine.

## Prerequisites

A SearXNG server must be running and accessible.

To set up your own SearXNG server:
```bash
docker run -d --name searxng -p 8080:8080 searxng/searxng
```

## Configuration

Create a configuration file at `~/.config/searxng/config.json` or `./searxng.config.json`:

```json
{
  "baseUrl": "http://localhost:8080",
  "defaultEngine": "",
  "allowedEngines": [],
  "defaultLimit": 10,
  "useProxy": false,
  "proxyUrl": "",
  "timeout": 10000
}
```

Or use environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `SEARXNG_BASE_URL` | SearXNG server URL | `http://localhost:8080` |
| `SEARXNG_DEFAULT_ENGINE` | Default search engine | (none) |
| `SEARXNG_ALLOWED_ENGINES` | Comma-separated allowed engines | (all) |
| `SEARXNG_DEFAULT_LIMIT` | Default result limit | `10` |
| `SEARXNG_USE_PROXY` | Use proxy (`true`/`false`) | `false` |
| `SEARXNG_PROXY_URL` | Proxy URL | (none) |
| `SEARXNG_TIMEOUT` | Request timeout in ms | `10000` |

## CLI Reference

```
searxng <query> [options]
searxng --health
searxng --engines-list
searxng --categories-list

Options:
  -e, --engines <engines>      Comma-separated list of search engines
  -c, --categories <cats>      Comma-separated list of categories
  -l, --limit <n>              Maximum number of results (default: 10)
  -p, --page <n>               Page number for pagination
  --lang <code>                Language code (e.g., en, zh, ja)
  --time <range>               Time range: day, week, month, year, all
  -f, --format <fmt>           Output format: json, csv, html (default: json)
  --engines-list               List available search engines
  --categories-list            List available categories
  --health                     Check SearXNG server health
  -h, --help                   Show help message
```

## Examples

```bash
# Simple search
searxng "TypeScript tutorial"

# Limit results
searxng "TypeScript tutorial" --limit 5

# Use specific engines
searxng --engines google,github "react hooks"

# Search in specific categories
searxng --categories it,science "machine learning"

# Recent results only
searxng --time week "latest news"

# Specific language
searxng --lang zh "TypeScript"

# Output as CSV
searxng "docker tutorial" --format csv --limit 20 > results.csv
```

## Output Format

The CLI returns results in a standardized JSON envelope format:

```json
{
  "status": "ok",
  "data": {
    "query": "search query",
    "totalResults": 100,
    "returnedResults": 10,
    "results": [
      {
        "title": "Result Title",
        "url": "https://example.com",
        "content": "Snippet or description...",
        "engine": "google",
        "category": "general"
      }
    ],
    "suggestions": ["related query 1"],
    "answers": [],
    "unresponsiveEngines": []
  },
  "error": null,
  "hint": null
}
```

## Available Categories

- `general` - General web search
- `images` - Image search
- `videos` - Video search
- `news` - News articles
- `it` - IT/Technology
- `science` - Scientific content
- `music` - Music
- `files` - Files
- `books` - Books
- `q&a` - Q&A sites
- ...

## Available Engines

- General: `google`, `bing`, `duckduckgo`, `brave`, `startpage`
- Code: `github`, `gitlab`, `stackoverflow`, `npm`, `pypi`
- Academic: `arxiv`, `pubmed`, `google scholar`
- Knowledge: `wikipedia`, `wiktionary`
- Social: `reddit`, `hackernews`
- ...

List all available engines:
```bash
searxng --engines-list
```

## Health Check

```bash
searxng --health
```

## Error Handling

Always check the `status` field before using `data`:

```bash
result=$(searxng "query" 2>/dev/null)
status=$(echo "$result" | grep -o '"status": "[^"]*"' | cut -d'"' -f4)

if [ "$status" = "ok" ]; then
    echo "Search successful"
    echo "$result"
else
    echo "Search failed"
    echo "$result" | grep -o '"message": "[^"]*"' | cut -d'"' -f4
fi
```
