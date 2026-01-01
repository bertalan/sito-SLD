from wagtail import hooks
from wagtail.admin.menu import MenuItem, Menu, SubmenuMenuItem
from wagtail.admin.ui.tables import Column
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from wagtail.admin.views.generic.base import WagtailAdminTemplateMixin
from django.urls import reverse, path
from django.views.generic import TemplateView
from django.utils import timezone
from datetime import timedelta
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
    ]


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
