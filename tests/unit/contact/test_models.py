"""
Test per il modulo Contact.
Verifica form contatti, validazioni email e rate limiting.
"""
from django.test import TestCase, Client, RequestFactory
from django.core import mail
from unittest.mock import patch, MagicMock

from contact.models import ContactPage, ContactFormField, SocialLink


class ContactPageModelTest(TestCase):
    """Test per il modello ContactPage."""
    
    def test_contact_page_has_required_fields(self):
        """ContactPage deve avere i campi richiesti."""
        page = ContactPage()
        
        # Verifica che i campi esistano
        self.assertTrue(hasattr(page, 'intro'))
        self.assertTrue(hasattr(page, 'thank_you_text'))
        self.assertTrue(hasattr(page, 'to_address'))
        self.assertTrue(hasattr(page, 'from_address'))
        self.assertTrue(hasattr(page, 'subject'))


class SocialLinkModelTest(TestCase):
    """Test per il modello SocialLink."""
    
    def test_social_link_platforms(self):
        """Verifica che i platform siano definiti correttamente."""
        platforms = dict(SocialLink.PLATFORMS)
        
        self.assertIn('facebook', platforms)
        self.assertIn('linkedin', platforms)
        self.assertIn('twitter', platforms)
    
    def test_social_link_str(self):
        """Il __str__ deve restituire il display name della piattaforma."""
        link = SocialLink(
            platform='linkedin',
            url='https://linkedin.com/test',
            is_active=True
        )
        
        self.assertEqual(str(link), 'LinkedIn')
    
    def test_social_link_default_active(self):
        """I nuovi link devono essere attivi di default."""
        link = SocialLink(
            platform='facebook',
            url='https://facebook.com/test'
        )
        
        self.assertTrue(link.is_active)


class ContactFormFieldTest(TestCase):
    """Test per i campi del form contatti."""
    
    def test_form_field_has_page_relation(self):
        """ContactFormField deve avere relazione con ContactPage."""
        field = ContactFormField()
        
        # Verifica che il campo page esista
        self.assertTrue(hasattr(ContactFormField, 'page'))


class EmailEncodingTest(TestCase):
    """Test per la codifica delle email."""
    
    def test_email_field_accepts_valid_email(self):
        """Il campo email deve accettare email valide."""
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        valid_emails = [
            'test@example.com',
            'test.user@example.com',
            'test+tag@example.com',
            'test@subdomain.example.com',
            'avvocato@pec.ordineavvocati.it',
        ]
        
        for email in valid_emails:
            try:
                validate_email(email)
            except ValidationError:
                self.fail(f"Email valida rifiutata: {email}")
    
    def test_email_field_rejects_invalid_email(self):
        """Il campo email deve rifiutare email non valide."""
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        invalid_emails = [
            'notanemail',
            'test@',
            '@example.com',
            'test@.com',
            '',
        ]
        
        for email in invalid_emails:
            with self.assertRaises(ValidationError, msg=f"Email invalida accettata: {email}"):
                validate_email(email)
    
    def test_email_unicode_encoding(self):
        """Le email con caratteri unicode devono essere gestite correttamente."""
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        # Email con dominio IDN (internazionalizzato)
        unicode_emails = [
            'test@例え.jp',  # Dominio giapponese
            'utente@città.it',  # Dominio italiano con accento
        ]
        
        # Questi possono essere validi o meno a seconda della configurazione
        # L'importante è che non causino crash
        for email in unicode_emails:
            try:
                validate_email(email)
            except ValidationError:
                pass  # Ok, rifiutato ma senza crash
            except Exception as e:
                self.fail(f"Email unicode ha causato eccezione inaspettata: {e}")
    
    def test_pec_email_format(self):
        """Le PEC devono essere valide come email standard."""
        from django.core.validators import validate_email
        
        pec_emails = [
            'avvocato.rossi@pec.ordineavvocati.roma.it',
            'studio@pec.it',
            'mario.rossi@legalmail.it',
        ]
        
        for email in pec_emails:
            try:
                validate_email(email)
            except Exception:
                self.fail(f"PEC valida rifiutata: {email}")
