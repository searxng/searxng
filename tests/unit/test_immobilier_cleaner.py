# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests unitaires pour le plugin immobilier_cleaner."""

import json
from unittest.mock import Mock

from tests import SearxTestCase
from searx.plugins.immobilier_cleaner import (
    ImmobilierCleanerPlugin,
    DataExtractor,
    SiteSpecificExtractor,
)


class TestDataExtractor(SearxTestCase):
    """Tests pour la classe DataExtractor."""

    def test_extract_price_euros(self):
        """Test extraction de prix en euros avec différents formats."""
        # Format standard : "250 000 €"
        self.assertEqual(250000, DataExtractor.extract_price("Appartement à 250 000 €"))

        # Format compact : "250000€"
        self.assertEqual(250000, DataExtractor.extract_price("Prix 250000€"))

        # Format avec points : "250.000 EUR"
        self.assertEqual(250000, DataExtractor.extract_price("250.000 EUR"))

        # Format avec "euros"
        self.assertEqual(150000, DataExtractor.extract_price("150 000 euros"))

        # Non-breaking space
        self.assertEqual(300000, DataExtractor.extract_price("300\xa0000 €"))

        # Avec virgule pour les centimes
        self.assertEqual(125500, DataExtractor.extract_price("125 500,00 €"))

    def test_extract_price_invalid(self):
        """Test extraction de prix avec valeurs invalides."""
        # Prix trop faible
        self.assertIsNone(DataExtractor.extract_price("500 €"))

        # Prix trop élevé (sanity check)
        self.assertIsNone(DataExtractor.extract_price("500 000 000 €"))

        # Pas de prix
        self.assertIsNone(DataExtractor.extract_price("Bel appartement"))

        # None
        self.assertIsNone(DataExtractor.extract_price(None))

    def test_extract_price_multiple(self):
        """Test extraction avec plusieurs prix (prendre le plus grand)."""
        text = "Loyer 800 € + charges 150 €. Prix total 950 €"
        # Devrait prendre le plus grand (950)
        self.assertEqual(950, DataExtractor.extract_price(text))

    def test_extract_surface(self):
        """Test extraction de surface."""
        # Format m²
        self.assertEqual(75, DataExtractor.extract_surface("Appartement 75 m²"))

        # Format m2
        self.assertEqual(120.5, DataExtractor.extract_surface("Maison de 120,5m2"))

        # Format "mètres carrés"
        self.assertEqual(90, DataExtractor.extract_surface("Surface : 90 mètres carrés"))

        # Avec virgule décimale
        self.assertEqual(65.5, DataExtractor.extract_surface("65,5 m²"))

    def test_extract_surface_invalid(self):
        """Test extraction de surface avec valeurs invalides."""
        # Surface trop petite
        self.assertIsNone(DataExtractor.extract_surface("2 m²"))

        # Surface trop grande
        self.assertIsNone(DataExtractor.extract_surface("50000 m²"))

        # Pas de surface
        self.assertIsNone(DataExtractor.extract_surface("Bel appartement"))

    def test_extract_rooms(self):
        """Test extraction du nombre de pièces."""
        # Format T3
        self.assertEqual(3, DataExtractor.extract_rooms("T3 Paris"))

        # Format F4
        self.assertEqual(4, DataExtractor.extract_rooms("F4 disponible"))

        # Format "pièces"
        self.assertEqual(5, DataExtractor.extract_rooms("Maison 5 pièces"))

        # Format "P"
        self.assertEqual(2, DataExtractor.extract_rooms("2P centre ville"))

    def test_extract_rooms_invalid(self):
        """Test extraction de pièces avec valeurs invalides."""
        # Trop peu de pièces
        self.assertIsNone(DataExtractor.extract_rooms("T0"))

        # Trop de pièces
        self.assertIsNone(DataExtractor.extract_rooms("25 pièces"))

    def test_extract_bedrooms(self):
        """Test extraction du nombre de chambres."""
        self.assertEqual(2, DataExtractor.extract_bedrooms("Appartement 2 chambres"))
        self.assertEqual(3, DataExtractor.extract_bedrooms("chambres : 3"))
        self.assertEqual(1, DataExtractor.extract_bedrooms("1 chambre"))

    def test_extract_property_type(self):
        """Test extraction du type de bien."""
        self.assertEqual('appartement', DataExtractor.extract_property_type("Bel appartement"))
        self.assertEqual('appartement', DataExtractor.extract_property_type("Studio à louer"))
        self.assertEqual('maison', DataExtractor.extract_property_type("Maison avec jardin"))
        self.assertEqual('maison', DataExtractor.extract_property_type("Villa moderne"))
        self.assertEqual('terrain', DataExtractor.extract_property_type("Terrain constructible"))
        self.assertEqual('parking', DataExtractor.extract_property_type("Parking sécurisé"))
        self.assertEqual('parking', DataExtractor.extract_property_type("Garage fermé"))
        self.assertEqual('local_commercial', DataExtractor.extract_property_type("Local commercial"))
        self.assertEqual('local_commercial', DataExtractor.extract_property_type("Bureau standing"))

    def test_extract_location(self):
        """Test extraction de la localisation."""
        # Format "Ville Code postal"
        location = DataExtractor.extract_location("Paris 75001")
        self.assertEqual('75001', location['postal_code'])
        self.assertEqual('Paris', location['city'])

        # Format "Code postal Ville"
        location = DataExtractor.extract_location("69007 Lyon")
        self.assertEqual('69007', location['postal_code'])
        self.assertEqual('Lyon', location['city'])

        # Avec département entre parenthèses
        location = DataExtractor.extract_location("Bordeaux (33)")
        self.assertEqual('33', location['department'])

        # Ville composée
        location = DataExtractor.extract_location("Saint-Étienne 42000")
        self.assertEqual('42000', location['postal_code'])
        self.assertEqual('Saint-Étienne', location['city'])

    def test_extract_location_invalid(self):
        """Test extraction de localisation invalide."""
        self.assertIsNone(DataExtractor.extract_location("Bel appartement"))
        self.assertIsNone(DataExtractor.extract_location(None))

    def test_extract_transaction_type(self):
        """Test extraction du type de transaction."""
        self.assertEqual('vente', DataExtractor.extract_transaction_type("Appartement à vendre"))
        self.assertEqual('vente', DataExtractor.extract_transaction_type("Vente maison"))
        self.assertEqual('vente', DataExtractor.extract_transaction_type("Achat immédiat"))

        self.assertEqual('location', DataExtractor.extract_transaction_type("Appartement à louer"))
        self.assertEqual('location', DataExtractor.extract_transaction_type("Location meublée"))
        self.assertEqual('location', DataExtractor.extract_transaction_type("Bail 3 ans"))

    def test_extract_transaction_type_invalid(self):
        """Test extraction de type de transaction invalide."""
        self.assertIsNone(DataExtractor.extract_transaction_type("Bel appartement"))
        self.assertIsNone(DataExtractor.extract_transaction_type(None))


