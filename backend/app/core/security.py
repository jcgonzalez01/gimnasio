"""Helpers de seguridad: hash de passwords y JWT."""
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from ..models.user import User, UserRole


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

ALGORITHM = "HS256"


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


def create_access_token(subject: str, role: str,
                        expires_minutes: Optional[int] = None) -> str:
    expires = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    payload = {
        "sub": subject,
        "role": role,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=expires),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])


# ── Dependencias FastAPI ──────────────────────────────────────────────────────

CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Credenciales inválidas o expiradas",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise CREDENTIALS_EXC
    try:
        payload = decode_token(token)
        username: str = payload.get("sub")
        if not username:
            raise CREDENTIALS_EXC
    except JWTError:
        raise CREDENTIALS_EXC

    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise CREDENTIALS_EXC
    return user


def require_roles(*allowed_roles: str):
    """Dependencia que valida que el usuario tenga uno de los roles permitidos."""
    def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles and user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado: requiere rol {' o '.join(allowed_roles)}",
            )
        return user
    return _checker


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: requiere rol admin",
        )
    return user
