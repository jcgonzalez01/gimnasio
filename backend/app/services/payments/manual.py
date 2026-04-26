"""Provider 'manual': el cobro se realiza fuera del sistema (efectivo, tarjeta presencial)."""
import uuid
from typing import Optional

from .base import PaymentProvider, PaymentResult, PaymentStatus


class ManualProvider(PaymentProvider):
    name = "manual"

    def create_payment(self, amount, description, reference, payer_email=None) -> PaymentResult:
        return PaymentResult(
            status=PaymentStatus.APPROVED,
            provider=self.name,
            transaction_id=f"MAN-{uuid.uuid4().hex[:12].upper()}",
        )

    def get_payment_status(self, transaction_id: str) -> PaymentResult:
        return PaymentResult(
            status=PaymentStatus.APPROVED,
            provider=self.name,
            transaction_id=transaction_id,
        )

    def refund(self, transaction_id, amount: Optional[float] = None) -> PaymentResult:
        return PaymentResult(
            status=PaymentStatus.REFUNDED,
            provider=self.name,
            transaction_id=transaction_id,
        )
