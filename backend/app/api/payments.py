"""Endpoints de pago (pasarela externa)."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import require_roles
from ..models.user import User
from ..models.pos import Sale
from ..services.payments import get_payment_provider
from ..services.payments.base import PaymentStatus

router = APIRouter(prefix="/payments", tags=["Pagos"])


class CreatePaymentRequest(BaseModel):
    sale_id: Optional[int] = None
    amount: float
    description: str
    reference: str
    payer_email: Optional[str] = None


@router.post("/create")
def create_payment(data: CreatePaymentRequest,
                   _: User = Depends(require_roles("cashier", "manager", "reception")),
                   db: Session = Depends(get_db)):
    provider = get_payment_provider()
    result = provider.create_payment(
        amount=data.amount,
        description=data.description,
        reference=data.reference,
        payer_email=data.payer_email,
    )

    if data.sale_id:
        sale = db.query(Sale).filter(Sale.id == data.sale_id).first()
        if sale and result.transaction_id:
            sale.payment_reference = result.transaction_id
            sale.payment_method = provider.name
            db.commit()

    return {
        "provider": result.provider,
        "status": result.status.value,
        "transaction_id": result.transaction_id,
        "checkout_url": result.checkout_url,
        "error": result.error,
    }


@router.get("/{transaction_id}/status")
def payment_status(transaction_id: str,
                   _: User = Depends(require_roles("cashier", "manager", "reception"))):
    provider = get_payment_provider()
    result = provider.get_payment_status(transaction_id)
    return {
        "provider": result.provider,
        "status": result.status.value,
        "transaction_id": result.transaction_id,
        "error": result.error,
    }


@router.post("/{transaction_id}/refund")
def refund_payment(transaction_id: str,
                   amount: Optional[float] = None,
                   _: User = Depends(require_roles("manager"))):
    provider = get_payment_provider()
    result = provider.refund(transaction_id, amount)
    if result.status == PaymentStatus.REJECTED:
        raise HTTPException(status_code=400, detail=result.error or "Refund rechazado")
    return {
        "provider": result.provider,
        "status": result.status.value,
        "transaction_id": result.transaction_id,
    }


@router.get("/config")
def payment_config():
    """Devuelve configuración pública (no expone access tokens)."""
    from ..core.config import settings
    return {
        "provider": settings.PAYMENT_PROVIDER,
        "public_key": settings.MERCADOPAGO_PUBLIC_KEY if settings.PAYMENT_PROVIDER == "mercadopago" else None,
    }
