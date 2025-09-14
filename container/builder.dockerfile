FROM ghcr.io/searxng/base:searxng-builder AS builder

COPY ./requirements*.txt ./

ARG TIMESTAMP="0"

RUN --mount=type=cache,id=uv,target=/root/.cache/uv set -eux; \
    uv venv; \
    uv pip install --no-managed-python --compile-bytecode --requirements ./requirements.txt --requirements ./requirements-server.txt; \
    uv cache prune --ci; \
    find ./.venv/ -exec touch -h -t $TIMESTAMP {} +

COPY ./searx/ ./searx/

ARG TIMESTAMP_SETTINGS="0"

RUN set -eux; \
    python -m compileall -q ./searx/; \
    touch -c -t $TIMESTAMP_SETTINGS ./searx/settings.yml; \
    find ./searx/static/ -type f \
    \( -name "*.html" -o -name "*.css" -o -name "*.js" -o -name "*.svg" \) \
    -exec gzip -9 -k {} + \
    -exec brotli -9 -k {} + \
    -exec gzip --test {}.gz + \
    -exec brotli --test {}.br +; \
    # Move always changing files to /usr/local/searxng/
    mv ./searx/version_frozen.py ./
