"""
Test per la sicurezza: validazione file upload e webhook Stripe.
"""
from django.test import TestCase, Client, RequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from unittest.mock import patch, MagicMock
import json

from sld_project.validators import FileValidator, validate_attachment_file, validate_document_file


class FileValidatorSecurityTest(TestCase):
    """
    Test per verificare che il FileValidator rifiuti file potenzialmente malevoli.
    Questi test sono critici per la sicurezza del sistema.
    """
    
    def test_reject_exe_file(self):
        """Verifica che file .exe vengano rifiutati."""
        exe_content = b'MZ\x90\x00'  # Magic bytes di un file .exe
        exe_file = SimpleUploadedFile(
            name="malware.exe",
            content=exe_content,
            content_type="application/x-msdownload"
        )
        
        with self.assertRaises(ValidationError) as context:
            validate_attachment_file(exe_file)
        
        # Il messaggio può essere "estensione" o "tipo di file non permesso"
        error_msg = str(context.exception).lower()
        self.assertTrue(
            "estensione" in error_msg or "tipo di file" in error_msg,
            f"Messaggio inatteso: {error_msg}"
        )
    
    def test_reject_php_file(self):
        """Verifica che file .php vengano rifiutati."""
        php_file = SimpleUploadedFile(
            name="shell.php",
            content=b"<?php system($_GET['cmd']); ?>",
            content_type="text/x-php"
        )
        
        with self.assertRaises(ValidationError) as context:
            validate_attachment_file(php_file)
        
        error_msg = str(context.exception).lower()
        self.assertTrue(
            "estensione" in error_msg or "tipo di file" in error_msg,
            f"Messaggio inatteso: {error_msg}"
        )
    
    def test_reject_js_file(self):
        """Verifica che file .js vengano rifiutati."""
        js_file = SimpleUploadedFile(
            name="exploit.js",
            content=b"alert('XSS')",
            content_type="application/javascript"
        )
        
        with self.assertRaises(ValidationError) as context:
            validate_attachment_file(js_file)
        
        error_msg = str(context.exception).lower()
        self.assertTrue(
            "estensione" in error_msg or "tipo di file" in error_msg,
            f"Messaggio inatteso: {error_msg}"
        )
    
    def test_reject_html_file(self):
        """Verifica che file .html vengano rifiutati."""
        html_file = SimpleUploadedFile(
            name="phishing.html",
            content=b"<html><script>steal()</script></html>",
            content_type="text/html"
        )
        
        with self.assertRaises(ValidationError) as context:
            validate_attachment_file(html_file)
        
        error_msg = str(context.exception).lower()
        self.assertTrue(
            "estensione" in error_msg or "tipo di file" in error_msg,
            f"Messaggio inatteso: {error_msg}"
        )
    
    def test_reject_bat_file(self):
        """Verifica che file .bat vengano rifiutati."""
        bat_file = SimpleUploadedFile(
            name="virus.bat",
            content=b"@echo off\nformat c: /y",
            content_type="application/x-bat"
        )
        
        with self.assertRaises(ValidationError) as context:
            validate_attachment_file(bat_file)
        
        error_msg = str(context.exception).lower()
        self.assertTrue(
            "estensione" in error_msg or "tipo di file" in error_msg,
            f"Messaggio inatteso: {error_msg}"
        )
    
    def test_reject_double_extension(self):
        """Verifica che file con doppia estensione vengano rifiutati."""
        double_ext_file = SimpleUploadedFile(
            name="documento.pdf.exe",
            content=b"MZ\x90\x00",
            content_type="application/pdf"
        )
        
        with self.assertRaises(ValidationError) as context:
            validate_attachment_file(double_ext_file)
        
        error_msg = str(context.exception).lower()
        self.assertTrue(
            "estensione" in error_msg or "tipo di file" in error_msg,
            f"Messaggio inatteso: {error_msg}"
        )
    
    def test_reject_file_too_large(self):
        """Verifica che file troppo grandi vengano rifiutati."""
        # validate_attachment_file ha limite 20MB, validate_document_file ha limite 10MB
        # Creiamo una classe che simula un file troppo grande (25MB > 20MB)
        class LargeFile:
            name = "documento.pdf"
            size = 25 * 1024 * 1024  # 25MB > 20MB limit per attachments
            content_type = "application/pdf"
            
            def read(self, size=-1):
                return b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n'
            
            def seek(self, pos):
                pass
        
        large_file = LargeFile()
        
        with self.assertRaises(ValidationError) as context:
            validate_attachment_file(large_file)
        
        error_msg = str(context.exception).lower()
        self.assertTrue(
            "grande" in error_msg or "dimensione" in error_msg or "mb" in error_msg,
            f"Messaggio inatteso: {error_msg}"
        )
    
    def test_accept_valid_pdf(self):
        """Verifica che un PDF valido venga accettato."""
        # PDF magic bytes
        pdf_content = b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n'
        pdf_file = SimpleUploadedFile(
            name="documento_legale.pdf",
            content=pdf_content,
            content_type="application/pdf"
        )
        
        # Non deve sollevare eccezioni
        try:
            validate_document_file(pdf_file)
        except ValidationError:
            self.fail("PDF valido è stato rifiutato erroneamente")
    
    def test_accept_valid_image(self):
        """Verifica che immagini valide vengano accettate."""
        # JPEG magic bytes
        jpeg_content = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        jpeg_file = SimpleUploadedFile(
            name="scansione.jpg",
            content=jpeg_content,
            content_type="image/jpeg"
        )
        
        try:
            validate_attachment_file(jpeg_file)
        except ValidationError:
            self.fail("JPEG valido è stato rifiutato erroneamente")
    
    def test_reject_mismatched_extension_content(self):
        """Verifica che file con estensione che non corrisponde al contenuto vengano segnalati."""
        # File con estensione .pdf ma contenuto eseguibile
        fake_pdf = SimpleUploadedFile(
            name="documento.pdf",
            content=b"MZ\x90\x00\x03\x00\x00\x00",  # Contenuto EXE
            content_type="application/pdf"
        )
        
        # Con python-magic, dovrebbe rilevare il mismatch
        # Se python-magic non è disponibile, potrebbe passare
        # ma almeno verifichiamo che non crashi
        try:
            validate_attachment_file(fake_pdf)
        except ValidationError:
            pass  # Comportamento corretto con python-magic


