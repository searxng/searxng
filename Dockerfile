# =========================
# 📦 Base Image
# =========================
ARG DEBIAN_CODENAME="bookworm"
FROM mcr.microsoft.com/devcontainers/base:${DEBIAN_CODENAME}

# =========================
# 📥 Debian Sources
# =========================
RUN cat <<EOF > /etc/apt/sources.list.d/debian.sources
Types: deb
URIs: http://deb.debian.org/debian
Suites: ${DEBIAN_CODENAME} ${DEBIAN_CODENAME}-updates ${DEBIAN_CODENAME}-backports
Components: main
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg

Types: deb
URIs: http://security.debian.org/debian-security
Suites: ${DEBIAN_CODENAME}-security
Components: main
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
EOF

# =========================
# 🛠 Install Dependencies
# =========================
RUN apt-get update && \
    apt-get -y install --no-install-recommends \
        python3 python3-venv python3-pip \
        valkey-server \
        firefox-esr \
        graphviz \
        imagemagick \
        librsvg2-bin \
        fonts-dejavu \
        shellcheck \
        uwsgi uwsgi-plugin-python3 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# =========================
# 📂 Copy App Files
# =========================
WORKDIR /app
COPY . /app

# =========================
# 🌍 Environment Variables
# =========================
ENV SEARXNG_SECRET="${SEARXNG_SECRET}" \
    SEARXNG_BASE_URL="${SEARXNG_BASE_URL}" \
    SEARXNG_PORT="${PORT}" \
    SEARXNG_SETTINGS_PATH="/app/searx/settings.yml"

# =========================
# 📡 Expose Port
# =========================
EXPOSE 8888

# =========================
# 🚀 Start SearXNG
# =========================
CMD ["uwsgi", "--ini", "/app/utils/templates/etc/uwsgi/apps-available/searxng.ini"]
