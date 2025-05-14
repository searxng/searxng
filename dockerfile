FROM ghcr.io/searxng/searxng:latest

# Expose the port that SearXNG uses internally
EXPOSE 8080

# Start the app
CMD ["uwsgi", "--ini", "/etc/searxng/uwsgi.ini"]
