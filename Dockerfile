# Use the official SearXNG image
FROM searxng/searxng:latest

# Copy the settings file
COPY searx/settings.yml /app/searx/settings.yml

# ✅ Copy your custom logo to replace the default SearXNG logo
COPY searx/static/themes/simple/img/searxng.png /usr/local/searxng/searx/static/themes/simple/img/searxng.png

# ✅ Copy your custom homepage (index.html) to override the default one
COPY searx/templates/simple/index.html /usr/local/searxng/searx/templates/simple/index.html

# ✅ Copy your customized base.html if you edited header/footer
COPY searx/templates/simple/base.html /usr/local/searxng/searx/templates/simple/base.html

# Set environment variables for Railway
ENV SEARXNG_SETTINGS_PATH=/app/searx/settings.yml
ENV SEARXNG_PORT=${PORT}
ENV SEARXNG_BASE_URL=${SEARXNG_BASE_URL}
ENV SEARXNG_SECRET=${SEARXNG_SECRET}

# Expose the port used by Railway
EXPOSE ${PORT}

# Start the SearXNG application
CMD uwsgi --http-socket 0.0.0.0:${PORT} --module searx.webapp --callable app

