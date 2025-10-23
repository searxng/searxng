#!/usr/bin/env python3
"""
Test du plugin avec ParuVendu.fr
"""

import re
import json
from typing import Dict, Any, Optional
from urllib.parse import urlparse


REAL_ESTATE_DOMAINS = {
    'paruvendu.fr': 'paruvendu',
}


def is_real_estate_site(url: str) -> Optional[str]:
    """Vérifie si l'URL provient d'un site immobilier connu."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower().replace('www.', '')

    for known_domain, site_name in REAL_ESTATE_DOMAINS.items():
        if known_domain in domain:
            return site_name

    return None


# Test avec l'URL fournie
test_url = "https://www.paruvendu.fr/immobilier/prix-m2/aix-en-provence/"

print("=" * 80)
print("TEST DU PLUGIN AVEC PARUVENDU.FR")
print("=" * 80)
print()
print(f"URL testée : {test_url}")
print()

site_detected = is_real_estate_site(test_url)

if site_detected:
    print(f"✅ Site détecté : {site_detected}")
    print()
    print("Le plugin traitera automatiquement les résultats de ce site !")
    print()
    print("Exemple de résultat traité :")
    print("-" * 80)

    # Exemple de données qui seraient extraites
    example_title = "Appartement T3 - 75 m² - Aix-en-Provence"
    example_content = """
    Bel appartement de 75 m² à vendre dans le centre d'Aix-en-Provence.
    Prix : 320 000 €
    3 pièces dont 2 chambres
    Aix-en-Provence 13100 (Bouches-du-Rhône)
    """

    print(f"Titre original : {example_title}")
    print(f"Contenu : {example_content.strip()}")
    print()
    print("↓ APRÈS TRAITEMENT PAR LE PLUGIN ↓")
    print()
    print(f"Titre modifié : [PARUVENDU] {example_title}")
    print()
    print("Données extraites :")
    print("  • Site source: paruvendu")
    print("  • Type de bien: appartement")
    print("  • Type de transaction: vente")
    print("  • Prix: 320000.0 EUR")
    print("  • Surface: 75.0 m²")
    print("  • Nombre de pièces: 3")
    print("  • Nombre de chambres: 2")
    print("  • Localisation:")
    print("    - Ville: Aix-en-Provence")
    print("    - Code postal: 13100")
    print()
    print("JSON structuré :")

    json_example = {
        "listing": {
            "price": 320000.0,
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
            "postal_code": "13100",
            "city": "Aix-en-Provence"
        },
        "source": {
            "site": "paruvendu",
            "url": test_url
        }
    }

    print(json.dumps(json_example, ensure_ascii=False, indent=2))
else:
    print("❌ Site non détecté")

print()
print("=" * 80)