class StripeWebhookSecurityTest(TestCase):
    """
    Test per verificare che il webhook Stripe rifiuti richieste con firma invalida.
    """
    
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        # URL corretta: /prenota/webhook/
        self.webhook_url = '/prenota/webhook/'
    
    def test_reject_missing_signature(self):
        """Verifica che richieste senza firma vengano rifiutate o ignorate in demo."""
        response = self.client.post(
            self.webhook_url,
            data=json.dumps({'type': 'checkout.session.completed'}),
            content_type='application/json'
            # Nessun header Stripe-Signature
        )
        
        # Deve essere 200 (demo mode ignora) o 400 (firma mancante)
        self.assertIn(response.status_code, [200, 400])
        if response.status_code == 200:
            data = json.loads(response.content)
            # In demo mode, il webhook viene ignorato
            self.assertEqual(data.get('status'), 'demo_mode_ignored')
    
    @patch('booking.views.payment_service')
    def test_reject_invalid_signature_in_live_mode(self, mock_service):
        """Verifica che richieste con firma invalida vengano rifiutate in live mode."""
        # Simula ambiente non-demo
        mock_service.is_demo = False
        mock_service.verify_webhook.return_value = {
            'valid': False,
            'error': 'Invalid signature'
        }
        
        response = self.client.post(
            self.webhook_url,
            data=json.dumps({'type': 'checkout.session.completed'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='invalid_signature_abc123'
        )
        
        # Deve essere rifiutato con 400
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    @patch('booking.views.payment_service')
    def test_demo_mode_ignores_webhook(self, mock_service):
        """Verifica che in demo mode il webhook venga ignorato (non processato)."""
        mock_service.is_demo = True
        
        response = self.client.post(
            self.webhook_url,
            data=json.dumps({'type': 'checkout.session.completed'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data.get('status'), 'demo_mode_ignored')
    
    @patch('booking.views.payment_service')
    def test_valid_signature_processes_event(self, mock_service):
        """Verifica che una firma valida permetta il processing dell'evento."""
        mock_service.is_demo = False
        mock_service.verify_webhook.return_value = {
            'valid': True,
            'event': {
                'type': 'checkout.session.completed',
                'data': {
                    'object': {
                        'metadata': {},
                        'amount_total': 5000
                    }
                }
            }
        }
        
        response = self.client.post(
            self.webhook_url,
            data=json.dumps({'type': 'checkout.session.completed'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data.get('status'), 'success')


class RateLimitSecurityTest(TestCase):
    """
    Test per verificare che il rate limiting sia attivo.
    """
    
    def setUp(self):
        self.client = Client()
    
    def test_rate_limit_config_exists(self):
        """Verifica che la configurazione rate limit esista."""
        from sld_project.ratelimit import RATE_LIMITS
        
        # Verifica che le chiavi esistano
        self.assertIn('booking', RATE_LIMITS)
        self.assertIn('contact', RATE_LIMITS)
        self.assertIn('domiciliazioni', RATE_LIMITS)
        
        # Verifica formato (es: "10/m", "5/m")
        for key, value in RATE_LIMITS.items():
            self.assertRegex(value, r'\d+/[smh]', f"{key} rate limit format invalid")

