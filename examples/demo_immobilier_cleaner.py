#!/usr/bin/env python3
"""
Script de démonstration du plugin immobilier_cleaner.

Ce script montre comment le plugin extrait et structure les données
des annonces immobilières françaises.
"""

import sys
import os
import json

# Ajouter le chemin du projet au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from searx.plugins.immobilier_cleaner import ImmobilierCleanerPlugin


def demo_extraction():
    """Démonstration des capacités d'extraction du plugin."""

    plugin = ImmobilierCleanerPlugin()

    print("=" * 80)
    print("DÉMONSTRATION DU PLUGIN IMMOBILIER CLEANER")
    print("=" * 80)
    print()

    # Exemples d'annonces
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
                Suivez-nous sur Facebook
                Téléchargez notre application
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
                Contactez-nous pour plus d'informations
                Newsletter - Mentions légales
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
                Sans frais d\'agence
                Lyon 7ème arrondissement (69)
                Publié par un particulier
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
                Disponible immédiatement
            ''',
        },
        {
            'name': 'Annonce incomplète (filtrée)',
            'url': 'https://www.seloger.com/annonces/incomplete',
            'title': 'Bel appartement',
            'content': '''
                Très beau bien immobilier
                Contactez-nous pour plus d'informations
                Cookies - Politique de confidentialité
            ''',
        },
    ]

    # Traiter chaque exemple
    for i, example in enumerate(examples, 1):
        print(f"\n{'─' * 80}")
        print(f"EXEMPLE {i}: {example['name']}")
        print('─' * 80)
        print(f"\nURL: {example['url']}")
        print(f"\nTitre original: {example['title']}")
        print(f"\nContenu original (extrait):")
        print(example['content'][:200] + '...')

        # Simuler le résultat de recherche
        result = {
            'url': example['url'],
            'title': example['title'],
            'content': example['content'],
            'metadata': {}
        }

        # Appliquer le plugin
        keep_result = plugin.on_result(None, None, result)

        if not keep_result:
            print(f"\n⚠️  RÉSULTAT FILTRÉ (annonce incomplète)")
            continue

        print(f"\n✓ RÉSULTAT CONSERVÉ")
        print(f"\nTitre modifié: {result['title']}")

        # Afficher les données structurées extraites
        if 'metadata' in result and 'immobilier_data' in result['metadata']:
            data = result['metadata']['immobilier_data']

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

            if 'agency_fees' in data and data['agency_fees'] is False:
                print(f"  • Sans frais d'agence")

            # Afficher le JSON structuré
            structured_json = plugin.create_structured_json(data)
            print(f"\n📄 JSON STRUCTURÉ:")
            print(structured_json)

    print("\n" + "=" * 80)
    print("FIN DE LA DÉMONSTRATION")
    print("=" * 80)


def test_data_extractors():
    """Test des fonctions d'extraction individuelles."""

    from searx.plugins.immobilier_cleaner import DataExtractor

    print("\n" + "=" * 80)
    print("TEST DES EXTRACTEURS DE DONNÉES")
    print("=" * 80)

    test_cases = [
        {
            'function': 'extract_price',
            'tests': [
                ("Appartement à 250 000 €", 250000),
                ("Prix 125.500 EUR", 125500),
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
    # Démo principale
    demo_extraction()

    # Tests des extracteurs
    test_data_extractors()
