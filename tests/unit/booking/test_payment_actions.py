"""
Test TDD per le azioni di pagamento sugli appuntamenti:
1. Rimborso pagamento (quando annullato)
2. Invio link pagamento (quando in attesa)
"""
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import date, time
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model

from booking.models import Appointment


class TestRefundPayment(TestCase):
    """Test per la funzionalità di rimborso."""
    
    def setUp(self):
        self.appointment = Appointment.objects.create(
            first_name="Mario",
            last_name="Rossi",
            email="mario@example.com",
            phone="+39123456789",
            notes="Test",
            date=date(2026, 2, 15),
            time=time(10, 0),
            status='cancelled',
            payment_method='stripe',
            stripe_payment_intent_id='pi_test_123456',
            amount_paid=Decimal('60.00'),
        )
    
    def test_can_refund_returns_true_when_cancelled_and_paid(self):
        """Un appuntamento annullato con pagamento può essere rimborsato."""
        self.assertTrue(self.appointment.can_refund)
    
    def test_can_refund_returns_false_when_not_cancelled(self):
        """Un appuntamento non annullato non può essere rimborsato."""
        self.appointment.status = 'confirmed'
        self.appointment.save()
        self.assertFalse(self.appointment.can_refund)
    
    def test_can_refund_returns_false_when_no_payment(self):
        """Un appuntamento senza pagamento non può essere rimborsato."""
        self.appointment.amount_paid = Decimal('0.00')
        self.appointment.save()
        self.assertFalse(self.appointment.can_refund)
    
    def test_can_refund_returns_false_when_already_refunded(self):
        """Un appuntamento già rimborsato non può essere rimborsato di nuovo."""
        self.appointment.refund_id = 're_test_123'
        self.appointment.save()
        self.assertFalse(self.appointment.can_refund)
    
    @patch('stripe.Refund.create')
    def test_refund_stripe_payment_success(self, mock_refund_create):
        """Il rimborso Stripe va a buon fine."""
        from booking.payment_service import refund_payment
        
        # Mock Stripe refund response
        mock_refund = MagicMock()
        mock_refund.id = 're_test_456'
        mock_refund_create.return_value = mock_refund
        
        result = refund_payment(self.appointment)
        
        self.assertTrue(result['success'])
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.refund_id, 're_test_456')
        self.assertIsNotNone(self.appointment.refunded_at)
    
    @patch('requests.post')
    @patch('requests.get')
    def test_refund_paypal_payment_success(self, mock_get, mock_post):
        """Il rimborso PayPal va a buon fine."""
        from booking.payment_service import refund_payment
        
        self.appointment.payment_method = 'paypal'
        self.appointment.paypal_payment_id = 'PAYPAL_123'
        self.appointment.stripe_payment_intent_id = ''
        self.appointment.save()
        
        # Mock GET order details
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            'purchase_units': [{
                'payments': {
                    'captures': [{'id': 'CAPTURE_123'}]
                }
            }]
        }
        mock_get.return_value = mock_get_response
        
        # Mock POST per OAuth (prima chiamata) e refund (seconda chiamata)
        mock_oauth_response = MagicMock()
        mock_oauth_response.status_code = 200
        mock_oauth_response.json.return_value = {'access_token': 'test_token', 'expires_in': 3600}
        
        mock_refund_response = MagicMock()
        mock_refund_response.status_code = 201
        mock_refund_response.json.return_value = {'id': 'REFUND_PAYPAL_456', 'status': 'COMPLETED'}
        
        mock_post.side_effect = [mock_oauth_response, mock_refund_response]
        
        result = refund_payment(self.appointment)
        
        self.assertTrue(result['success'])


