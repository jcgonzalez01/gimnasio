from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class HikvisionDeviceBase(BaseModel):
    name: str
    ip_address: str
    port: int = 80
    username: str = "admin"
    password: str
    device_type: str = "access_control"
    location: Optional[str] = None
    direction: str = "both"
    is_active: bool = True
    face_lib_id: str = "1"


class HikvisionDeviceCreate(HikvisionDeviceBase):
    pass


class HikvisionDeviceUpdate(BaseModel):
    name: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    location: Optional[str] = None
    direction: Optional[str] = None
    is_active: Optional[bool] = None


class HikvisionDeviceOut(BaseModel):
    id: int
    name: str
    ip_address: str
    port: int
    username: str
    device_type: str
    location: Optional[str] = None
    direction: str
    is_active: bool
    last_heartbeat: Optional[datetime] = None
    serial_number: Optional[str] = None
    model: Optional[str] = None
    firmware: Optional[str] = None
    face_lib_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class AccessLogBase(BaseModel):
    member_id: Optional[int] = None
    device_id: Optional[int] = None
    direction: str = "in"
    access_type: str = "face"
    result: str = "granted"
    temperature: Optional[float] = None
    notes: Optional[str] = None


class AccessLogCreate(AccessLogBase):
    pass


class AccessLogOut(AccessLogBase):
    id: int
    timestamp: datetime
    member_name: Optional[str] = None
    device_name: Optional[str] = None

    class Config:
        from_attributes = True


class AccessEventWS(BaseModel):
    """Evento enviado via WebSocket"""
    event_type: str = "access"
    log_id: int
    member_id: Optional[int] = None
    member_name: Optional[str] = None
    member_number: Optional[str] = None
    photo_path: Optional[str] = None
    device_name: Optional[str] = None
    device_location: Optional[str] = None
    direction: str = "in"
    result: str = "granted"
    access_type: str = "face"
    temperature: Optional[float] = None
    timestamp: str
