FROM python:3.13-alpine
EXPOSE 8080
VOLUME /etc/searxng

ARG SEARXNG_GID=977
ARG SEARXNG_UID=977

RUN addgroup -g ${SEARXNG_GID} searxng && \
    adduser -u ${SEARXNG_UID} -D -h /usr/local/searxng -s /bin/sh -G searxng searxng

ENV INSTANCE_NAME=searxng \
    AUTOCOMPLETE= \
    BASE_URL= \
    SEARXNG_SETTINGS_PATH=/etc/searxng/settings.yml \
    UWSGI_SETTINGS_PATH=/etc/searxng/uwsgi.ini \
    UWSGI_WORKERS=%k \
    UWSGI_THREADS=4

WORKDIR /usr/local/searxng

# install necessary runtime packages
RUN apk add --no-cache brotli openssl mailcap libxml2 libxslt pcre && rm -rf /root/.cache

COPY requirements.txt ./requirements.txt

# build and install uwsgi and necessary python packages
RUN apk add --no-cache -t build-dependencies build-base libffi-dev libxml2-dev libxslt-dev pcre-dev \
&& pip install --no-cache "uwsgi~=2.0.0" \
&& pip install --no-cache -r requirements.txt \
&& apk del build-dependencies \
&& rm -rf /root/.cache

COPY --chown=searxng:searxng dockerfiles ./dockerfiles
COPY --chown=searxng:searxng searx ./searx

ARG TIMESTAMP_SETTINGS=0
ARG TIMESTAMP_UWSGI=0
ARG VERSION_GITCOMMIT=unknown

RUN su searxng -c "/usr/local/bin/python3 -m compileall -q searx" \
 && touch -c --date=@${TIMESTAMP_SETTINGS} searx/settings.yml \
 && touch -c --date=@${TIMESTAMP_UWSGI} dockerfiles/uwsgi.ini \
 && find /usr/local/searxng/searx/static -a \( -name '*.html' -o -name '*.css' -o -name '*.js' \
    -o -name '*.svg' -o -name '*.ttf' -o -name '*.eot' \) \
    -type f -exec gzip -9 -k {} \+ -exec brotli --best {} \+

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
