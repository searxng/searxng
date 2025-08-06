FROM searxng/searxng:latest

# Copy custom settings file into the default expected directory
COPY searx/settings.yml /app/searx/settings.yml

# Set environment variables for Railway
ENV SEARXNG_SETTINGS_PATH=/app/searx/settings.yml
ENV SEARXNG_PORT=${PORT}
ENV SEARXNG_BASE_URL=${SEARXNG_BASE_URL}
ENV SEARXNG_SECRET=${SEARXNG_SECRET}

# Expose the Railway port
EXPOSE ${PORT}

# Start command for Railway
CMD uwsgi --http-socket 0.0.0.0:${PORT} --module searx.webapp --callable app