class TestSendPaymentLink(TestCase):
    """Test per l'invio del link di pagamento."""
    
    def setUp(self):
        self.appointment = Appointment.objects.create(
            first_name="Luigi",
            last_name="Verdi",
            email="luigi@example.com",
            phone="+39987654321",
            notes="Test pending",
            date=date(2026, 2, 20),
            time=time(14, 30),
            status='pending',
            payment_method='stripe',
            amount_paid=Decimal('0.00'),
        )
    
    def test_can_send_payment_link_returns_true_when_pending(self):
        """Un appuntamento in attesa può ricevere il link di pagamento."""
        self.assertTrue(self.appointment.can_send_payment_link)
    
    def test_can_send_payment_link_returns_false_when_confirmed(self):
        """Un appuntamento confermato non ha bisogno del link."""
        self.appointment.status = 'confirmed'
        self.appointment.save()
        self.assertFalse(self.appointment.can_send_payment_link)
    
    def test_can_send_payment_link_returns_false_when_cancelled(self):
        """Un appuntamento annullato non può ricevere il link."""
        self.appointment.status = 'cancelled'
        self.appointment.save()
        self.assertFalse(self.appointment.can_send_payment_link)
    
    def test_payment_link_url_contains_appointment_id(self):
        """Il link di pagamento contiene l'ID dell'appuntamento."""
        url = self.appointment.get_payment_link_url()
        self.assertIn(str(self.appointment.id), url)
    
    def test_payment_link_url_contains_token(self):
        """Il link di pagamento contiene un token di sicurezza."""
        url = self.appointment.get_payment_link_url()
        self.assertIn('token=', url)
    
    @patch('booking.email_service.send_payment_link_email')
    def test_send_payment_link_email_called(self, mock_send_email):
        """L'invio del link chiama la funzione email."""
        from booking.payment_service import send_payment_link
        
        mock_send_email.return_value = True
        
        result = send_payment_link(self.appointment)
        
        self.assertTrue(result)
        mock_send_email.assert_called_once()
    
    def test_change_payment_method_updates_appointment(self):
        """È possibile cambiare il metodo di pagamento."""
        self.assertEqual(self.appointment.payment_method, 'stripe')
        
        self.appointment.payment_method = 'paypal'
        self.appointment.save()
        
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.payment_method, 'paypal')


class TestPaymentActionsAdmin(TestCase):
    """Test per le azioni admin sui pagamenti."""
    
    def setUp(self):
        User = get_user_model()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='testpass123'
        )
        self.factory = RequestFactory()
    
    def test_refund_button_visible_when_cancelled_and_paid(self):
        """Il pulsante rimborso è visibile per appuntamenti annullati con pagamento."""
        appointment = Appointment.objects.create(
            first_name="Test",
            last_name="Refund",
            email="test@example.com",
            phone="+39111222333",
            notes="",
            date=date(2026, 3, 1),
            time=time(9, 0),
            status='cancelled',
            payment_method='stripe',
            stripe_payment_intent_id='pi_123',
            amount_paid=Decimal('60.00'),
        )
        
        # Il pulsante dovrebbe essere visibile
        self.assertTrue(appointment.can_refund)
    
    def test_send_link_button_visible_when_pending(self):
        """Il pulsante invia link è visibile per appuntamenti pending."""
        appointment = Appointment.objects.create(
            first_name="Test",
            last_name="Link",
            email="test@example.com",
            phone="+39111222333",
            notes="",
            date=date(2026, 3, 2),
            time=time(11, 0),
            status='pending',
            payment_method='paypal',
            amount_paid=Decimal('0.00'),
        )
        
        # Il pulsante dovrebbe essere visibile
        self.assertTrue(appointment.can_send_payment_link)


