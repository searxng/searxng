FROM ghcr.io/searxng/base:searxng-builder AS builder

COPY ./requirements*.txt ./

RUN --mount=type=cache,id=pip,target=/root/.cache/pip set -eux; \
    python -m venv ./.venv/; \
    . ./.venv/bin/activate; \
    pip install -r ./requirements.txt -r ./requirements-server.txt

COPY ./searx/ ./searx/

ARG TIMESTAMP_SETTINGS="0"

RUN set -eux; \
    python -m compileall -q ./searx/; \
    touch -c --date=@$TIMESTAMP_SETTINGS ./searx/settings.yml; \
    find ./searx/static/ -type f \
        \( -name "*.html" -o -name "*.css" -o -name "*.js" -o -name "*.svg" \) \
        -exec gzip -9 -k {} + \
        -exec brotli -9 -k {} + \
        -exec gzip --test {}.gz + \
        -exec brotli --test {}.br +; \
    # Move always changing files to /usr/local/searxng/
    mv ./searx/version_frozen.py ./
