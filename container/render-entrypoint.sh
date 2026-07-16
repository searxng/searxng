#!/bin/sh
# Render injects PORT at runtime; map it to GRANIAN_PORT before starting SearXNG.
export GRANIAN_PORT="${PORT:-8080}"
exec /usr/local/searxng/entrypoint.sh
