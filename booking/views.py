from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from datetime import datetime, date, timedelta
import stripe
import paypalrestsdk
import json

from .models import Appointment, AvailabilityRule, BlockedDate, AppointmentAttachment
from .email_service import send_booking_confirmation

# Configurazione Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

# Configurazione PayPal
paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,  # sandbox o live
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})


class BookingView(TemplateView):
    template_name = 'booking/booking.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stripe_public_key'] = settings.STRIPE_PUBLIC_KEY
        context['paypal_client_id'] = settings.PAYPAL_CLIENT_ID
        context['booking_price'] = settings.BOOKING_PRICE_CENTS / 100
        
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
            
            if payment_method == 'paypal':
                return self._create_paypal_payment(request, appointment, data)
            else:
                return self._create_stripe_session(request, appointment, data)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    def _create_stripe_session(self, request, appointment, data):
        """Crea sessione di checkout Stripe."""
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'unit_amount': settings.BOOKING_PRICE_CENTS,
                    'product_data': {
                        'name': 'Consulenza legale',
                        'description': f'Appuntamento {data["date"]} alle {data["time"]}',
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri('/prenota/success/') + f'?session_id={{CHECKOUT_SESSION_ID}}&method=stripe',
            cancel_url=request.build_absolute_uri('/prenota/cancel/'),
            customer_email=data['email'],
            metadata={'appointment_id': appointment.id}
        )
        
        appointment.stripe_payment_intent_id = checkout_session.payment_intent
        appointment.save()
        
        return JsonResponse({'url': checkout_session.url})
    
    def _create_paypal_payment(self, request, appointment, data):
        """Crea pagamento PayPal."""
        price = settings.BOOKING_PRICE_CENTS / 100
        
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": request.build_absolute_uri(f'/prenota/paypal/execute/?appointment_id={appointment.id}'),
                "cancel_url": request.build_absolute_uri('/prenota/cancel/')
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": "Consulenza legale",
                        "description": f"Appuntamento {data['date']} alle {data['time']}",
                        "quantity": "1",
                        "price": f"{price:.2f}",
                        "currency": "EUR"
                    }]
                },
                "amount": {
                    "total": f"{price:.2f}",
                    "currency": "EUR"
                },
                "description": f"Consulenza legale - Appuntamento {data['date']}"
            }]
        })
        
        if payment.create():
            appointment.paypal_payment_id = payment.id
            appointment.save()
            
            # Trova l'URL di approvazione
            for link in payment.links:
                if link.rel == "approval_url":
                    return JsonResponse({'url': link.href})
            
            return JsonResponse({'error': 'URL di approvazione PayPal non trovato'}, status=400)
        else:
            appointment.delete()
            return JsonResponse({'error': payment.error}, status=400)


class BookingSuccessView(TemplateView):
    template_name = 'booking/success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_id = self.request.GET.get('session_id')
        
        if session_id:
            try:
                session = stripe.checkout.Session.retrieve(session_id)
                appointment_id = session.metadata.get('appointment_id')
                if appointment_id:
                    appointment = Appointment.objects.get(id=appointment_id)
                    # Evita di inviare email multiple se già confermato
                    if appointment.status != 'confirmed':
                        appointment.status = 'confirmed'
                        appointment.amount_paid = settings.BOOKING_PRICE_CENTS / 100
                        appointment.save()
                        # Invia email di conferma con iCal
                        send_booking_confirmation(appointment)
                    context['appointment'] = appointment
            except Exception:
                pass
        
        return context


class BookingCancelView(TemplateView):
    template_name = 'booking/cancel.html'


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Webhook Stripe per conferma pagamento."""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        appointment_id = session.get('metadata', {}).get('appointment_id')
        
        if appointment_id:
            try:
                appointment = Appointment.objects.get(id=appointment_id)
                appointment.status = 'confirmed'
                appointment.amount_paid = session.get('amount_total', 0) / 100
                appointment.save()
            except Appointment.DoesNotExist:
                pass
    
    return JsonResponse({'status': 'success'})


def paypal_execute(request):
    """Esegue il pagamento PayPal dopo l'approvazione dell'utente."""
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')
    appointment_id = request.GET.get('appointment_id')
    
    if not all([payment_id, payer_id, appointment_id]):
        return redirect('/prenota/cancel/')
    
    try:
        payment = paypalrestsdk.Payment.find(payment_id)
        
        if payment.execute({"payer_id": payer_id}):
            appointment = Appointment.objects.get(id=appointment_id)
            appointment.status = 'confirmed'
            appointment.amount_paid = settings.BOOKING_PRICE_CENTS / 100
            appointment.save()
            
            # Invia email di conferma con iCal
            send_booking_confirmation(appointment)
            
            return redirect(f'/prenota/success/?appointment_id={appointment_id}&method=paypal')
        else:
            return redirect('/prenota/cancel/')
    
    except Exception:
        return redirect('/prenota/cancel/')


class PayPalSuccessView(TemplateView):
    """Pagina di successo per pagamenti PayPal."""
    template_name = 'booking/success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        appointment_id = self.request.GET.get('appointment_id')
        
        if appointment_id:
            try:
                appointment = Appointment.objects.get(id=appointment_id)
                context['appointment'] = appointment
            except Appointment.DoesNotExist:
                pass
        
        return context
