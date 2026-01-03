"""
Test TDD per l'azione bulk di reinvio email in Wagtail admin.

Questi test verificano che l'azione di reinvio email sia disponibile
nell'admin Wagtail per gli snippet Appointment e funzioni correttamente.
"""

from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth.models import User
from datetime import date, time

from booking.models import Appointment


class TestResendEmailBulkActionRegistration(TestCase):
    """Test che l'azione bulk sia registrata correttamente."""
    
    def test_resend_email_action_class_exists(self):
        """L'azione ResendEmailBulkAction deve esistere."""
        from booking.wagtail_bulk_actions import ResendEmailBulkAction
        self.assertIsNotNone(ResendEmailBulkAction)
    
    def test_action_is_snippet_bulk_action(self):
        """L'azione deve estendere SnippetBulkAction."""
        from booking.wagtail_bulk_actions import ResendEmailBulkAction
        from wagtail.snippets.bulk_actions.snippet_bulk_action import SnippetBulkAction
        self.assertTrue(issubclass(ResendEmailBulkAction, SnippetBulkAction))
    
    def test_action_applies_to_appointment_model(self):
        """L'azione deve applicarsi solo al modello Appointment."""
        from booking.wagtail_bulk_actions import ResendEmailBulkAction
        from booking.models import Appointment
        self.assertIn(Appointment, ResendEmailBulkAction.models)
    
    def test_action_has_correct_display_name(self):
        """L'azione deve avere il nome corretto per l'UI."""
        from booking.wagtail_bulk_actions import ResendEmailBulkAction
        self.assertIn("email", ResendEmailBulkAction.display_name.lower())
    
    def test_action_has_correct_action_type(self):
        """L'azione deve avere un action_type unico."""
        from booking.wagtail_bulk_actions import ResendEmailBulkAction
        self.assertEqual(ResendEmailBulkAction.action_type, "resend_email")


class TestResendEmailBulkActionExecution(TestCase):
    """Test dell'esecuzione dell'azione bulk."""
    
    def setUp(self):
        """Crea appuntamenti di test."""
        self.appointment1 = Appointment.objects.create(
            first_name="Mario",
            last_name="Rossi",
            email="mario@example.com",
            phone="1234567890",
            date=date(2024, 6, 15),
            time=time(10, 0),
            status="confirmed",
        )
        self.appointment2 = Appointment.objects.create(
            first_name="Luigi",
            last_name="Verdi",
            email="luigi@example.com",
            phone="0987654321",
            date=date(2024, 6, 16),
            time=time(11, 0),
            status="confirmed",
        )
    
    @patch('booking.wagtail_bulk_actions.send_booking_confirmation')
    def test_execute_action_calls_send_email_for_each_appointment(self, mock_send):
        """execute_action deve chiamare send_booking_confirmation per ogni appuntamento."""
        mock_send.return_value = {'client_success': True, 'studio_success': True}
        
        from booking.wagtail_bulk_actions import ResendEmailBulkAction
        
        objects = [self.appointment1, self.appointment2]
        success_count, error_count = ResendEmailBulkAction.execute_action(objects)
        
        self.assertEqual(mock_send.call_count, 2)
        self.assertEqual(success_count, 2)
        self.assertEqual(error_count, 0)
    
    @patch('booking.wagtail_bulk_actions.send_booking_confirmation')
    def test_execute_action_handles_partial_success(self, mock_send):
        """execute_action deve gestire successi parziali."""
        # Prima chiamata successo, seconda fallimento
        mock_send.side_effect = [
            {'client_success': True, 'studio_success': True},
            {'client_success': False, 'studio_success': False},
        ]
        
        from booking.wagtail_bulk_actions import ResendEmailBulkAction
        
        objects = [self.appointment1, self.appointment2]
        success_count, error_count = ResendEmailBulkAction.execute_action(objects)
        
        self.assertEqual(success_count, 1)
        self.assertEqual(error_count, 1)
    
    @patch('booking.wagtail_bulk_actions.send_booking_confirmation')
    def test_execute_action_handles_exceptions(self, mock_send):
        """execute_action deve gestire eccezioni senza bloccarsi."""
        mock_send.side_effect = [
            {'client_success': True, 'studio_success': True},
            Exception("Errore SMTP"),
        ]
        
        from booking.wagtail_bulk_actions import ResendEmailBulkAction
        
        objects = [self.appointment1, self.appointment2]
        success_count, error_count = ResendEmailBulkAction.execute_action(objects)
        
        self.assertEqual(success_count, 1)
        self.assertEqual(error_count, 1)
    
    @patch('booking.wagtail_bulk_actions.send_booking_confirmation')
    def test_execute_action_with_empty_list(self, mock_send):
        """execute_action con lista vuota non deve fare nulla."""
        from booking.wagtail_bulk_actions import ResendEmailBulkAction
        
        success_count, error_count = ResendEmailBulkAction.execute_action([])
        
        mock_send.assert_not_called()
        self.assertEqual(success_count, 0)
        self.assertEqual(error_count, 0)


class TestResendEmailBulkActionSuccessMessage(TestCase):
    """Test dei messaggi di successo."""
    
    def test_success_message_with_all_success(self):
        """Il messaggio deve indicare quante email sono state inviate."""
        from booking.wagtail_bulk_actions import ResendEmailBulkAction
        
        action = ResendEmailBulkAction.__new__(ResendEmailBulkAction)
        message = action.get_success_message(3, 0)
        
        self.assertIn("3", message)
        self.assertIn("email", message.lower())
    
    def test_success_message_with_errors(self):
        """Il messaggio deve indicare sia successi che errori."""
        from booking.wagtail_bulk_actions import ResendEmailBulkAction
        
        action = ResendEmailBulkAction.__new__(ResendEmailBulkAction)
        message = action.get_success_message(2, 1)
        
        self.assertIn("2", message)
        self.assertIn("1", message)
