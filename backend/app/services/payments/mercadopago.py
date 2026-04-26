"""Provider MercadoPago — Checkout Pro / Preferencias.

Requiere variables MERCADOPAGO_ACCESS_TOKEN y MERCADOPAGO_PUBLIC_KEY.
Usa la API HTTP directamente (no requiere SDK). Si el token no está configurado,
crear un pago retorna error.
"""
import logging
from typing import Optional
import httpx

from .base import PaymentProvider, PaymentResult, PaymentStatus
from ...core.config import settings

logger = logging.getLogger(__name__)
MP_API_BASE = "https://api.mercadopago.com"


def _mp_headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.MERCADOPAGO_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


def _map_status(mp_status: str) -> PaymentStatus:
    return {
        "approved":   PaymentStatus.APPROVED,
        "in_process": PaymentStatus.PENDING,
        "pending":    PaymentStatus.PENDING,
        "rejected":   PaymentStatus.REJECTED,
        "cancelled":  PaymentStatus.CANCELLED,
        "refunded":   PaymentStatus.REFUNDED,
    }.get(mp_status, PaymentStatus.PENDING)


class MercadoPagoProvider(PaymentProvider):
    name = "mercadopago"

    def _check_config(self) -> Optional[str]:
        if not settings.MERCADOPAGO_ACCESS_TOKEN:
            return "MERCADOPAGO_ACCESS_TOKEN no configurado"
        return None

    def create_payment(self, amount, description, reference, payer_email=None) -> PaymentResult:
        err = self._check_config()
        if err:
            return PaymentResult(status=PaymentStatus.REJECTED, provider=self.name, error=err)

        body = {
            "items": [{
                "title": description,
                "quantity": 1,
                "unit_price": float(amount),
                "currency_id": "ARS",
            }],
            "external_reference": reference,
            "back_urls": {
                "success": f"{settings.BACKEND_BASE_URL}/payment/success",
                "failure": f"{settings.BACKEND_BASE_URL}/payment/failure",
                "pending": f"{settings.BACKEND_BASE_URL}/payment/pending",
            },
            "auto_return": "approved",
        }
        if payer_email:
            body["payer"] = {"email": payer_email}

        try:
            with httpx.Client(timeout=15) as cli:
                r = cli.post(f"{MP_API_BASE}/checkout/preferences",
                             json=body, headers=_mp_headers())
                data = r.json()
                if r.status_code >= 400:
                    return PaymentResult(
                        status=PaymentStatus.REJECTED, provider=self.name,
                        error=data.get("message", f"HTTP {r.status_code}"),
                        raw_response=data,
                    )
                return PaymentResult(
                    status=PaymentStatus.PENDING, provider=self.name,
                    transaction_id=data.get("id"),
                    checkout_url=data.get("init_point"),
                    raw_response=data,
                )
        except Exception as exc:
            logger.error(f"MercadoPago error: {exc}")
            return PaymentResult(status=PaymentStatus.REJECTED, provider=self.name,
                                 error=str(exc))

    def get_payment_status(self, transaction_id: str) -> PaymentResult:
        err = self._check_config()
        if err:
            return PaymentResult(status=PaymentStatus.PENDING, provider=self.name, error=err)
        try:
            with httpx.Client(timeout=15) as cli:
                r = cli.get(f"{MP_API_BASE}/v1/payments/{transaction_id}", headers=_mp_headers())
                data = r.json()
                return PaymentResult(
                    status=_map_status(data.get("status", "pending")),
                    provider=self.name,
                    transaction_id=str(data.get("id")),
                    raw_response=data,
                )
        except Exception as exc:
            return PaymentResult(status=PaymentStatus.PENDING, provider=self.name, error=str(exc))

    def refund(self, transaction_id, amount=None) -> PaymentResult:
        err = self._check_config()
        if err:
            return PaymentResult(status=PaymentStatus.REJECTED, provider=self.name, error=err)
        try:
            payload = {"amount": float(amount)} if amount is not None else {}
            with httpx.Client(timeout=15) as cli:
                r = cli.post(f"{MP_API_BASE}/v1/payments/{transaction_id}/refunds",
                             json=payload, headers=_mp_headers())
                data = r.json()
                if r.status_code >= 400:
                    return PaymentResult(status=PaymentStatus.REJECTED, provider=self.name,
                                         error=data.get("message", f"HTTP {r.status_code}"),
                                         raw_response=data)
                return PaymentResult(status=PaymentStatus.REFUNDED, provider=self.name,
                                     transaction_id=transaction_id, raw_response=data)
        except Exception as exc:
            return PaymentResult(status=PaymentStatus.REJECTED, provider=self.name, error=str(exc))
