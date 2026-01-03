from wagtail import hooks
from wagtail.admin.menu import MenuItem, Menu, SubmenuMenuItem
from wagtail.admin.ui.tables import Column, StatusTagColumn
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from wagtail.admin.views.generic.base import WagtailAdminTemplateMixin
from django.urls import reverse, path
from django.views.generic import TemplateView
from django.views import View
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.html import format_html
from django.conf import settings
from datetime import timedelta, datetime
import json

from .models import Appointment, AvailabilityRule, BlockedDate, GoogleCalendarEvent


class CalendarAdminView(WagtailAdminTemplateMixin, TemplateView):
    """Vista admin con calendario interattivo e lista appuntamenti."""
    
    template_name = 'booking/admin/calendar_view.html'
    page_title = "Calendario Studio"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Sincronizza Google Calendar
        from .google_calendar import sync_google_calendar_events
        sync_google_calendar_events()
        
        now = timezone.now()
        today = now.date()
        
        # Prepara eventi per FullCalendar
        calendar_events = []
        
        # Eventi Google Calendar (prossimi 60 giorni)
        google_events = GoogleCalendarEvent.objects.filter(
            start_datetime__gte=now,
            start_datetime__lte=now + timedelta(days=60)
        )
        
        for event in google_events:
            calendar_events.append({
                'id': f'google-{event.id}',
                'title': event.summary,
                'start': event.start_datetime.isoformat(),
                'end': event.end_datetime.isoformat(),
                'eventType': 'google',
                'allDay': False,
            })
        
        # Prenotazioni online (confermate e pending)
        appointments = Appointment.objects.filter(
            date__gte=today,
            date__lte=today + timedelta(days=60)
        ).exclude(status='cancelled')
        
        for appt in appointments:
            event_type = 'pending' if appt.status == 'pending' else 'booking'
            start_dt = timezone.make_aware(
                timezone.datetime.combine(appt.date, appt.time)
            )
            end_dt = start_dt + timedelta(minutes=30)
            
            calendar_events.append({
                'id': f'booking-{appt.id}',
                'title': f"{appt.first_name} {appt.last_name}",
                'start': start_dt.isoformat(),
                'end': end_dt.isoformat(),
                'eventType': event_type,
                'url': reverse('wagtailsnippets_booking_appointment:edit', args=[appt.pk]),
                'allDay': False,
            })
        
        context['calendar_events_json'] = json.dumps(calendar_events)
        
        # Lista prossimi appuntamenti (unione Google + Booking)
        upcoming_events = []
        
        # Google events
        for event in google_events.order_by('start_datetime')[:20]:
            local_start = timezone.localtime(event.start_datetime)
            upcoming_events.append({
                'date': local_start.date(),
                'time': local_start.strftime('%H:%M'),
                'title': event.summary.replace('App ', '').replace('app ', ''),
                'type': 'google',
                'type_label': 'Tel.',
                'sort_key': event.start_datetime,
            })
        
        # Booking events
        for appt in appointments.order_by('date', 'time')[:20]:
            event_type = 'pending' if appt.status == 'pending' else 'booking'
            type_label = 'Attesa' if appt.status == 'pending' else 'Online'
            
            upcoming_events.append({
                'date': appt.date,
                'time': appt.time.strftime('%H:%M'),
                'title': f"{appt.first_name} {appt.last_name}",
                'type': event_type,
                'type_label': type_label,
                'sort_key': timezone.make_aware(
                    timezone.datetime.combine(appt.date, appt.time)
                ),
            })
        
        # Ordina per data/ora, più vicini in cima
        upcoming_events.sort(key=lambda x: x['sort_key'])
        context['upcoming_events'] = upcoming_events[:25]
        
        # Ultima sincronizzazione
        last_event = GoogleCalendarEvent.objects.order_by('-synced_at').first()
        context['last_sync'] = last_event.synced_at if last_event else None
        
        return context


@hooks.register('register_admin_urls')
def register_calendar_url():
    """Registra URL per la vista calendario."""
    return [
        path('calendario/', CalendarAdminView.as_view(), name='booking_calendar'),
        path('calendario/verifica-allineamento/', AllineamentoView.as_view(), name='booking_alignment_check'),
        path('calendario/download-ics/<int:appointment_id>/', DownloadAppointmentICSView.as_view(), name='booking_download_ics'),
    ]


