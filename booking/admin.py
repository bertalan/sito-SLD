from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'date', 'time', 'status', 'created_at']
    list_filter = ['status', 'date']
    search_fields = ['first_name', 'last_name', 'email']
    readonly_fields = ['created_at', 'updated_at', 'stripe_payment_intent_id']
    ordering = ['-date', '-time']
