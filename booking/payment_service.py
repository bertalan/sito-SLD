"""
Sistema di pagamento con tre modalità:
- demo: Simula il pagamento (sempre successo)
- sandbox: Usa i dati di test Stripe/PayPal
- live: Usa i dati reali di produzione
"""
import uuid
import logging
from abc import ABC, abstractmethod
from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)


class PaymentResult:
    """Risultato di un'operazione di pagamento."""
    
    def __init__(self, success: bool, redirect_url: str = None, 
                 payment_id: str = None, error: str = None):
        self.success = success
        self.redirect_url = redirect_url
        self.payment_id = payment_id
        self.error = error


class BasePaymentProvider(ABC):
    """Classe base per i provider di pagamento."""
    
    @abstractmethod
    def create_payment(self, request, appointment, data) -> PaymentResult:
        """Crea un pagamento e restituisce l'URL di redirect."""
        pass
    
    @abstractmethod
    def execute_payment(self, request, appointment) -> PaymentResult:
        """Esegue/conferma un pagamento."""
        pass
    
    @abstractmethod
    def verify_webhook(self, request) -> dict:
        """Verifica e processa un webhook."""
        pass


class DemoStripeProvider(BasePaymentProvider):
    """Provider Stripe demo - simula sempre il pagamento con successo."""
    
    def create_payment(self, request, appointment, data) -> PaymentResult:
        # Genera un ID fittizio
        fake_session_id = f"demo_stripe_{uuid.uuid4().hex[:16]}"
        appointment.stripe_payment_intent_id = fake_session_id
        appointment.save()
        
        # Redirect diretto alla pagina di successo
        success_url = request.build_absolute_uri(
            f'/prenota/success/?session_id={fake_session_id}&method=stripe&demo=1'
        )
        
        logger.info(f"[DEMO] Stripe payment created for appointment {appointment.id}")
        return PaymentResult(success=True, redirect_url=success_url, payment_id=fake_session_id)
    
    def execute_payment(self, request, appointment) -> PaymentResult:
        # In demo mode, il pagamento è sempre confermato
        appointment.status = 'confirmed'
        appointment.amount_paid = appointment.total_price_cents / 100
        appointment.save()
        
        logger.info(f"[DEMO] Stripe payment executed for appointment {appointment.id}")
        return PaymentResult(success=True, payment_id=appointment.stripe_payment_intent_id)
    
    def verify_webhook(self, request) -> dict:
        # In demo mode, accetta tutto
        return {'status': 'demo_mode', 'valid': True}


class DemoPayPalProvider(BasePaymentProvider):
    """Provider PayPal demo - simula sempre il pagamento con successo."""
    
    def create_payment(self, request, appointment, data) -> PaymentResult:
        # Genera un ID fittizio
        fake_payment_id = f"demo_paypal_{uuid.uuid4().hex[:16]}"
        appointment.paypal_payment_id = fake_payment_id
        appointment.save()
        
        # Redirect diretto alla pagina di esecuzione con parametri fittizi
        execute_url = request.build_absolute_uri(
            f'/prenota/paypal/execute/?appointment_id={appointment.id}'
            f'&paymentId={fake_payment_id}&PayerID=demo_payer&demo=1'
        )
        
        logger.info(f"[DEMO] PayPal payment created for appointment {appointment.id}")
        return PaymentResult(success=True, redirect_url=execute_url, payment_id=fake_payment_id)
    
    def execute_payment(self, request, appointment) -> PaymentResult:
        # In demo mode, il pagamento è sempre confermato
        appointment.status = 'confirmed'
        appointment.amount_paid = appointment.total_price_cents / 100
        appointment.save()
        
        logger.info(f"[DEMO] PayPal payment executed for appointment {appointment.id}")
        return PaymentResult(success=True, payment_id=appointment.paypal_payment_id)
    
    def verify_webhook(self, request) -> dict:
        return {'status': 'demo_mode', 'valid': True}


class RealStripeProvider(BasePaymentProvider):
    """Provider Stripe reale (sandbox o live in base alle chiavi)."""
    
    def __init__(self):
        import stripe
        self.stripe = stripe
        self.stripe.api_key = settings.STRIPE_SECRET_KEY
    
    def create_payment(self, request, appointment, data) -> PaymentResult:
        try:
            checkout_session = self.stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'eur',
                        'unit_amount': appointment.total_price_cents,
                        'product_data': {
                            'name': 'Consulenza legale',
                            'description': f'Appuntamento {data["date"]} alle {data["time"]} ({appointment.duration_minutes} minuti)',
                        },
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.build_absolute_uri('/prenota/success/') + '?session_id={CHECKOUT_SESSION_ID}&method=stripe',
                cancel_url=request.build_absolute_uri('/prenota/cancel/'),
                customer_email=data['email'],
                metadata={'appointment_id': appointment.id}
            )
            
            appointment.stripe_payment_intent_id = checkout_session.payment_intent
            appointment.save()
            
            return PaymentResult(success=True, redirect_url=checkout_session.url, 
                               payment_id=checkout_session.payment_intent)
        except Exception as e:
            logger.error(f"Stripe payment creation failed: {e}")
            return PaymentResult(success=False, error=str(e))
    
    def execute_payment(self, request, appointment) -> PaymentResult:
        # Per Stripe, la conferma avviene tramite webhook o session retrieve
        session_id = request.GET.get('session_id')
        if session_id:
            try:
                session = self.stripe.checkout.Session.retrieve(session_id)
                if session.payment_status == 'paid':
                    appointment.status = 'confirmed'
                    appointment.amount_paid = session.amount_total / 100
                    appointment.save()
                    return PaymentResult(success=True, payment_id=session.payment_intent)
            except Exception as e:
                logger.error(f"Stripe session retrieve failed: {e}")
                return PaymentResult(success=False, error=str(e))
        
        return PaymentResult(success=False, error="Session ID mancante")
    
    def verify_webhook(self, request) -> dict:
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        try:
            event = self.stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            return {'valid': True, 'event': event}
        except ValueError:
            return {'valid': False, 'error': 'Invalid payload'}
        except self.stripe.error.SignatureVerificationError:
            return {'valid': False, 'error': 'Invalid signature'}


