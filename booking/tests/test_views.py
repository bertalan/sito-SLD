"""
Test per le views del sistema di prenotazione.
"""
from django.test import TestCase, Client
from datetime import date, time, timedelta
from unittest.mock import patch, MagicMock
import json

from booking.models import AvailabilityRule, Appointment


class BookingViewTest(TestCase):
    """Test per le views di prenotazione."""
    
    def setUp(self):
        self.client = Client()
        AvailabilityRule.objects.create(
            name="Test", weekday=0, start_time=time(9, 0), end_time=time(13, 0), is_active=True
        )
    
    def test_booking_page_returns_success(self):
        """Verifica che la pagina di prenotazione restituisca 200 o il template sia corretto."""
        from booking.views import BookingView
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/prenota/')
        view = BookingView.as_view()
        
        # Verifica che il context sia corretto
        response = BookingView()
        response.request = request
        context = response.get_context_data()
        
        self.assertIn('stripe_public_key', context)
        self.assertIn('paypal_client_id', context)
        self.assertIn('booking_price', context)
        self.assertIn('available_dates', context)
    
    def test_get_available_slots_api(self):
        """Verifica l'API per ottenere gli slot disponibili."""
        today = date.today()
        days_until_monday = (7 - today.weekday()) % 7 or 7
        next_monday = today + timedelta(days=days_until_monday)
        
        response = self.client.get(f'/prenota/slots/{next_monday.isoformat()}/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('slots', data)
    
    def test_invalid_date_returns_error(self):
        """Verifica che una data invalida restituisca errore."""
        response = self.client.get('/prenota/slots/invalid-date/')
        self.assertEqual(response.status_code, 400)


class BookingViewContextTest(TestCase):
    """Test per il context della BookingView con le nuove variabili."""
    
    def test_booking_view_has_slot_config(self):
        """Verifica che la BookingView passi le configurazioni slot."""
        from booking.views import BookingView
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/prenota/')
        
        view = BookingView()
        view.request = request
        context = view.get_context_data()
        
        # Verifica presenza delle nuove variabili
        self.assertIn('slot_duration', context)
        self.assertIn('max_slots', context)
        self.assertIn('booking_price_cents', context)
        
        # Verifica valori di default
        self.assertEqual(context['slot_duration'], 30)
        self.assertEqual(context['max_slots'], 4)
        self.assertEqual(context['booking_price_cents'], 6000)


class DuplicateSlotTest(TestCase):
    """Test per la gestione slot duplicati."""
    
    def setUp(self):
        self.client = Client()
        AvailabilityRule.objects.create(
            weekday=0, start_time=time(9, 0), end_time=time(18, 0), is_active=True
        )
    
    @patch('stripe.checkout.Session.create')
    def test_pending_slot_replaced(self, mock_stripe):
        """Test che slot pending viene sostituito."""
        mock_stripe.return_value = MagicMock(
            id='cs_test', url='https://stripe.com/test', payment_intent='pi_test'
        )
        
        today = date.today()
        days_until_monday = (7 - today.weekday()) % 7 or 7
        next_monday = today + timedelta(days=days_until_monday)
        
        data = {
            'first_name': 'Mario', 'last_name': 'Rossi',
            'email': 'mario@example.com', 'phone': '123',
            'date': next_monday.isoformat(), 'time': '09:30',
            'payment_method': 'stripe', 'consultation_type': 'in_person'
        }
        
        # Prima prenotazione
        self.client.post('/prenota/checkout/', json.dumps(data), content_type='application/json')
        
        # Seconda prenotazione stesso slot
        self.client.post('/prenota/checkout/', json.dumps(data), content_type='application/json')
        
        # Solo 1 pending deve esistere
        pending_count = Appointment.objects.filter(status='pending', date=next_monday, time=time(9, 30)).count()
        self.assertEqual(pending_count, 1)
    
    def test_confirmed_slot_blocks(self):
        """Test che slot confermato blocca nuove prenotazioni."""
        today = date.today()
        days_until_monday = (7 - today.weekday()) % 7 or 7
        next_monday = today + timedelta(days=days_until_monday)
        
        # Crea appuntamento confermato
        Appointment.objects.create(
            first_name='Altro', last_name='Utente', email='altro@example.com',
            phone='123', date=next_monday, time=time(9, 30), status='confirmed'
        )
        
        data = {
            'first_name': 'Mario', 'last_name': 'Rossi',
            'email': 'mario@example.com', 'phone': '123',
            'date': next_monday.isoformat(), 'time': '09:30',
            'payment_method': 'stripe'
        }
        
        response = self.client.post('/prenota/checkout/', json.dumps(data), content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('non è disponibile', response.json()['error'])
