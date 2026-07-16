# syntax=docker/dockerfile:1
# Standalone multi-stage Dockerfile for Render deployment.
# The upstream build relies on a locally pre-built builder image; this file
# inlines both stages so Render can build from a clean git clone.

# ── builder ──────────────────────────────────────────────────────────────────
FROM docker.io/searxng/base:searxng-builder AS builder

COPY ./requirements.txt ./requirements-server.txt ./

ENV UV_NO_MANAGED_PYTHON="true" \
    UV_NATIVE_TLS="true"

ARG TIMESTAMP_VENV="0"

RUN --mount=type=cache,id=uv,target=/root/.cache/uv set -eux -o pipefail; \
    export SOURCE_DATE_EPOCH="$TIMESTAMP_VENV"; \
    uv venv; \
    uv pip install --requirements ./requirements.txt --requirements ./requirements-server.txt; \
    uv cache prune --ci; \
    find ./.venv/lib/ -type f -exec strip --strip-unneeded {} + || true; \
    find ./.venv/lib/ -type d -name "__pycache__" -exec rm -rf {} +; \
    find ./.venv/lib/ -type f -name "*.pyc" -delete; \
    python -m compileall -q -f -j 0 --invalidation-mode=unchecked-hash ./.venv/lib/; \
    find ./.venv/lib/python*/site-packages/*.dist-info/ -type f -name "RECORD" \
        -exec sort -t, -k1,1 -o {} {} \;; \
    find ./.venv/ -exec touch -h --date="@$TIMESTAMP_VENV" {} +

# version_frozen.py is generated externally (not available in a fresh clone),
# so we exclude it; the app falls back to runtime git introspection.
COPY --exclude=./searx/version_frozen.py ./searx/ ./searx/

RUN set -eux -o pipefail; \
    python -m compileall -q -f -j 0 --invalidation-mode=unchecked-hash ./searx/; \
    find ./searx/static/ -type f \
        \( -name "*.html" -o -name "*.css" -o -name "*.js" -o -name "*.svg" \) \
        -exec gzip -9 -k {} + \
        -exec brotli -9 -k {} + \
        -exec gzip --test {}.gz + \
        -exec brotli --test {}.br +

# ── dist ─────────────────────────────────────────────────────────────────────
FROM docker.io/searxng/base:searxng AS dist

COPY --chown=977:977 --from=builder /usr/local/searxng/.venv/ ./.venv/
COPY --chown=977:977 --from=builder /usr/local/searxng/searx/ ./searx/
COPY --chown=977:977 ./container/entrypoint.sh \
                      ./container/render-entrypoint.sh \
                      ./container/settings.template.yml \
                      ./

RUN chmod +x ./render-entrypoint.sh

ENV GRANIAN_PROCESS_NAME="searxng" \
    GRANIAN_INTERFACE="wsgi" \
    GRANIAN_HOST="::" \
    GRANIAN_PORT="8080" \
    GRANIAN_WEBSOCKETS="false" \
    GRANIAN_BLOCKING_THREADS="4" \
    GRANIAN_WORKERS_KILL_TIMEOUT="30s" \
    GRANIAN_BLOCKING_THREADS_IDLE_TIMEOUT="5m"

EXPOSE 8080

ENTRYPOINT ["/usr/local/searxng/render-entrypoint.sh"]
