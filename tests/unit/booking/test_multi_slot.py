"""
Test per la funzionalità multi-slot del sistema di prenotazione.
"""
from django.test import TestCase, Client
from datetime import date, time, timedelta
import json
import re

from booking.models import AvailabilityRule, Appointment


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
        start_match = re.search(r'DTSTART:(\d{8}T\d{6})', ical)
        end_match = re.search(r'DTEND:(\d{8}T\d{6})', ical)
        
        self.assertIsNotNone(start_match)
        self.assertIsNotNone(end_match)
        
        # Differenza deve essere 30 min
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
        
        start_match = re.search(r'DTSTART:(\d{8}T\d{6})', ical)
        end_match = re.search(r'DTEND:(\d{8}T\d{6})', ical)
        
        start_time = start_match.group(1)[-6:]
        end_time = end_match.group(1)[-6:]
        
        start_mins = int(start_time[:2]) * 60 + int(start_time[2:4])
        end_mins = int(end_time[:2]) * 60 + int(end_time[2:4])
        
        # 4 slot = 120 min
        self.assertEqual(end_mins - start_mins, 120)
