"""
Wagtail hooks per il modulo Domiciliazioni.
"""
from wagtail import hooks
from wagtail.admin.menu import MenuItem, Menu, SubmenuMenuItem

from .models import DomiciliazioniSubmission


@hooks.register('register_admin_menu_item')
def register_domiciliazioni_menu():
    """Registra il menu Domiciliazioni nel pannello admin."""
    
    domiciliazioni_menu = Menu(items=[
        MenuItem(
            'Richieste',
            '/admin/snippets/domiciliazioni/domiciliazionisubmission/',
            icon_name='list-ul',
            order=100
        ),
    ])
    
    return SubmenuMenuItem(
        'Domiciliazioni',
        domiciliazioni_menu,
        icon_name='doc-full',
        order=300
    )
