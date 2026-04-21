from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class ProductCategory(Base):
    __tablename__ = "product_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    sku = Column(String(50), unique=True, nullable=True)
    barcode = Column(String(50), nullable=True)
    price = Column(Float, nullable=False)
    cost = Column(Float, nullable=True)
    stock = Column(Integer, default=0)
    min_stock = Column(Integer, default=5)  # Alerta de stock minimo
    category_id = Column(Integer, ForeignKey("product_categories.id"), nullable=True)
    is_service = Column(Boolean, default=False)  # True = servicio (clases, etc.)
    is_active = Column(Boolean, default=True)
    image_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    category = relationship("ProductCategory", back_populates="products")
    sale_items = relationship("SaleItem", back_populates="product")


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    sale_number = Column(String(20), unique=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    cashier = Column(String(100), nullable=True)
    subtotal = Column(Float, nullable=False, default=0)
    discount = Column(Float, default=0)
    tax = Column(Float, default=0)
    total = Column(Float, nullable=False, default=0)
    payment_method = Column(String(50), default="cash")  # cash, card, transfer
    payment_reference = Column(String(100), nullable=True)
    status = Column(String(20), default="completed")  # completed, cancelled, refunded
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)

    member = relationship("Member", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    memberships = relationship("MemberMembership", foreign_keys="MemberMembership.sale_id")


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    product_name = Column(String(150), nullable=False)  # Snapshot del nombre
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)
    discount = Column(Float, default=0)
    total = Column(Float, nullable=False)

    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")
