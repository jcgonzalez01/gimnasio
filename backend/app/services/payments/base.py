"""Interfaz común para pasarelas de pago."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PaymentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


@dataclass
class PaymentResult:
    status: PaymentStatus
    provider: str
    transaction_id: Optional[str] = None
    checkout_url: Optional[str] = None  # Para pagos asíncronos (MP, Stripe)
    raw_response: Optional[dict] = None
    error: Optional[str] = None


class PaymentProvider(ABC):
    name: str = "base"

    @abstractmethod
    def create_payment(self, amount: float, description: str,
                       reference: str, payer_email: Optional[str] = None) -> PaymentResult:
        """Crea un pago/preferencia. Para 'manual' simplemente lo da por aprobado."""

    @abstractmethod
    def get_payment_status(self, transaction_id: str) -> PaymentResult:
        """Consulta el estado de un pago previamente creado."""

    @abstractmethod
    def refund(self, transaction_id: str, amount: Optional[float] = None) -> PaymentResult:
        """Reversa total o parcial."""
