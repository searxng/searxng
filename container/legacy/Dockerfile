FROM docker.io/library/python:3.13-slim AS builder

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    build-essential \
    brotli \
    # lxml
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/local/searxng/

COPY ./requirements.txt ./requirements.txt

RUN --mount=type=cache,id=pip,target=/root/.cache/pip python -m venv ./venv \
 && . ./venv/bin/activate \
 && pip install -r requirements.txt \
 && pip install "granian~=2.0"

COPY ./searx/ ./searx/

ARG TIMESTAMP_SETTINGS="0"

RUN python -m compileall -q searx \
 && touch -c --date=@$TIMESTAMP_SETTINGS ./searx/settings.yml \
 && find ./searx/static \
    \( -name '*.html' -o -name '*.css' -o -name '*.js' -o -name '*.svg' -o -name '*.ttf' -o -name '*.eot' \) \
    -type f -exec gzip -9 -k {} + -exec brotli --best {} +

ARG SEARXNG_UID=977
ARG SEARXNG_GID=977

RUN grep -m1 root /etc/group > /tmp/.searxng.group \
 && grep -m1 root /etc/passwd > /tmp/.searxng.passwd \
 && echo "searxng:x:$SEARXNG_GID:" >> /tmp/.searxng.group \
 && echo "searxng:x:$SEARXNG_UID:$SEARXNG_GID:searxng:/usr/local/searxng:/bin/bash" >> /tmp/.searxng.passwd

FROM docker.io/library/python:3.13-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    # healthcheck
    wget \
    # lxml (ARMv7)
    libxslt1.1 \
 && rm -rf /var/lib/apt/lists/*

COPY --chown=root:root --from=builder /tmp/.searxng.passwd /etc/passwd
COPY --chown=root:root --from=builder /tmp/.searxng.group /etc/group

ARG LABEL_DATE="0001-01-01T00:00:00Z"
ARG GIT_URL="unspecified"
ARG SEARXNG_GIT_VERSION="unspecified"
ARG LABEL_VCS_REF="unspecified"
ARG LABEL_VCS_URL="unspecified"

WORKDIR /usr/local/searxng/

COPY --chown=searxng:searxng --from=builder /usr/local/searxng/venv/ ./venv/
COPY --chown=searxng:searxng --from=builder /usr/local/searxng/searx/ ./searx/
COPY --chown=searxng:searxng ./container/entrypoint.sh ./entrypoint.sh

LABEL org.opencontainers.image.authors="searxng <$GIT_URL>" \
      org.opencontainers.image.created="$LABEL_DATE" \
      org.opencontainers.image.description="A privacy-respecting, hackable metasearch engine" \
      org.opencontainers.image.documentation="https://github.com/searxng/searxng-docker" \
      org.opencontainers.image.licenses="AGPL-3.0-or-later" \
      org.opencontainers.image.revision="$LABEL_VCS_REF" \
      org.opencontainers.image.source="$LABEL_VCS_URL" \
      org.opencontainers.image.title="searxng" \
      org.opencontainers.image.url="$LABEL_VCS_URL" \
      org.opencontainers.image.version="$SEARXNG_GIT_VERSION"

ENV CONFIG_PATH="/etc/searxng" \
    DATA_PATH="/var/cache/searxng"

ENV SEARXNG_VERSION="$SEARXNG_GIT_VERSION" \
    INSTANCE_NAME="SearXNG" \
    AUTOCOMPLETE="" \
    BASE_URL="" \
    SEARXNG_SETTINGS_PATH="$CONFIG_PATH/settings.yml" \
    GRANIAN_PROCESS_NAME="searxng" \
    GRANIAN_INTERFACE="wsgi" \
    GRANIAN_HOST="::" \
    GRANIAN_PORT="8080" \
    # https://github.com/emmett-framework/granian/issues/568
    GRANIAN_HTTP1_KEEP_ALIVE="false" \
    GRANIAN_WEBSOCKETS="false" \
    GRANIAN_LOOP="uvloop" \
    GRANIAN_RUNTIME_MODE="mt" \
    GRANIAN_BLOCKING_THREADS="3" \
    GRANIAN_RUNTIME_THREADS="2" \
    GRANIAN_RESPAWN_INTERVAL="0" \
    GRANIAN_WORKERS_KILL_TIMEOUT="30" \
    GRANIAN_BACKPRESSURE="100" \
    GRANIAN_STATIC_PATH_MOUNT="/usr/local/searxng/searx/static/" \
    GRANIAN_STATIC_PATH_EXPIRES="3600"

VOLUME $CONFIG_PATH
VOLUME $DATA_PATH

EXPOSE 8080

HEALTHCHECK CMD wget --quiet --tries=1 --spider http://localhost:8080/healthz || exit 1

ENTRYPOINT ["/usr/local/searxng/entrypoint.sh"]
