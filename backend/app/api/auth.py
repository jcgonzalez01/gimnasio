"""Endpoints de autenticación y gestión de usuarios."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from typing import List, Optional

from ..core.database import get_db
from ..core.security import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_admin,
)
from ..models.user import User, UserRole
from ..models.audit import AuditLog
from ..schemas.user import (
    UserCreate, UserUpdate, UserOut,
    LoginRequest, TokenResponse, ChangePasswordRequest,
)
from ..services.audit import log_action
from ..services.deletion import assess_user, to_409_payload

router = APIRouter(prefix="/auth", tags=["Autenticación"])


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.hashed_password):
        log_action(db, None, "login_failed",
                   summary=f"Intento fallido para '{data.username}'", request=request)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario deshabilitado",
        )
    user.last_login = datetime.utcnow()
    db.commit()
    log_action(db, user, "login", summary=f"Login exitoso", request=request)
    token = create_access_token(subject=user.username, role=user.role)
    return TokenResponse(access_token=token, user=user)


@router.post("/login-form", response_model=TokenResponse)
def login_form(form: OAuth2PasswordRequestForm = Depends(),
               request: Request = None,
               db: Session = Depends(get_db)):
    """Endpoint compatible con OAuth2 (Swagger UI)."""
    return login(LoginRequest(username=form.username, password=form.password), request, db)


# ── Usuario actual ────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/change-password")
def change_password(data: ChangePasswordRequest,
                    user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
    user.hashed_password = hash_password(data.new_password)
    db.commit()
    return {"message": "Contraseña actualizada"}


# ── Gestión de usuarios (solo admin) ─────────────────────────────────────────

@router.get("/users", response_model=List[UserOut])
def list_users(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).all()


@router.post("/users", response_model=UserOut, status_code=201)
def create_user(data: UserCreate,
                _: User = Depends(require_admin),
                db: Session = Depends(get_db)):
    if data.role not in [r.value for r in UserRole]:
        raise HTTPException(status_code=400, detail="Rol inválido")

    user = User(
        username=data.username,
        email=data.email,
        full_name=data.full_name,
        role=data.role,
        is_active=data.is_active,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username o email ya en uso")
    db.refresh(user)
    return user


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, data: UserUpdate,
                _: User = Depends(require_admin),
                db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    payload = data.model_dump(exclude_none=True)
    if "password" in payload:
        user.hashed_password = hash_password(payload.pop("password"))
    if "role" in payload and payload["role"] not in [r.value for r in UserRole]:
        raise HTTPException(status_code=400, detail="Rol inválido")
    for k, v in payload.items():
        setattr(user, k, v)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username o email ya en uso")
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def delete_user(user_id: int,
                request: Request,
                force: bool = False,
                current: User = Depends(require_admin),
                db: Session = Depends(get_db)):
    if user_id == current.id:
        raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    impact = assess_user(db, user)
    if impact["history"] and not force:
        raise HTTPException(status_code=409,
                            detail=to_409_payload("El usuario", impact))

    user.is_active = False
    db.commit()
    log_action(db, current, "delete", entity_type="user", entity_id=user.id,
               summary=f"Deshabilitó usuario '{user.username}'" + (" (forzado)" if force else ""),
               request=request)
    return {"message": "Usuario deshabilitado"}


# ── Notificaciones (disparo manual) ──────────────────────────────────────────

@router.post("/notifications/run-expiry-check")
def run_expiry_check(_: User = Depends(require_admin)):
    """Dispara manualmente la revisión de vencimientos (útil para test o cron externo)."""
    from ..services.notifications import check_expiring_memberships, update_expired_member_status
    notif = check_expiring_memberships()
    status_update = update_expired_member_status()
    return {"notifications": notif, "status_update": status_update}


# ── Auditoría ─────────────────────────────────────────────────────────────────

@router.get("/audit")
def get_audit_log(
    limit: int = 100,
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(AuditLog).order_by(AuditLog.timestamp.desc())
    if action:
        q = q.filter(AuditLog.action == action)
    if user_id:
        q = q.filter(AuditLog.user_id == user_id)
    rows = q.limit(min(limit, 1000)).all()
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "username": r.username,
            "action": r.action,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "summary": r.summary,
            "details": r.details,
            "ip_address": r.ip_address,
            "timestamp": r.timestamp,
        }
        for r in rows
    ]
