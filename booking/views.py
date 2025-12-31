from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from datetime import datetime, date, timedelta
import json
import logging

from .models import Appointment, AvailabilityRule, BlockedDate, AppointmentAttachment
from .email_service import send_booking_confirmation
from .payment_service import payment_service

logger = logging.getLogger(__name__)


class BookingView(TemplateView):
    template_name = 'booking/booking.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stripe_public_key'] = settings.STRIPE_PUBLIC_KEY
        context['paypal_client_id'] = settings.PAYPAL_CLIENT_ID
        context['booking_price'] = settings.BOOKING_PRICE_CENTS / 100
        
        # Modalità pagamento per il frontend
        context['payment_mode'] = settings.PAYMENT_MODE
        context['is_demo_mode'] = payment_service.is_demo
        
        today = date.today()
        available_dates = []
        
        for i in range(1, 61):  # 60 giorni di disponibilità
            check_date = today + timedelta(days=i)
            if Appointment.get_available_slots(check_date):
                available_dates.append(check_date.isoformat())
        
        context['available_dates'] = json.dumps(available_dates)
        return context


def get_available_slots(request, date):
    """API per ottenere gli slot disponibili per una data."""
    try:
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
        slots = Appointment.get_available_slots(target_date)
        return JsonResponse({
            'slots': [slot.strftime('%H:%M') for slot in slots]
        })
    except ValueError:
        return JsonResponse({'error': 'Data non valida'}, status=400)


class CreateCheckoutSession(View):
    MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20MB
    PENDING_TIMEOUT_MINUTES = 30  # Timeout per appuntamenti pending
    
    def post(self, request):
        try:
            # Supporta sia JSON che FormData
            if request.content_type and 'multipart/form-data' in request.content_type:
                data = request.POST.dict()
                files = request.FILES.getlist('attachments')
                
                # Verifica dimensione totale file
                total_size = sum(f.size for f in files)
                if total_size > self.MAX_UPLOAD_SIZE:
                    return JsonResponse({'error': 'La dimensione totale degli allegati supera i 20MB'}, status=400)
            else:
                data = json.loads(request.body)
                files = []
            
            payment_method = data.get('payment_method', 'stripe')
            consultation_type = data.get('consultation_type', 'in_person')
            
            target_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            target_time = datetime.strptime(data['time'], '%H:%M').time()
            
            # Pulisci appuntamenti pending scaduti (più vecchi di 30 minuti)
            from django.utils import timezone
            cutoff_time = timezone.now() - timedelta(minutes=self.PENDING_TIMEOUT_MINUTES)
            Appointment.objects.filter(
                status='pending',
                created_at__lt=cutoff_time
            ).delete()
            
            # Verifica se lo slot è già occupato da un appuntamento confermato
            existing = Appointment.objects.filter(
                date=target_date,
                time=target_time,
                status='confirmed'
            ).exists()
            
            if existing:
                return JsonResponse({'error': 'Questo slot non è più disponibile. Seleziona un altro orario.'}, status=400)
            
            # Rimuovi eventuali pending per lo stesso slot (stesso utente che riprova)
            Appointment.objects.filter(
                date=target_date,
                time=target_time,
                status='pending'
            ).delete()
            
            # Crea l'appuntamento in stato pending
            appointment = Appointment.objects.create(
                first_name=data['first_name'],
                last_name=data['last_name'],
                email=data['email'],
                phone=data['phone'],
                notes=data.get('notes', ''),
                consultation_type=consultation_type,
                date=target_date,
                time=target_time,
                status='pending',
                payment_method=payment_method
            )
            
            # Genera il codice videochiamata se necessario (forza save per avere pk)
            if consultation_type == 'video':
                appointment.save()
            
            # Salva gli allegati
            for f in files:
                AppointmentAttachment.objects.create(
                    appointment=appointment,
                    file=f,
                    original_filename=f.name
                )
            
            # Usa il servizio di pagamento unificato
            result = payment_service.create_payment(request, appointment, data)
            
            if result.success:
                return JsonResponse({'url': result.redirect_url})
            else:
                appointment.delete()
                return JsonResponse({'error': result.error}, status=400)
            
        except Exception as e:
            logger.error(f"CreateCheckoutSession error: {e}")
            return JsonResponse({'error': str(e)}, status=400)


