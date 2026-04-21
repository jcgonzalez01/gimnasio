from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ProductCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool = True


class ProductCategoryCreate(ProductCategoryBase):
    pass


class ProductCategoryOut(ProductCategoryBase):
    id: int

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    price: float
    cost: Optional[float] = None
    stock: int = 0
    min_stock: int = 5
    category_id: Optional[int] = None
    is_service: bool = False
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    name: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None


class ProductOut(ProductBase):
    id: int
    image_path: Optional[str] = None
    created_at: datetime
    category: Optional[ProductCategoryOut] = None

    class Config:
        from_attributes = True


class SaleItemCreate(BaseModel):
    product_id: Optional[int] = None
    product_name: str
    quantity: int = 1
    unit_price: float
    discount: float = 0


class SaleItemOut(BaseModel):
    id: int
    product_id: Optional[int] = None
    product_name: str
    quantity: int
    unit_price: float
    discount: float
    total: float

    class Config:
        from_attributes = True


class SaleCreate(BaseModel):
    member_id: Optional[int] = None
    cashier: Optional[str] = None
    discount: float = 0
    tax: float = 0
    payment_method: str = "cash"
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
    items: List[SaleItemCreate]


class SaleOut(BaseModel):
    id: int
    sale_number: str
    member_id: Optional[int] = None
    cashier: Optional[str] = None
    subtotal: float
    discount: float
    tax: float
    total: float
    payment_method: str
    payment_reference: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime
    items: List[SaleItemOut] = []
    member_name: Optional[str] = None

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_members: int
    active_members: int
    expired_members: int
    entries_today: int
    entries_this_month: int
    sales_today: float
    sales_this_month: float
    low_stock_products: int
    memberships_expiring_soon: int  # proximos 7 dias
