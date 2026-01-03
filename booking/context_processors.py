"""
Context processor per iniettare PaymentConfig nei template.
"""
from .payment_config import PaymentConfig


def payment_config_context(request):
    """
    Inietta la configurazione pagamento in tutti i template.
    
    Uso nel template:
        {% if payment_config.stripe_enabled %}
            <button>Paga con Carta</button>
        {% endif %}
    """
    config = PaymentConfig()
    return {
        'payment_config': config,
    }