class BookingSuccessView(TemplateView):
    template_name = 'booking/success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_id = self.request.GET.get('session_id')
        appointment_id = self.request.GET.get('appointment_id')
        is_demo = self.request.GET.get('demo') == '1'
        method = self.request.GET.get('method', 'stripe')
        
        context['is_demo_mode'] = payment_service.is_demo
        context['payment_mode'] = settings.PAYMENT_MODE
        
        # Gestisci pagamento demo
        if is_demo and session_id:
            # In demo mode, trova l'appuntamento dal session_id simulato
            try:
                appointment = Appointment.objects.filter(
                    stripe_payment_intent_id=session_id
                ).first()
                if appointment and appointment.status != 'confirmed':
                    appointment.status = 'confirmed'
                    appointment.amount_paid = settings.BOOKING_PRICE_CENTS / 100
                    appointment.save()
                    send_booking_confirmation(appointment)
                context['appointment'] = appointment
            except Exception as e:
                logger.error(f"Demo success error: {e}")
        
        # Gestisci pagamento Stripe reale
        elif session_id and not is_demo:
            try:
                import stripe
                stripe.api_key = settings.STRIPE_SECRET_KEY
                session = stripe.checkout.Session.retrieve(session_id)
                apt_id = session.metadata.get('appointment_id')
                if apt_id:
                    appointment = Appointment.objects.get(id=apt_id)
                    if appointment.status != 'confirmed':
                        appointment.status = 'confirmed'
                        appointment.amount_paid = settings.BOOKING_PRICE_CENTS / 100
                        appointment.save()
                        send_booking_confirmation(appointment)
                    context['appointment'] = appointment
            except Exception as e:
                logger.error(f"Stripe success error: {e}")
        
        # Gestisci pagamento PayPal (redirect da paypal_execute)
        elif appointment_id:
            try:
                appointment = Appointment.objects.get(id=appointment_id)
                context['appointment'] = appointment
            except Appointment.DoesNotExist:
                pass
        
        return context


class BookingCancelView(TemplateView):
    template_name = 'booking/cancel.html'


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Webhook Stripe per conferma pagamento."""
    # In demo mode, accetta tutto
    if payment_service.is_demo:
        return JsonResponse({'status': 'demo_mode'})
    
    result = payment_service.verify_webhook(request, 'stripe')
    
    if not result.get('valid'):
        return JsonResponse({'error': result.get('error', 'Invalid webhook')}, status=400)
    
    event = result.get('event')
    if event and event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        appointment_id = session.get('metadata', {}).get('appointment_id')
        
        if appointment_id:
            try:
                appointment = Appointment.objects.get(id=appointment_id)
                if appointment.status != 'confirmed':
                    appointment.status = 'confirmed'
                    appointment.amount_paid = session.get('amount_total', 0) / 100
                    appointment.save()
                    send_booking_confirmation(appointment)
            except Appointment.DoesNotExist:
                pass
    
    return JsonResponse({'status': 'success'})


def paypal_execute(request):
    """Esegue il pagamento PayPal dopo l'approvazione dell'utente."""
    appointment_id = request.GET.get('appointment_id')
    is_demo = request.GET.get('demo') == '1'
    
    if not appointment_id:
        return redirect('/prenota/cancel/')
    
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        
        # In demo mode, conferma direttamente
        if is_demo or payment_service.is_demo:
            if appointment.status != 'confirmed':
                appointment.status = 'confirmed'
                appointment.amount_paid = settings.BOOKING_PRICE_CENTS / 100
                appointment.save()
                send_booking_confirmation(appointment)
            return redirect(f'/prenota/success/?appointment_id={appointment_id}&method=paypal&demo=1')
        
        # Pagamento reale PayPal
        result = payment_service.execute_payment(request, appointment)
        
        if result.success:
            if appointment.status != 'confirmed':
                send_booking_confirmation(appointment)
            return redirect(f'/prenota/success/?appointment_id={appointment_id}&method=paypal')
        else:
            return redirect('/prenota/cancel/')
    
    except Exception as e:
        logger.error(f"PayPal execute error: {e}")
        return redirect('/prenota/cancel/')


class PayPalSuccessView(TemplateView):
    """Pagina di successo per pagamenti PayPal."""
    template_name = 'booking/success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        appointment_id = self.request.GET.get('appointment_id')
        
        context['is_demo_mode'] = payment_service.is_demo
        context['payment_mode'] = settings.PAYMENT_MODE
        
        if appointment_id:
            try:
                appointment = Appointment.objects.get(id=appointment_id)
                context['appointment'] = appointment
            except Appointment.DoesNotExist:
                pass
        
        return context
