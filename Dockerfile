# Multi-stage build pour optimiser la taille de l'image finale
# Stage 1: Builder - Installation des dépendances
FROM python:3.12-slim AS builder

# Variables d'environnement pour Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Installation des dépendances système nécessaires pour la compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    git \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Création du répertoire de travail
WORKDIR /usr/local/searxng

# Copie des fichiers de requirements
COPY requirements.txt requirements-server.txt ./

# Installation des dépendances Python dans un environnement virtuel
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt -r requirements-server.txt

# Copie du code source
COPY searx/ ./searx/
COPY babel.cfg setup.py ./

# Compilation des fichiers Python
RUN /opt/venv/bin/python -m compileall -q -f -j 0 ./searx/

# Stage 2: Runtime - Image finale légère
FROM python:3.12-slim

# Installation des dépendances runtime uniquement
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libxml2 \
    libxslt1.1 \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Création de l'utilisateur non-root pour la sécurité
RUN groupadd -g 977 searxng && \
    useradd -u 977 -g searxng -s /bin/sh -m -d /usr/local/searxng searxng

# Définition du répertoire de travail
WORKDIR /usr/local/searxng

# Copie de l'environnement virtuel depuis le builder
COPY --from=builder --chown=searxng:searxng /opt/venv /opt/venv

# Copie du code source compilé
COPY --from=builder --chown=searxng:searxng /usr/local/searxng/searx ./searx

# Copie du script d'entrypoint si nécessaire
COPY --chown=searxng:searxng container/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

# Variables d'environnement pour l'application
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/usr/local/searxng:$PYTHONPATH" \
    SEARXNG_SETTINGS_PATH="/etc/searxng/settings.yml" \
    CONFIG_PATH="/etc/searxng" \
    DATA_PATH="/var/lib/searxng" \
    GRANIAN_PROCESS_NAME="searxng" \
    GRANIAN_INTERFACE="wsgi" \
    GRANIAN_HOST="::" \
    GRANIAN_PORT="8080" \
    GRANIAN_WEBSOCKETS="false" \
    GRANIAN_BLOCKING_THREADS="4" \
    GRANIAN_WORKERS_KILL_TIMEOUT="30s" \
    GRANIAN_BLOCKING_THREADS_IDLE_TIMEOUT="5m" \
    FORCE_OWNERSHIP="true"

# Création des répertoires de configuration et données
RUN mkdir -p /etc/searxng /var/lib/searxng && \
    chown -R searxng:searxng /etc/searxng /var/lib/searxng

# Volumes pour la configuration et les données
VOLUME ["/etc/searxng", "/var/lib/searxng"]

# Exposition du port de l'application
EXPOSE 8080

# Utilisation de l'utilisateur non-root
USER searxng

# Healthcheck pour Kubernetes
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/healthz', timeout=5)" || exit 1

# Point d'entrée de l'application
ENTRYPOINT ["/usr/local/searxng/entrypoint.sh"]
