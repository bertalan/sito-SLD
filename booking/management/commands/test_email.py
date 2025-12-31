"""
Comando per testare la connessione SMTP e l'invio email.
Uso: python manage.py test_email [email_destinatario]
"""
import socket
import smtplib
from django.core.management.base import BaseCommand
from django.core.mail import send_mail, get_connection, EmailMessage
from django.conf import settings


class Command(BaseCommand):
    help = 'Testa la connessione SMTP e l\'invio email'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'recipient',
            nargs='?',
            default=None,
            help='Email destinatario per il test (default: STUDIO_EMAIL)'
        )
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Mostra dettagli completi della connessione SMTP'
        )
    
    def handle(self, *args, **options):
        recipient = options['recipient'] or settings.STUDIO_EMAIL
        verbose = options['debug']
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.HTTP_INFO("📧 TEST CONFIGURAZIONE EMAIL"))
        self.stdout.write("=" * 60 + "\n")
        
        # 1. Mostra configurazione corrente
        self._show_config(verbose)
        
        # 2. Test connessione di rete al server SMTP
        self._test_network_connection()
        
        # 3. Test connessione SMTP
        self._test_smtp_connection(verbose)
        
        # 4. Test invio email
        self._test_send_email(recipient)
        
        self.stdout.write("\n" + "=" * 60 + "\n")
    
    def _show_config(self, verbose):
        """Mostra la configurazione email corrente."""
        self.stdout.write(self.style.MIGRATE_HEADING("\n📋 CONFIGURAZIONE ATTUALE:\n"))
        
        config = {
            'EMAIL_BACKEND': settings.EMAIL_BACKEND,
            'EMAIL_HOST': settings.EMAIL_HOST,
            'EMAIL_PORT': settings.EMAIL_PORT,
            'EMAIL_USE_TLS': settings.EMAIL_USE_TLS,
            'EMAIL_USE_SSL': getattr(settings, 'EMAIL_USE_SSL', False),
            'EMAIL_HOST_USER': settings.EMAIL_HOST_USER,
            'EMAIL_HOST_PASSWORD': '***' + settings.EMAIL_HOST_PASSWORD[-4:] if settings.EMAIL_HOST_PASSWORD else '(vuota)',
            'DEFAULT_FROM_EMAIL': settings.DEFAULT_FROM_EMAIL,
            'STUDIO_EMAIL': settings.STUDIO_EMAIL,
            'STUDIO_NAME': settings.STUDIO_NAME,
        }
        
        for key, value in config.items():
            if 'PASSWORD' in key and not verbose:
                self.stdout.write(f"  {key}: {'✓ configurata' if value != '(vuota)' else '✗ NON configurata'}")
            else:
                self.stdout.write(f"  {key}: {value}")
        
        # Verifica problemi comuni
        self.stdout.write(self.style.MIGRATE_HEADING("\n🔍 VERIFICA CONFIGURAZIONE:\n"))
        
        issues = []
        
        if not settings.EMAIL_HOST:
            issues.append("EMAIL_HOST non configurato")
        
        if not settings.EMAIL_HOST_USER:
            issues.append("EMAIL_HOST_USER non configurato")
        
        if not settings.EMAIL_HOST_PASSWORD:
            issues.append("EMAIL_HOST_PASSWORD non configurata")
        
        if settings.EMAIL_USE_TLS and getattr(settings, 'EMAIL_USE_SSL', False):
            issues.append("EMAIL_USE_TLS e EMAIL_USE_SSL sono entrambi True (solo uno dovrebbe essere attivo)")
        
        if settings.EMAIL_PORT == 587 and not settings.EMAIL_USE_TLS:
            issues.append("Porta 587 richiede solitamente TLS (EMAIL_USE_TLS=True)")
        
        if settings.EMAIL_PORT == 465 and not getattr(settings, 'EMAIL_USE_SSL', False):
            issues.append("Porta 465 richiede solitamente SSL (EMAIL_USE_SSL=True)")
        
        if 'console' in settings.EMAIL_BACKEND.lower():
            issues.append("Backend è Console - le email non saranno inviate realmente!")
        
        if issues:
            for issue in issues:
                self.stdout.write(self.style.WARNING(f"  ⚠️  {issue}"))
        else:
            self.stdout.write(self.style.SUCCESS("  ✓ Configurazione sembra corretta"))
    
    def _test_network_connection(self):
        """Testa la connessione di rete al server SMTP."""
        self.stdout.write(self.style.MIGRATE_HEADING(f"\n🌐 TEST CONNESSIONE RETE A {settings.EMAIL_HOST}:{settings.EMAIL_PORT}\n"))
        
        try:
            sock = socket.create_connection(
                (settings.EMAIL_HOST, settings.EMAIL_PORT),
                timeout=10
            )
            sock.close()
            self.stdout.write(self.style.SUCCESS(f"  ✓ Connessione di rete OK"))
        except socket.timeout:
            self.stdout.write(self.style.ERROR(f"  ✗ TIMEOUT - Il server non risponde"))
            self.stdout.write(self.style.WARNING("    Possibili cause: firewall, porta bloccata, server offline"))
        except socket.gaierror as e:
            self.stdout.write(self.style.ERROR(f"  ✗ ERRORE DNS - Impossibile risolvere {settings.EMAIL_HOST}"))
            self.stdout.write(self.style.WARNING(f"    Errore: {e}"))
        except ConnectionRefusedError:
            self.stdout.write(self.style.ERROR(f"  ✗ CONNESSIONE RIFIUTATA"))
            self.stdout.write(self.style.WARNING("    Il server rifiuta la connessione sulla porta specificata"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ✗ ERRORE: {type(e).__name__}: {e}"))
    
    def _test_smtp_connection(self, verbose):
        """Testa la connessione SMTP con autenticazione."""
        self.stdout.write(self.style.MIGRATE_HEADING("\n🔐 TEST AUTENTICAZIONE SMTP:\n"))
        
        try:
            # Usa il metodo appropriato in base a TLS/SSL
            if getattr(settings, 'EMAIL_USE_SSL', False):
                server = smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10)
            else:
                server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10)
                if settings.EMAIL_USE_TLS:
                    server.starttls()
            
            if verbose:
                server.set_debuglevel(1)
            
            # Tentativo di login
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            self.stdout.write(self.style.SUCCESS("  ✓ Autenticazione SMTP riuscita!"))
            
            server.quit()
            
        except smtplib.SMTPAuthenticationError as e:
            self.stdout.write(self.style.ERROR(f"  ✗ ERRORE AUTENTICAZIONE"))
            self.stdout.write(self.style.WARNING(f"    Codice: {e.smtp_code}"))
            self.stdout.write(self.style.WARNING(f"    Messaggio: {e.smtp_error.decode() if isinstance(e.smtp_error, bytes) else e.smtp_error}"))
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("    Possibili cause:"))
            self.stdout.write("    - Username o password errati")
            self.stdout.write("    - Account bloccato o richiede verifica")
            self.stdout.write("    - Per Gmail: richiede 'App Password' (non la password normale)")
            self.stdout.write("    - Per alcuni provider: richiede abilitare SMTP nelle impostazioni")
        
        except smtplib.SMTPConnectError as e:
            self.stdout.write(self.style.ERROR(f"  ✗ ERRORE CONNESSIONE SMTP: {e}"))
        
        except smtplib.SMTPException as e:
            self.stdout.write(self.style.ERROR(f"  ✗ ERRORE SMTP: {type(e).__name__}: {e}"))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ✗ ERRORE: {type(e).__name__}: {e}"))
    
    def _test_send_email(self, recipient):
        """Testa l'invio effettivo di un'email."""
        self.stdout.write(self.style.MIGRATE_HEADING(f"\n📤 TEST INVIO EMAIL A: {recipient}\n"))
        
        try:
            # Usa il backend Django
            result = send_mail(
                subject='[TEST] Email di prova - Studio Legale D\'Onofrio',
                message=f"""Questa è un'email di test inviata dal sistema di prenotazione.

Se ricevi questa email, la configurazione SMTP è corretta!

Configurazione usata:
- Server: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}
- Mittente: {settings.DEFAULT_FROM_EMAIL}
- TLS: {settings.EMAIL_USE_TLS}

Timestamp: {__import__('datetime').datetime.now().isoformat()}

---
Studio Legale D'Onofrio
Sistema automatico di prenotazione
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            
            if result == 1:
                self.stdout.write(self.style.SUCCESS(f"  ✓ Email inviata con successo a {recipient}!"))
                self.stdout.write(self.style.SUCCESS("    Controlla la casella di posta (anche SPAM/Junk)"))
            else:
                self.stdout.write(self.style.WARNING(f"  ⚠️  Risultato invio: {result} (atteso 1)"))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ✗ ERRORE INVIO: {type(e).__name__}"))
            self.stdout.write(self.style.ERROR(f"    {e}"))
            
            # Suggerimenti specifici per errori comuni
            error_str = str(e).lower()
            if 'authentication' in error_str:
                self.stdout.write(self.style.WARNING("\n    💡 Suggerimento: Verifica username e password"))
            elif 'connection' in error_str or 'refused' in error_str:
                self.stdout.write(self.style.WARNING("\n    💡 Suggerimento: Verifica host, porta e firewall"))
            elif 'tls' in error_str or 'ssl' in error_str:
                self.stdout.write(self.style.WARNING("\n    💡 Suggerimento: Prova a invertire EMAIL_USE_TLS"))
            elif 'timeout' in error_str:
                self.stdout.write(self.style.WARNING("\n    💡 Suggerimento: Il server non risponde, verifica l'host"))
