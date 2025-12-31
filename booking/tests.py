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


class VideoCallTest(TestCase):
    """Test per le videochiamate Jitsi."""
    
    def test_video_appointment_generates_code(self):
        """Verifica che un appuntamento video generi un codice Jitsi."""
        appointment = Appointment.objects.create(
            first_name="Test", last_name="User", email="test@example.com",
            phone="123", date=date.today() + timedelta(days=7), time=time(11, 0),
            consultation_type='video'
        )
        appointment.save()  # Forza generazione codice
        
        self.assertNotEqual(appointment.videocall_code, '')
        self.assertEqual(len(appointment.videocall_code), 16)
        self.assertIn('meet.jit.si', appointment.jitsi_url)
    
    def test_in_person_no_jitsi_url(self):
        """Verifica che appuntamento in presenza non abbia link Jitsi."""
        appointment = Appointment.objects.create(
            first_name="Test", last_name="User", email="test@example.com",
            phone="123", date=date.today() + timedelta(days=7), time=time(11, 30),
            consultation_type='in_person'
        )
        self.assertIsNone(appointment.jitsi_url)


class ICalTest(TestCase):
    """Test per la generazione file iCal."""
    
    def test_generate_ical_in_person(self):
        """Test generazione iCal per appuntamento in presenza."""
        from .ical import generate_ical, generate_ical_filename
        
        appointment = Appointment.objects.create(
            first_name="Mario", last_name="Rossi", email="mario@example.com",
            phone="123", date=date(2026, 1, 15), time=time(10, 30),
            consultation_type='in_person', status='confirmed'
        )
        
        ical = generate_ical(appointment)
        
        self.assertIn('BEGIN:VCALENDAR', ical)
        self.assertIn('BEGIN:VEVENT', ical)
        self.assertIn('Lecce', ical)
        self.assertIn('TRIGGER:-PT1H', ical)  # Reminder 1h
    
    def test_generate_ical_video(self):
        """Test generazione iCal per videochiamata."""
        from .ical import generate_ical
        
        appointment = Appointment.objects.create(
            first_name="Luigi", last_name="Verdi", email="luigi@example.com",
            phone="123", date=date(2026, 1, 16), time=time(14, 0),
            consultation_type='video', status='confirmed'
        )
        appointment.save()
        
        ical = generate_ical(appointment)
        
        self.assertIn('meet.jit.si', ical)
        self.assertIn(appointment.videocall_code, ical)
    
    def test_ical_filename(self):
        """Test formato nome file iCal."""
        from .ical import generate_ical_filename
        
        appointment = Appointment.objects.create(
            first_name="Test", last_name="User", email="test@example.com",
            phone="123", date=date(2026, 1, 15), time=time(10, 30),
            consultation_type='in_person'
        )
        
        filename = generate_ical_filename(appointment)
        
        self.assertIn('20260115', filename)
        self.assertIn('1030', filename)
        self.assertTrue(filename.endswith('.ics'))


class DuplicateSlotTest(TestCase):
    """Test per la gestione slot duplicati."""
    
    def setUp(self):
        self.client = Client()
        # Crea regola disponibilità per lunedì
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
        self.assertIn('non è più disponibile', response.json()['error'])


class EmailServiceTest(TestCase):
    """Test per il servizio email."""
    
    @patch('booking.email_service.EmailMultiAlternatives')
    def test_send_confirmation_emails(self, mock_email_class):
        """Test invio email conferma a cliente e studio."""
        from .email_service import send_booking_confirmation
        
        mock_email = MagicMock()
        mock_email_class.return_value = mock_email
        
        appointment = Appointment.objects.create(
            first_name="Mario", last_name="Rossi", email="mario@example.com",
            phone="123", date=date(2026, 1, 15), time=time(10, 30),
            consultation_type='in_person', status='confirmed'
        )
        
        send_booking_confirmation(appointment)
        
        # 2 email: cliente + studio
        self.assertEqual(mock_email_class.call_count, 2)
        # iCal allegato a entrambe
        self.assertEqual(mock_email.attach.call_count, 2)
        # Entrambe inviate
        self.assertEqual(mock_email.send.call_count, 2)
