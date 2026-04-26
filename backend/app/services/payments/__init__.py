"""Pasarelas de pago. Por defecto usa el provider configurado en settings.PAYMENT_PROVIDER."""
from .base import PaymentProvider, PaymentResult, PaymentStatus
from .manual import ManualProvider
from .mercadopago import MercadoPagoProvider
from ...core.config import settings


def get_payment_provider() -> PaymentProvider:
    """Devuelve la implementación del provider configurado."""
    provider = (settings.PAYMENT_PROVIDER or "manual").lower()
    if provider == "mercadopago":
        return MercadoPagoProvider()
    return ManualProvider()
