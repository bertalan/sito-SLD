from django.contrib import admin
from django.contrib import messages
from .models import Appointment
from .email_service import send_booking_confirmation


def resend_confirmation_email(modeladmin, request, queryset):
    """Azione admin per re-inviare le email di conferma."""
    success_count = 0
    error_count = 0
    
    for appointment in queryset:
        try:
            result = send_booking_confirmation(appointment)
            if result.get('client_success') or result.get('studio_success'):
                success_count += 1
            else:
                error_count += 1
        except Exception as e:
            error_count += 1
    
    if success_count:
        messages.success(request, f"✓ Email inviate con successo per {success_count} appuntamento/i.")
    if error_count:
        messages.error(request, f"✗ Errore invio email per {error_count} appuntamento/i.")

resend_confirmation_email.short_description = "📧 Reinvia email di conferma"


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'date', 'time', 'status', 'created_at']
    list_filter = ['status', 'date']
    search_fields = ['first_name', 'last_name', 'email']
    readonly_fields = ['created_at', 'updated_at', 'stripe_payment_intent_id']
    ordering = ['-date', '-time']
    actions = [resend_confirmation_email]
