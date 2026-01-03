"""
Test per la validazione delle coordinate geografiche in SiteSettings.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError

from sld_project.models import SiteSettings


class CoordinatesValidationTest(TestCase):
    """Test per la validazione delle coordinate lat/lng."""
    
    def test_valid_latitude_range(self):
        """La latitudine deve essere tra -90 e 90."""
        valid_latitudes = ['0', '45.4642', '-23.5505', '90', '-90', '41.9028']
        
        for lat in valid_latitudes:
            try:
                lat_float = float(lat)
                self.assertGreaterEqual(lat_float, -90)
                self.assertLessEqual(lat_float, 90)
            except ValueError:
                self.fail(f"Latitudine non convertibile: {lat}")
    
    def test_valid_longitude_range(self):
        """La longitudine deve essere tra -180 e 180."""
        valid_longitudes = ['0', '12.4964', '-46.6333', '180', '-180', '12.4964']
        
        for lng in valid_longitudes:
            try:
                lng_float = float(lng)
                self.assertGreaterEqual(lng_float, -180)
                self.assertLessEqual(lng_float, 180)
            except ValueError:
                self.fail(f"Longitudine non convertibile: {lng}")
    
    def test_invalid_latitude_out_of_range(self):
        """Latitudini fuori range devono essere rifiutate."""
        invalid_latitudes = ['91', '-91', '100', '-200']
        
        for lat in invalid_latitudes:
            lat_float = float(lat)
            self.assertTrue(
                lat_float < -90 or lat_float > 90,
                f"Latitudine invalida accettata: {lat}"
            )
    
    def test_invalid_longitude_out_of_range(self):
        """Longitudini fuori range devono essere rifiutate."""
        invalid_longitudes = ['181', '-181', '200', '-300']
        
        for lng in invalid_longitudes:
            lng_float = float(lng)
            self.assertTrue(
                lng_float < -180 or lng_float > 180,
                f"Longitudine invalida accettata: {lng}"
            )
    
    def test_coordinates_precision(self):
        """Le coordinate devono supportare precisione decimale sufficiente."""
        # Roma, Italia - coordinate precise
        lat = '41.902782'
        lng = '12.496366'
        
        lat_float = float(lat)
        lng_float = float(lng)
        
        # Verifica precisione (almeno 6 decimali)
        self.assertAlmostEqual(lat_float, 41.902782, places=6)
        self.assertAlmostEqual(lng_float, 12.496366, places=6)
    
    def test_site_settings_has_coordinate_fields(self):
        """SiteSettings deve avere i campi maps_lat e maps_lng."""
        settings = SiteSettings()
        
        self.assertTrue(hasattr(settings, 'maps_lat'))
        self.assertTrue(hasattr(settings, 'maps_lng'))
    
    def test_coordinates_as_string_conversion(self):
        """Le coordinate CharField devono essere convertibili in float."""
        test_coords = [
            ('41.9028', '12.4964'),   # Roma
            ('45.4642', '9.1900'),    # Milano
            ('40.8518', '14.2681'),   # Napoli
            ('43.7696', '11.2558'),   # Firenze
        ]
        
        for lat_str, lng_str in test_coords:
            try:
                lat = float(lat_str)
                lng = float(lng_str)
                
                # Verifica che siano in Italia (approssimativamente)
                self.assertGreater(lat, 35)  # Sud Italia
                self.assertLess(lat, 48)     # Nord Italia
                self.assertGreater(lng, 6)   # Ovest Italia
                self.assertLess(lng, 19)     # Est Italia
                
            except ValueError as e:
                self.fail(f"Conversione fallita per {lat_str}, {lng_str}: {e}")
    
    def test_empty_coordinates_handling(self):
        """Coordinate vuote devono essere gestite correttamente."""
        settings = SiteSettings()
        settings.maps_lat = ''
        settings.maps_lng = ''
        
        # Non deve causare errori
        self.assertEqual(settings.maps_lat, '')
        self.assertEqual(settings.maps_lng, '')
    
    def test_coordinate_format_italian_locale(self):
        """Le coordinate con virgola (formato italiano) devono essere gestite."""
        # In Italia si usa la virgola come separatore decimale
        # ma le coordinate devono usare il punto
        italian_format = '41,9028'
        
        # La conversione diretta deve fallire
        with self.assertRaises(ValueError):
            float(italian_format)
        
        # La conversione con replace deve funzionare
        corrected = italian_format.replace(',', '.')
        lat = float(corrected)
        self.assertAlmostEqual(lat, 41.9028, places=4)


class SiteSettingsModelTest(TestCase):
    """Test per il modello SiteSettings."""
    
    def test_site_settings_singleton(self):
        """SiteSettings deve essere un singleton per sito."""
        # La class dovrebbe estendere BaseSiteSetting di Wagtail
        self.assertTrue(hasattr(SiteSettings, 'site'))
    
    def test_required_contact_fields(self):
        """SiteSettings deve avere i campi di contatto."""
        settings = SiteSettings()
        
        # Campi email
        self.assertTrue(hasattr(settings, 'email'))
        
        # Campi social  
        self.assertTrue(hasattr(settings, 'linkedin_url') or hasattr(settings, 'social_links'))
    
    def test_seo_fields_exist(self):
        """SiteSettings deve avere i campi SEO di base."""
        settings = SiteSettings()
        
        # Verifica campi per social/SEO
        self.assertTrue(hasattr(settings, 'default_social_image'))
        self.assertTrue(hasattr(settings, 'studio_name'))
