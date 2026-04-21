from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class MembershipPlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    duration_days: int
    price: float
    max_entries_per_day: Optional[int] = None
    allows_guest: bool = False
    is_active: bool = True
    color: str = "#4CAF50"


class MembershipPlanCreate(MembershipPlanBase):
    pass


class MembershipPlanUpdate(MembershipPlanBase):
    name: Optional[str] = None
    duration_days: Optional[int] = None
    price: Optional[float] = None


class MembershipPlanOut(MembershipPlanBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class MemberMembershipBase(BaseModel):
    plan_id: int
    start_date: datetime
    end_date: datetime
    price_paid: float
    payment_method: str = "cash"
    notes: Optional[str] = None


class MemberMembershipCreate(MemberMembershipBase):
    member_id: Optional[int] = None   # también llega en el path, se puede omitir


class MemberMembershipOut(MemberMembershipBase):
    id: int
    member_id: int
    is_active: bool
    created_at: datetime
    plan: Optional[MembershipPlanOut] = None
    sale_id: Optional[int] = None

    class Config:
        from_attributes = True


class AccessEnrollResult(BaseModel):
    device: str
    user_added: bool = False
    face_enrolled: bool = False
    error: Optional[str] = None


class AssignMembershipResponse(BaseModel):
    membership: MemberMembershipOut
    sale_id: int
    sale_number: str
    sale_total: float
    payment_method: str
    access_enrolled: bool
    access_results: List[AccessEnrollResult] = []
    access_skipped: bool = False   # True si no hay foto

    class Config:
        from_attributes = True


class MemberBase(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[datetime] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    notes: Optional[str] = None


class MemberCreate(MemberBase):
    pass


class MemberUpdate(MemberBase):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: Optional[str] = None


class MemberOut(MemberBase):
    id: int
    member_number: str
    status: str
    photo_path: Optional[str] = None
    face_enrolled: bool
    hikvision_card_no: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    memberships: List[MemberMembershipOut] = []

    class Config:
        from_attributes = True


class MemberListOut(BaseModel):
    id: int
    member_number: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str
    face_enrolled: bool
    photo_path: Optional[str] = None
    created_at: datetime
    has_active_membership: bool = False
    membership_expires: Optional[datetime] = None

    class Config:
        from_attributes = True
