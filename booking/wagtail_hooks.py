from wagtail import hooks
from wagtail.admin.menu import MenuItem, Menu, SubmenuMenuItem
from wagtail.admin.ui.tables import Column
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from django.urls import reverse

from .models import Appointment, AvailabilityRule, BlockedDate


class AllegatiColumn(Column):
    """Colonna personalizzata per mostrare il conteggio allegati."""
    
    def get_value(self, instance):
        count = instance.attachments.count()
        if count == 0:
            return "—"
        return f"✓ {count}"


class AppointmentViewSet(SnippetViewSet):
    model = Appointment
    icon = "calendar"
    menu_label = "Appuntamenti"
    menu_order = 100
    add_to_admin_menu = False
    list_display = ['first_name', 'last_name', 'date', 'time', AllegatiColumn("allegati", label="📎 Allegati"), 'status', 'created_at']
    list_filter = ['status', 'date', 'consultation_type']
    search_fields = ['first_name', 'last_name', 'email']
    ordering = ['-date', '-time']


# Registra il ViewSet personalizzato
register_snippet(AppointmentViewSet)


class BookingMenu(Menu):
    """Menu per la gestione prenotazioni."""
    pass


@hooks.register('register_admin_menu_item')
def register_booking_menu():
    """Registra il menu Prenotazioni nell'admin Wagtail."""
    
    booking_menu = Menu(items=[
        MenuItem(
            'Appuntamenti',
            reverse('wagtailsnippets_booking_appointment:list'),
            icon_name='calendar',
            order=100
        ),
        MenuItem(
            'Regole disponibilità',
            reverse('wagtailsnippets_booking_availabilityrule:list'),
            icon_name='time',
            order=200
        ),
        MenuItem(
            'Date bloccate',
            reverse('wagtailsnippets_booking_blockeddate:list'),
            icon_name='cross',
            order=300
        ),
    ])
    
    return SubmenuMenuItem(
        'Prenotazioni',
        booking_menu,
        icon_name='calendar-check',
        order=400
    )
