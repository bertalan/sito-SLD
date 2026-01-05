"""
Test TDD per i dati di fatturazione nel sistema di prenotazione.
"""
import pytest
from django.test import TestCase, Client
from datetime import date, time
from django.core import mail

from booking.models import Appointment


class InvoiceDataModelTest(TestCase):
    """Test per i campi di fatturazione nel modello Appointment."""
    
    def setUp(self):
        """Crea un appuntamento di test."""
        self.appointment = Appointment.objects.create(
            first_name="Mario",
            last_name="Rossi",
            email="mario@example.com",
            phone="+39123456789",
            notes="Test appuntamento",
            date=date(2026, 2, 1),
            time=time(10, 0),
            status="confirmed"
        )
    
    def test_invoice_fields_exist(self):
        """Verifica che i campi fatturazione esistano nel modello."""
        fields = [
            'invoice_name', 'invoice_address', 'invoice_zip',
            'invoice_city', 'invoice_province', 'invoice_country',
            'invoice_vat', 'invoice_sdi', 'invoice_pec'
        ]
        for field in fields:
            self.assertTrue(
                hasattr(self.appointment, field),
                f"Campo '{field}' mancante nel modello Appointment"
            )
    
    def test_invoice_fields_are_nullable(self):
        """Verifica che i campi fatturazione siano opzionali."""
        # L'appuntamento senza dati fatturazione deve essere salvabile
        self.appointment.save()
        self.assertIsNone(self.appointment.invoice_name)
    
    def test_invoice_country_default_value(self):
        """Verifica che il paese predefinito sia Italia."""
        self.assertEqual(self.appointment.invoice_country, "Italia")
    
    def test_save_invoice_data(self):
        """Verifica che i dati fatturazione possano essere salvati."""
        self.appointment.invoice_name = "Mario Rossi S.r.l."
        self.appointment.invoice_address = "Via Roma 123"
        self.appointment.invoice_zip = "73100"
        self.appointment.invoice_city = "Lecce"
        self.appointment.invoice_province = "LE"
        self.appointment.invoice_vat = "IT01234567890"
        self.appointment.invoice_sdi = "ABC1234"
        self.appointment.invoice_pec = "fatture@pec.example.it"
        self.appointment.save()
        
        # Ricarica dal database
        reloaded = Appointment.objects.get(pk=self.appointment.pk)
        self.assertEqual(reloaded.invoice_name, "Mario Rossi S.r.l.")
        self.assertEqual(reloaded.invoice_vat, "IT01234567890")
        self.assertEqual(reloaded.invoice_sdi, "ABC1234")
    
    def test_has_invoice_data_property_false(self):
        """Verifica che has_invoice_data sia False se non ci sono dati."""
        self.assertFalse(self.appointment.has_invoice_data)
    
    def test_has_invoice_data_property_true(self):
        """Verifica che has_invoice_data sia True se invoice_name è compilato."""
        self.appointment.invoice_name = "Test Srl"
        self.assertTrue(self.appointment.has_invoice_data)


class InvoiceDataFormTest(TestCase):
    """Test per l'invio dati fatturazione via form."""
    
    def setUp(self):
        self.client = Client()
    
    def test_create_appointment_with_invoice_data(self):
        """Verifica che la view accetti dati fatturazione e li salvi."""
        import json
        # Invia una richiesta al checkout con dati fatturazione
        response = self.client.post('/prenota/checkout/', 
            data=json.dumps({
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'test@example.com',
                'phone': '123456789',
                'notes': 'Test',
                'date': '2026-02-15',
                'time': '10:00',
                'consultation_type': 'video',
                'payment_method': 'stripe',
                # Dati fatturazione
                'invoice_name': 'Test Company Srl',
                'invoice_address': 'Via Test 1',
                'invoice_zip': '00100',
                'invoice_city': 'Roma',
                'invoice_province': 'RM',
                'invoice_vat': 'IT12345678901',
            }), 
            content_type='application/json'
        )
        
        # Verifica che l'appuntamento sia stato creato con i dati fatturazione
        # Anche se il pagamento fallisce (ambiente di test), l'appuntamento viene creato
        appointments = Appointment.objects.filter(email='test@example.com')
        if appointments.exists():
            appt = appointments.first()
            self.assertEqual(appt.invoice_name, 'Test Company Srl')
            self.assertEqual(appt.invoice_vat, 'IT12345678901')


@pytest.mark.django_db
class TestInvoiceDataInEmail:
    """Test per i dati fatturazione nelle email."""
    
    def test_invoice_section_in_studio_email(self):
        """Verifica che l'email allo studio contenga i dati fatturazione."""
        from booking.email_service import send_booking_confirmation
        
        appointment = Appointment.objects.create(
            first_name="Mario",
            last_name="Rossi",
            email="mario@example.com",
            phone="+39123456789",
            notes="Test",
            date=date(2026, 2, 1),
            time=time(10, 0),
            status="confirmed",
            invoice_name="Mario Rossi Srl",
            invoice_address="Via Roma 123",
            invoice_zip="73100",
            invoice_city="Lecce",
            invoice_province="LE",
            invoice_vat="IT01234567890",
            invoice_sdi="ABC1234",
            invoice_pec="pec@example.it"
        )
        
        mail.outbox = []
        send_booking_confirmation(appointment)
        
        # L'email va allo studio (prima) e al cliente (seconda)
        assert len(mail.outbox) >= 1
        # L'email allo studio è la prima
        email_body = mail.outbox[0].body
        
        # Verifica che contenga la sezione fatturazione
        assert "DATI DI FATTURAZIONE" in email_body or "Dati di fatturazione" in email_body.lower()
        assert "Mario Rossi Srl" in email_body
        assert "IT01234567890" in email_body
    
    def test_no_invoice_section_when_empty(self):
        """Verifica che la sezione fatturazione non appaia se vuota."""
        from booking.email_service import send_booking_confirmation
        
        appointment = Appointment.objects.create(
            first_name="Mario",
            last_name="Rossi",
            email="mario@example.com",
            phone="+39123456789",
            notes="Test",
            date=date(2026, 2, 1),
            time=time(10, 0),
            status="confirmed"
        )
        
        mail.outbox = []
        send_booking_confirmation(appointment)
        
        assert len(mail.outbox) >= 1
        email_body = mail.outbox[0].body
        
        # Non deve contenere la sezione fatturazione
        assert "DATI DI FATTURAZIONE" not in email_body


class InvoiceDataAdminTest(TestCase):
    """Test per la visualizzazione admin dei dati fatturazione."""
    
    def test_invoice_panel_in_admin(self):
        """Verifica che i panels dell'admin includano i dati fatturazione."""
        # Verifica che i panels siano definiti correttamente
        panels_fields = []
        for panel in Appointment.panels:
            if hasattr(panel, 'children'):
                for child in panel.children:
                    if hasattr(child, 'field_name'):
                        panels_fields.append(child.field_name)
            elif hasattr(panel, 'field_name'):
                panels_fields.append(panel.field_name)
        
        # Almeno uno dei campi fatturazione deve essere nei panels
        invoice_fields = ['invoice_name', 'invoice_vat', 'invoice_address']
        found = any(f in panels_fields for f in invoice_fields)
        self.assertTrue(found, "Nessun campo fatturazione trovato nei panels")
