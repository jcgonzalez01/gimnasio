from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class AuditLog(Base):
    """Registro de acciones sensibles realizadas por usuarios."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(50), nullable=True, index=True)
    action = Column(String(50), nullable=False, index=True)  # create, update, delete, login, refund, open_door, ...
    entity_type = Column(String(50), nullable=True, index=True)  # member, sale, plan, device, ...
    entity_id = Column(String(50), nullable=True)
    summary = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)  # JSON con cambios o contexto
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, server_default=func.now(), index=True)

    user = relationship("User", foreign_keys=[user_id])
