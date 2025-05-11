FROM cgr.dev/chainguard/wolfi-base:latest AS builder

RUN apk add --no-cache \
    build-base \
    python-3.13-dev \
    py3-pip \
    brotli

WORKDIR /usr/local/searxng/

COPY ./requirements.txt ./requirements.txt

RUN --mount=type=cache,id=pip,target=/root/.cache/pip python -m venv ./venv \
 && . ./venv/bin/activate \
 && pip install -r requirements.txt \
 && pip install "uwsgi~=2.0"

COPY ./searx/ ./searx/

ARG TIMESTAMP_SETTINGS="0"
ARG TIMESTAMP_UWSGI="0"

RUN python -m compileall -q searx \
 && touch -c --date=@$TIMESTAMP_SETTINGS ./searx/settings.yml \
 && touch -c --date=@$TIMESTAMP_UWSGI ./container/uwsgi.ini \
 && find /usr/local/searxng/searx/static \
    \( -name "*.html" -o -name "*.css" -o -name "*.js" -o -name "*.svg" -o -name "*.ttf" -o -name "*.eot" \) \
    -type f -exec gzip -9 -k {} + -exec brotli --best {} +

ARG SEARXNG_UID="977"
ARG SEARXNG_GID="977"

RUN echo "root:x:0:root" >/tmp/.group \
 && echo "root:x:0:0:root:/usr/local/searxng:/bin/ash" >/tmp/.passwd \
 && echo "searxng:x:$SEARXNG_GID:searxng" >>/tmp/.group \
 && echo "searxng:x:$SEARXNG_UID:$SEARXNG_GID:searxng:/usr/local/searxng:/bin/ash" >>/tmp/.passwd

FROM scratch AS dist

# Prepare base image
COPY --from=builder /tmp/.passwd /etc/passwd
COPY --from=builder /tmp/.group /etc/group
COPY --chown=root:root --from=cgr.dev/chainguard/wolfi-base:latest / /
COPY --chown=root:root --from=builder /tmp/.passwd /etc/passwd
COPY --chown=root:root --from=builder /tmp/.group /etc/group
RUN rm -rf /root/ /home/

RUN apk add --no-cache \
    python-3.13 \
    # healthcheck
    wget \
    # uwsgi
    mailcap

ARG LABEL_DATE="0001-01-01T00:00:00Z"
ARG GIT_URL="unspecified"
ARG SEARXNG_GIT_VERSION="unspecified"
ARG LABEL_VCS_REF="unspecified"
ARG LABEL_VCS_URL="unspecified"

WORKDIR /usr/local/searxng/

COPY --chown=searxng:searxng --from=builder /usr/local/searxng/venv/ ./venv/
COPY --chown=searxng:searxng --from=builder /usr/local/searxng/searx/ ./searx/
COPY --chown=searxng:searxng ./container/ ./container/

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

# Image specific environment variables
ENV PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    SSL_CERT_FILE="/etc/ssl/certs/ca-certificates.crt" \
    HISTFILE="/dev/null" \
    CONFIG_PATH="/etc/searxng" \
    DATA_PATH="/var/cache/searxng"

# SearXNG specific environment variables
ENV SEARXNG_VERSION="$SEARXNG_GIT_VERSION" \
    INSTANCE_NAME="searxng" \
    AUTOCOMPLETE="" \
    BASE_URL="" \
    BIND_ADDRESS="[::]:8080" \
    SEARXNG_SETTINGS_PATH="$CONFIG_PATH/settings.yml" \
    UWSGI_SETTINGS_PATH="$CONFIG_PATH/uwsgi.ini" \
    UWSGI_WORKERS="%k" \
    UWSGI_THREADS="4"

# Volume ownership
RUN mkdir -p $CONFIG_PATH $DATA_PATH \
 && chown -R searxng:searxng $CONFIG_PATH $DATA_PATH

VOLUME $CONFIG_PATH
VOLUME $DATA_PATH

EXPOSE 8080

HEALTHCHECK CMD wget --quiet --tries=1 --spider http://localhost:8080/healthz || exit 1

ENTRYPOINT ["/usr/local/searxng/container/docker-entrypoint.sh"]