class AllineamentoView(WagtailAdminTemplateMixin, TemplateView):
    """Vista per verificare l'allineamento tra appuntamenti locali e Google Calendar."""
    
    template_name = 'booking/admin/alignment_check.html'
    page_title = "Verifica Allineamento"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Forza sincronizzazione (ignora cache)
        from .google_calendar import sync_google_calendar_events
        sync_google_calendar_events(force=True)
        
        now = timezone.now()
        today = now.date()
        
        # Appuntamenti futuri confermati
        local_appointments = Appointment.objects.filter(
            date__gte=today,
            status='confirmed'
        ).order_by('date', 'time')
        
        # Eventi Google Calendar futuri
        google_events = GoogleCalendarEvent.objects.filter(
            start_datetime__gte=now
        ).order_by('start_datetime')
        
        # Analisi allineamento
        alignment_info = []
        
        for appt in local_appointments:
            appt_datetime = timezone.make_aware(
                timezone.datetime.combine(appt.date, appt.time)
            )
            
            # Cerca un evento Google corrispondente (stesso orario ±5 minuti)
            matching_event = None
            for event in google_events:
                time_diff = abs((event.start_datetime - appt_datetime).total_seconds())
                if time_diff < 300:  # 5 minuti di tolleranza
                    matching_event = event
                    break
            
            alignment_info.append({
                'appointment': appt,
                'datetime': appt_datetime,
                'google_event': matching_event,
                'is_aligned': matching_event is not None,
            })
        
        context['alignment_info'] = alignment_info
        context['total_local'] = local_appointments.count()
        context['total_google'] = google_events.count()
        context['aligned_count'] = sum(1 for a in alignment_info if a['is_aligned'])
        context['orphan_count'] = sum(1 for a in alignment_info if not a['is_aligned'])
        
        return context


class DownloadAppointmentICSView(View):
    """Genera e scarica un file .ics per un appuntamento."""
    
    def get(self, request, appointment_id):
        from icalendar import Calendar, Event
        import uuid
        
        appointment = get_object_or_404(Appointment, pk=appointment_id)
        
        # Crea calendario
        cal = Calendar()
        cal.add('prodid', '-//Studio Legale//Appuntamenti//IT')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        
        # Crea evento
        event = Event()
        
        # Titolo con prefisso "App " per coerenza con Google Calendar
        event.add('summary', f"App {appointment.first_name} {appointment.last_name}")
        
        # Data/ora inizio e fine
        start_dt = timezone.make_aware(
            datetime.combine(appointment.date, appointment.time)
        )
        # Calcola la fine usando il metodo duration_minutes del modello
        end_dt = start_dt + timedelta(minutes=appointment.duration_minutes)
        
        event.add('dtstart', start_dt)
        event.add('dtend', end_dt)
        event.add('dtstamp', timezone.now())
        
        # UID univoco
        event.add('uid', f"appointment-{appointment.id}@studiolegale")
        
        # Descrizione con dettagli
        description = f"""Appuntamento con: {appointment.first_name} {appointment.last_name}
Email: {appointment.email}
Telefono: {appointment.phone or 'Non specificato'}

Note: {appointment.notes or 'Nessuna'}

Prezzo: €{appointment.total_price_cents / 100:.2f}
Stato: {appointment.get_status_display()}"""
        
        event.add('description', description)
        
        # Luogo (se configurato)
        studio_address = getattr(settings, 'STUDIO_ADDRESS', '')
        if studio_address:
            event.add('location', studio_address)
        
        # Organizzatore
        studio_email = getattr(settings, 'STUDIO_EMAIL', '')
        if studio_email:
            event.add('organizer', f'mailto:{studio_email}')
        
        cal.add_component(event)
        
        # Genera risposta
        response = HttpResponse(cal.to_ical(), content_type='text/calendar')
        filename = f"appuntamento_{appointment.date}_{appointment.first_name}_{appointment.last_name}.ics"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response


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


class StatoRegolaColumn(Column):
    """Colonna per mostrare lo stato attivo/disabilitato con etichetta colorata."""
    
    def get_value(self, instance):
        if instance.is_active:
            return format_html(
                '<span style="background:#057a55;color:white;padding:2px 8px;border-radius:4px;font-size:0.85em;">✓ Attiva</span>'
            )
        else:
            return format_html(
                '<span style="background:#9ca3af;color:white;padding:2px 8px;border-radius:4px;font-size:0.85em;">✗ Disabilitata</span>'
            )


class GiornoColumn(Column):
    """Colonna per mostrare il giorno della settimana."""
    
    def get_value(self, instance):
        return instance.get_weekday_display()


