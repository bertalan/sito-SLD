from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet


@register_snippet
class AvailabilityRule(models.Model):
    """Regola di disponibilità ricorsiva per appuntamenti."""
    
    WEEKDAYS = [
        (0, 'Lunedì'),
        (1, 'Martedì'),
        (2, 'Mercoledì'),
        (3, 'Giovedì'),
        (4, 'Venerdì'),
        (5, 'Sabato'),
        (6, 'Domenica'),
    ]
    
    name = models.CharField("Nome regola", max_length=100)
    weekday = models.IntegerField("Giorno della settimana", choices=WEEKDAYS)
    start_time = models.TimeField("Ora inizio")
    end_time = models.TimeField("Ora fine")
    is_active = models.BooleanField("Attiva", default=True)
    
    panels = [
        FieldPanel('name'),
        FieldPanel('weekday'),
        FieldPanel('start_time'),
        FieldPanel('end_time'),
        FieldPanel('is_active'),
    ]
    
    class Meta:
        verbose_name = "Regola di disponibilità"
        verbose_name_plural = "Regole di disponibilità"
        ordering = ['weekday', 'start_time']
    
    def __str__(self):
        return f"{self.name} - {self.get_weekday_display()} ({self.start_time}-{self.end_time})"


@register_snippet
class BlockedDate(models.Model):
    """Date bloccate (ferie, festivi, etc.)."""
    
    date = models.DateField("Data")
    reason = models.CharField("Motivo", max_length=200, blank=True)
    
    panels = [
        FieldPanel('date'),
        FieldPanel('reason'),
    ]
    
    class Meta:
        verbose_name = "Data bloccata"
        verbose_name_plural = "Date bloccate"
        ordering = ['date']
    
    def __str__(self):
        return f"{self.date} - {self.reason}"


class Appointment(models.Model):
    """Prenotazione appuntamento."""
    
    STATUS_CHOICES = [
        ('pending', 'In attesa di pagamento'),
        ('confirmed', 'Confermato'),
        ('cancelled', 'Annullato'),
        ('completed', 'Completato'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('stripe', 'Carta di credito (Stripe)'),
        ('paypal', 'PayPal'),
    ]
    
    # Dati cliente
    first_name = models.CharField("Nome", max_length=100)
    last_name = models.CharField("Cognome", max_length=100)
    email = models.EmailField("Email")
    phone = models.CharField("Telefono", max_length=20)
    notes = models.TextField("Note", blank=True)
    
    # Data/ora appuntamento
    date = models.DateField("Data")
    time = models.TimeField("Ora")
    
    # Stato e pagamento
    status = models.CharField("Stato", max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField("Metodo pagamento", max_length=20, choices=PAYMENT_METHOD_CHOICES, default='stripe')
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    paypal_payment_id = models.CharField(max_length=255, blank=True)
    amount_paid = models.DecimalField("Importo pagato", max_digits=10, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Appuntamento"
        verbose_name_plural = "Appuntamenti"
        ordering = ['-date', '-time']
        unique_together = ['date', 'time']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.date} {self.time}"
    
    @classmethod
    def get_available_slots(cls, date):
        """Restituisce gli slot disponibili per una data."""
        from django.conf import settings
        
        if BlockedDate.objects.filter(date=date).exists():
            return []
        
        weekday = date.weekday()
        rules = AvailabilityRule.objects.filter(weekday=weekday, is_active=True)
        
        if not rules.exists():
            return []
        
        slots = []
        slot_duration = getattr(settings, 'BOOKING_SLOT_DURATION', 30)
        
        for rule in rules:
            current_time = datetime.combine(date, rule.start_time)
            end_time = datetime.combine(date, rule.end_time)
            
            while current_time + timedelta(minutes=slot_duration) <= end_time:
                time_slot = current_time.time()
                if not cls.objects.filter(date=date, time=time_slot).exclude(status='cancelled').exists():
                    slots.append(time_slot)
                current_time += timedelta(minutes=slot_duration)
        
        return sorted(set(slots))
