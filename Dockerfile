FROM searxng/searxng:latest

# Copie la config
COPY ./settings.yml /usr/local/searxng/searx/settings.yml

# Copie les templates personnalisés
COPY ./templates /usr/local/searxng/searx/templates

# Copie le thème
COPY ./themes /usr/local/searxng/searx/static/themes

# Commande pour lancer SearxNG
CMD ["uwsgi", "--ini", "/usr/local/searxng/searx/webapp/uwsgi.ini"]
