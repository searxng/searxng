#!/bin/sh
# start-searxng-dev.sh
# Starts the SearXNG dev server inside the searxng-dev Podman container.
# Run this from your HOST after creating the container, or exec it from inside.
#
# Usage (from host):
#   podman exec -it searxng-dev sh /usr/local/searxng/start-searxng-dev.sh
#
# Or launch a fresh container and run it in one go:
#   podman rm -f searxng-dev 2>/dev/null; \
#   podman run -it --name searxng-dev -p 8889:8888 \
#     -v ~/Gemini/searxng-dev:/usr/local/searxng:z \
#     -w /usr/local/searxng \
#     --entrypoint sh \
#     docker.io/searxng/searxng:latest \
#     /usr/local/searxng/start-searxng-dev.sh

set -e

REPO=/usr/local/searxng
SETTINGS_DIR=/etc/searxng
SETTINGS_FILE=$SETTINGS_DIR/settings.yml

echo "==> Bootstrapping pip..."
python -m ensurepip --upgrade

echo "==> Installing requirements..."
python -m pip install -q -r $REPO/requirements.txt

echo "==> Setting up /etc/searxng/settings.yml..."
mkdir -p $SETTINGS_DIR
cp $REPO/searx/settings.yml $SETTINGS_FILE
sed -i 's/bind_address: .*/bind_address: "0.0.0.0"/' $SETTINGS_FILE

echo "==> Creating version_frozen.py..."
cat > $REPO/searx/version_frozen.py << 'EOF'
VERSION_STRING = "dev"
VERSION_TAG = "dev"
DOCKER_TAG = "dev"
GIT_URL = "https://github.com/searxng/searxng"
GIT_BRANCH = "master"
EOF

echo "==> Starting SearXNG dev server on 0.0.0.0:8888..."
echo "    Access from host at: http://localhost:8889"
echo ""
PYTHONPATH=$REPO SEARXNG_DEBUG=1 python -m searx.webapp
