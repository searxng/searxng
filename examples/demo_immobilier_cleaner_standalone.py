#!/usr/bin/env python3
"""
Script de démonstration standalone du plugin immobilier_cleaner.

Ce script montre les capacités d'extraction sans nécessiter les dépendances SearXNG.
"""

import re
import json
from typing import Dict, Any, Optional
from urllib.parse import urlparse


# Configuration des sites immobiliers supportés
REAL_ESTATE_DOMAINS = {
    'seloger.com': 'seloger',
    'leboncoin.fr': 'leboncoin',
    'pap.fr': 'pap',
    'logic-immo.com': 'logic_immo',
    'bienici.com': 'bienici',
}


class DataExtractor:
    """Classe de base pour l'extraction de données immobilières."""

    @staticmethod
    def extract_price(text: str) -> Optional[float]:
        """Extrait le prix d'une annonce immobilière."""
        if not text:
            return None

        text = text.replace('\xa0', ' ')

        patterns = [
            r'(?:€|EUR|euros?)\s*([\d\s.,]+)',
            r'([\d\s.,]+)\s*(?:€|EUR|euros?)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                prices = []
                for match in matches:
                    clean_price = match.strip()
                    clean_price = clean_price.replace(' ', '').replace('.', '').replace(',', '.')
                    try:
                        price = float(clean_price)
                        if 1000 <= price <= 100000000:
                            prices.append(price)
                    except ValueError:
                        continue
                if prices:
                    return max(prices)

        return None

    @staticmethod
    def extract_surface(text: str) -> Optional[float]:
        """Extrait la surface en m²."""
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
                        if 5 <= surface <= 10000:
                            surfaces.append(surface)
                    except ValueError:
                        continue
                if surfaces:
                    return max(surfaces)

        return None

    @staticmethod
    def extract_rooms(text: str) -> Optional[int]:
        """Extrait le nombre de pièces."""
        if not text:
            return None

        patterns = [
            r'(?:T|F)(\d+)',
            r'(\d+)\s*(?:pièces?|P)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    rooms = int(match.group(1))
                    if 1 <= rooms <= 20:
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
        """Extrait le type de bien."""
        if not text:
            return None

        text_lower = text.lower()

        property_types = {
            'appartement': ['appartement', 'appart', 'flat', 'studio'],
            'maison': ['maison', 'villa', 'pavillon', 'house'],
            'terrain': ['terrain', 'parcelle', 'land'],
            'parking': ['parking', 'garage', 'box'],
            'local_commercial': ['local commercial', 'bureau', 'commerce', 'boutique'],
        }

        for prop_type, keywords in property_types.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return prop_type

        return None

    @staticmethod
    def extract_location(text: str) -> Optional[Dict[str, str]]:
        """Extrait la localisation (ville, code postal)."""
        if not text:
            return None

        location_data = {}

        postal_match = re.search(r'\b(\d{5})\b', text)
        if postal_match:
            location_data['postal_code'] = postal_match.group(1)

        dept_match = re.search(r'\((\d{2,3})\)', text)
        if dept_match:
            location_data['department'] = dept_match.group(1)

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


def is_real_estate_site(url: str) -> Optional[str]:
    """Vérifie si l'URL provient d'un site immobilier connu."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower().replace('www.', '')

    for known_domain, site_name in REAL_ESTATE_DOMAINS.items():
        if known_domain in domain:
            return site_name

    return None


def extract_all_data(title: str, content: str, url: str) -> Dict[str, Any]:
    """Extrait toutes les données d'une annonce."""
    full_text = f"{title} {content}"

    data = {
        'price': DataExtractor.extract_price(full_text),
        'surface': DataExtractor.extract_surface(full_text),
        'rooms': DataExtractor.extract_rooms(full_text),
        'bedrooms': DataExtractor.extract_bedrooms(full_text),
        'property_type': DataExtractor.extract_property_type(full_text),
        'location': DataExtractor.extract_location(full_text),
        'transaction_type': DataExtractor.extract_transaction_type(full_text),
        'source_site': is_real_estate_site(url),
        'source_url': url,
    }

    return data


def create_structured_json(data: Dict[str, Any]) -> str:
    """Crée un JSON propre et standardisé."""
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
    }

    def remove_none(obj):
        if isinstance(obj, dict):
            return {k: remove_none(v) for k, v in obj.items() if v is not None}
        return obj

    structured = remove_none(structured)
    return json.dumps(structured, ensure_ascii=False, indent=2)


def demo_extraction():
    """Démonstration des capacités d'extraction du plugin."""

    print("=" * 80)
    print("DÉMONSTRATION DU PLUGIN IMMOBILIER CLEANER")
    print("=" * 80)
    print()

    examples = [
        {
            'name': 'SeLoger - Appartement Paris',
            'url': 'https://www.seloger.com/annonces/achat/appartement/paris-1er-75001/louvre/123456.htm',
            'title': 'Appartement T3 Paris 75001',
            'content': '''
                Magnifique appartement de 75 m² à vendre dans le quartier du Louvre.
                Prix : 450 000 €
                3 pièces dont 2 chambres
                Cuisine équipée
            ''',
        },
        {
            'name': 'LeBonCoin - Maison Bordeaux',
            'url': 'https://www.leboncoin.fr/ventes_immobilieres/2345678.htm',
            'title': 'Maison 120m2 Bordeaux',
            'content': '''
                Belle maison de 120 m² avec jardin
                5 pièces - 4 chambres
                Prix : 380 000 euros
                33000 Bordeaux
            ''',
        },
        {
            'name': 'PAP - Appartement Lyon',
            'url': 'https://www.pap.fr/annonce/vente-appartement-lyon-69007-g123456',
            'title': 'T2 Lyon 69007',
            'content': '''
                Appartement 2 pièces 50 m²
                1 chambre
                À vendre : 200 000 €
                Sans frais d'agence
                Lyon 7ème arrondissement (69)
            ''',
        },
        {
            'name': 'Logic-Immo - Studio Paris',
            'url': 'https://www.logic-immo.com/location-studio-paris-75018/123.html',
            'title': 'Studio 25m² Paris 18',
            'content': '''
                Studio meublé à louer
                25 m² - 1 pièce
                Loyer : 850 € par mois + charges 50 €
                Métro Marcadet-Poissonniers
                Paris 75018
            ''',
        },
    ]

    for i, example in enumerate(examples, 1):
        print(f"\n{'─' * 80}")
        print(f"EXEMPLE {i}: {example['name']}")
        print('─' * 80)
        print(f"\nURL: {example['url']}")
        print(f"\nTitre: {example['title']}")
        print(f"\nContenu (extrait):")
        print(example['content'][:200].strip() + '...')

        # Extraire les données
        data = extract_all_data(example['title'], example['content'], example['url'])

        print(f"\n📊 DONNÉES EXTRAITES:")
        print(f"  • Site source: {data.get('source_site', 'N/A')}")
        print(f"  • Type de bien: {data.get('property_type', 'N/A')}")
        print(f"  • Type de transaction: {data.get('transaction_type', 'N/A')}")
        print(f"  • Prix: {data.get('price', 'N/A')} EUR" if data.get('price') else "  • Prix: N/A")
        print(f"  • Surface: {data.get('surface', 'N/A')} m²" if data.get('surface') else "  • Surface: N/A")
        print(f"  • Nombre de pièces: {data.get('rooms', 'N/A')}")
        print(f"  • Nombre de chambres: {data.get('bedrooms', 'N/A')}")

        location = data.get('location', {})
        if location:
            print(f"  • Localisation:")
            if 'city' in location:
                print(f"    - Ville: {location['city']}")
            if 'postal_code' in location:
                print(f"    - Code postal: {location['postal_code']}")
            if 'department' in location:
                print(f"    - Département: {location['department']}")

        # Afficher le JSON structuré
        structured_json = create_structured_json(data)
        print(f"\n📄 JSON STRUCTURÉ:")
        print(structured_json)

    print("\n" + "=" * 80)
    print("FIN DE LA DÉMONSTRATION")
    print("=" * 80)


def test_data_extractors():
    """Test des fonctions d'extraction individuelles."""

    print("\n" + "=" * 80)
    print("TEST DES EXTRACTEURS DE DONNÉES")
    print("=" * 80)

    test_cases = [
        {
            'function': 'extract_price',
            'tests': [
                ("Appartement à 250 000 €", 250000),
                ("Prix 125500 EUR", 125500),
                ("300000€", 300000),
                ("Loyer 850 euros", 850),
            ]
        },
        {
            'function': 'extract_surface',
            'tests': [
                ("Appartement 75 m²", 75),
                ("120,5 m2", 120.5),
                ("Surface 90 mètres carrés", 90),
            ]
        },
        {
            'function': 'extract_rooms',
            'tests': [
                ("T3 Paris", 3),
                ("F4 disponible", 4),
                ("Maison 5 pièces", 5),
            ]
        },
        {
            'function': 'extract_property_type',
            'tests': [
                ("Bel appartement", "appartement"),
                ("Maison avec jardin", "maison"),
                ("Terrain constructible", "terrain"),
                ("Garage fermé", "parking"),
            ]
        },
        {
            'function': 'extract_transaction_type',
            'tests': [
                ("Appartement à vendre", "vente"),
                ("Location meublée", "location"),
            ]
        },
    ]

    for test_group in test_cases:
        func_name = test_group['function']
        func = getattr(DataExtractor, func_name)

        print(f"\n{'─' * 80}")
        print(f"Test de {func_name}()")
        print('─' * 80)

        for text, expected in test_group['tests']:
            result = func(text)
            status = "✓" if result == expected else "✗"
            print(f"{status} '{text}' → {result} (attendu: {expected})")


if __name__ == '__main__':
    demo_extraction()
    test_data_extractors()
