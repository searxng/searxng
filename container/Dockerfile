FROM ghcr.io/searxng/base:searxng-builder AS builder

COPY ./requirements.txt ./requirements.txt

RUN --mount=type=cache,id=pip,target=/root/.cache/pip python -m venv ./venv \
 && . ./venv/bin/activate \
 && pip install -r requirements.txt \
 && pip install "uwsgi~=2.0"

COPY ./searx/ ./searx/

ARG TIMESTAMP_SETTINGS="0"

RUN python -m compileall -q searx \
 && touch -c --date=@$TIMESTAMP_SETTINGS ./searx/settings.yml \
 && find ./searx/static \
    \( -name "*.html" -o -name "*.css" -o -name "*.js" -o -name "*.svg" -o -name "*.ttf" -o -name "*.eot" \) \
    -type f -exec gzip -9 -k {} + -exec brotli --best {} +

FROM ghcr.io/searxng/base:searxng AS dist

ARG LABEL_DATE="0001-01-01T00:00:00Z"
ARG GIT_URL="unspecified"
ARG SEARXNG_GIT_VERSION="unspecified"
ARG LABEL_VCS_REF="unspecified"
ARG LABEL_VCS_URL="unspecified"

COPY --chown=searxng:searxng --from=builder /usr/local/searxng/venv/ ./venv/
COPY --chown=searxng:searxng --from=builder /usr/local/searxng/searx/ ./searx/
COPY --chown=searxng:searxng ./container/config/ ./.template/
COPY --chown=searxng:searxng ./container/entrypoint.sh ./entrypoint.sh

ARG TIMESTAMP_UWSGI="0"

RUN touch -c --date=@$TIMESTAMP_UWSGI ./.template/uwsgi.ini

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

ENV SEARXNG_VERSION="$SEARXNG_GIT_VERSION" \
    INSTANCE_NAME="SearXNG" \
    AUTOCOMPLETE="" \
    BASE_URL="" \
    BIND_ADDRESS="[::]:8080" \
    SEARXNG_SETTINGS_PATH="$CONFIG_PATH/settings.yml" \
    UWSGI_SETTINGS_PATH="$CONFIG_PATH/uwsgi.ini" \
    UWSGI_WORKERS="%k" \
    UWSGI_THREADS="4"

VOLUME $CONFIG_PATH
VOLUME $DATA_PATH

EXPOSE 8080

HEALTHCHECK CMD wget --quiet --tries=1 --spider http://localhost:8080/healthz || exit 1

ENTRYPOINT ["/usr/local/searxng/entrypoint.sh"]
