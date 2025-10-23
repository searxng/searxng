# Plugin Immobilier Cleaner pour SearXNG

## Description

Plugin de nettoyage et structuration automatique des données immobilières françaises pour SearXNG.

Ce plugin intercepte les résultats de recherche provenant des principaux sites immobiliers français, extrait les informations structurées pertinentes et élimine le contenu parasité (publicités, navigation, footer, etc.).

## Fonctionnalités

### 🎯 Détection automatique

Le plugin détecte automatiquement les résultats provenant des sites immobiliers français suivants :

- **SeLoger.com** - Leader de la recherche immobilière en France
- **LeBonCoin.fr** - Petites annonces immobilières
- **PAP.fr** - De Particulier à Particulier
- **Logic-Immo.com** - Portail immobilier
- **BienIci.com** - Annonces immobilières
- **Immobilier.notaires.fr** - Annonces des notaires
- **OuestFrance-Immo.com** - Immobilier Ouest France
- **LaForet.com** - Réseau d'agences immobilières
- **Century21.fr** - Réseau d'agences immobilières
- **Orpi.com** - Réseau d'agences immobilières
- **ParuVendu.fr** - Petites annonces
- **Fnaim.fr** - Fédération nationale de l'immobilier
- **AvendreAlouer.fr** - Annonces immobilières

### 📊 Extraction structurée

Le plugin extrait automatiquement les données suivantes :

#### Informations financières
- **Prix** : Extraction avec support de multiples formats (€, EUR, euros)
  - Format : `250 000 €`, `250000€`, `250.000 EUR`
  - Filtrage automatique des valeurs aberrantes

#### Caractéristiques du bien
- **Surface** : Extraction en m²
  - Formats : `75 m²`, `75m2`, `75 mètres carrés`
- **Nombre de pièces** : Support des notations françaises
  - Formats : `T3`, `F4`, `3 pièces`, `3P`
- **Nombre de chambres** : Extraction explicite
- **Type de bien** : Classification automatique
  - Appartement, Maison, Terrain, Parking, Local commercial, Immeuble

#### Localisation
- **Code postal** : Format français (5 chiffres)
- **Ville** : Détection avec support des noms composés
- **Département** : Extraction quand disponible

#### Transaction
- **Type** : Vente ou Location
- **Frais d'agence** : Détection "sans frais" (PAP)

### 🧹 Nettoyage du contenu

Le plugin élimine automatiquement :
- Publicités
- Newsletters
- Mentions de cookies
- Mentions légales
- Réseaux sociaux
- Appels à télécharger des applications
- Lignes trop courtes (bruit)

### 📤 Sortie JSON standardisée

Le plugin génère un JSON structuré et normalisé :

```json
{
  "listing": {
    "price": 450000.0,
    "currency": "EUR",
    "transaction_type": "vente"
  },
  "property": {
    "type": "appartement",
    "surface_m2": 75.0,
    "rooms": 3,
    "bedrooms": 2
  },
  "location": {
    "postal_code": "75001",
    "city": "Paris"
  },
  "source": {
    "site": "seloger",
    "url": "https://www.seloger.com/annonces/..."
  }
}
```

## Installation

### 1. Le plugin est déjà installé

Le fichier `searx/plugins/immobilier_cleaner.py` contient le code du plugin.

### 2. Configuration dans settings.yml

Le plugin est activé par défaut dans `searx/settings.yml` :

```yaml
plugins:
  searx.plugins.immobilier_cleaner.SXNGPlugin:
    active: true
```

### 3. Options de configuration (optionnel)

Vous pouvez ajouter des options de configuration personnalisées :

```yaml
immobilier_cleaner:
  min_price: 0                    # Prix minimum (en EUR)
  max_price: 10000000             # Prix maximum (en EUR)
  min_surface: 5                  # Surface minimum (en m²)
  max_surface: 10000              # Surface maximum (en m²)
  filter_incomplete: true         # Filtrer les annonces sans prix ni localisation
```

## Utilisation

Le plugin fonctionne automatiquement sans intervention de l'utilisateur.

### Exemples de recherches

```
appartement paris
maison à vendre bordeaux
location lyon 3 pièces
T3 marseille
studio 75018
terrain constructible toulouse
```

### Comportement

1. **Pour les sites immobiliers** : Le plugin extrait et structure les données
   - Le titre du résultat est préfixé par `[SITE]` (ex: `[SELOGER]`)
   - Le contenu est remplacé par les données structurées en JSON
   - Les métadonnées `immobilier_data` sont ajoutées au résultat

2. **Pour les autres sites** : Aucune modification

3. **Annonces incomplètes** : Filtrées si elles n'ont ni prix ni localisation

## Démonstration

Un script de démonstration standalone est disponible :

```bash
python examples/demo_immobilier_cleaner_standalone.py
```

Ce script montre :
- L'extraction de données sur des exemples réels
- Les tests des extracteurs individuels
- Le format JSON de sortie

## Tests

Des tests unitaires complets sont disponibles dans `tests/unit/test_immobilier_cleaner.py`.