class TestSiteSpecificExtractor(SearxTestCase):
    """Tests pour les extracteurs spécifiques par site."""

    def test_extract_seloger(self):
        """Test extraction pour SeLoger.com"""
        title = "T3 Paris 75001"
        content = "Appartement 75 m² à vendre pour 450 000 €. 3 pièces dont 2 chambres."
        url = "https://www.seloger.com/annonces/achat/appartement/paris-1er-75001/..."

        data = SiteSpecificExtractor.extract_seloger(title, content, url)

        self.assertEqual(450000, data['price'])
        self.assertEqual(75, data['surface'])
        self.assertEqual(3, data['rooms'])
        self.assertEqual(2, data['bedrooms'])
        self.assertEqual('appartement', data['property_type'])
        self.assertEqual('vente', data['transaction_type'])
        self.assertIsNotNone(data['location'])
        self.assertEqual('75001', data['location']['postal_code'])

    def test_extract_leboncoin(self):
        """Test extraction pour LeBonCoin.fr"""
        title = "Maison 120m2 Bordeaux"
        content = "Belle maison 5 pièces à vendre 380 000 € - 33000 Bordeaux"
        url = "https://www.leboncoin.fr/ventes_immobilieres/..."

        data = SiteSpecificExtractor.extract_leboncoin(title, content, url)

        self.assertEqual(380000, data['price'])
        self.assertEqual(120, data['surface'])
        self.assertEqual(5, data['rooms'])
        self.assertEqual('maison', data['property_type'])
        self.assertEqual('vente', data['transaction_type'])

    def test_extract_pap(self):
        """Test extraction pour PAP.fr (avec détection sans frais)"""
        title = "Appartement T2 Lyon"
        content = "2 pièces 50 m² à vendre 200 000 € sans frais d'agence - Lyon 69007"
        url = "https://www.pap.fr/annonce/vente-appartement..."

        data = SiteSpecificExtractor.extract_pap(title, content, url)

        self.assertEqual(200000, data['price'])
        self.assertEqual(50, data['surface'])
        self.assertEqual(2, data['rooms'])
        self.assertEqual('appartement', data['property_type'])
        self.assertFalse(data['agency_fees'])

    def test_extract_generic(self):
        """Test extraction générique pour sites non spécifiques."""
        title = "Studio 30m²"
        content = "Studio à louer 650 € par mois - Lille 59000"
        url = "https://www.example-immo.fr/annonce/123"

        data = SiteSpecificExtractor.extract_generic(title, content, url)

        self.assertEqual(650, data['price'])
        self.assertEqual(30, data['surface'])
        self.assertEqual('appartement', data['property_type'])
        self.assertEqual('location', data['transaction_type'])


