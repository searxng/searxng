#!/bin/sh
# Render injects PORT at runtime; map it to GRANIAN_PORT before starting SearXNG.
export GRANIAN_PORT="${PORT:-8080}"

# Trust all upstream IPs for X-Forwarded-For so SearXNG sees the real client IP
# (Render's edge network terminates TLS and forwards via private IPs).
export GRANIAN_FORWARDED_ALLOW_IPS="${GRANIAN_FORWARDED_ALLOW_IPS:-*}"

# Copy limiter.toml template if not already present in the config directory.
_cfg="${__SEARXNG_CONFIG_PATH:-/etc/searxng}"
if [ ! -f "${_cfg}/limiter.toml" ]; then
    cp -f /usr/local/searxng/limiter.toml "${_cfg}/limiter.toml" 2>/dev/null || true
fi

exec /usr/local/searxng/entrypoint.sh
