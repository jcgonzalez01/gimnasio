"""Verificación de impacto antes de borrar entidades con historial.

Cada función `assess_*` devuelve un dict con:
  {
    "history": bool,                 # True si hay registros relacionados
    "blocked": bool,                 # True si NO se puede borrar ni con force
    "block_reason": str | None,      # Motivo del bloqueo
    "items": [{"label": str, "count": int}]  # detalle para mostrar al usuario
  }
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.member import Member, MembershipPlan, MemberMembership
from ..models.pos import Product, ProductCategory, Sale, SaleItem
from ..models.access import HikvisionDevice, AccessLog
from ..models.user import User
from ..models.audit import AuditLog


def _empty() -> Dict[str, Any]:
    return {"history": False, "blocked": False, "block_reason": None, "items": []}


def assess_member(db: Session, member: Member) -> Dict[str, Any]:
    res = _empty()
    now = datetime.utcnow()
    active = [m for m in member.memberships
              if m.is_active and m.start_date <= now and m.end_date >= now]
    if active:
        res["blocked"] = True
        res["block_reason"] = "El miembro tiene una membresía vigente. Anúlala antes de eliminar."
        return res

    counts = [
        ("Membresías históricas", len(member.memberships)),
        ("Ventas vinculadas", db.query(Sale).filter(Sale.member_id == member.id).count()),
        ("Registros de acceso", db.query(AccessLog).filter(AccessLog.member_id == member.id).count()),
    ]
    res["items"] = [{"label": l, "count": c} for l, c in counts if c > 0]
    res["history"] = bool(res["items"])
    return res


def assess_plan(db: Session, plan: MembershipPlan) -> Dict[str, Any]:
    res = _empty()
    n = db.query(MemberMembership).filter(MemberMembership.plan_id == plan.id).count()
    if n:
        res["history"] = True
        res["items"] = [{"label": "Membresías que usaron este plan", "count": n}]
    return res


def assess_product(db: Session, product: Product) -> Dict[str, Any]:
    res = _empty()
    n = db.query(SaleItem).filter(SaleItem.product_id == product.id).count()
    if n:
        res["history"] = True
        res["items"] = [{"label": "Ventas que incluyen este producto", "count": n}]
    return res


def assess_category(db: Session, category: ProductCategory) -> Dict[str, Any]:
    res = _empty()
    n = db.query(Product).filter(Product.category_id == category.id,
                                  Product.is_active == True).count()
    if n:
        res["history"] = True
        res["items"] = [{"label": "Productos activos en esta categoría", "count": n}]
    return res


def assess_device(db: Session, device: HikvisionDevice) -> Dict[str, Any]:
    res = _empty()
    n = db.query(AccessLog).filter(AccessLog.device_id == device.id).count()
    if n:
        res["history"] = True
        res["items"] = [{"label": "Eventos de acceso registrados", "count": n}]
    return res


def assess_user(db: Session, user: User) -> Dict[str, Any]:
    res = _empty()
    n = db.query(AuditLog).filter(AuditLog.user_id == user.id).count()
    if n:
        res["history"] = True
        res["items"] = [{"label": "Acciones en auditoría", "count": n}]
    return res


def assess_sale(db: Session, sale: Sale) -> Dict[str, Any]:
    """Las ventas no se borran físicamente — se cancelan."""
    res = _empty()
    if sale.status == "cancelled":
        res["blocked"] = True
        res["block_reason"] = "La venta ya está cancelada."
    return res


def to_409_payload(label: str, assess: Dict[str, Any]) -> Dict[str, Any]:
    """Formato unificado para devolver al frontend en 409."""
    return {
        "detail": f"{label} tiene historial asociado. Confirma para continuar.",
        "requires_force": True,
        "history": assess["history"],
        "items": assess["items"],
    }
