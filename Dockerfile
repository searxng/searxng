# =========================
# 📦 Base Image
# =========================
ARG DEBIAN_CODENAME="bookworm"
FROM mcr.microsoft.com/devcontainers/base:${DEBIAN_CODENAME}

# =========================
# 🛠 Install Dependencies
# =========================
RUN apt-get update && \
    apt-get -y install --no-install-recommends \
        python3 python3-venv python3-pip \
        redis-server \
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
COPY . /app
WORKDIR /app

# =========================
# 🛠 Create Virtualenv for SearXNG
# =========================
ENV SEARXNG_PYENV="/app/.venv"
RUN python3 -m venv ${SEARXNG_PYENV} && \
    ${SEARXNG_PYENV}/bin/pip install --no-cache-dir -r requirements.txt

# =========================
# 📁 Create User and Set Permissions
# =========================
RUN useradd --no-create-home --shell /bin/false --uid 977 searxng && \
    chown -R searxng:searxng /app

# =========================
# 🌍 Environment Variables
# =========================
ENV SEARXNG_SECRET="${SEARXNG_SECRET:-ultrasecretkey}" \
    SEARXNG_BASE_URL="${SEARXNG_BASE_URL:-}" \
    SEARXNG_PORT="${PORT:-8080}" \
    SEARXNG_SETTINGS_PATH="/app/searx/settings.yml" \
    SEARXNG_STATIC_PATH="/app/searx/static" \
    SEARXNG_TEMPLATES_PATH="/app/searx/templates" \
    PYTHONPATH="/app:${PYTHONPATH}"

# =========================
# 📄 Create uwsgi.ini for Railway
# =========================
RUN cat > /app/uwsgi.ini << 'EOF'
[uwsgi]
# Application
module = searx.webapp
callable = app
pythonpath = /app
virtualenv = /app/.venv

# Server
http = 0.0.0.0:$(PORT)
master = true
processes = 2
threads = 2
enable-threads = true

# Performance
buffer-size = 8192
harakiri = 30
max-requests = 1000
max-requests-delta = 100

# Logging
disable-logging = false
log-4xx = true
log-5xx = true

# Security
uid = searxng
gid = searxng

# Environment
env = SEARXNG_SETTINGS_PATH=/app/searx/settings.yml
EOF

# =========================
# 📡 Expose Port
# =========================
EXPOSE ${PORT}

# =========================
# 🔄 Switch to searxng user
# =========================
USER searxng

# =========================
# 🚀 Start SearXNG
# =========================
CMD ["sh", "-c", "sed -i 's/$(PORT)/'${PORT}'/g' /app/uwsgi.ini && uwsgi /app/uwsgi.ini"]
