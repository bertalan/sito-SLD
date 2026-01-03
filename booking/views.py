from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.core.exceptions import ValidationError
from datetime import datetime, date, timedelta
import json
import logging

from .models import Appointment, AvailabilityRule, BlockedDate, AppointmentAttachment
from .email_service import send_booking_confirmation
from .payment_service import payment_service
from sld_project.validators import validate_attachment_file
from sld_project.ratelimit import RateLimitMixin, RATE_LIMITS

logger = logging.getLogger(__name__)


class BookingView(TemplateView):
    template_name = 'booking/booking.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stripe_public_key'] = settings.STRIPE_PUBLIC_KEY
        context['paypal_client_id'] = settings.PAYPAL_CLIENT_ID
        
        # Prezzi e durate dal settings (da .env)
        context['booking_price_cents'] = settings.BOOKING_PRICE_CENTS
        context['booking_price'] = f"{settings.BOOKING_PRICE_CENTS / 100:.2f}".replace('.', ',')
        context['slot_duration'] = settings.BOOKING_SLOT_DURATION
        context['max_slots'] = settings.BOOKING_MAX_SLOTS
        
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


class CreateCheckoutSession(RateLimitMixin, View):
    """Creates a payment checkout session for booking appointments."""
    MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20MB
    PENDING_TIMEOUT_MINUTES = 30  # Timeout per appuntamenti pending
    rate_limit = RATE_LIMITS['booking']  # Rate limit: 10/minute per IP
    
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
                
                # Valida tipo e contenuto di ogni file
                for f in files:
                    try:
                        validate_attachment_file(f)
                    except ValidationError as e:
                        return JsonResponse({'error': f'File "{f.name}": {e.message}'}, status=400)
            else:
                data = json.loads(request.body)
                files = []
            
            payment_method = data.get('payment_method', 'stripe')
            consultation_type = data.get('consultation_type', 'in_person')
            slot_count = int(data.get('slot_count', 1))
            
            # Valida slot_count
            max_slots = settings.BOOKING_MAX_SLOTS
            if slot_count < 1 or slot_count > max_slots:
                return JsonResponse({'error': f'Il numero di slot deve essere tra 1 e {max_slots}'}, status=400)
            
            target_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            target_time = datetime.strptime(data['time'], '%H:%M').time()
            
            # Calcola tutti gli slot necessari
            slot_duration = settings.BOOKING_SLOT_DURATION
            required_slots = []
            current_dt = datetime.combine(target_date, target_time)
            for i in range(slot_count):
                required_slots.append(current_dt.time())
                current_dt += timedelta(minutes=slot_duration)
            
            # Pulisci appuntamenti pending scaduti (più vecchi di 30 minuti)
            from django.utils import timezone
            cutoff_time = timezone.now() - timedelta(minutes=self.PENDING_TIMEOUT_MINUTES)
            Appointment.objects.filter(
                status='pending',
                created_at__lt=cutoff_time
            ).delete()
            
            # Verifica che tutti gli slot consecutivi siano disponibili
            available_slots = Appointment.get_available_slots(target_date)
            for slot in required_slots:
                if slot not in available_slots:
                    return JsonResponse({
                        'error': f'Lo slot delle {slot.strftime("%H:%M")} non è disponibile. Seleziona un altro orario.'
                    }, status=400)
            
            # Verifica se uno degli slot è già occupato da un appuntamento confermato
            existing = Appointment.objects.filter(
                date=target_date,
                time__in=required_slots,
                status='confirmed'
            ).exists()
            
            if existing:
                return JsonResponse({'error': 'Uno o più slot selezionati non sono più disponibili. Seleziona un altro orario.'}, status=400)
            
            # Rimuovi eventuali pending per gli stessi slot (stesso utente che riprova)
            Appointment.objects.filter(
                date=target_date,
                time__in=required_slots,
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
                slot_count=slot_count,
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
                    appointment.amount_paid = appointment.total_price_cents / 100
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
                        appointment.amount_paid = appointment.total_price_cents / 100
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
    """
    Webhook Stripe per conferma pagamento.
    
    SICUREZZA:
    - La firma viene SEMPRE verificata tramite STRIPE_WEBHOOK_SECRET
    - In demo mode, il webhook è disabilitato (non ci sono pagamenti reali)
    - @csrf_exempt è corretto qui perché Stripe non può inviare token CSRF
    """
    # In demo mode, non ci sono pagamenti reali, ignora il webhook
    # ma logga comunque per debugging
    if payment_service.is_demo:
        logger.info("Stripe webhook received in demo mode - ignoring")
        return JsonResponse({'status': 'demo_mode_ignored'})
    
    # VERIFICA FIRMA OBBLIGATORIA per tutti gli altri casi
    result = payment_service.verify_webhook(request, 'stripe')
    
    if not result.get('valid'):
        logger.warning(f"Invalid Stripe webhook: {result.get('error')}")
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
                appointment.amount_paid = appointment.total_price_cents / 100
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


class PaymentLinkView(View):
    """
    View per il pagamento tramite link diretto.
    Usata quando lo studio invia il link di pagamento al cliente.
    """
    
    def get(self, request, appointment_id):
        """Mostra la pagina di pagamento con i dati dell'appuntamento."""
        from django.shortcuts import get_object_or_404
        
        token = request.GET.get('token')
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        # Verifica token
        if not token or token != appointment.payment_token:
            return render(request, 'booking/payment_link_error.html', {
                'error': 'Link di pagamento non valido o scaduto.'
            }, status=403)
        
        # Verifica che sia ancora pending
        if appointment.status != 'pending':
            return render(request, 'booking/payment_link_error.html', {
                'error_message': 'Questo appuntamento è già stato pagato o annullato.'
            })
        
        # Calcola importo dovuto
        amount_due = appointment.service.prezzo if appointment.service else Decimal('60.00')
        
        context = {
            'appointment': appointment,
            'amount_due': amount_due,
            'payment_method': appointment.payment_method,
            'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
            'paypal_client_id': settings.PAYPAL_CLIENT_ID,
            'payment_mode': settings.PAYMENT_MODE,
            'is_demo_mode': payment_service.is_demo,
        }
        
        return render(request, 'booking/payment_link.html', context)
    
    def post(self, request, appointment_id):
        """Processa il pagamento dal link."""
        from django.shortcuts import get_object_or_404
        
        token = request.POST.get('token') or request.GET.get('token')
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        # Verifica token
        if not token or token != appointment.payment_token:
            return JsonResponse({'error': 'Token non valido'}, status=403)
        
        if appointment.status != 'pending':
            return JsonResponse({'error': 'Appuntamento non più disponibile'}, status=400)
        
        # Aggiorna metodo di pagamento se cambiato
        new_method = request.POST.get('payment_method')
        if new_method in ['stripe', 'paypal']:
            appointment.payment_method = new_method
            appointment.save(update_fields=['payment_method'])
        
        # Crea sessione di pagamento
        data = {
            'date': appointment.date.isoformat(),
            'time': appointment.time.strftime('%H:%M'),
        }
        
        result = payment_service.create_payment(request, appointment, data)
        
        if result.success:
            return JsonResponse({
                'success': True,
                'redirect_url': result.redirect_url
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.error
            }, status=400)
