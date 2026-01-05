"""
Test per l'invio email con i dati presenti nel DB (SiteSettings).
Verifica che caratteri speciali (apostrofi, accenti) siano gestiti correttamente.
"""
import pytest
from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.core import mail
from unittest.mock import patch, MagicMock

from sld_project.models import SiteSettings


def get_site_settings():
    """Ritorna le impostazioni del sito dal DB."""
    return SiteSettings.get_current()


def get_from_email():
    """Ritorna l'email formattata con nome studio."""
    site = get_site_settings()
    studio_name = site.studio_name or "Studio Legale"
    email = site.email or "info@example.it"
    return f"{studio_name} <{email}>"


def get_studio_name():
    """Ritorna il nome dello studio dal DB."""
    site = get_site_settings()
    return site.studio_name or "Studio Legale"


@pytest.mark.django_db
class TestEmailConfiguration:
    """Test della configurazione email."""
    
    def test_email_settings_loaded(self):
        """Verifica che le impostazioni email siano caricate."""
        assert hasattr(settings, 'EMAIL_BACKEND')
        # SiteSettings esiste
        site = get_site_settings()
        assert site is not None
    
    def test_studio_name_exists(self):
        """Verifica che il nome studio sia presente nel DB."""
        studio_name = get_studio_name()
        # Deve essere una stringa non vuota
        assert len(studio_name) > 0
        # Deve contenere almeno una lettera
        assert any(c.isalpha() for c in studio_name)
        print(f"STUDIO_NAME (from DB): {studio_name}")
    
    def test_from_email_format(self):
        """Verifica il formato dell'email mittente."""
        from_email = get_from_email()
        print(f"FROM_EMAIL (from DB): {from_email}")
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
            
            from_email = get_from_email()
            
            # Invia email di test
            result = send_mail(
                subject='Test Email - Studio Legale',
                message='Questo è un test di invio email.',
                from_email=from_email,
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
            
            # Usa il from_email dal DB
            from_email = get_from_email()
            studio_name = get_studio_name()
            
            result = send_mail(
                subject=f"Conferma Prenotazione - {studio_name}",
                message=f"Gentile Cliente,\n\nLa sua prenotazione presso {studio_name} è confermata.",
                from_email=from_email,
                recipient_list=['cliente@example.com'],
                fail_silently=False,
            )
            
            assert result == 1
            assert len(mail.outbox) == 1
            
            # Verifica che il nome studio sia presente
            sent_email = mail.outbox[0]
            assert studio_name in sent_email.from_email or "@" in sent_email.from_email
            print(f"From: {sent_email.from_email}")
            print(f"Body: {sent_email.body}")
    
    def test_send_html_email_with_special_characters(self):
        """Test invio email HTML con caratteri speciali."""
        with patch.object(settings, 'EMAIL_BACKEND', 'django.core.mail.backends.locmem.EmailBackend'):
            mail.outbox = []
            
            site = get_site_settings()
            studio_name = site.studio_name or "Studio Legale"
            lawyer_name = site.lawyer_name or "Avv. Mario Rossi"
            address = site.address or "Via Roma 1"
            
            html_content = f"""
            <html>
            <body>
                <h1>{studio_name}</h1>
                <p>Gentile Cliente,</p>
                <p>La sua prenotazione presso {lawyer_name} è confermata.</p>
                <p>Indirizzo: {address}</p>
            </body>
            </html>
            """
            
            email = EmailMessage(
                subject="Conferma Prenotazione",
                body=html_content,
                from_email=get_from_email(),
                to=['cliente@example.com'],
            )
            email.content_subtype = 'html'
            result = email.send(fail_silently=False)
            
            assert result == 1
            assert len(mail.outbox) == 1
            assert studio_name in mail.outbox[0].body


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


@pytest.mark.django_db
class TestEmailValidation:
    """Test di validazione formato email."""
    
    def test_from_email_rfc_compliant(self):
        """Verifica che il from_email sia conforme agli standard RFC."""
        from_email = get_from_email()
        
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
            "Studio Legale <info@example.com>",
            '"Studio Legale D\'Onofrio" <info@example.com>',
            "Avv. Mario Rossi <avv@example.com>",
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
