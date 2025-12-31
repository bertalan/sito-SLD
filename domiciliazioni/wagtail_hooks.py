"""
Wagtail hooks per il modulo Domiciliazioni.
"""
from wagtail import hooks
from wagtail.admin.menu import MenuItem, Menu, SubmenuMenuItem

from .models import DomiciliazioniSubmission


class DomiciliazioniMenu(Menu):
    """Menu per gestione domiciliazioni."""
    pass


@hooks.register('register_admin_menu_item')
def register_domiciliazioni_menu():
    """Registra il menu Domiciliazioni nel pannello admin."""
    
    submenu = DomiciliazioniMenu(
        register_hook_name='register_domiciliazioni_menu_item',
        construct_hook_name='construct_domiciliazioni_menu'
    )
    
    return SubmenuMenuItem(
        'Domiciliazioni',
        submenu,
        icon_name='doc-full',
        order=300
    )


@hooks.register('register_domiciliazioni_menu_item')
def register_domiciliazioni_submenu_items():
    """Registra le voci del sottomenu domiciliazioni."""
    return MenuItem(
        'Richieste',
        '/admin/snippets/domiciliazioni/domiciliazionisubmission/',
        icon_name='list-ul',
        order=100
    )
