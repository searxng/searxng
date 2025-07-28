# Utilise l'image officielle de SearxNG
FROM searxng/searxng:latest

# Définir le dossier de travail
WORKDIR /usr/local/searxng

# Copie ton fichier settings.yml personnalisé (si tu en as un)
# REMARQUE : facultatif, si tu n'en as pas, tu peux l'ignorer
COPY ./settings.yml ./searx/settings.yml

# Copie les fichiers de thème HTML/CSS personnalisés (si tu en as)
COPY ./themes /usr/local/searxng/searx/static/themes
COPY ./templates /usr/local/searxng/searx/templates

# (Facultatif) Active ton thème dans settings.yml :
# ui:
#   static_theme: mon-theme

# Port utilisé par SearxNG
EXPOSE 8080

# Commande de lancement
CMD ["./manage.sh", "run"]
