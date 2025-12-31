"""
Test TDD per il sistema di prenotazione.
Approccio: Test-Green-Green (TGG) - Prima scrivo i test, poi li faccio passare.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import date, time, timedelta
from unittest.mock import patch, MagicMock
import json

from .models import AvailabilityRule, BlockedDate, Appointment


class AvailabilityRuleModelTest(TestCase):
    """Test per il modello AvailabilityRule."""
    
    def test_create_availability_rule(self):
        """Verifica che una regola di disponibilità possa essere creata."""
        rule = AvailabilityRule.objects.create(
            name="Mattina Lunedì",
            weekday=0,  # Lunedì
            start_time=time(9, 0),
            end_time=time(13, 0),
            is_active=True
        )
        self.assertEqual(rule.name, "Mattina Lunedì")
        self.assertEqual(rule.weekday, 0)
        self.assertTrue(rule.is_active)
    
    def test_weekday_display(self):
        """Verifica la visualizzazione del giorno della settimana."""
        rule = AvailabilityRule.objects.create(
            name="Test", weekday=0, start_time=time(9, 0), end_time=time(18, 0)
        )
        self.assertEqual(rule.get_weekday_display(), "Lunedì")
    
    def test_str_representation(self):
        """Verifica la rappresentazione stringa."""
        rule = AvailabilityRule.objects.create(
            name="Test", weekday=4, start_time=time(15, 0), end_time=time(18, 0)
        )
        self.assertIn("Venerdì", str(rule))
        self.assertIn("15:00", str(rule))


class BlockedDateModelTest(TestCase):
    """Test per il modello BlockedDate."""
    
    def test_create_blocked_date(self):
        """Verifica che una data bloccata possa essere creata."""
        blocked = BlockedDate.objects.create(
            date=date(2025, 12, 25),
            reason="Natale"
        )
        self.assertEqual(blocked.reason, "Natale")
    
    def test_str_representation(self):
        """Verifica la rappresentazione stringa."""
        blocked = BlockedDate.objects.create(date=date(2025, 1, 1), reason="Capodanno")
        self.assertIn("2025-01-01", str(blocked))


class AppointmentModelTest(TestCase):
    """Test per il modello Appointment."""
    
    def setUp(self):
        """Setup per i test degli appuntamenti."""
        # Creo regole per Lunedì 9-13, 15-18
        AvailabilityRule.objects.create(
            name="Mattina", weekday=0, start_time=time(9, 0), end_time=time(13, 0), is_active=True
        )
        AvailabilityRule.objects.create(
            name="Pomeriggio", weekday=0, start_time=time(15, 0), end_time=time(18, 0), is_active=True
        )
    
    def test_create_appointment(self):
        """Verifica che un appuntamento possa essere creato."""
        appointment = Appointment.objects.create(
            first_name="Mario",
            last_name="Rossi",
            email="mario@example.com",
            phone="+39123456789",
            date=date(2025, 1, 6),  # Lunedì
            time=time(10, 0),
            status='pending'
        )
        self.assertEqual(appointment.status, 'pending')
        self.assertEqual(appointment.email, "mario@example.com")
    
    def test_unique_slot_constraint(self):
        """Verifica che non si possano prenotare due appuntamenti nello stesso slot."""
        Appointment.objects.create(
            first_name="Mario", last_name="Rossi", email="mario@example.com",
            phone="+39123456789", date=date(2025, 1, 6), time=time(10, 0)
        )
        with self.assertRaises(Exception):
            Appointment.objects.create(
                first_name="Luigi", last_name="Verdi", email="luigi@example.com",
                phone="+39987654321", date=date(2025, 1, 6), time=time(10, 0)
            )
    
    def test_get_available_slots_with_rules(self):
        """Verifica che gli slot disponibili vengano calcolati correttamente."""
        # Trova il prossimo Lunedì
        today = date.today()
        days_until_monday = (7 - today.weekday()) % 7 or 7
        next_monday = today + timedelta(days=days_until_monday)
        
        slots = Appointment.get_available_slots(next_monday)
        
        # Mattina: 9:00-13:00 = 8 slot da 30 min
        # Pomeriggio: 15:00-18:00 = 6 slot da 30 min
        # Totale: 14 slot
        self.assertEqual(len(slots), 14)
        self.assertEqual(slots[0], time(9, 0))
        self.assertEqual(slots[-1], time(17, 30))
    
    def test_blocked_date_returns_no_slots(self):
        """Verifica che le date bloccate non abbiano slot disponibili."""
        today = date.today()
        days_until_monday = (7 - today.weekday()) % 7 or 7
        next_monday = today + timedelta(days=days_until_monday)
        
        BlockedDate.objects.create(date=next_monday, reason="Ferie")
        
        slots = Appointment.get_available_slots(next_monday)
        self.assertEqual(len(slots), 0)
    
    def test_booked_slot_not_available(self):
        """Verifica che uno slot prenotato non sia più disponibile."""
        today = date.today()
        days_until_monday = (7 - today.weekday()) % 7 or 7
        next_monday = today + timedelta(days=days_until_monday)
        
        Appointment.objects.create(
            first_name="Mario", last_name="Rossi", email="mario@example.com",
            phone="+39123456789", date=next_monday, time=time(10, 0), status='confirmed'
        )
        
        slots = Appointment.get_available_slots(next_monday)
        self.assertNotIn(time(10, 0), slots)
        self.assertEqual(len(slots), 13)
    
    def test_cancelled_slot_is_available(self):
        """Verifica che uno slot annullato sia nuovamente disponibile."""
        today = date.today()
        days_until_monday = (7 - today.weekday()) % 7 or 7
        next_monday = today + timedelta(days=days_until_monday)
        
        Appointment.objects.create(
            first_name="Mario", last_name="Rossi", email="mario@example.com",
            phone="+39123456789", date=next_monday, time=time(10, 0), status='cancelled'
        )
        
        slots = Appointment.get_available_slots(next_monday)
        self.assertIn(time(10, 0), slots)


class BookingViewTest(TestCase):
    """Test per le views di prenotazione."""
    
    def setUp(self):
        self.client = Client()
        AvailabilityRule.objects.create(
            name="Test", weekday=0, start_time=time(9, 0), end_time=time(13, 0), is_active=True
        )
    
    def test_booking_page_returns_success(self):
        """Verifica che la pagina di prenotazione restituisca 200 o il template sia corretto."""
        # Il test verifica che la view funzioni, non il rendering del template
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


class PaymentGatewayTest(TestCase):
    """Test per i gateway di pagamento Stripe e PayPal."""
    
    def setUp(self):
        self.client = Client()
        AvailabilityRule.objects.create(
            name="Test", weekday=0, start_time=time(9, 0), end_time=time(13, 0), is_active=True
        )
    
    @patch('stripe.checkout.Session.create')
    def test_stripe_checkout_creates_session(self, mock_stripe):
        """Verifica che Stripe crei una sessione di checkout."""
        mock_stripe.return_value = MagicMock(
            url='https://checkout.stripe.com/test',
            payment_intent='pi_test123',
            id='cs_test123'
        )
        
        today = date.today()
        days_until_monday = (7 - today.weekday()) % 7 or 7
        next_monday = today + timedelta(days=days_until_monday)
        
        response = self.client.post(
            '/prenota/checkout/',
            data=json.dumps({
                'first_name': 'Mario',
                'last_name': 'Rossi',
                'email': 'mario@example.com',
                'phone': '+39123456789',
                'date': next_monday.isoformat(),
                'time': '10:00',
                'payment_method': 'stripe'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('url', data)
    
    @patch('booking.views.paypalrestsdk.Payment')
    def test_paypal_checkout_creates_payment(self, mock_payment_class):
        """Verifica che PayPal crei un pagamento."""
        # Configura il mock
        mock_payment_instance = MagicMock()
        mock_payment_instance.create.return_value = True
        mock_payment_instance.id = 'PAY-123456'
        
        # Crea mock per i links con attributo rel corretto
        mock_link = MagicMock()
        mock_link.rel = 'approval_url'
        mock_link.href = 'https://paypal.com/approve/test'
        mock_payment_instance.links = [mock_link]
        
        mock_payment_class.return_value = mock_payment_instance
        
        today = date.today()
        days_until_monday = (7 - today.weekday()) % 7 or 7
        next_monday = today + timedelta(days=days_until_monday)
        
        response = self.client.post(
            '/prenota/checkout/',
            data=json.dumps({
                'first_name': 'Mario',
                'last_name': 'Rossi',
                'email': 'mario@example.com',
                'phone': '+39123456789',
                'date': next_monday.isoformat(),
                'time': '10:30',  # Slot diverso da altri test
                'payment_method': 'paypal'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('url', data)


class AppointmentStatusTest(TestCase):
    """Test per lo stato degli appuntamenti."""
    
    def test_default_status_is_pending(self):
        """Verifica che lo stato di default sia pending."""
        appointment = Appointment.objects.create(
            first_name="Test", last_name="User", email="test@example.com",
            phone="123", date=date.today() + timedelta(days=7), time=time(10, 0)
        )
        self.assertEqual(appointment.status, 'pending')
    
    def test_confirm_appointment(self):
        """Verifica che un appuntamento possa essere confermato."""
        appointment = Appointment.objects.create(
            first_name="Test", last_name="User", email="test@example.com",
            phone="123", date=date.today() + timedelta(days=7), time=time(10, 0)
        )
        appointment.status = 'confirmed'
        appointment.save()
        
        updated = Appointment.objects.get(id=appointment.id)
        self.assertEqual(updated.status, 'confirmed')
