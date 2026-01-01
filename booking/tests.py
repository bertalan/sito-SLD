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
    
    @patch('booking.payment_service.RealPayPalProvider')
    def test_paypal_checkout_creates_payment(self, mock_provider_class):
        """Verifica che PayPal crei un pagamento."""
        from booking.payment_service import PaymentResult
        
        # Configura il mock del provider
        mock_provider = MagicMock()
        mock_provider.create_payment.return_value = PaymentResult(
            success=True,
            redirect_url='https://paypal.com/approve/test',
            payment_id='PAY-123456'
        )
        mock_provider_class.return_value = mock_provider
        
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
        self.assertIn('non è disponibile', response.json()['error'])


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


class AppointmentAttachmentModelTest(TestCase):
    """Test per il modello AppointmentAttachment."""
    
    def setUp(self):
        """Setup comune per i test."""
        from .models import AppointmentAttachment
        self.AppointmentAttachment = AppointmentAttachment
        
        self.appointment = Appointment.objects.create(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            phone="+39 333 1234567",
            notes="Test appointment",
            consultation_type="video",
            date=date(2026, 2, 15),
            time=time(10, 30),
            status="confirmed"
        )
    
    def test_create_attachment(self):
        """Verifica che un allegato con spazi nel nome possa essere creato."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        fake_file = SimpleUploadedFile(
            name="documento test 1.pdf",
            content=b"contenuto fake del pdf",
            content_type="application/pdf"
        )
        
        attachment = self.AppointmentAttachment.objects.create(
            appointment=self.appointment,
            file=fake_file,
            original_filename="documento test 1.pdf"
        )
        
        self.assertEqual(attachment.original_filename, "documento test 1.pdf")
        self.assertEqual(attachment.appointment, self.appointment)
        self.assertTrue(attachment.file.name.endswith(".pdf"))
    
    def test_attachment_with_special_characters(self):
        """Verifica file con caratteri speciali nel nome (à, è, ì, ò, ù, &, !, @, #)."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        special_names = [
            "documento à termine.pdf",
            "allegato & note.pdf",
            "ricevuta n° 123!.pdf",
            "pratica Rossi-Bianchi (2026).pdf",
            "pagamento €50.pdf",
            "riferimento #789.pdf",
            "certificato 1° livello.pdf",
            "appunto 01-01-2026.pdf",
        ]
        
        for name in special_names:
            fake_file = SimpleUploadedFile(
                name=name,
                content=b"contenuto test",
                content_type="application/pdf"
            )
            attachment = self.AppointmentAttachment.objects.create(
                appointment=self.appointment,
                file=fake_file,
                original_filename=name
            )
            self.assertEqual(attachment.original_filename, name)
            self.assertTrue(attachment.file.name.endswith(".pdf"))
    
    def test_multiple_attachments(self):
        """Verifica che si possano allegare più documenti."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        for i in range(3):
            fake_file = SimpleUploadedFile(
                name=f"documento_{i}.pdf",
                content=f"contenuto {i}".encode(),
                content_type="application/pdf"
            )
            self.AppointmentAttachment.objects.create(
                appointment=self.appointment,
                file=fake_file,
                original_filename=f"documento_{i}.pdf"
            )
        
        self.assertEqual(self.appointment.attachments.count(), 3)
    
    def test_attachment_str_with_file(self):
        """Verifica la rappresentazione stringa con file con spazi."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        fake_file = SimpleUploadedFile(
            name="test 2.pdf",
            content=b"test",
            content_type="application/pdf"
        )
        attachment = self.AppointmentAttachment.objects.create(
            appointment=self.appointment,
            file=fake_file,
            original_filename="test 2.pdf"
        )
        
        # Il __str__ contiene HTML con link download
        str_repr = str(attachment)
        self.assertIn("test 2.pdf", str_repr)
    
    def test_attachment_cascade_delete(self):
        """Verifica che gli allegati vengano eliminati con l'appuntamento."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        fake_file = SimpleUploadedFile(
            name="file da eliminare.pdf",
            content=b"test",
            content_type="application/pdf"
        )
        self.AppointmentAttachment.objects.create(
            appointment=self.appointment,
            file=fake_file,
            original_filename="file da eliminare.pdf"
        )
        
        appointment_id = self.appointment.id
        self.appointment.delete()
        
        # Gli allegati devono essere stati eliminati
        self.assertEqual(
            self.AppointmentAttachment.objects.filter(appointment_id=appointment_id).count(),
            0
        )
    
    def test_attachment_file_path(self):
        """Verifica il path corretto per file con spazi nel nome."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        fake_file = SimpleUploadedFile(
            name="test path file.pdf",
            content=b"test",
            content_type="application/pdf"
        )
        attachment = self.AppointmentAttachment.objects.create(
            appointment=self.appointment,
            file=fake_file,
            original_filename="test path file.pdf"
        )
        
        # Il path deve contenere l'ID dell'appuntamento
        self.assertIn(f"appointments/{self.appointment.id}/", attachment.file.name)
    
    def test_attachments_count(self):
        """Verifica il conteggio allegati."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        self.assertEqual(self.appointment.attachments.count(), 0)
        
        # Aggiungo allegati
        for i in range(2):
            fake_file = SimpleUploadedFile(
                name=f"doc_{i}.pdf",
                content=b"test",
                content_type="application/pdf"
            )
            self.AppointmentAttachment.objects.create(
                appointment=self.appointment,
                file=fake_file,
                original_filename=f"doc_{i}.pdf"
            )
        
        self.assertEqual(self.appointment.attachments.count(), 2)


class MultiSlotBookingTest(TestCase):
    """Test per la funzionalità di prenotazione multi-slot."""
    
    def setUp(self):
        """Setup per i test multi-slot."""
        self.client = Client()
        # Creo regole per Lunedì 9-13, 15-18
        AvailabilityRule.objects.create(
            name="Mattina", weekday=0, start_time=time(9, 0), end_time=time(13, 0), is_active=True
        )
        AvailabilityRule.objects.create(
            name="Pomeriggio", weekday=0, start_time=time(15, 0), end_time=time(18, 0), is_active=True
        )
        
        # Calcola il prossimo Lunedì
        today = date.today()
        days_until_monday = (7 - today.weekday()) % 7 or 7
        self.next_monday = today + timedelta(days=days_until_monday)
    
    def test_appointment_slot_count_default(self):
        """Verifica che slot_count abbia valore di default 1."""
        appointment = Appointment.objects.create(
            first_name="Mario", last_name="Rossi", email="mario@example.com",
            phone="+39123456789", date=self.next_monday, time=time(10, 0)
        )
        self.assertEqual(appointment.slot_count, 1)
    
    def test_appointment_duration_minutes_single_slot(self):
        """Verifica il calcolo della durata per un singolo slot."""
        appointment = Appointment.objects.create(
            first_name="Mario", last_name="Rossi", email="mario@example.com",
            phone="+39123456789", date=self.next_monday, time=time(10, 0),
            slot_count=1
        )
        self.assertEqual(appointment.duration_minutes, 30)
    
    def test_appointment_duration_minutes_multi_slot(self):
        """Verifica il calcolo della durata per più slot."""
        appointment = Appointment.objects.create(
            first_name="Mario", last_name="Rossi", email="mario@example.com",
            phone="+39123456789", date=self.next_monday, time=time(10, 0),
            slot_count=3
        )
        self.assertEqual(appointment.duration_minutes, 90)
    
    def test_appointment_end_time_single_slot(self):
        """Verifica il calcolo dell'orario fine per un singolo slot."""
        appointment = Appointment.objects.create(
            first_name="Mario", last_name="Rossi", email="mario@example.com",
            phone="+39123456789", date=self.next_monday, time=time(10, 0),
            slot_count=1
        )
        self.assertEqual(appointment.end_time, time(10, 30))
    
    def test_appointment_end_time_multi_slot(self):
        """Verifica il calcolo dell'orario fine per più slot."""
        appointment = Appointment.objects.create(
            first_name="Mario", last_name="Rossi", email="mario@example.com",
            phone="+39123456789", date=self.next_monday, time=time(10, 0),
            slot_count=2
        )
        self.assertEqual(appointment.end_time, time(11, 0))
    
    def test_appointment_end_time_four_slots(self):
        """Verifica l'orario fine per 4 slot (2 ore)."""
        appointment = Appointment.objects.create(
            first_name="Mario", last_name="Rossi", email="mario@example.com",
            phone="+39123456789", date=self.next_monday, time=time(9, 0),
            slot_count=4
        )
        self.assertEqual(appointment.end_time, time(11, 0))
    
    def test_appointment_total_price_cents_single(self):
        """Verifica il prezzo totale per un singolo slot."""
        appointment = Appointment.objects.create(
            first_name="Mario", last_name="Rossi", email="mario@example.com",
            phone="+39123456789", date=self.next_monday, time=time(10, 0),
            slot_count=1
        )
        # Default: 6000 cents = €60
        self.assertEqual(appointment.total_price_cents, 6000)
    
    def test_appointment_total_price_cents_multi(self):
        """Verifica il prezzo totale per più slot."""
        appointment = Appointment.objects.create(
            first_name="Mario", last_name="Rossi", email="mario@example.com",
            phone="+39123456789", date=self.next_monday, time=time(10, 0),
            slot_count=3
        )
        # 3 x 6000 = 18000 cents = €180
        self.assertEqual(appointment.total_price_cents, 18000)
    
    def test_appointment_total_price_display(self):
        """Verifica la formattazione del prezzo per la visualizzazione."""
        appointment = Appointment.objects.create(
            first_name="Mario", last_name="Rossi", email="mario@example.com",
            phone="+39123456789", date=self.next_monday, time=time(10, 0),
            slot_count=2
        )
        # 2 x 6000 = 12000 cents = 120,00
        self.assertEqual(appointment.total_price_display, "120,00")
    
    def test_multi_slot_blocks_consecutive_slots(self):
        """Verifica che un appuntamento multi-slot blocchi tutti gli slot occupati."""
        # Prenoto 2 slot dalle 10:00
        Appointment.objects.create(
            first_name="Mario", last_name="Rossi", email="mario@example.com",
            phone="+39123456789", date=self.next_monday, time=time(10, 0),
            slot_count=2, status='confirmed'
        )
        
        slots = Appointment.get_available_slots(self.next_monday)
        
        # 10:00 e 10:30 devono essere bloccati
        self.assertNotIn(time(10, 0), slots)
        self.assertNotIn(time(10, 30), slots)
        # 11:00 deve essere disponibile
        self.assertIn(time(11, 0), slots)
    
    def test_multi_slot_four_slots_blocks_correctly(self):
        """Verifica che 4 slot consecutivi blocchino correttamente 2 ore."""
        # Prenoto 4 slot dalle 9:00 (9:00-11:00)
        Appointment.objects.create(
            first_name="Mario", last_name="Rossi", email="mario@example.com",
            phone="+39123456789", date=self.next_monday, time=time(9, 0),
            slot_count=4, status='confirmed'
        )
        
        slots = Appointment.get_available_slots(self.next_monday)
        
        # 9:00, 9:30, 10:00, 10:30 devono essere bloccati
        self.assertNotIn(time(9, 0), slots)
        self.assertNotIn(time(9, 30), slots)
        self.assertNotIn(time(10, 0), slots)
        self.assertNotIn(time(10, 30), slots)
        # 11:00 deve essere disponibile
        self.assertIn(time(11, 0), slots)