class OrarioColumn(Column):
    """Colonna per mostrare l'orario della regola."""
    
    def get_value(self, instance):
        return f"{instance.start_time.strftime('%H:%M')} - {instance.end_time.strftime('%H:%M')}"


class AvailabilityRuleViewSet(SnippetViewSet):
    """ViewSet per le regole di disponibilità con stato visibile."""
    model = AvailabilityRule
    icon = "time"
    menu_label = "Regole disponibilità"
    menu_order = 200
    add_to_admin_menu = False
    list_display = [
        'name',
        GiornoColumn("giorno", label="Giorno"),
        OrarioColumn("orario", label="Orario"),
        StatoRegolaColumn("stato", label="Stato"),
    ]
    list_filter = ['weekday', 'is_active']
    ordering = ['weekday', 'start_time']


# Registra il ViewSet per AvailabilityRule
register_snippet(AvailabilityRuleViewSet)


class BookingMenu(Menu):
    """Menu per la gestione prenotazioni."""
    pass


@hooks.register('register_admin_menu_item')
def register_booking_menu():
    """Registra il menu Prenotazioni nell'admin Wagtail."""
    
    booking_menu = Menu(items=[
        MenuItem(
            '📅 Calendario',
            reverse('booking_calendar'),
            icon_name='calendar-alt',
            order=50
        ),
        MenuItem(
            'Appuntamenti',
            reverse('wagtailsnippets_booking_appointment:list'),
            icon_name='calendar',
            order=100
        ),
        MenuItem(
            '🔄 Verifica allineamento',
            reverse('booking_alignment_check'),
            icon_name='resubmit',
            order=150
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


# =============================================================================
# VIEW PER AZIONI PAGAMENTO (Rimborso e Invio Link)
# =============================================================================

class RefundPaymentView(WagtailAdminTemplateMixin, View):
    """View per rimborsare un pagamento."""
    
    page_title = "Rimborsa Pagamento"
    
    def get(self, request, appointment_id):
        """Mostra conferma rimborso con captcha."""
        import random
        
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        if not appointment.can_refund:
            from django.contrib import messages
            messages.error(request, "Questo appuntamento non può essere rimborsato.")
            return HttpResponseRedirect(
                reverse('wagtailsnippets_booking_appointment:edit', args=[appointment.pk])
            )
        
        # Genera captcha matematico
        num1 = random.randint(10, 50)
        num2 = random.randint(1, 20)
        
        return render(request, 'booking/admin/refund_confirm.html', {
            'appointment': appointment,
            'num1': num1,
            'num2': num2,
            'expected_result': num1 + num2,
        })
    
    def post(self, request, appointment_id):
        """Esegue il rimborso dopo verifica captcha."""
        from django.contrib import messages
        from . import payment_service as ps
        
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        if not appointment.can_refund:
            messages.error(request, "Questo appuntamento non può essere rimborsato.")
            return HttpResponseRedirect(
                reverse('wagtailsnippets_booking_appointment:edit', args=[appointment.pk])
            )
        
        # Verifica captcha
        try:
            expected = int(request.POST.get('expected_result', 0))
            user_result = int(request.POST.get('captcha_result', -1))
            if user_result != expected:
                messages.error(request, "Verifica di sicurezza fallita. Riprova.")
                return HttpResponseRedirect(reverse('booking_refund', args=[appointment.pk]))
        except (ValueError, TypeError):
            messages.error(request, "Inserisci un numero valido per la verifica.")
            return HttpResponseRedirect(reverse('booking_refund', args=[appointment.pk]))
        
        # Esegui rimborso
        result = ps.refund_payment(appointment)
        if result.get('success'):
            refund_id = result.get('refund_id')
            messages.success(request, f"Rimborso effettuato con successo! ID: {refund_id}")
            
            # Invia email di notifica rimborso al cliente
            from . import email_service
            email_service.send_refund_notification(appointment, refund_id)
        else:
            messages.error(request, f"Errore nel rimborso: {result.get('error')}")
        
        return HttpResponseRedirect(
            reverse('wagtailsnippets_booking_appointment:edit', args=[appointment.pk])
        )


class SendPaymentLinkView(WagtailAdminTemplateMixin, View):
    """View per inviare il link di pagamento."""
    
    page_title = "Invia Link Pagamento"
    
    def get(self, request, appointment_id):
        """Mostra form per invio link con captcha."""
        import random
        
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        if not appointment.can_send_payment_link:
            from django.contrib import messages
            messages.error(request, "Non è possibile inviare il link per questo appuntamento.")
            return HttpResponseRedirect(
                reverse('wagtailsnippets_booking_appointment:edit', args=[appointment.pk])
            )
        
        # Genera captcha matematico
        num1 = random.randint(5, 30)
        num2 = random.randint(1, 15)
        
        return render(request, 'booking/admin/send_payment_link.html', {
            'appointment': appointment,
            'payment_methods': [
                ('stripe', 'Carta di credito (Stripe)'),
                ('paypal', 'PayPal'),
            ],
            'num1': num1,
            'num2': num2,
            'expected_result': num1 + num2,
        })
    
    def post(self, request, appointment_id):
        """Invia il link di pagamento dopo verifica captcha."""
        from django.contrib import messages
        from . import payment_service as ps
        import secrets
        
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        if not appointment.can_send_payment_link:
            messages.error(request, "Non è possibile inviare il link per questo appuntamento.")
            return HttpResponseRedirect(
                reverse('wagtailsnippets_booking_appointment:edit', args=[appointment.pk])
            )
        
        # Verifica captcha
        try:
            expected = int(request.POST.get('expected_result', 0))
            user_result = int(request.POST.get('captcha_result', -1))
            if user_result != expected:
                messages.error(request, "Verifica di sicurezza fallita. Riprova.")
                return HttpResponseRedirect(reverse('booking_send_payment_link', args=[appointment.pk]))
        except (ValueError, TypeError):
            messages.error(request, "Inserisci un numero valido per la verifica.")
            return HttpResponseRedirect(reverse('booking_send_payment_link', args=[appointment.pk]))
        
        # Aggiorna metodo di pagamento se specificato
        new_method = request.POST.get('payment_method')
        if new_method in ['stripe', 'paypal']:
            appointment.payment_method = new_method
        
        # Genera token se non esiste
        if not appointment.payment_token:
            appointment.payment_token = secrets.token_urlsafe(32)
        
        appointment.save()
        
        # Invia email con link
        result = ps.send_payment_link(appointment, request)
        if result:
            messages.success(request, f"Link di pagamento inviato a {appointment.email}!")
        else:
            messages.error(request, "Errore nell'invio dell'email.")
        
        return HttpResponseRedirect(
            reverse('wagtailsnippets_booking_appointment:edit', args=[appointment.pk])
        )


from django.shortcuts import render
from django.http import HttpResponseRedirect


@hooks.register('register_admin_urls')
def register_payment_action_urls():
    """Registra URL per azioni pagamento."""
    return [
        path('booking/refund/<int:appointment_id>/', RefundPaymentView.as_view(), name='booking_refund'),
        path('booking/send-payment-link/<int:appointment_id>/', SendPaymentLinkView.as_view(), name='booking_send_payment_link'),
    ]


from wagtail.snippets.action_menu import ActionMenuItem


class RefundPaymentActionItem(ActionMenuItem):
    """Pulsante Rimborsa Pagamento nel menu azioni snippet."""
    name = 'refund_payment'
    label = "💰 Rimborsa Pagamento"
    
    def is_shown(self, context):
        instance = context.get('instance')
        if instance and hasattr(instance, 'can_refund'):
            return instance.can_refund
        return False
    
    def get_url(self, context):
        instance = context.get('instance')
        if instance:
            return reverse('booking_refund', args=[instance.pk])
        return '#'


class SendPaymentLinkActionItem(ActionMenuItem):
    """Pulsante Invia Link Pagamento nel menu azioni snippet."""
    name = 'send_payment_link'
    label = "📧 Invia Link Pagamento"
    
    def is_shown(self, context):
        instance = context.get('instance')
        if instance and hasattr(instance, 'can_send_payment_link'):
            return instance.can_send_payment_link
        return False
    
    def get_url(self, context):
        instance = context.get('instance')
        if instance:
            return reverse('booking_send_payment_link', args=[instance.pk])
        return '#'


@hooks.register('construct_snippet_action_menu')
def add_payment_actions_to_appointment(menu_items, request, context):
    """Aggiunge azioni pagamento al menu snippet Appointment."""
    instance = context.get('instance')
    
    # Solo per Appointment
    if instance and isinstance(instance, Appointment):
        # Inserisci le azioni prima del pulsante Delete
        insert_position = len(menu_items)
        for i, item in enumerate(menu_items):
            if item.name == 'delete':
                insert_position = i
                break
        
        if instance.can_send_payment_link:
            menu_items.insert(insert_position, SendPaymentLinkActionItem())
            insert_position += 1
        
        if instance.can_refund:
            menu_items.insert(insert_position, RefundPaymentActionItem())
