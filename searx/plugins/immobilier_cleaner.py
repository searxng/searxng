"""
Plugin de nettoyage et structuration des données immobilières françaises.

Ce plugin intercepte les résultats de recherche des sites immobiliers français,
extrait les informations structurées et élimine le contenu parasité.

Sortie : JSON propre et standardisé pour l'estimation immobilière.
"""

import re
import json
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from searx.plugins._core import Plugin, PluginCfg, PluginInfo

# Configuration des sites immobiliers supportés
REAL_ESTATE_DOMAINS = {
    'seloger.com': 'seloger',
    'leboncoin.fr': 'leboncoin',
    'pap.fr': 'pap',
    'logic-immo.com': 'logic_immo',
    'bienici.com': 'bienici',
    'immobilier.notaires.fr': 'notaires',
    'ouestfrance-immo.com': 'ouestfrance',
    'laforet.com': 'laforet',
    'century21.fr': 'century21',
    'orpi.com': 'orpi',
    'paruvendu.fr': 'paruvendu',
    'fnaim.fr': 'fnaim',
    'avendrealouer.fr': 'avendrealouer',
}

# Mots-clés pour identifier les contenus parasités
NOISE_PATTERNS = [
    r'publicit[ée]',
    r'newsletter',
    r'cookies?',
    r'mentions l[ée]gales',
    r'conditions g[ée]n[ée]rales',
    r'r[ée]seaux sociaux',
    r'suivez-nous',
    r'abonnez-vous',
    r't[ée]l[ée]chargez l\'application',
    r'app store',
    r'google play',
]

NOISE_REGEX = re.compile('|'.join(NOISE_PATTERNS), re.IGNORECASE)


