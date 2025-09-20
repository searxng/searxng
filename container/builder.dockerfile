FROM ghcr.io/searxng/base:searxng-builder AS builder

ARG TIMESTAMP_VENV="0"

COPY ./requirements.txt ./requirements-server.txt ./

RUN --mount=type=cache,id=uv,target=/root/.cache/uv set -eux -o pipefail; \
    export SOURCE_DATE_EPOCH="$TIMESTAMP_VENV"; \
    uv venv; \
    uv pip install --no-managed-python --compile-bytecode --requirements ./requirements.txt --requirements ./requirements-server.txt; \
    uv cache prune --ci; \
    find ./.venv/lib/python*/site-packages/*.dist-info/ -type f -name "RECORD" -exec sort -t, -k1,1 -o {} {} \;; \
    find ./.venv/ -exec touch -h --date="@$TIMESTAMP_VENV" {} +; \
    unset SOURCE_DATE_EPOCH

# use "--exclude=./searx/version_frozen.py" when actions/runner-images updates to Podman 5.0+
COPY ./searx/ ./searx/

ARG TIMESTAMP_SETTINGS="0"

RUN set -eux -o pipefail; \
    python -m compileall -q ./searx/; \
    find ./searx/static/ -type f \
    \( -name "*.html" -o -name "*.css" -o -name "*.js" -o -name "*.svg" \) \
    -exec gzip -9 -k {} + \
    -exec brotli -9 -k {} + \
    -exec gzip --test {}.gz + \
    -exec brotli --test {}.br +; \
    touch -c --date="@$TIMESTAMP_SETTINGS" ./searx/settings.yml
