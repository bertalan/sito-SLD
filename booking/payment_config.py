"""
PaymentConfig - Configurazione flessibile per metodi di pagamento.

Gestisce STRIPE_MODE e PAYPAL_MODE con valori: sandbox | live | off
- off: nasconde il pulsante dalla pagina prenotazione
- sandbox: usa API di test
- live: usa API di produzione

Se entrambi sono off, il pagamento avviene in un secondo momento via link email.
"""
from django.conf import settings


class PaymentConfig:
    """
    Configurazione centralizzata per i metodi di pagamento.
    
    Uso:
        config = PaymentConfig()
        if config.stripe_enabled:
            # mostra pulsante Stripe
        if config.payment_deferred:
            # mostra messaggio "pagamento in seguito"
    """
    
    @property
    def stripe_mode(self) -> str:
        """Ritorna la modalità Stripe: sandbox, live, o off."""
        return getattr(settings, 'STRIPE_MODE', 'sandbox')
    
    @property
    def paypal_mode(self) -> str:
        """Ritorna la modalità PayPal: sandbox, live, o off."""
        return getattr(settings, 'PAYPAL_MODE', 'sandbox')
    
    @property
    def payment_mode(self) -> str:
        """Ritorna la modalità pagamento globale: demo o live."""
        return getattr(settings, 'PAYMENT_MODE', 'demo')
    
    # === Provider enabled flags ===
    
    @property
    def stripe_enabled(self) -> bool:
        """True se Stripe è abilitato (non off)."""
        return self.stripe_mode != 'off'
    
    @property
    def paypal_enabled(self) -> bool:
        """True se PayPal è abilitato (non off)."""
        return self.paypal_mode != 'off'
    
    @property
    def any_payment_enabled(self) -> bool:
        """True se almeno un metodo di pagamento è abilitato."""
        return self.stripe_enabled or self.paypal_enabled
    
    @property
    def payment_deferred(self) -> bool:
        """True se il pagamento è differito (entrambi off)."""
        return not self.any_payment_enabled
    
    # === Mode flags ===
    
    @property
    def is_demo_mode(self) -> bool:
        """True se siamo in modalità demo (simula pagamenti)."""
        return self.payment_mode == 'demo'
    
    @property
    def stripe_is_live(self) -> bool:
        """True se Stripe usa l'ambiente di produzione."""
        return self.stripe_mode == 'live'
    
    @property
    def paypal_is_live(self) -> bool:
        """True se PayPal usa l'ambiente di produzione."""
        return self.paypal_mode == 'live'
    
    # === API endpoints ===
    
    @property
    def paypal_api_base(self) -> str:
        """Ritorna l'URL base delle API PayPal."""
        if self.paypal_mode == 'live':
            return 'https://api-m.paypal.com'
        return 'https://api-m.sandbox.paypal.com'
    
    # === Serialization ===
    
    def to_dict(self) -> dict:
        """Converte la configurazione in dict per i template."""
        return {
            'stripe_enabled': self.stripe_enabled,
            'paypal_enabled': self.paypal_enabled,
            'any_payment_enabled': self.any_payment_enabled,
            'payment_deferred': self.payment_deferred,
            'is_demo_mode': self.is_demo_mode,
            'stripe_is_live': self.stripe_is_live,
            'paypal_is_live': self.paypal_is_live,
            'stripe_mode': self.stripe_mode,
            'paypal_mode': self.paypal_mode,
        }


# Singleton per uso globale
payment_config = PaymentConfig()
