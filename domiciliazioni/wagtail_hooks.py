"""
Wagtail hooks per il modulo Domiciliazioni.
"""
from wagtail import hooks
from wagtail.admin.menu import MenuItem, Menu, SubmenuMenuItem
from wagtail.admin.ui.tables import Column
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import DomiciliazioniSubmission


class AllegatiColumn(Column):
    """Colonna personalizzata per mostrare il conteggio allegati."""
    
    def get_value(self, instance):
        count = instance.documents.count()
        if count == 0:
            return "—"
        return f"✓ {count}"


class DomiciliazioniSubmissionViewSet(SnippetViewSet):
    model = DomiciliazioniSubmission
    icon = "doc-full"
    menu_label = "Richieste"
    menu_order = 100
    add_to_admin_menu = False
    list_display = ['numero_rg', 'tribunale', 'nome_avvocato', 'data_udienza', 'ora_udienza', AllegatiColumn("allegati", label="📎 Allegati"), 'status', 'submit_time']
    list_filter = ['status', 'tribunale', 'tipo_udienza', 'data_udienza']
    search_fields = ['nome_avvocato', 'email', 'numero_rg', 'parti_causa']
    ordering = ['-submit_time']


# Registra il ViewSet personalizzato
register_snippet(DomiciliazioniSubmissionViewSet)


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