class TestImmobilierCleanerPlugin(SearxTestCase):
    """Tests pour le plugin ImmobilierCleanerPlugin."""

    def setUp(self):
        """Initialisation avant chaque test."""
        super().setUp()
        self.plugin = ImmobilierCleanerPlugin()

    def test_is_real_estate_site(self):
        """Test détection des sites immobiliers."""
        # Sites connus
        self.assertEqual('seloger', self.plugin.is_real_estate_site('https://www.seloger.com/annonces/...'))
        self.assertEqual('leboncoin', self.plugin.is_real_estate_site('https://www.leboncoin.fr/ventes_immobilieres/...'))
        self.assertEqual('pap', self.plugin.is_real_estate_site('https://www.pap.fr/annonce/...'))

        # Sans www
        self.assertEqual('seloger', self.plugin.is_real_estate_site('https://seloger.com/annonces/...'))

        # Site non immobilier
        self.assertIsNone(self.plugin.is_real_estate_site('https://www.google.com'))
        self.assertIsNone(self.plugin.is_real_estate_site('https://www.wikipedia.org'))

    def test_clean_noise(self):
        """Test nettoyage du contenu parasité."""
        noisy_text = """
Bel appartement 3 pièces
Prix : 250 000 €
Suivez-nous sur les réseaux sociaux
Téléchargez l'application sur App Store
Cookies et mentions légales
        """

        clean = self.plugin.clean_noise(noisy_text)

        # Le contenu utile doit être conservé
        self.assertIn("Bel appartement 3 pièces", clean)
        self.assertIn("250 000", clean)

        # Le bruit doit être supprimé
        self.assertNotIn("réseaux sociaux", clean)
        self.assertNotIn("App Store", clean)
        self.assertNotIn("Cookies", clean)

    def test_clean_noise_short_lines(self):
        """Test que les lignes courtes (bruit) sont supprimées."""
        text = "Bel appartement\nOK\nPrix 250000€\nVoir\nSurface 75m²"
        clean = self.plugin.clean_noise(text)

        # Les lignes courtes "OK" et "Voir" doivent être supprimées
        self.assertNotIn("OK", clean)
        self.assertNotIn("Voir", clean)

        # Les lignes utiles sont conservées
        self.assertIn("appartement", clean)
        self.assertIn("250000", clean)

    def test_extract_structured_data(self):
        """Test extraction complète de données structurées."""
        site_name = 'seloger'
        title = "Appartement T3 Paris 75001"
        content = "Bel appartement de 75 m² à vendre pour 450 000 €. 3 pièces dont 2 chambres."
        url = "https://www.seloger.com/annonces/..."

        data = self.plugin.extract_structured_data(site_name, title, content, url)

        self.assertEqual('seloger', data['source_site'])
        self.assertEqual(url, data['source_url'])
        self.assertEqual(450000, data['price'])
        self.assertEqual(75, data['surface'])
        self.assertEqual(3, data['rooms'])
        self.assertEqual(2, data['bedrooms'])
        self.assertEqual('appartement', data['property_type'])
        self.assertIsNotNone(data['location'])

    def test_create_structured_json(self):
        """Test création du JSON structuré."""
        data = {
            'price': 250000,
            'surface': 60,
            'rooms': 2,
            'bedrooms': 1,
            'property_type': 'appartement',
            'transaction_type': 'vente',
            'location': {'city': 'Paris', 'postal_code': '75001'},
            'source_site': 'seloger',
            'source_url': 'https://www.seloger.com/...',
            'raw_title': 'T2 Paris',
            'raw_content': 'Bel appartement',
        }

        json_output = self.plugin.create_structured_json(data)
        parsed = json.loads(json_output)

        # Vérifier la structure
        self.assertIn('listing', parsed)
        self.assertIn('property', parsed)
        self.assertIn('location', parsed)
        self.assertIn('source', parsed)
        self.assertIn('metadata', parsed)

        # Vérifier les valeurs
        self.assertEqual(250000, parsed['listing']['price'])
        self.assertEqual('EUR', parsed['listing']['currency'])
        self.assertEqual('vente', parsed['listing']['transaction_type'])

        self.assertEqual('appartement', parsed['property']['type'])
        self.assertEqual(60, parsed['property']['surface_m2'])
        self.assertEqual(2, parsed['property']['rooms'])
        self.assertEqual(1, parsed['property']['bedrooms'])

        self.assertEqual('Paris', parsed['location']['city'])
        self.assertEqual('75001', parsed['location']['postal_code'])

        self.assertEqual('seloger', parsed['source']['site'])

    def test_on_result_real_estate_site(self):
        """Test traitement d'un résultat d'un site immobilier."""
        request = Mock()
        search = Mock()
        result = {
            'url': 'https://www.seloger.com/annonces/achat/appartement/paris/...',
            'title': 'Appartement T3 Paris 75001',
            'content': 'Bel appartement 75 m² à vendre pour 450 000 €.',
            'metadata': {}
        }

        ret = self.plugin.on_result(request, search, result)

        # Le résultat doit être conservé (True)
        self.assertTrue(ret)

        # Le titre doit être modifié avec le marqueur [SELOGER]
        self.assertIn('[SELOGER]', result['title'])

        # Les métadonnées immobilières doivent être ajoutées
        self.assertIn('immobilier_data', result['metadata'])
        self.assertEqual(450000, result['metadata']['immobilier_data']['price'])

    def test_on_result_non_real_estate_site(self):
        """Test qu'un résultat non-immobilier n'est pas modifié."""
        request = Mock()
        search = Mock()
        result = {
            'url': 'https://www.wikipedia.org/wiki/Real_estate',
            'title': 'Real Estate - Wikipedia',
            'content': 'Real estate is property...',
        }

        original_title = result['title']
        original_content = result['content']

        ret = self.plugin.on_result(request, search, result)

        # Le résultat doit être conservé
        self.assertTrue(ret)

        # Le résultat ne doit pas être modifié
        self.assertEqual(original_title, result['title'])
        self.assertEqual(original_content, result['content'])

    def test_on_result_incomplete_listing(self):
        """Test filtrage d'une annonce incomplète (sans prix ni localisation)."""
        request = Mock()
        search = Mock()
        result = {
            'url': 'https://www.seloger.com/annonces/...',
            'title': 'Bel appartement',
            'content': 'Très beau, contactez-nous',
        }

        ret = self.plugin.on_result(request, search, result)

        # L'annonce incomplète doit être filtrée (False)
        self.assertFalse(ret)

    def test_on_result_with_location_only(self):
        """Test qu'une annonce avec localisation mais sans prix est conservée."""
        request = Mock()
        search = Mock()
        result = {
            'url': 'https://www.seloger.com/annonces/...',
            'title': 'Appartement Paris 75001',
            'content': 'Bel appartement disponible',
        }

        ret = self.plugin.on_result(request, search, result)

        # Devrait être conservé car a une localisation
        self.assertTrue(ret)

    def test_on_result_with_price_only(self):
        """Test qu'une annonce avec prix mais sans localisation est conservée."""
        request = Mock()
        search = Mock()
        result = {
            'url': 'https://www.seloger.com/annonces/...',
            'title': 'Appartement à vendre',
            'content': 'Prix : 250 000 €',
        }

        ret = self.plugin.on_result(request, search, result)

        # Devrait être conservé car a un prix
        self.assertTrue(ret)

    def test_json_no_none_values(self):
        """Test que le JSON ne contient pas de valeurs None."""
        data = {
            'price': 250000,
            'surface': None,  # Pas de surface
            'rooms': 3,
            'bedrooms': None,  # Pas de chambres
            'property_type': 'appartement',
            'transaction_type': None,  # Type inconnu
            'location': {'city': 'Paris', 'postal_code': None},
            'source_site': 'seloger',
            'source_url': 'https://www.seloger.com/...',
            'raw_title': 'Appartement Paris',
            'raw_content': 'Bel appartement',
        }

        json_output = self.plugin.create_structured_json(data)

        # Le JSON ne doit pas contenir "null"
        self.assertNotIn('null', json_output)

        parsed = json.loads(json_output)

        # Les valeurs None ne doivent pas être présentes
        self.assertNotIn('surface_m2', parsed['property'])
        self.assertNotIn('bedrooms', parsed['property'])
        self.assertNotIn('transaction_type', parsed['listing'])