### Exécuter les tests

```bash
# Avec pytest (si disponible)
pytest tests/unit/test_immobilier_cleaner.py -v

# Avec unittest
python -m unittest tests.unit.test_immobilier_cleaner -v
```

### Couverture des tests

Les tests couvrent :
- ✅ Extraction de prix (multiples formats)
- ✅ Extraction de surface
- ✅ Extraction du nombre de pièces et chambres
- ✅ Détection du type de bien
- ✅ Extraction de localisation (ville, code postal, département)
- ✅ Détection du type de transaction (vente/location)
- ✅ Nettoyage du contenu parasité
- ✅ Filtrage des annonces incomplètes
- ✅ Génération du JSON structuré
- ✅ Détection des sites immobiliers

## Architecture

### Classes principales

#### `ImmobilierCleanerPlugin`
- Classe principale du plugin héritant de `searx.plugins.Plugin`
- Implémente le hook `on_result()` pour traiter chaque résultat
- Gère la détection, extraction et structuration

#### `DataExtractor`
- Classe utilitaire pour l'extraction de données
- Méthodes statiques pour chaque type de donnée
- Support des formats français

#### `SiteSpecificExtractor`
- Extracteurs spécialisés par site immobilier
- `extract_seloger()`, `extract_leboncoin()`, `extract_pap()`
- `extract_generic()` pour les sites non spécifiques

### Flux de traitement

```
Résultat de recherche
    ↓
is_real_estate_site() → Détection du site
    ↓
extract_structured_data() → Extraction
    ↓
clean_noise() → Nettoyage
    ↓
create_structured_json() → Structuration
    ↓
on_result() → Modification du résultat
```

## Filtres de sanité

Le plugin applique des filtres pour éviter les données aberrantes :

| Donnée | Min | Max |
|--------|-----|-----|
| Prix | 1 000 € | 100 000 000 € |
| Surface | 5 m² | 10 000 m² |
| Pièces | 1 | 20 |
| Chambres | 0 | 15 |

## Extension

### Ajouter un nouveau site immobilier

1. Ajouter le domaine dans `REAL_ESTATE_DOMAINS` :

```python
REAL_ESTATE_DOMAINS = {
    # ...
    'nouveausite.fr': 'nouveausite',
}
```

2. (Optionnel) Créer un extracteur spécifique :

```python
class SiteSpecificExtractor:
    @staticmethod
    def extract_nouveausite(title: str, content: str, url: str) -> Dict[str, Any]:
        # Logique d'extraction spécifique
        pass
```

3. Enregistrer l'extracteur :

```python
self.site_extractors = {
    # ...
    'nouveausite': SiteSpecificExtractor.extract_nouveausite,
}
```

### Ajouter un nouveau type de donnée

1. Créer une méthode dans `DataExtractor` :

```python
@staticmethod
def extract_nouvelle_donnee(text: str) -> Optional[Any]:
    # Logique d'extraction
    pass
```

2. L'appeler dans les extracteurs de sites :

```python
data['nouvelle_donnee'] = DataExtractor.extract_nouvelle_donnee(full_text)
```

3. L'ajouter au schéma JSON :

```python
structured = {
    # ...
    'nouvelle_section': {
        'nouvelle_donnee': data.get('nouvelle_donnee'),
    }
}
```

## Cas d'usage

### Estimation immobilière
Le JSON structuré peut être utilisé pour :
- Comparer les prix au m² par quartier
- Analyser les tendances du marché
- Calculer des estimations automatiques

### Recherche avancée
- Filtrage par caractéristiques précises
- Tri par prix/m²
- Détection des bonnes affaires

### Agrégation de données
- Collecte de données pour analyse
- Création de bases de données immobilières
- Études de marché

## Limitations connues

1. **Extraction de prix**
   - Les prix < 1000 € ne sont pas extraits (filtre de sanité)
   - Peut ne pas détecter certains formats exotiques

2. **Localisation**
   - Nécessite un code postal ou ville avec majuscule
   - Peut avoir des difficultés avec les noms de villes très composés

3. **Type de bien**
   - Basé sur des mots-clés, peut manquer certains types spécifiques
   - Classification simplifiée

## Contribution

Pour contribuer au plugin :

1. Ajouter des tests dans `tests/unit/test_immobilier_cleaner.py`
2. Documenter les nouvelles fonctionnalités
3. Respecter le style de code existant
4. Tester sur des exemples réels

## Licence

Ce plugin suit la licence du projet SearXNG (AGPL-3.0).

## Support

Pour toute question ou suggestion :
- Créer une issue sur le dépôt GitHub
- Consulter la documentation SearXNG sur les plugins

## Changelog

### Version 1.0.0 (Initial)
- ✅ Détection automatique de 13 sites immobiliers français
- ✅ Extraction de 10+ champs de données
- ✅ Nettoyage du contenu parasité
- ✅ JSON structuré et standardisé
- ✅ Tests unitaires complets
- ✅ Script de démonstration
- ✅ Documentation complète
