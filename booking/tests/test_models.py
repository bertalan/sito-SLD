"""
Test per i modelli del sistema di prenotazione.
"""
from django.test import TestCase
from datetime import date, time, timedelta

from booking.models import AvailabilityRule, BlockedDate, Appointment


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
        from booking.ical import generate_ical, generate_ical_filename
        
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
        from booking.ical import generate_ical
        
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
        from booking.ical import generate_ical_filename
        
        appointment = Appointment.objects.create(
            first_name="Test", last_name="User", email="test@example.com",
            phone="123", date=date(2026, 1, 15), time=time(10, 30),
            consultation_type='in_person'
        )
        
        filename = generate_ical_filename(appointment)
        
        self.assertIn('20260115', filename)
        self.assertIn('1030', filename)
        self.assertTrue(filename.endswith('.ics'))
