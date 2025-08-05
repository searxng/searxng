# =========================
# 📦 Base Image
# =========================
ARG DEBIAN_CODENAME="bookworm"
FROM mcr.microsoft.com/devcontainers/base:${DEBIAN_CODENAME}

# =========================
# 🛠 Install Dependencies (بدون مشاكل valkey أو duplicate sources)
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
# 🌍 Environment Variables
# =========================
ENV SEARXNG_SECRET="${SEARXNG_SECRET}" \
    SEARXNG_BASE_URL="${SEARXNG_BASE_URL}" \
    SEARXNG_PORT="${PORT}" \
    SEARXNG_SETTINGS_PATH="/app/searx/settings.yml"

# =========================
# 📡 Expose Port
# =========================
EXPOSE ${PORT}

# =========================
# 🚀 Start SearXNG
# =========================
CMD ["uwsgi", "--ini", "utils/templates/etc/uwsgi/apps-available/searxng.ini"]

