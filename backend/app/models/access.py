from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class HikvisionDevice(Base):
    __tablename__ = "hikvision_devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    ip_address = Column(String(50), nullable=False)
    port = Column(Integer, default=80)
    username = Column(String(50), default="admin")
    password = Column(String(100), nullable=False)
    device_type = Column(String(50), default="access_control")  # access_control, camera
    location = Column(String(100), nullable=True)  # Ej: "Entrada Principal"
    direction = Column(String(10), default="both")  # in, out, both
    is_active = Column(Boolean, default=True)
    last_heartbeat = Column(DateTime, nullable=True)
    serial_number = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    firmware = Column(String(50), nullable=True)
    face_lib_id = Column(String(50), default="1")  # ID de libreria facial en Hikvision
    created_at = Column(DateTime, server_default=func.now())

    access_logs = relationship("AccessLog", back_populates="device")


class AccessLog(Base):
    __tablename__ = "access_logs"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    device_id = Column(Integer, ForeignKey("hikvision_devices.id"), nullable=True)
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    direction = Column(String(10), default="in")  # in, out
    access_type = Column(String(30), default="face")  # face, card, pin, manual
    result = Column(String(20), default="granted")  # granted, denied, unknown
    temperature = Column(Float, nullable=True)  # Si el dispositivo tiene termometro
    raw_event = Column(Text, nullable=True)  # JSON raw del evento Hikvision
    capture_path = Column(String(255), nullable=True)  # Foto capturada en el momento
    notes = Column(String(255), nullable=True)

    member = relationship("Member", back_populates="access_logs")
    device = relationship("HikvisionDevice", back_populates="access_logs")
