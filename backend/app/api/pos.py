from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime, timedelta

from ..core.database import get_db
from ..models.pos import Product, ProductCategory, Sale, SaleItem
from ..models.member import Member
from ..schemas.pos import (
    ProductCategoryCreate, ProductCategoryOut,
    ProductCreate, ProductUpdate, ProductOut,
    SaleCreate, SaleOut, DashboardStats,
)
from ..models.access import AccessLog
from ..models.member import MemberMembership

router = APIRouter(prefix="/pos", tags=["Punto de Venta"])


# ── Categorías ────────────────────────────────────────────────────────────────

@router.get("/categories", response_model=List[ProductCategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(ProductCategory).filter(ProductCategory.is_active == True).all()


@router.post("/categories", response_model=ProductCategoryOut, status_code=201)
def create_category(cat: ProductCategoryCreate, db: Session = Depends(get_db)):
    db_cat = ProductCategory(**cat.model_dump())
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat


# ── Productos ─────────────────────────────────────────────────────────────────

@router.get("/products", response_model=List[ProductOut])
def list_products(
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    is_service: Optional[bool] = None,
    low_stock: bool = False,
    db: Session = Depends(get_db)
):
    q = db.query(Product).filter(Product.is_active == True)
    if search:
        q = q.filter(Product.name.ilike(f"%{search}%"))
    if category_id:
        q = q.filter(Product.category_id == category_id)
    if is_service is not None:
        q = q.filter(Product.is_service == is_service)
    if low_stock:
        q = q.filter(Product.stock <= Product.min_stock, Product.is_service == False)
    return q.all()


@router.post("/products", response_model=ProductOut, status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_prod = Product(**product.model_dump())
    db.add(db_prod)
    db.commit()
    db.refresh(db_prod)
    return db_prod


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return p


@router.put("/products/{product_id}", response_model=ProductOut)
def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    for k, v in product.model_dump(exclude_none=True).items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    p.is_active = False
    db.commit()
    return {"message": "Producto desactivado"}


@router.put("/products/{product_id}/stock")
def update_stock(product_id: int, quantity: int, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    p.stock = quantity
    db.commit()
    return {"stock": p.stock}


# ── Ventas ────────────────────────────────────────────────────────────────────

def generate_sale_number(db: Session) -> str:
    last = db.query(Sale).order_by(Sale.id.desc()).first()
    next_id = (last.id + 1) if last else 1
    return f"V{datetime.utcnow().strftime('%Y%m%d')}-{next_id:04d}"


@router.post("/sales", response_model=SaleOut, status_code=201)
def create_sale(sale_data: SaleCreate, db: Session = Depends(get_db)):
    if not sale_data.items:
        raise HTTPException(status_code=400, detail="La venta debe tener al menos un artículo")

    # Calcular totales
    subtotal = 0.0
    items_to_create = []

    for item in sale_data.items:
        item_total = (item.unit_price * item.quantity) - item.discount
        subtotal += item_total
        items_to_create.append({
            **item.model_dump(),
            "total": item_total
        })

    total = subtotal - sale_data.discount + sale_data.tax

    sale = Sale(
        sale_number=generate_sale_number(db),
        member_id=sale_data.member_id,
        cashier=sale_data.cashier,
        subtotal=subtotal,
        discount=sale_data.discount,
        tax=sale_data.tax,
        total=total,
        payment_method=sale_data.payment_method,
        payment_reference=sale_data.payment_reference,
        notes=sale_data.notes,
    )
    db.add(sale)
    db.flush()  # para obtener el ID

    for item_data in items_to_create:
        item = SaleItem(sale_id=sale.id, **item_data)
        db.add(item)

        # Descontar stock si es producto físico
        if item_data.get("product_id"):
            product = db.query(Product).filter(Product.id == item_data["product_id"]).first()
            if product and not product.is_service:
                product.stock = max(0, product.stock - item_data["quantity"])

    db.commit()
    db.refresh(sale)

    member = db.query(Member).filter(Member.id == sale.member_id).first() if sale.member_id else None
    result = SaleOut(
        id=sale.id,
        sale_number=sale.sale_number,
        member_id=sale.member_id,
        cashier=sale.cashier,
        subtotal=sale.subtotal,
        discount=sale.discount,
        tax=sale.tax,
        total=sale.total,
        payment_method=sale.payment_method,
        payment_reference=sale.payment_reference,
        status=sale.status,
        notes=sale.notes,
        created_at=sale.created_at,
        items=[SaleOut.model_fields["items"].default] if False else [],
        member_name=member.full_name if member else None,
    )
    result.items = [
        {
            "id": i.id,
            "product_id": i.product_id,
            "product_name": i.product_name,
            "quantity": i.quantity,
            "unit_price": i.unit_price,
            "discount": i.discount,
            "total": i.total,
        }
        for i in sale.items
    ]
    return result


@router.get("/sales", response_model=List[SaleOut])
def list_sales(
    member_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    q = db.query(Sale).order_by(desc(Sale.created_at))
    if member_id:
        q = q.filter(Sale.member_id == member_id)
    if start_date:
        q = q.filter(Sale.created_at >= start_date)
    if end_date:
        q = q.filter(Sale.created_at <= end_date)
    sales = q.offset(skip).limit(limit).all()

    result = []
    for s in sales:
        member = db.query(Member).filter(Member.id == s.member_id).first() if s.member_id else None
        so = SaleOut(
            id=s.id, sale_number=s.sale_number, member_id=s.member_id,
            cashier=s.cashier, subtotal=s.subtotal, discount=s.discount,
            tax=s.tax, total=s.total, payment_method=s.payment_method,
            payment_reference=s.payment_reference, status=s.status,
            notes=s.notes, created_at=s.created_at, items=[],
            member_name=member.full_name if member else None,
        )
        so.items = [
            {
                "id": i.id, "product_id": i.product_id, "product_name": i.product_name,
                "quantity": i.quantity, "unit_price": i.unit_price,
                "discount": i.discount, "total": i.total,
            }
            for i in s.items
        ]
        result.append(so)
    return result


@router.get("/sales/{sale_id}", response_model=SaleOut)
def get_sale(sale_id: int, db: Session = Depends(get_db)):
    s = db.query(Sale).filter(Sale.id == sale_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    member = db.query(Member).filter(Member.id == s.member_id).first() if s.member_id else None
    so = SaleOut(
        id=s.id, sale_number=s.sale_number, member_id=s.member_id,
        cashier=s.cashier, subtotal=s.subtotal, discount=s.discount,
        tax=s.tax, total=s.total, payment_method=s.payment_method,
        payment_reference=s.payment_reference, status=s.status,
        notes=s.notes, created_at=s.created_at, items=[],
        member_name=member.full_name if member else None,
    )
    so.items = [
        {
            "id": i.id, "product_id": i.product_id, "product_name": i.product_name,
            "quantity": i.quantity, "unit_price": i.unit_price,
            "discount": i.discount, "total": i.total,
        }
        for i in s.items
    ]
    return so


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    week_ahead = now + timedelta(days=7)

    total_members = db.query(func.count(Member.id)).scalar()
    active_members = db.query(func.count(Member.id)).filter(Member.status == "active").scalar()
    expired_members = db.query(func.count(Member.id)).filter(Member.status == "expired").scalar()

    entries_today = db.query(func.count(AccessLog.id)).filter(
        AccessLog.timestamp >= today_start,
        AccessLog.result == "granted"
    ).scalar()

    entries_this_month = db.query(func.count(AccessLog.id)).filter(
        AccessLog.timestamp >= month_start,
        AccessLog.result == "granted"
    ).scalar()

    sales_today = db.query(func.sum(Sale.total)).filter(
        Sale.created_at >= today_start,
        Sale.status == "completed"
    ).scalar() or 0.0

    sales_this_month = db.query(func.sum(Sale.total)).filter(
        Sale.created_at >= month_start,
        Sale.status == "completed"
    ).scalar() or 0.0

    low_stock = db.query(func.count(Product.id)).filter(
        Product.stock <= Product.min_stock,
        Product.is_service == False,
        Product.is_active == True
    ).scalar()

    expiring_soon = db.query(func.count(MemberMembership.id)).filter(
        MemberMembership.end_date >= now,
        MemberMembership.end_date <= week_ahead,
        MemberMembership.is_active == True
    ).scalar()

    return DashboardStats(
        total_members=total_members,
        active_members=active_members,
        expired_members=expired_members,
        entries_today=entries_today,
        entries_this_month=entries_this_month,
        sales_today=sales_today,
        sales_this_month=sales_this_month,
        low_stock_products=low_stock,
        memberships_expiring_soon=expiring_soon,
    )
