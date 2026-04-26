from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from ..core.database import Base
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"           # Acceso total
    MANAGER = "manager"       # Gestión de miembros, ventas, reportes (no usuarios ni dispositivos)
    CASHIER = "cashier"       # Solo POS y consulta de miembros
    RECEPTION = "reception"   # Asistencia, ver miembros, registrar entrada manual


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=True)
    full_name = Column(String(150), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default=UserRole.CASHIER, nullable=False)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
