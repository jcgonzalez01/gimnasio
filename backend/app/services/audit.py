"""Servicio para registrar acciones en la auditoría."""
import json
import logging
from typing import Any, Optional
from sqlalchemy.orm import Session
from fastapi import Request

from ..models.audit import AuditLog
from ..models.user import User

logger = logging.getLogger(__name__)


def log_action(
    db: Session,
    user: Optional[User],
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[Any] = None,
    summary: Optional[str] = None,
    details: Optional[dict] = None,
    request: Optional[Request] = None,
) -> None:
    """Registra una acción de auditoría. Nunca lanza excepción al fallar."""
    try:
        ip = None
        if request is not None:
            ip = request.client.host if request.client else None
            fwd = request.headers.get("x-forwarded-for")
            if fwd:
                ip = fwd.split(",")[0].strip()

        entry = AuditLog(
            user_id=user.id if user else None,
            username=user.username if user else None,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            summary=summary,
            details=json.dumps(details, default=str) if details else None,
            ip_address=ip,
        )
        db.add(entry)
        db.commit()
    except Exception as exc:
        logger.warning(f"Error registrando auditoría ({action}): {exc}")
        try:
            db.rollback()
        except Exception:
            pass
