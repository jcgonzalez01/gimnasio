from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import enum


class MemberStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    member_number = Column(String(20), unique=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=True)
    phone = Column(String(20), nullable=True)
    birth_date = Column(DateTime, nullable=True)
    gender = Column(String(10), nullable=True)
    address = Column(Text, nullable=True)
    emergency_contact = Column(String(150), nullable=True)
    emergency_phone = Column(String(20), nullable=True)
    photo_path = Column(String(255), nullable=True)
    face_enrolled = Column(Boolean, default=False)
    hikvision_card_no = Column(String(50), nullable=True)  # ID facial en Hikvision
    status = Column(String(20), default=MemberStatus.ACTIVE)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    memberships = relationship("MemberMembership", back_populates="member", cascade="all, delete-orphan")
    access_logs = relationship("AccessLog", back_populates="member")
    sales = relationship("Sale", back_populates="member")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def active_membership(self):
        from datetime import datetime
        now = datetime.utcnow()
        for m in self.memberships:
            if m.start_date <= now and m.end_date >= now and m.is_active:
                return m
        return None


class MembershipPlan(Base):
    __tablename__ = "membership_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    duration_days = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    max_entries_per_day = Column(Integer, nullable=True)  # None = ilimitado
    allows_guest = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    color = Column(String(7), default="#4CAF50")  # Color hex para UI
    created_at = Column(DateTime, server_default=func.now())

    member_memberships = relationship("MemberMembership", back_populates="plan")


class MemberMembership(Base):
    __tablename__ = "member_memberships"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("membership_plans.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    price_paid = Column(Float, nullable=False)
    payment_method = Column(String(50), default="cash")
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=True)

    member = relationship("Member", back_populates="memberships")
    plan = relationship("MembershipPlan", back_populates="member_memberships")
