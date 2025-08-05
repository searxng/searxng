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

