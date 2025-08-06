# Use official SearXNG image as base
FROM searxng/searxng:latest

# Copy custom settings
COPY searx/settings.yml /etc/searxng/settings.yml

# Set environment variables for Railway
ENV SEARXNG_SETTINGS_PATH=/etc/searxng/settings.yml
ENV SEARXNG_PORT=$PORT
ENV SEARXNG_BASE_URL=$SEARXNG_BASE_URL
ENV SEARXNG_SECRET=$SEARXNG_SECRET

# Expose port
EXPOSE $PORT

# Start command for Railway
CMD ["uwsgi", "--http-socket", "0.0.0.0:$PORT", "--module", "searx.webapp", "--callable", "app"]
