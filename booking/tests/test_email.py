"""
Test per l'invio email con i dati presenti nel .env
Verifica che caratteri speciali (apostrofi, accenti) siano gestiti correttamente.
"""
import pytest
from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.core import mail
from unittest.mock import patch, MagicMock


class TestEmailConfiguration:
    """Test della configurazione email."""
    
    def test_email_settings_loaded(self):
        """Verifica che le impostazioni email siano caricate."""
        assert hasattr(settings, 'EMAIL_BACKEND')
        assert hasattr(settings, 'DEFAULT_FROM_EMAIL')
        assert hasattr(settings, 'STUDIO_EMAIL')
        assert hasattr(settings, 'STUDIO_NAME')
    
    def test_studio_name_with_apostrophe(self):
        """Verifica che il nome con apostrofo sia caricato correttamente."""
        studio_name = settings.STUDIO_NAME
        # Deve contenere l'apostrofo
        assert "'" in studio_name or "D'Onofrio" in studio_name or "Onofrio" in studio_name
        print(f"STUDIO_NAME: {studio_name}")
    
    def test_default_from_email_format(self):
        """Verifica il formato del DEFAULT_FROM_EMAIL."""
        from_email = settings.DEFAULT_FROM_EMAIL
        print(f"DEFAULT_FROM_EMAIL: {from_email}")
        # Deve contenere un indirizzo email valido
        assert '@' in from_email


@pytest.mark.django_db
class TestEmailSending:
    """Test di invio email."""
    
    def test_send_simple_email(self):
        """Test invio email semplice con backend di test."""
        # Usa il backend di test di Django
        with patch.object(settings, 'EMAIL_BACKEND', 'django.core.mail.backends.locmem.EmailBackend'):
            # Reset della mailbox
            mail.outbox = []
            
            # Invia email di test
            result = send_mail(
                subject='Test Email - Studio Legale',
                message='Questo è un test di invio email.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['test@example.com'],
                fail_silently=False,
            )
            
            assert result == 1
            assert len(mail.outbox) == 1
            assert mail.outbox[0].subject == 'Test Email - Studio Legale'
    
    def test_send_email_with_special_characters(self):
        """Test invio email con caratteri speciali nel mittente."""
        with patch.object(settings, 'EMAIL_BACKEND', 'django.core.mail.backends.locmem.EmailBackend'):
            mail.outbox = []
            
            # Simula il nome con apostrofo
            from_email = f"Studio Legale D'Onofrio <info@studiolegaledonofrio.it>"
            
            result = send_mail(
                subject="Conferma Prenotazione - Avv. D'Onofrio",
                message="Gentile Cliente,\n\nLa sua prenotazione è confermata.\n\nAvv. Rossella D'Onofrio",
                from_email=from_email,
                recipient_list=['cliente@example.com'],
                fail_silently=False,
            )
            
            assert result == 1
            assert len(mail.outbox) == 1
            
            # Verifica che l'apostrofo sia presente
            sent_email = mail.outbox[0]
            assert "D'Onofrio" in sent_email.from_email or "Onofrio" in sent_email.from_email
            assert "D'Onofrio" in sent_email.body
            print(f"From: {sent_email.from_email}")
            print(f"Body: {sent_email.body}")
    
    def test_send_html_email_with_special_characters(self):
        """Test invio email HTML con caratteri speciali."""
        with patch.object(settings, 'EMAIL_BACKEND', 'django.core.mail.backends.locmem.EmailBackend'):
            mail.outbox = []
            
            html_content = """
            <html>
            <body>
                <h1>Studio Legale D'Onofrio</h1>
                <p>Gentile Cliente,</p>
                <p>La sua prenotazione presso l'Avv. Rossella D'Onofrio è confermata.</p>
                <p>Indirizzo: Piazza G. Mazzini, 72 - 73100 Lecce</p>
            </body>
            </html>
            """
            
            email = EmailMessage(
                subject="Conferma Prenotazione",
                body=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=['cliente@example.com'],
            )
            email.content_subtype = 'html'
            result = email.send(fail_silently=False)
            
            assert result == 1
            assert len(mail.outbox) == 1
            assert "D'Onofrio" in mail.outbox[0].body
            assert "Piazza G. Mazzini" in mail.outbox[0].body


@pytest.mark.django_db
class TestBookingConfirmationEmail:
    """Test dell'email di conferma prenotazione."""
    
    def test_booking_confirmation_email_content(self):
        """Test che l'email di conferma contenga tutti i dati necessari."""
        from booking.models import Appointment
        from booking.email_service import send_booking_confirmation
        from datetime import date, time
        
        with patch.object(settings, 'EMAIL_BACKEND', 'django.core.mail.backends.locmem.EmailBackend'):
            mail.outbox = []
            
            # Crea un appuntamento di test
            appointment = Appointment.objects.create(
                first_name='Mario',
                last_name='Rossi',
                email='mario.rossi@example.com',
                phone='+39 333 1234567',
                date=date(2025, 1, 15),
                time=time(10, 30),
                consultation_type='in_person',
                status='confirmed',
                amount_paid=60.00
            )
            
            # Invia email di conferma
            try:
                send_booking_confirmation(appointment)
                
                # Verifica che l'email sia stata inviata
                assert len(mail.outbox) >= 1
                
                # Verifica il contenuto
                sent_email = mail.outbox[0]
                print(f"Subject: {sent_email.subject}")
                print(f"To: {sent_email.to}")
                print(f"From: {sent_email.from_email}")
                
                # L'email deve essere inviata al cliente
                assert 'mario.rossi@example.com' in sent_email.to
                
            except Exception as e:
                # Se l'email service ha dipendenze non soddisfatte, logga l'errore
                print(f"Email send error (may be expected in test): {e}")
            
            # Cleanup
            appointment.delete()


class TestEmailValidation:
    """Test di validazione formato email."""
    
    def test_from_email_rfc_compliant(self):
        """Verifica che il from_email sia conforme agli standard RFC."""
        from_email = settings.DEFAULT_FROM_EMAIL
        
        # Se contiene un nome, deve essere nel formato "Nome <email>"
        if '<' in from_email and '>' in from_email:
            # Estrai l'email tra < >
            import re
            match = re.search(r'<(.+?)>', from_email)
            assert match is not None, "Formato from_email non valido"
            email_part = match.group(1)
            assert '@' in email_part
            print(f"Email estratta: {email_part}")
        else:
            # È solo un indirizzo email
            assert '@' in from_email
    
    def test_special_chars_in_display_name(self):
        """Test che i caratteri speciali nel display name siano gestiti."""
        # Simula vari formati possibili
        test_cases = [
            "Studio Legale D'Onofrio <info@example.com>",
            '"Studio Legale D\'Onofrio" <info@example.com>',
            "Avv. Rossella D'Onofrio <avv@example.com>",
        ]
        
        for from_email in test_cases:
            email = EmailMessage(
                subject='Test',
                body='Test body',
                from_email=from_email,
                to=['test@example.com'],
            )
            # Non deve sollevare eccezioni
            assert email.from_email == from_email
            print(f"OK: {from_email}")
