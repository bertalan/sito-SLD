"""
Test TDD per PaymentConfig - gestione modalità pagamento flessibile.

STRIPE_MODE e PAYPAL_MODE possono essere: sandbox | live | off
- off: nasconde il pulsante dalla pagina prenotazione
- sandbox: usa API di test
- live: usa API di produzione

Se entrambi sono off, il pagamento avviene in un secondo momento via link email.
"""
import pytest
from unittest.mock import patch
from django.test import TestCase, override_settings


class TestPaymentConfigStripeMode(TestCase):
    """Test STRIPE_MODE: off, sandbox, live."""
    
    @override_settings(STRIPE_MODE='off')
    def test_stripe_mode_off_disables_stripe(self):
        """STRIPE_MODE=off deve disabilitare Stripe."""
        from booking.payment_config import PaymentConfig
        config = PaymentConfig()
        self.assertFalse(config.stripe_enabled)
    
    @override_settings(STRIPE_MODE='sandbox')
    def test_stripe_mode_sandbox_enables_stripe(self):
        """STRIPE_MODE=sandbox deve abilitare Stripe."""
        from booking.payment_config import PaymentConfig
        config = PaymentConfig()
        self.assertTrue(config.stripe_enabled)
    
    @override_settings(STRIPE_MODE='live')
    def test_stripe_mode_live_enables_stripe(self):
        """STRIPE_MODE=live deve abilitare Stripe."""
        from booking.payment_config import PaymentConfig
        config = PaymentConfig()
        self.assertTrue(config.stripe_enabled)
    
    def test_stripe_mode_default_is_sandbox(self):
        """Se STRIPE_MODE non è impostato, default a sandbox (abilitato)."""
        from booking.payment_config import PaymentConfig
        # Il default in settings è sandbox
        config = PaymentConfig()
        self.assertTrue(config.stripe_enabled)


class TestPaymentConfigPayPalMode(TestCase):
    """Test PAYPAL_MODE: off, sandbox, live."""
    
    @override_settings(PAYPAL_MODE='off')
    def test_paypal_mode_off_disables_paypal(self):
        """PAYPAL_MODE=off deve disabilitare PayPal."""
        from booking.payment_config import PaymentConfig
        config = PaymentConfig()
        self.assertFalse(config.paypal_enabled)
    
    @override_settings(PAYPAL_MODE='sandbox')
    def test_paypal_mode_sandbox_enables_paypal(self):
        """PAYPAL_MODE=sandbox deve abilitare PayPal."""
        from booking.payment_config import PaymentConfig
        config = PaymentConfig()
        self.assertTrue(config.paypal_enabled)
    
    @override_settings(PAYPAL_MODE='live')
    def test_paypal_mode_live_enables_paypal(self):
        """PAYPAL_MODE=live deve abilitare PayPal."""
        from booking.payment_config import PaymentConfig
        config = PaymentConfig()
        self.assertTrue(config.paypal_enabled)


class TestPaymentConfigCombinations(TestCase):
    """Test combinazioni di STRIPE_MODE e PAYPAL_MODE."""
    
    @override_settings(STRIPE_MODE='off', PAYPAL_MODE='off')
    def test_both_off_no_payment_required(self):
        """Se entrambi off, nessun pagamento richiesto ora."""
        from booking.payment_config import PaymentConfig
        config = PaymentConfig()
        self.assertFalse(config.any_payment_enabled)
        self.assertTrue(config.payment_deferred)
    
    @override_settings(STRIPE_MODE='sandbox', PAYPAL_MODE='off')
    def test_only_stripe_enabled(self):
        """Solo Stripe abilitato."""
        from booking.payment_config import PaymentConfig
        config = PaymentConfig()
        self.assertTrue(config.stripe_enabled)
        self.assertFalse(config.paypal_enabled)
        self.assertTrue(config.any_payment_enabled)
        self.assertFalse(config.payment_deferred)
    
    @override_settings(STRIPE_MODE='off', PAYPAL_MODE='sandbox')
    def test_only_paypal_enabled(self):
        """Solo PayPal abilitato."""
        from booking.payment_config import PaymentConfig
        config = PaymentConfig()
        self.assertFalse(config.stripe_enabled)
        self.assertTrue(config.paypal_enabled)
        self.assertTrue(config.any_payment_enabled)
        self.assertFalse(config.payment_deferred)
    
    @override_settings(STRIPE_MODE='live', PAYPAL_MODE='live')
    def test_both_enabled(self):
        """Entrambi abilitati in live."""
        from booking.payment_config import PaymentConfig
        config = PaymentConfig()
        self.assertTrue(config.stripe_enabled)
        self.assertTrue(config.paypal_enabled)
        self.assertTrue(config.any_payment_enabled)
        self.assertFalse(config.payment_deferred)


class TestPaymentConfigDemoMode(TestCase):
    """Test PAYMENT_MODE=demo per simulazione."""
    
    @override_settings(PAYMENT_MODE='demo')
    def test_demo_mode_detected(self):
        """PAYMENT_MODE=demo deve essere rilevato."""
        from booking.payment_config import PaymentConfig
        config = PaymentConfig()
        self.assertTrue(config.is_demo_mode)
    
    @override_settings(PAYMENT_MODE='live')
    def test_live_mode_not_demo(self):
        """PAYMENT_MODE=live non è demo."""
        from booking.payment_config import PaymentConfig
        config = PaymentConfig()
        self.assertFalse(config.is_demo_mode)


class TestPaymentConfigAPIEndpoints(TestCase):
    """Test che le API usino l'endpoint corretto in base alla modalità."""
    
    @override_settings(STRIPE_MODE='sandbox')
    def test_stripe_sandbox_uses_test_keys(self):
        """Stripe sandbox deve usare chiavi di test."""
        from booking.payment_config import PaymentConfig
        config = PaymentConfig()
        self.assertFalse(config.stripe_is_live)
    
    @override_settings(STRIPE_MODE='live')
    def test_stripe_live_uses_production_keys(self):
        """Stripe live deve usare chiavi di produzione."""
        from booking.payment_config import PaymentConfig
        config = PaymentConfig()
        self.assertTrue(config.stripe_is_live)
    
    @override_settings(PAYPAL_MODE='sandbox')
    def test_paypal_sandbox_uses_sandbox_api(self):
        """PayPal sandbox deve usare API sandbox."""
        from booking.payment_config import PaymentConfig
        config = PaymentConfig()
        self.assertEqual(config.paypal_api_base, 'https://api-m.sandbox.paypal.com')
    
    @override_settings(PAYPAL_MODE='live')
    def test_paypal_live_uses_production_api(self):
        """PayPal live deve usare API di produzione."""
        from booking.payment_config import PaymentConfig
        config = PaymentConfig()
        self.assertEqual(config.paypal_api_base, 'https://api-m.paypal.com')


class TestPaymentConfigContextDict(TestCase):
    """Test che PaymentConfig possa essere convertito in dict per i template."""
    
    @override_settings(STRIPE_MODE='sandbox', PAYPAL_MODE='live', PAYMENT_MODE='live')
    def test_to_dict_returns_all_flags(self):
        """to_dict() deve restituire tutti i flag necessari ai template."""
        from booking.payment_config import PaymentConfig
        config = PaymentConfig()
        d = config.to_dict()
        
        self.assertIn('stripe_enabled', d)
        self.assertIn('paypal_enabled', d)
        self.assertIn('any_payment_enabled', d)
        self.assertIn('payment_deferred', d)
        self.assertIn('is_demo_mode', d)