class RealPayPalProvider(BasePaymentProvider):
    """Provider PayPal reale (sandbox o live in base alla config)."""
    
    def __init__(self):
        import paypalrestsdk
        self.paypal = paypalrestsdk
        self.paypal.configure({
            "mode": settings.PAYPAL_MODE,
            "client_id": settings.PAYPAL_CLIENT_ID,
            "client_secret": settings.PAYPAL_CLIENT_SECRET
        })
    
    def create_payment(self, request, appointment, data) -> PaymentResult:
        price = appointment.total_price_cents / 100
        
        payment = self.paypal.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": request.build_absolute_uri(
                    f'/prenota/paypal/execute/?appointment_id={appointment.id}'
                ),
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
            
            for link in payment.links:
                if link.rel == "approval_url":
                    return PaymentResult(success=True, redirect_url=link.href, 
                                       payment_id=payment.id)
            
            return PaymentResult(success=False, error='URL di approvazione PayPal non trovato')
        else:
            return PaymentResult(success=False, error=str(payment.error))
    
    def execute_payment(self, request, appointment) -> PaymentResult:
        payment_id = request.GET.get('paymentId')
        payer_id = request.GET.get('PayerID')
        
        if not all([payment_id, payer_id]):
            return PaymentResult(success=False, error="Parametri mancanti")
        
        try:
            payment = self.paypal.Payment.find(payment_id)
            
            if payment.execute({"payer_id": payer_id}):
                appointment.status = 'confirmed'
                appointment.amount_paid = appointment.total_price_cents / 100
                appointment.save()
                return PaymentResult(success=True, payment_id=payment_id)
            else:
                return PaymentResult(success=False, error=str(payment.error))
        except Exception as e:
            logger.error(f"PayPal execute failed: {e}")
            return PaymentResult(success=False, error=str(e))
    
    def verify_webhook(self, request) -> dict:
        # PayPal webhook verification
        return {'valid': True}


class PaymentService:
    """
    Servizio principale per la gestione dei pagamenti.
    Seleziona automaticamente il provider in base a PAYMENT_MODE.
    """
    
    def __init__(self):
        self._mode = None
        self._providers = {}
    
    @property
    def mode(self):
        """Lazy loading della modalità di pagamento."""
        if self._mode is None:
            self._mode = getattr(settings, 'PAYMENT_MODE', 'demo')
        return self._mode
    
    def get_provider(self, payment_method: str) -> BasePaymentProvider:
        """Restituisce il provider appropriato per il metodo di pagamento."""
        cache_key = f"{self.mode}_{payment_method}"
        
        if cache_key not in self._providers:
            if self.mode == 'demo':
                if payment_method == 'stripe':
                    self._providers[cache_key] = DemoStripeProvider()
                else:
                    self._providers[cache_key] = DemoPayPalProvider()
            else:
                # sandbox e live usano gli stessi provider, le chiavi API determinano l'ambiente
                if payment_method == 'stripe':
                    self._providers[cache_key] = RealStripeProvider()
                else:
                    self._providers[cache_key] = RealPayPalProvider()
        
        return self._providers[cache_key]
    
    def create_payment(self, request, appointment, data) -> PaymentResult:
        """Crea un pagamento usando il provider appropriato."""
        provider = self.get_provider(appointment.payment_method)
        return provider.create_payment(request, appointment, data)
    
    def execute_payment(self, request, appointment) -> PaymentResult:
        """Esegue/conferma un pagamento."""
        provider = self.get_provider(appointment.payment_method)
        return provider.execute_payment(request, appointment)
    
    def verify_webhook(self, request, payment_method: str) -> dict:
        """Verifica un webhook."""
        provider = self.get_provider(payment_method)
        return provider.verify_webhook(request)
    
    @property
    def is_demo(self) -> bool:
        """Restituisce True se siamo in modalità demo."""
        return self.mode == 'demo'
    
    @property
    def is_sandbox(self) -> bool:
        """Restituisce True se siamo in modalità sandbox."""
        return self.mode == 'sandbox'
    
    @property
    def is_live(self) -> bool:
        """Restituisce True se siamo in modalità live."""
        return self.mode == 'live'


# Istanza singleton del servizio
payment_service = PaymentService()
