FROM python:3.13-slim AS builder

RUN mkdir /usr/local/searxng
WORKDIR /usr/local/searxng

RUN python3 -m venv /venv
ENV PATH=/venv/bin:$PATH

COPY requirements.txt ./requirements.txt

# Install build dependencies and Python packages
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpcre3-dev libxml2-dev libxslt1-dev zlib1g-dev 
RUN --mount=type=cache,target=/root/.cache/pip  pip install "uwsgi~=2.0.0"
RUN --mount=type=cache,target=/root/.cache/pip  pip install -r requirements.txt 

COPY dockerfiles ./dockerfiles
COPY searx ./searx

ARG TIMESTAMP_SETTINGS=0
ARG TIMESTAMP_UWSGI=0

RUN python3 -m compileall -q searx \
  && touch -c --date=@${TIMESTAMP_SETTINGS} searx/settings.yml \
  && touch -c --date=@${TIMESTAMP_UWSGI} dockerfiles/uwsgi.ini

# Final image stage
FROM python:3.13-slim

EXPOSE 8080

ARG SEARXNG_GID=977
ARG SEARXNG_UID=977

RUN groupadd -g ${SEARXNG_GID} searxng && \
  useradd -u ${SEARXNG_UID} -d /usr/local/searxng -s /bin/sh -g searxng searxng

ENV INSTANCE_NAME=searxng \
  AUTOCOMPLETE= \
  BASE_URL= \
  MORTY_KEY= \
  MORTY_URL= \
  SEARXNG_SETTINGS_PATH=/etc/searxng/settings.yml \
  UWSGI_SETTINGS_PATH=/etc/searxng/uwsgi.ini \
  UWSGI_WORKERS=%k \
  UWSGI_THREADS=4

WORKDIR /usr/local/searxng

# Install necessary runtime packages
RUN apt-get update && apt-get install -y --no-install-recommends \
  brotli \
  mailcap \
  libxml2 \
  libxslt1.1 \
  libpcre3 && \
  rm -rf /var/lib/apt/lists/*

# Copy only the necessary files from the builder stage
COPY --from=builder --chown=searxng:searxng /usr/local/searxng /usr/local/searxng
COPY --from=builder --chown=searxng:searxng /venv /venv

RUN mkdir /etc/searxng && chown searxng:searxng /etc/searxng

ENV PATH=/venv/bin:$PATH

USER searxng

RUN find /usr/local/searxng/searx/static \( -name '*.html' -o -name '*.css' -o -name '*.js' \
  -o -name '*.svg' -o -name '*.ttf' -o -name '*.eot' \) \
  -type f -exec gzip -9 -k {} + -exec brotli --best {} +

# Keep these arguments at the end to prevent redundant layer rebuilds
ARG LABEL_DATE=
ARG GIT_URL=unknown
ARG SEARXNG_GIT_VERSION=unknown
ARG SEARXNG_DOCKER_TAG=unknown
ARG LABEL_VCS_REF=
ARG LABEL_VCS_URL=
LABEL maintainer="searxng <${GIT_URL}>" \
    description="A privacy-respecting, hackable metasearch engine." \
    version="${SEARXNG_GIT_VERSION}" \
    org.label-schema.schema-version="1.0" \
    org.label-schema.name="searxng" \
    org.label-schema.version="${SEARXNG_GIT_VERSION}" \
    org.label-schema.url="${LABEL_VCS_URL}" \
    org.label-schema.vcs-ref=${LABEL_VCS_REF} \
    org.label-schema.vcs-url=${LABEL_VCS_URL} \
    org.label-schema.build-date="${LABEL_DATE}" \
    org.label-schema.usage="https://github.com/searxng/searxng-docker" \
    org.opencontainers.image.title="searxng" \
    org.opencontainers.image.version="${SEARXNG_DOCKER_TAG}" \
    org.opencontainers.image.url="${LABEL_VCS_URL}" \
    org.opencontainers.image.revision=${LABEL_VCS_REF} \
    org.opencontainers.image.source=${LABEL_VCS_URL} \
    org.opencontainers.image.created="${LABEL_DATE}" \
    org.opencontainers.image.documentation="https://github.com/searxng/searxng-docker"
    
ENTRYPOINT ["/usr/local/searxng/dockerfiles/docker-entrypoint.sh"]