class DataExtractor:
    """Classe de base pour l'extraction de données immobilières."""

    @staticmethod
    def extract_price(text: str) -> Optional[float]:
        """
        Extrait le prix d'une annonce immobilière.

        Formats supportés:
        - 250 000 €
        - 250000€
        - 250.000 EUR
        - 250 000 euros
        """
        if not text:
            return None

        # Nettoyage du texte
        text = text.replace('\xa0', ' ')  # Non-breaking space

        # Patterns de prix français
        patterns = [
            r'(?:€|EUR|euros?)\s*([\d\s.,]+)',  # € 250000
            r'([\d\s.,]+)\s*(?:€|EUR|euros?)',  # 250000 €
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Prendre le plus grand prix trouvé (généralement le prix principal)
                prices = []
                for match in matches:
                    # Nettoyer et convertir
                    clean_price = match.strip()
                    clean_price = clean_price.replace(' ', '').replace('.', '').replace(',', '.')
                    try:
                        price = float(clean_price)
                        if 1000 <= price <= 100000000:  # Filtre de sanité
                            prices.append(price)
                    except ValueError:
                        continue
                if prices:
                    return max(prices)

        return None

    @staticmethod
    def extract_surface(text: str) -> Optional[float]:
        """
        Extrait la surface en m².

        Formats supportés:
        - 75 m²
        - 75m2
        - 75 mètres carrés
        """
        if not text:
            return None

        patterns = [
            r'(\d+(?:[.,]\d+)?)\s*(?:m²|m2|mètres?[\s-]carr[ée]s?)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                surfaces = []
                for match in matches:
                    clean_surface = match.replace(',', '.')
                    try:
                        surface = float(clean_surface)
                        if 5 <= surface <= 10000:  # Filtre de sanité
                            surfaces.append(surface)
                    except ValueError:
                        continue
                if surfaces:
                    return max(surfaces)

        return None

    @staticmethod
    def extract_rooms(text: str) -> Optional[int]:
        """
        Extrait le nombre de pièces.

        Formats supportés:
        - 3 pièces
        - T3
        - F3
        - 3P
        """
        if not text:
            return None

        patterns = [
            r'(?:T|F)(\d+)',  # T3, F3
            r'(\d+)\s*(?:pièces?|P)',  # 3 pièces, 3P
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    rooms = int(match.group(1))
                    if 1 <= rooms <= 20:  # Filtre de sanité
                        return rooms
                except ValueError:
                    continue

        return None

    @staticmethod
    def extract_bedrooms(text: str) -> Optional[int]:
        """Extrait le nombre de chambres."""
        if not text:
            return None

        patterns = [
            r'(\d+)\s*chambres?',
            r'chambres?\s*:\s*(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    bedrooms = int(match.group(1))
                    if 0 <= bedrooms <= 15:
                        return bedrooms
                except ValueError:
                    continue

        return None

    @staticmethod
    def extract_property_type(text: str) -> Optional[str]:
        """
        Extrait le type de bien.

        Types supportés: appartement, maison, terrain, parking, local commercial
        """
        if not text:
            return None

        text_lower = text.lower()

        property_types = {
            'appartement': ['appartement', 'appart', 'flat', 'studio'],
            'maison': ['maison', 'villa', 'pavillon', 'house'],
            'terrain': ['terrain', 'parcelle', 'land'],
            'parking': ['parking', 'garage', 'box'],
            'local_commercial': ['local commercial', 'bureau', 'commerce', 'boutique'],
            'immeuble': ['immeuble', 'building'],
        }

        for prop_type, keywords in property_types.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return prop_type

        return None

    @staticmethod
    def extract_location(text: str) -> Optional[Dict[str, str]]:
        """
        Extrait la localisation (ville, code postal).

        Formats supportés:
        - Paris 75001
        - 75001 Paris
        - Paris (75)
        """
        if not text:
            return None

        location_data = {}

        # Code postal français (5 chiffres)
        postal_match = re.search(r'\b(\d{5})\b', text)
        if postal_match:
            location_data['postal_code'] = postal_match.group(1)

        # Département (2 ou 3 chiffres entre parenthèses)
        dept_match = re.search(r'\((\d{2,3})\)', text)
        if dept_match:
            location_data['department'] = dept_match.group(1)

        # Ville (mot capitalisé avant ou après le code postal)
        city_patterns = [
            r'([A-ZÀÂÄÉÈÊËÏÎÔÙÛÜ][a-zàâäéèêëïîôùûü]+(?: [A-ZÀÂÄÉÈÊËÏÎÔÙÛÜ][a-zàâäéèêëïîôùûü]+)*)\s+\d{5}',
            r'\d{5}\s+([A-ZÀÂÄÉÈÊËÏÎÔÙÛÜ][a-zàâäéèêëïîôùûü]+(?: [A-ZÀÂÄÉÈÊËÏÎÔÙÛÜ][a-zàâäéèêëïîôùûü]+)*)',
        ]

        for pattern in city_patterns:
            city_match = re.search(pattern, text)
            if city_match:
                location_data['city'] = city_match.group(1).strip()
                break

        return location_data if location_data else None

    @staticmethod
    def extract_transaction_type(text: str) -> Optional[str]:
        """Extrait le type de transaction (vente, location)."""
        if not text:
            return None

        text_lower = text.lower()

        if any(word in text_lower for word in ['vente', 'vendre', 'à vendre', 'achat', 'acheter']):
            return 'vente'
        elif any(word in text_lower for word in ['location', 'louer', 'à louer', 'bail']):
            return 'location'

        return None


class SiteSpecificExtractor:
    """Extracteurs spécifiques par site immobilier."""

    @staticmethod
    def extract_seloger(title: str, content: str, url: str) -> Dict[str, Any]:
        """Extraction spécifique pour SeLoger.com"""
        data = {}
        full_text = f"{title} {content}"

        # SeLoger a souvent le format "Type - Ville - Prix"
        data['price'] = DataExtractor.extract_price(full_text)
        data['surface'] = DataExtractor.extract_surface(full_text)
        data['rooms'] = DataExtractor.extract_rooms(full_text)
        data['bedrooms'] = DataExtractor.extract_bedrooms(full_text)
        data['property_type'] = DataExtractor.extract_property_type(full_text)
        data['location'] = DataExtractor.extract_location(full_text)
        data['transaction_type'] = DataExtractor.extract_transaction_type(full_text)

        return data

    @staticmethod
    def extract_leboncoin(title: str, content: str, url: str) -> Dict[str, Any]:
        """Extraction spécifique pour LeBonCoin.fr"""
        data = {}
        full_text = f"{title} {content}"

        data['price'] = DataExtractor.extract_price(full_text)
        data['surface'] = DataExtractor.extract_surface(full_text)
        data['rooms'] = DataExtractor.extract_rooms(full_text)
        data['property_type'] = DataExtractor.extract_property_type(full_text)
        data['location'] = DataExtractor.extract_location(full_text)
        data['transaction_type'] = DataExtractor.extract_transaction_type(full_text)

        return data

    @staticmethod
    def extract_pap(title: str, content: str, url: str) -> Dict[str, Any]:
        """Extraction spécifique pour PAP.fr (De Particulier à Particulier)"""
        data = {}
        full_text = f"{title} {content}"

        data['price'] = DataExtractor.extract_price(full_text)
        data['surface'] = DataExtractor.extract_surface(full_text)
        data['rooms'] = DataExtractor.extract_rooms(full_text)
        data['bedrooms'] = DataExtractor.extract_bedrooms(full_text)
        data['property_type'] = DataExtractor.extract_property_type(full_text)
        data['location'] = DataExtractor.extract_location(full_text)
        data['transaction_type'] = DataExtractor.extract_transaction_type(full_text)

        # PAP indique souvent "sans frais d'agence"
        if 'sans frais' in full_text.lower() or 'sans commission' in full_text.lower():
            data['agency_fees'] = False

        return data

    @staticmethod
    def extract_generic(title: str, content: str, url: str) -> Dict[str, Any]:
        """Extraction générique pour tous les autres sites"""
        data = {}
        full_text = f"{title} {content}"

        data['price'] = DataExtractor.extract_price(full_text)
        data['surface'] = DataExtractor.extract_surface(full_text)
        data['rooms'] = DataExtractor.extract_rooms(full_text)
        data['bedrooms'] = DataExtractor.extract_bedrooms(full_text)
        data['property_type'] = DataExtractor.extract_property_type(full_text)
        data['location'] = DataExtractor.extract_location(full_text)
        data['transaction_type'] = DataExtractor.extract_transaction_type(full_text)

        return data


class ImmobilierCleanerPlugin(Plugin):
    """
    Plugin de nettoyage et structuration des résultats immobiliers.

    Fonctionnalités :
    - Détection automatique des sites immobiliers français
    - Extraction structurée des données (prix, surface, pièces, localisation)
    - Élimination du contenu parasité
    - JSON standardisé en sortie
    """

    info = PluginInfo(
        id='immobilier_cleaner',
        name='Nettoyeur de données immobilières',
        description='Nettoie et structure les résultats de recherche immobilière française',
        preference_section='query',
        examples=[
            'appartement paris',
            'maison à vendre bordeaux',
            'location lyon 3 pièces',
        ],
        keywords=['immobilier', 'appartement', 'maison', 'location', 'vente', 'achat'],
    )

    cfg = PluginCfg(active=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.site_extractors = {
            'seloger': SiteSpecificExtractor.extract_seloger,
            'leboncoin': SiteSpecificExtractor.extract_leboncoin,
            'pap': SiteSpecificExtractor.extract_pap,
        }

    def is_real_estate_site(self, url: str) -> Optional[str]:
        """
        Vérifie si l'URL provient d'un site immobilier connu.

        Returns:
            Le nom court du site si reconnu, None sinon
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Retirer les www.
        domain = domain.replace('www.', '')

        for known_domain, site_name in REAL_ESTATE_DOMAINS.items():
            if known_domain in domain:
                return site_name

        return None

    def clean_noise(self, text: str) -> str:
        """
        Élimine le contenu parasité (pubs, footer, etc.).

        Args:
            text: Texte brut à nettoyer

        Returns:
            Texte nettoyé
        """
        if not text:
            return text

        # Découper par phrases/lignes
        lines = text.split('\n')
        clean_lines = []

        for line in lines:
            # Ignorer les lignes contenant du bruit
            if not NOISE_REGEX.search(line):
                # Ignorer les lignes très courtes (souvent du bruit)
                if len(line.strip()) > 10:
                    clean_lines.append(line.strip())

        return '\n'.join(clean_lines)

    def extract_structured_data(self, site_name: str, title: str, content: str, url: str) -> Dict[str, Any]:
        """
        Extrait les données structurées selon le site source.

        Args:
            site_name: Nom du site immobilier
            title: Titre de l'annonce
            content: Contenu/description de l'annonce
            url: URL de l'annonce

        Returns:
            Dictionnaire de données structurées
        """
        # Nettoyer le contenu avant extraction
        clean_title = self.clean_noise(title)
        clean_content = self.clean_noise(content)

        # Utiliser l'extracteur spécifique au site si disponible
        extractor = self.site_extractors.get(site_name, SiteSpecificExtractor.extract_generic)
        extracted_data = extractor(clean_title, clean_content, url)

        # Ajouter les métadonnées
        extracted_data['source_site'] = site_name
        extracted_data['source_url'] = url
        extracted_data['raw_title'] = clean_title
        extracted_data['raw_content'] = clean_content[:500]  # Limiter la taille

        return extracted_data

    def create_structured_json(self, data: Dict[str, Any]) -> str:
        """
        Crée un JSON propre et standardisé.

        Args:
            data: Données extraites

        Returns:
            JSON formaté
        """
        # Structure standardisée pour l'estimation immobilière
        structured = {
            'listing': {
                'price': data.get('price'),
                'currency': 'EUR',
                'transaction_type': data.get('transaction_type'),
            },
            'property': {
                'type': data.get('property_type'),
                'surface_m2': data.get('surface'),
                'rooms': data.get('rooms'),
                'bedrooms': data.get('bedrooms'),
            },
            'location': data.get('location', {}),
            'source': {
                'site': data.get('source_site'),
                'url': data.get('source_url'),
            },
            'metadata': {
                'title': data.get('raw_title'),
                'description': data.get('raw_content'),
                'agency_fees': data.get('agency_fees'),
            }
        }

        # Retirer les valeurs None pour un JSON plus propre
        def remove_none(obj):
            if isinstance(obj, dict):
                return {k: remove_none(v) for k, v in obj.items() if v is not None}
            return obj

        structured = remove_none(structured)

        return json.dumps(structured, ensure_ascii=False, indent=2)

    def on_result(self, request, search, result) -> bool:
        """
        Hook appelé pour chaque résultat de recherche.

        Modifie le résultat s'il provient d'un site immobilier.

        Returns:
            True pour garder le résultat, False pour le filtrer
        """
        # Vérifier si c'est un site immobilier
        site_name = self.is_real_estate_site(result.get('url', ''))

        if not site_name:
            # Pas un site immobilier, laisser passer sans modification
            return True

        # Extraire les données structurées
        title = result.get('title', '')
        content = result.get('content', '')
        url = result.get('url', '')

        structured_data = self.extract_structured_data(site_name, title, content, url)

        # Vérifier que les données minimales sont présentes
        has_price = structured_data.get('price') is not None
        has_location = structured_data.get('location') is not None

        # Filtrer les annonces incomplètes
        if not has_price and not has_location:
            return False

        # Créer le JSON structuré
        structured_json = self.create_structured_json(structured_data)

        # Modifier le contenu du résultat avec le JSON structuré
        result['content'] = f"{structured_data.get('raw_title', '')}\n\n{structured_json}"

        # Ajouter un marqueur pour faciliter l'identification
        result['title'] = f"[{site_name.upper()}] {structured_data.get('raw_title', title)}"

        # Ajouter les données structurées dans un champ personnalisé si possible
        if not result.get('metadata'):
            result['metadata'] = {}
        result['metadata']['immobilier_data'] = structured_data

        return True


# Instance du plugin à enregistrer
SXNGPlugin = ImmobilierCleanerPlugin
