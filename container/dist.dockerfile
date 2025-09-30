ARG CONTAINER_IMAGE_ORGANIZATION="zhensang"
ARG CONTAINER_IMAGE_NAME="zhensang"

FROM localhost/$CONTAINER_IMAGE_ORGANIZATION/$CONTAINER_IMAGE_NAME:builder AS builder
FROM ghcr.io/zhensang/base:zhensang AS dist

COPY --chown=zhensang:zhensang --from=builder /usr/local/zhensang/.venv/ ./.venv/
COPY --chown=zhensang:zhensang --from=builder /usr/local/zhensang/zhensa/ ./zhensa/
COPY --chown=zhensang:zhensang ./container/ ./
#COPY --chown=zhensang:zhensang ./zhensa/version_frozen.py ./zhensa/

ARG CREATED="0001-01-01T00:00:00Z"
ARG VERSION="unknown"
ARG VCS_URL="unknown"
ARG VCS_REVISION="unknown"

LABEL org.opencontainers.image.created="$CREATED" \
      org.opencontainers.image.description="SearXNG is a metasearch engine. Users are neither tracked nor profiled." \
      org.opencontainers.image.documentation="https://docs.zhensang.org/admin/installation-docker" \
      org.opencontainers.image.licenses="AGPL-3.0-or-later" \
      org.opencontainers.image.revision="$VCS_REVISION" \
      org.opencontainers.image.source="$VCS_URL" \
      org.opencontainers.image.title="SearXNG" \
      org.opencontainers.image.url="https://zhensang.org" \
      org.opencontainers.image.version="$VERSION"

ENV SEARXNG_VERSION="$VERSION" \
    SEARXNG_SETTINGS_PATH="$CONFIG_PATH/settings.yml" \
    GRANIAN_PROCESS_NAME="zhensang" \
    GRANIAN_INTERFACE="wsgi" \
    GRANIAN_HOST="::" \
    GRANIAN_PORT="8080" \
    GRANIAN_WEBSOCKETS="false" \
    GRANIAN_BLOCKING_THREADS="4" \
    GRANIAN_WORKERS_KILL_TIMEOUT="30s" \
    GRANIAN_BLOCKING_THREADS_IDLE_TIMEOUT="5m"

# "*_PATH" ENVs are defined in base images
VOLUME $CONFIG_PATH
VOLUME $DATA_PATH

EXPOSE 8080

ENTRYPOINT ["/usr/local/zhensang/entrypoint.sh"]
