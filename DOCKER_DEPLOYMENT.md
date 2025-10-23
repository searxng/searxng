# Guide de déploiement Docker et Kubernetes pour SearXNG

Ce guide vous explique comment construire et déployer l'application SearXNG avec Docker et Kubernetes.

## Construction de l'image Docker

### Build simple
```bash
docker build -t searxng:latest .
```

### Build avec tag de version
```bash
docker build -t searxng:1.0.0 -t searxng:latest .
```

### Build pour un registry spécifique
```bash
docker build -t votre-registry.com/searxng:latest .
docker push votre-registry.com/searxng:latest
```

## Exécution locale avec Docker

### Démarrage rapide
```bash
docker run -d \
  --name searxng \
  -p 8080:8080 \
  -v searxng-config:/etc/searxng \
  -v searxng-data:/var/lib/searxng \
  searxng:latest
```

### Avec configuration personnalisée
```bash
# Créer un fichier de configuration settings.yml
mkdir -p ./config
# Placez votre settings.yml dans ./config/

docker run -d \
  --name searxng \
  -p 8080:8080 \
  -v $(pwd)/config:/etc/searxng \
  -v searxng-data:/var/lib/searxng \
  searxng:latest
```

### Variables d'environnement disponibles
- `GRANIAN_PORT`: Port d'écoute (défaut: 8080)
- `GRANIAN_HOST`: Adresse d'écoute (défaut: ::)
- `GRANIAN_BLOCKING_THREADS`: Nombre de threads bloquants (défaut: 4)
- `SEARXNG_SETTINGS_PATH`: Chemin vers le fichier de configuration (défaut: /etc/searxng/settings.yml)
- `CONFIG_PATH`: Répertoire de configuration (défaut: /etc/searxng)
- `DATA_PATH`: Répertoire de données (défaut: /var/lib/searxng)

## Déploiement sur Kubernetes

### 1. Créer un Namespace (optionnel)
```bash
kubectl create namespace searxng
```

### 2. Créer un ConfigMap pour la configuration
```bash
kubectl create configmap searxng-config \
  --from-file=settings.yml=./config/settings.yml \
  -n searxng
```

### 3. Appliquer les manifestes Kubernetes
Voir le fichier `k8s-deployment.yaml` pour un exemple complet.

```bash
kubectl apply -f k8s-deployment.yaml -n searxng
```

### 4. Vérifier le déploiement
```bash
kubectl get pods -n searxng
kubectl get services -n searxng
```

### 5. Accéder à l'application
```bash
# Via port-forward pour les tests
kubectl port-forward -n searxng service/searxng 8080:8080

# Ou via l'URL de votre Ingress si configuré
```

## Architecture de l'image Docker

### Multi-stage build
L'image utilise un build en plusieurs étapes :
1. **Stage Builder**: Installation des dépendances de compilation et build de l'application
2. **Stage Runtime**: Image finale légère avec uniquement les dépendances runtime

### Caractéristiques de sécurité
- Utilisation d'un utilisateur non-root (UID/GID 977)
- Image basée sur Python slim pour réduire la surface d'attaque
- Healthcheck intégré pour Kubernetes

### Volumes
- `/etc/searxng`: Configuration de l'application
- `/var/lib/searxng`: Données persistantes

### Ports
- `8080`: Port HTTP de l'application

## Optimisations pour la production

### Ressources Kubernetes recommandées
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### Mise à l'échelle horizontale (HPA)
```bash
kubectl autoscale deployment searxng \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  -n searxng
```

### Stratégie de déploiement
Le manifeste Kubernetes utilise une stratégie RollingUpdate pour des mises à jour sans interruption.

## Dépannage

### Vérifier les logs
```bash
# Docker
docker logs searxng

# Kubernetes
kubectl logs -f deployment/searxng -n searxng
```

### Vérifier la santé de l'application
```bash
# Docker
curl http://localhost:8080/healthz

# Kubernetes
kubectl get pods -n searxng
kubectl describe pod <pod-name> -n searxng
```

### Problèmes de permissions
Si vous rencontrez des problèmes de permissions sur les volumes, assurez-vous que :
- Les répertoires ont les bonnes permissions (chown 977:977)
- La variable d'environnement `FORCE_OWNERSHIP=true` est définie (activée par défaut)

## Maintenance

### Mise à jour de l'image
```bash
# 1. Builder la nouvelle version
docker build -t searxng:v1.1.0 .

# 2. Pousser vers le registry
docker push votre-registry.com/searxng:v1.1.0

# 3. Mettre à jour le déploiement Kubernetes
kubectl set image deployment/searxng searxng=votre-registry.com/searxng:v1.1.0 -n searxng

# 4. Vérifier le rollout
kubectl rollout status deployment/searxng -n searxng
```

### Rollback en cas de problème
```bash
kubectl rollout undo deployment/searxng -n searxng
```

## Ressources additionnelles

- Documentation officielle SearXNG: https://docs.searxng.org/
- Documentation Kubernetes: https://kubernetes.io/docs/
- Documentation Docker: https://docs.docker.com/