class TestAdminPages(TestCase):
    """Test per le pagine admin di rimborso e invio link."""
    
    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_superuser(
            username='admin', password='admin123', email='admin@test.com'
        )
        self.client.login(username='admin', password='admin123')
        
        self.cancelled_appointment = Appointment.objects.create(
            first_name="Mario",
            last_name="Rimborso",
            email="mario@test.com",
            phone="+39123456789",
            notes="Test rimborso",
            date=date(2026, 4, 1),
            time=time(10, 0),
            status='cancelled',
            payment_method='stripe',
            stripe_payment_intent_id='pi_test_refund',
            amount_paid=Decimal('60.00'),
        )
        
        self.pending_appointment = Appointment.objects.create(
            first_name="Luigi",
            last_name="Pending",
            email="luigi@test.com",
            phone="+39987654321",
            notes="Test pending",
            date=date(2026, 4, 2),
            time=time(11, 0),
            status='pending',
            payment_method='paypal',
            amount_paid=Decimal('0.00'),
        )
    
    def test_refund_page_contains_helper_text(self):
        """La pagina rimborso contiene l'helper text esplicativo."""
        from django.urls import reverse
        response = self.client.get(
            reverse('booking_refund', args=[self.cancelled_appointment.pk])
        )
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        # Verifica helper text
        self.assertIn('Come funziona il rimborso', content)
        self.assertIn('5-10 giorni lavorativi', content)
    
    def test_send_link_page_contains_helper_text(self):
        """La pagina invio link contiene l'helper text esplicativo."""
        from django.urls import reverse
        response = self.client.get(
            reverse('booking_send_payment_link', args=[self.pending_appointment.pk])
        )
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        # Verifica helper text
        self.assertIn('Come funziona', content)
        self.assertIn('Link personalizzato', content)
    
    def test_refund_page_has_captcha(self):
        """La pagina rimborso ha il captcha matematico."""
        from django.urls import reverse
        response = self.client.get(
            reverse('booking_refund', args=[self.cancelled_appointment.pk])
        )
        content = response.content.decode('utf-8')
        self.assertIn('captcha_result', content)
        self.assertIn('expected_result', content)
    
    def test_send_link_page_has_captcha(self):
        """La pagina invio link ha il captcha matematico."""
        from django.urls import reverse
        response = self.client.get(
            reverse('booking_send_payment_link', args=[self.pending_appointment.pk])
        )
        content = response.content.decode('utf-8')
        self.assertIn('captcha_result', content)
        self.assertIn('expected_result', content)
    
    # ========== TDD: Test per struttura pulsanti Wagtail ==========
    
    def test_refund_page_has_cancel_button(self):
        """La pagina rimborso ha il pulsante Annulla che torna all'edit."""
        from django.urls import reverse
        response = self.client.get(
            reverse('booking_refund', args=[self.cancelled_appointment.pk])
        )
        content = response.content.decode('utf-8')
        # Verifica pulsante Annulla con link corretto
        self.assertIn('Annulla', content)
        edit_url = reverse('wagtailsnippets_booking_appointment:edit', args=[self.cancelled_appointment.pk])
        self.assertIn(edit_url, content)
    
    def test_refund_page_has_confirm_button(self):
        """La pagina rimborso ha il pulsante Conferma Rimborso."""
        from django.urls import reverse
        response = self.client.get(
            reverse('booking_refund', args=[self.cancelled_appointment.pk])
        )
        content = response.content.decode('utf-8')
        # Verifica pulsante submit
        self.assertIn('Conferma Rimborso', content)
        self.assertIn('type="submit"', content)
    
    def test_send_link_page_has_cancel_button(self):
        """La pagina invio link ha il pulsante Annulla che torna all'edit."""
        from django.urls import reverse
        response = self.client.get(
            reverse('booking_send_payment_link', args=[self.pending_appointment.pk])
        )
        content = response.content.decode('utf-8')
        # Verifica pulsante Annulla con link corretto
        self.assertIn('Annulla', content)
        edit_url = reverse('wagtailsnippets_booking_appointment:edit', args=[self.pending_appointment.pk])
        self.assertIn(edit_url, content)
    
    def test_send_link_page_has_submit_button(self):
        """La pagina invio link ha il pulsante Invia Link."""
        from django.urls import reverse
        response = self.client.get(
            reverse('booking_send_payment_link', args=[self.pending_appointment.pk])
        )
        content = response.content.decode('utf-8')
        # Verifica pulsante submit
        self.assertIn('Invia Link', content)
        self.assertIn('type="submit"', content)
    
    def test_refund_page_buttons_in_actions_container(self):
        """I pulsanti della pagina rimborso sono in un container con flex layout."""
        from django.urls import reverse
        response = self.client.get(
            reverse('booking_refund', args=[self.cancelled_appointment.pk])
        )
        content = response.content.decode('utf-8')
        # Verifica struttura con container per pulsanti (button class e flex layout)
        self.assertIn('button button-secondary', content)
        # Pulsante submit usa classi Wagtail: bicolor button--icon serious
        self.assertIn('bicolor button--icon serious', content)
    
    def test_send_link_page_buttons_in_actions_container(self):
        """I pulsanti della pagina invio link sono in un container con flex layout."""
        from django.urls import reverse
        response = self.client.get(
            reverse('booking_send_payment_link', args=[self.pending_appointment.pk])
        )
        content = response.content.decode('utf-8')
        # Verifica struttura con container per pulsanti (button class)
        self.assertIn('button button-secondary', content)
        # Pulsante submit usa classi Wagtail: bicolor button--icon
        self.assertIn('bicolor button--icon', content)