# Use the Debian bookworm base image
ARG DEBIAN_CODENAME="bookworm"
FROM mcr.microsoft.com/devcontainers/base:$DEBIAN_CODENAME

# Set up the Debian sources list
RUN cat <<EOF > /etc/apt/sources.list.d/debian.sources
Types: deb
URIs: http://deb.debian.org/debian
Suites: $DEBIAN_CODENAME $DEBIAN_CODENAME-updates $DEBIAN_CODENAME-backports
Components: main
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg

Types: deb
URIs: http://security.debian.org/debian-security
Suites: $DEBIAN_CODENAME-security
Components: main
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
EOF

# Update and install necessary packages
RUN apt-get update && \
    apt-get -y install python3 python3-venv valkey-server firefox-esr graphviz imagemagick librsvg2-bin fonts-dejavu shellcheck && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set environment variables for SearXNG
ENV SEARXNG_SECRET="${SEARXNG_SECRET}" \
    SEARXNG_BASE_URL="${SEARXNG_BASE_URL}" \
    SEARXNG_PORT="${SEARXNG_PORT}"

# Optionally, add any additional setup commands here
# For example, you might want to copy your SearXNG source code into the container
# COPY . /app
# WORKDIR /app

# Expose the port that SearXNG will run on
EXPOSE 8888

# Command to run SearXNG (adjust as necessary)
# CMD ["python3", "searxng/manage.py", "runserver", "0.0.0.0:8888"]
