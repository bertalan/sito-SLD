"""
Test per il checkout e i gateway di pagamento.
"""
from django.test import TestCase, Client
from datetime import date, time, timedelta
from unittest.mock import patch, MagicMock
import json

from booking.models import AvailabilityRule, Appointment


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


class EmailServiceTest(TestCase):
    """Test per il servizio email."""
    
    @patch('booking.email_service.EmailMultiAlternatives')
    def test_send_confirmation_emails(self, mock_email_class):
        """Test invio email conferma a cliente e studio."""
        from booking.email_service import send_booking_confirmation
        
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
