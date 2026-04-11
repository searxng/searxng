# SearXNG CLI

A command-line interface for searching with SearXNG, a privacy-respecting meta search engine.

## Installation

```bash
npm install -g searxng-cli
# or
pnpm add -g searxng-cli
# or
yarn global add searxng-cli
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
searxng "your search query"
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
searxng "TypeScript tutorial"

# Limit results
searxng "TypeScript tutorial" --limit 5

# Use specific engines
searxng --engines google,github "react hooks"

# Search in specific categories
searxng --categories it,science "machine learning"

# Recent results only
searxng --time week "latest news"

# Output as CSV
searxng "docker tutorial" --format csv > results.csv

# Check server health
searxng --health

# List available engines
searxng --engines-list

# List available categories
searxng --categories-list
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
