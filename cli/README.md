# SearXNG CLI

A command-line interface for searching with SearXNG, a privacy-respecting meta search engine.

## Installation

```bash
npm install -g sxng-cli
# or
pnpm add -g sxng-cli
# or
yarn global add sxng-cli
```

## Quick Start

1. Set up a SearXNG server:
```bash
docker run -d --name searxng -p 8080:8080 searxng/searxng
```

2. Create a configuration file:
```bash
cp searxng.config.example.json searxng.config.json
# Edit the file with your settings
```

3. Run a search:
```bash
sxng "your search query"
```

## Configuration

Configuration can be provided via:
1. Environment variables (highest priority)
2. Config file: `./searxng.config.json`
3. Default values (lowest priority)

See `searxng.config.example.json` for an example configuration.

## Usage

```bash
# Simple search
sxng "TypeScript tutorial"

# Limit results
sxng "TypeScript tutorial" --limit 5

# Use specific engines
sxng --engines google,github "react hooks"

# Search in specific categories
sxng --categories it,science "machine learning"

# Recent results only
sxng --time week "latest news"

# Output as CSV
sxng "docker tutorial" --format csv > results.csv

# Check server health
sxng --health

# List available engines
sxng --engines-list

# List available categories
sxng --categories-list
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SEARXNG_BASE_URL` | SearXNG server URL | `http://localhost:8080` |
| `SEARXNG_DEFAULT_LIMIT` | Default result limit | `10` |
| `SEARXNG_TIMEOUT` | Request timeout in ms | `10000` |
| `SEARXNG_USE_PROXY` | Use proxy (`true`/`false`) | `false` |
| `SEARXNG_PROXY_URL` | Proxy URL | (none) |

## License

MIT
