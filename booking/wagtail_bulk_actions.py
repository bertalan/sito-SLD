"""
Bulk actions personalizzate per gli snippet Wagtail.

Questo modulo contiene le azioni bulk disponibili nella lista degli snippet,
permettendo operazioni su più elementi selezionati.
"""

from django.utils.translation import gettext_lazy as _
from wagtail.snippets.bulk_actions.snippet_bulk_action import SnippetBulkAction
from wagtail import hooks

from .models import Appointment
from .email_service import send_booking_confirmation


@hooks.register('register_bulk_action')
class ResendEmailBulkAction(SnippetBulkAction):
    """Azione bulk per reinviare le email di conferma agli appuntamenti selezionati."""
    
    display_name = _("📧 Reinvia email")
    aria_label = _("Reinvia email di conferma per gli appuntamenti selezionati")
    action_type = "resend_email"
    template_name = "booking/bulk_actions/confirm_resend_email.html"
    models = [Appointment]
    
    @classmethod
    def execute_action(cls, objects, **kwargs):
        """
        Esegue l'invio delle email per tutti gli oggetti selezionati.
        
        Args:
            objects: Lista di appuntamenti selezionati
            **kwargs: Argomenti aggiuntivi (es. user dalla request)
        
        Returns:
            Tuple (success_count, error_count): Conteggio successi e errori
        """
        success_count = 0
        error_count = 0
        
        for appointment in objects:
            try:
                result = send_booking_confirmation(appointment)
                if result.get('client_success') or result.get('studio_success'):
                    success_count += 1
                else:
                    error_count += 1
            except Exception:
                error_count += 1
        
        return success_count, error_count
    
    def get_success_message(self, num_parent_objects, num_child_objects):
        """
        Genera il messaggio di successo da mostrare all'utente.
        
        Args:
            num_parent_objects: Numero di email inviate con successo
            num_child_objects: Numero di errori (usato come secondo valore)
        
        Returns:
            Stringa con il messaggio formattato
        """
        if num_child_objects == 0:
            return _("✓ Email inviate con successo per {} appuntamento/i.").format(num_parent_objects)
        else:
            return _("✓ {} email inviate con successo, {} errori.").format(
                num_parent_objects, 
                num_child_objects
            )