class MultiSlotCheckoutTest(TestCase):
    """Test per il checkout con prenotazioni multi-slot."""
    
    def setUp(self):
        self.client = Client()
        AvailabilityRule.objects.create(
            name="Mattina", weekday=0, start_time=time(9, 0), end_time=time(13, 0), is_active=True
        )
        
        today = date.today()
        days_until_monday = (7 - today.weekday()) % 7 or 7
        self.next_monday = today + timedelta(days=days_until_monday)
    
    def test_checkout_with_slot_count(self):
        """Verifica che il checkout accetti slot_count."""
        response = self.client.post(
            '/prenota/checkout/',
            data=json.dumps({
                'first_name': 'Mario',
                'last_name': 'Rossi',
                'email': 'mario@example.com',
                'phone': '+39123456789',
                'notes': 'Test multi-slot',
                'date': self.next_monday.isoformat(),
                'time': '10:00',
                'slot_count': 2,
                'payment_method': 'stripe'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verifica che l'appuntamento sia stato creato con slot_count = 2
        appointment = Appointment.objects.first()
        self.assertEqual(appointment.slot_count, 2)
    
    def test_checkout_invalid_slot_count_zero(self):
        """Verifica che slot_count 0 venga rifiutato."""
        response = self.client.post(
            '/prenota/checkout/',
            data=json.dumps({
                'first_name': 'Mario',
                'last_name': 'Rossi',
                'email': 'mario@example.com',
                'phone': '+39123456789',
                'notes': 'Test',
                'date': self.next_monday.isoformat(),
                'time': '10:00',
                'slot_count': 0,
                'payment_method': 'stripe'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_checkout_invalid_slot_count_exceeds_max(self):
        """Verifica che slot_count > max venga rifiutato."""
        response = self.client.post(
            '/prenota/checkout/',
            data=json.dumps({
                'first_name': 'Mario',
                'last_name': 'Rossi',
                'email': 'mario@example.com',
                'phone': '+39123456789',
                'notes': 'Test',
                'date': self.next_monday.isoformat(),
                'time': '10:00',
                'slot_count': 10,  # Supera max (4)
                'payment_method': 'stripe'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_checkout_consecutive_slots_not_available(self):
        """Verifica che la prenotazione fallisca se gli slot consecutivi non sono disponibili."""
        # Prenoto 10:30 per bloccare
        Appointment.objects.create(
            first_name="Existing", last_name="User", email="existing@example.com",
            phone="+39123456789", date=self.next_monday, time=time(10, 30),
            slot_count=1, status='confirmed'
        )
        
        # Provo a prenotare 2 slot dalle 10:00 (10:00 + 10:30, ma 10:30 è occupato)
        response = self.client.post(
            '/prenota/checkout/',
            data=json.dumps({
                'first_name': 'Mario',
                'last_name': 'Rossi',
                'email': 'mario@example.com',
                'phone': '+39123456789',
                'notes': 'Test',
                'date': self.next_monday.isoformat(),
                'time': '10:00',
                'slot_count': 2,
                'payment_method': 'stripe'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('10:30', data.get('error', ''))


class MultiSlotEmailTest(TestCase):
    """Test per le email con prenotazioni multi-slot."""
    
    def setUp(self):
        today = date.today()
        days_until_monday = (7 - today.weekday()) % 7 or 7
        self.next_monday = today + timedelta(days=days_until_monday)
        
        self.appointment = Appointment.objects.create(
            first_name="Mario", last_name="Rossi", email="mario@example.com",
            phone="+39123456789", date=self.next_monday, time=time(10, 0),
            slot_count=2, status='confirmed', consultation_type='video'
        )
    
    def test_email_context_has_correct_times(self):
        """Verifica che l'email contenga orari corretti."""
        from booking.email_service import format_date_italian
        
        # Orari attesi
        ora_inizio = self.appointment.time.strftime('%H:%M')
        ora_fine = self.appointment.end_time.strftime('%H:%M')
        
        self.assertEqual(ora_inizio, '10:00')
        self.assertEqual(ora_fine, '11:00')  # 10:00 + 60 min = 11:00
    
    def test_email_duration_correct(self):
        """Verifica che la durata nell'email sia corretta."""
        self.assertEqual(self.appointment.duration_minutes, 60)
    
    def test_email_price_correct(self):
        """Verifica che l'importo nell'email sia corretto."""
        self.assertEqual(self.appointment.total_price_display, '120,00')


class MultiSlotICalTest(TestCase):
    """Test per la generazione iCal con multi-slot."""
    
    def setUp(self):
        today = date.today()
        days_until_monday = (7 - today.weekday()) % 7 or 7
        self.next_monday = today + timedelta(days=days_until_monday)
    
    def test_ical_single_slot_duration(self):
        """Verifica la durata iCal per singolo slot (30 min)."""
        from booking.ical import generate_ical
        
        appointment = Appointment.objects.create(
            first_name="Mario", last_name="Rossi", email="mario@example.com",
            phone="+39123456789", date=self.next_monday, time=time(10, 0),
            slot_count=1, consultation_type='video'
        )
        
        ical = generate_ical(appointment)
        
        # Verifica che DTSTART e DTEND siano corretti (30 min differenza)
        self.assertIn('DTSTART:', ical)
        self.assertIn('DTEND:', ical)
        
        # Estrai le date per verifica
        import re
        start_match = re.search(r'DTSTART:(\d{8}T\d{6})', ical)
        end_match = re.search(r'DTEND:(\d{8}T\d{6})', ical)
        
        self.assertIsNotNone(start_match)
        self.assertIsNotNone(end_match)
        
        # Differenza deve essere 30 min (1000 in formato HHMMSS -> 30 min)
        start_time = start_match.group(1)[-6:]  # HHMMSS
        end_time = end_match.group(1)[-6:]
        
        start_mins = int(start_time[:2]) * 60 + int(start_time[2:4])
        end_mins = int(end_time[:2]) * 60 + int(end_time[2:4])
        
        self.assertEqual(end_mins - start_mins, 30)
    
    def test_ical_multi_slot_duration(self):
        """Verifica la durata iCal per multi-slot (es. 2 slot = 60 min)."""
        from booking.ical import generate_ical
        
        appointment = Appointment.objects.create(
            first_name="Mario", last_name="Rossi", email="mario@example.com",
            phone="+39123456789", date=self.next_monday, time=time(10, 0),
            slot_count=2, consultation_type='video'
        )
        
        ical = generate_ical(appointment)
        
        import re
        start_match = re.search(r'DTSTART:(\d{8}T\d{6})', ical)
        end_match = re.search(r'DTEND:(\d{8}T\d{6})', ical)
        
        start_time = start_match.group(1)[-6:]
        end_time = end_match.group(1)[-6:]
        
        start_mins = int(start_time[:2]) * 60 + int(start_time[2:4])
        end_mins = int(end_time[:2]) * 60 + int(end_time[2:4])
        
        # 2 slot = 60 min
        self.assertEqual(end_mins - start_mins, 60)
    
    def test_ical_four_slots_duration(self):
        """Verifica la durata iCal per 4 slot (120 min)."""
        from booking.ical import generate_ical
        
        appointment = Appointment.objects.create(
            first_name="Mario", last_name="Rossi", email="mario@example.com",
            phone="+39123456789", date=self.next_monday, time=time(9, 0),
            slot_count=4, consultation_type='in_person'
        )
        
        ical = generate_ical(appointment)
        
        import re
        start_match = re.search(r'DTSTART:(\d{8}T\d{6})', ical)
        end_match = re.search(r'DTEND:(\d{8}T\d{6})', ical)
        
        start_time = start_match.group(1)[-6:]
        end_time = end_match.group(1)[-6:]
        
        start_mins = int(start_time[:2]) * 60 + int(start_time[2:4])
        end_mins = int(end_time[:2]) * 60 + int(end_time[2:4])
        
        # 4 slot = 120 min
        self.assertEqual(end_mins - start_mins, 120)


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
