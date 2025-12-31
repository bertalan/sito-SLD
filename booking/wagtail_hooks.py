from wagtail import hooks
from wagtail.admin.menu import MenuItem, Menu, SubmenuMenuItem
from django.urls import reverse


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
