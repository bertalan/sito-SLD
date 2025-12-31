from django.contrib import admin
from django.contrib import messages
from .models import DomiciliazioniSubmission, DomiciliazioniDocument
from .views import send_domiciliazione_notification


def resend_domiciliazione_email(modeladmin, request, queryset):
    """Azione admin per re-inviare le email di conferma domiciliazione."""
    success_count = 0
    error_count = 0
    
    for submission in queryset:
        try:
            send_domiciliazione_notification(submission)
            success_count += 1
        except Exception as e:
            error_count += 1
    
    if success_count:
        messages.success(request, f"✓ Email inviate con successo per {success_count} domiciliazione/i.")
    if error_count:
        messages.error(request, f"✗ Errore invio email per {error_count} domiciliazione/i.")

resend_domiciliazione_email.short_description = "📧 Reinvia email di conferma"


class DomiciliazioniDocumentInline(admin.TabularInline):
    model = DomiciliazioniDocument
    extra = 0
    readonly_fields = ['original_filename', 'uploaded_at']


@admin.register(DomiciliazioniSubmission)
class DomiciliazioniSubmissionAdmin(admin.ModelAdmin):
    list_display = ['numero_rg', 'tribunale', 'nome_avvocato', 'data_udienza', 'ora_udienza', 'status', 'submit_time']
    list_filter = ['status', 'tribunale', 'tipo_udienza', 'data_udienza']
    search_fields = ['nome_avvocato', 'email', 'numero_rg', 'parti_causa']
    readonly_fields = ['submit_time']
    ordering = ['-submit_time']
    inlines = [DomiciliazioniDocumentInline]
    actions = [resend_domiciliazione_email]
    
    fieldsets = (
        ('Avvocato Richiedente', {
            'fields': ('nome_avvocato', 'email', 'telefono', 'ordine_appartenenza')
        }),
        ('Tribunale', {
            'fields': ('tribunale', 'sezione', 'giudice', 'tipo_udienza')
        }),
        ('Causa', {
            'fields': ('numero_rg', 'parti_causa', 'data_udienza', 'ora_udienza')
        }),
        ('Attività', {
            'fields': ('attivita_richieste', 'note')
        }),
        ('Stato', {
            'fields': ('status', 'esito_udienza', 'submit_time')
        }),
    )
