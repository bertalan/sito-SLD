from django.db import models
from django.utils import timezone
from django.utils.html import format_html
from datetime import datetime, timedelta
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.snippets.models import register_snippet


class GoogleCalendarEvent(models.Model):
    """
    Cache locale degli eventi Google Calendar con prefisso "App ".
    Sincronizzato on-demand quando un visitatore accede alla pagina prenotazioni.
    """
    google_uid = models.CharField("UID Google", max_length=255, unique=True, db_index=True)
    summary = models.CharField("Titolo", max_length=255)
    start_datetime = models.DateTimeField("Inizio")
    end_datetime = models.DateTimeField("Fine")
    synced_at = models.DateTimeField("Ultima sincronizzazione")
    
    class Meta:
        verbose_name = "Evento Google Calendar"
        verbose_name_plural = "Eventi Google Calendar"
        ordering = ['start_datetime']
    
    def __str__(self):
        return f"{self.summary} - {self.start_datetime.strftime('%d/%m/%Y %H:%M')}"
    
    @property
    def duration_minutes(self):
        """Durata in minuti."""
        delta = self.end_datetime - self.start_datetime
        return int(delta.total_seconds() / 60)


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


class Appointment(ClusterableModel):
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
    
    CONSULTATION_TYPE_CHOICES = [
        ('in_person', 'In presenza'),
        ('video', 'Videochiamata'),
    ]
    
    # Dati cliente
    first_name = models.CharField("Nome", max_length=100)
    last_name = models.CharField("Cognome", max_length=100)
    email = models.EmailField("Email")
    phone = models.CharField("Telefono", max_length=20)
    notes = models.TextField("Note")
    
    # Tipo consulenza
    consultation_type = models.CharField("Tipo consulenza", max_length=20, choices=CONSULTATION_TYPE_CHOICES, default='in_person')
    videocall_code = models.CharField("Codice videochiamata", max_length=32, blank=True)
    
    # Data/ora appuntamento
    date = models.DateField("Data")
    time = models.TimeField("Ora")
    slot_count = models.PositiveIntegerField("Numero slot", default=1, help_text="Numero di slot consecutivi da 30 minuti")
    
    # Stato e pagamento
    status = models.CharField("Stato", max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField("Metodo pagamento", max_length=20, choices=PAYMENT_METHOD_CHOICES, default='stripe')
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    paypal_payment_id = models.CharField(max_length=255, blank=True)
    amount_paid = models.DecimalField("Importo pagato", max_digits=10, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    panels = [
        FieldPanel('first_name'),
        FieldPanel('last_name'),
        FieldPanel('email'),
        FieldPanel('phone'),
        FieldPanel('notes'),
        FieldPanel('consultation_type'),
        FieldPanel('date'),
        FieldPanel('time'),
        FieldPanel('status'),
        FieldPanel('payment_method'),
        FieldPanel('amount_paid'),
        InlinePanel('attachments', label="📎 Documenti allegati", heading="Documenti allegati"),
    ]
    
    class Meta:
        verbose_name = "Appuntamento"
        verbose_name_plural = "Appuntamenti"
        ordering = ['-date', '-time']
        unique_together = ['date', 'time']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.date} {self.time}"
    
    def save(self, *args, **kwargs):
        # Genera codice videochiamata se è una consulenza video e non esiste già
        if self.consultation_type == 'video' and not self.videocall_code:
            import hashlib
            import secrets
            # Codice anonimo: hash di ID + segreto random
            secret = secrets.token_hex(8)
            raw = f"sld-{self.pk or secrets.token_hex(4)}-{secret}"
            self.videocall_code = hashlib.sha256(raw.encode()).hexdigest()[:16]
        super().save(*args, **kwargs)
    
    @property
    def jitsi_url(self):
        """Restituisce l'URL Jitsi per la videochiamata."""
        if self.consultation_type == 'video' and self.videocall_code:
            return f"https://meet.jit.si/StudioLegale-{self.videocall_code}"
        return None
    
    @property
    def duration_minutes(self):
        """Durata totale in minuti."""
        from django.conf import settings
        slot_duration = getattr(settings, 'BOOKING_SLOT_DURATION', 30)
        return self.slot_count * slot_duration
    
    @property
    def end_time(self):
        """Orario di fine appuntamento."""
        start_dt = datetime.combine(self.date, self.time)
        end_dt = start_dt + timedelta(minutes=self.duration_minutes)
        return end_dt.time()
    
    @property
    def total_price_cents(self):
        """Prezzo totale in centesimi."""
        from django.conf import settings
        price_per_slot = getattr(settings, 'BOOKING_PRICE_CENTS', 6000)
        return self.slot_count * price_per_slot
    
    @property
    def total_price_display(self):
        """Prezzo totale formattato per la visualizzazione (es: 60,00)."""
        return f"{self.total_price_cents / 100:.2f}".replace('.', ',')
    
    @classmethod
    def get_available_slots(cls, date):
        """Restituisce gli slot disponibili per una data."""
        from django.conf import settings
        
        # Blocca solo domenica (6)
        weekday = date.weekday()
        if weekday == 6:
            return []
        
        if BlockedDate.objects.filter(date=date).exists():
            return []
        
        rules = AvailabilityRule.objects.filter(weekday=weekday, is_active=True)
        
        if not rules.exists():
            return []
        
        # Ottieni slot bloccati da Google Calendar
        from .google_calendar import get_blocked_slots_from_google
        google_blocked_slots = get_blocked_slots_from_google(date)
        
        # Ottieni tutti gli slot occupati dagli appuntamenti (inclusi multi-slot)
        booked_slots = set()
        appointments = cls.objects.filter(date=date).exclude(status='cancelled')
        slot_duration = getattr(settings, 'BOOKING_SLOT_DURATION', 30)
        
        for apt in appointments:
            # Aggiungi tutti gli slot occupati dall'appuntamento
            apt_start = datetime.combine(date, apt.time)
            for i in range(apt.slot_count):
                slot_time = (apt_start + timedelta(minutes=slot_duration * i)).time()
                booked_slots.add(slot_time)
        
        slots = []
        
        for rule in rules:
            current_time = datetime.combine(date, rule.start_time)
            end_time = datetime.combine(date, rule.end_time)
            
            while current_time + timedelta(minutes=slot_duration) <= end_time:
                time_slot = current_time.time()
                # Escludi slot già prenotati nel DB
                is_booked = time_slot in booked_slots
                # Escludi slot bloccati da Google Calendar
                is_google_blocked = time_slot in google_blocked_slots
                
                if not is_booked and not is_google_blocked:
                    slots.append(time_slot)
                current_time += timedelta(minutes=slot_duration)
        
        return sorted(set(slots))


def appointment_attachment_path(instance, filename):
    """Genera il path per gli allegati degli appuntamenti."""
    return f'appointments/{instance.appointment.id}/{filename}'


class AppointmentAttachment(models.Model):
    """Allegato per un appuntamento."""
    
    appointment = ParentalKey(
        Appointment, 
        on_delete=models.CASCADE, 
        related_name='attachments',
        verbose_name="Appuntamento"
    )
    file = models.FileField("File", upload_to=appointment_attachment_path)
    original_filename = models.CharField("Nome file originale", max_length=255)
    uploaded_at = models.DateTimeField("Caricato il", auto_now_add=True)
    
    panels = [
        FieldPanel('file'),
        FieldPanel('original_filename', read_only=True),
    ]
    
    class Meta:
        verbose_name = "Allegato"
        verbose_name_plural = "Allegati"
    
    def __str__(self):
        if self.file:
            return format_html('<a href="{}" target="_blank">📥 {}</a>', self.file.url, self.original_filename)
        return self.original_filename
