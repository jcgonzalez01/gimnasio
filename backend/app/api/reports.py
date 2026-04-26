from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from ..core.database import get_db
from ..models.access import AccessLog
from ..models.pos import Sale, SaleItem, Product, ProductCategory
from ..models.member import Member, MemberMembership

router = APIRouter(prefix="/reports", tags=["Reportes"])


class DailyStats(BaseModel):
    date: str
    access_count: int
    access_granted: int
    access_denied: int
    sales_count: int
    sales_total: float
    new_members: int

    class Config:
        from_attributes = True


class TopMember(BaseModel):
    member_id: int
    member_name: str
    member_number: str
    visits: int

    class Config:
        from_attributes = True


class TopProduct(BaseModel):
    product_id: int
    product_name: str
    quantity_sold: int
    total_sales: float

    class Config:
        from_attributes = True


class AccessReport(BaseModel):
    id: int
    member_name: Optional[str]
    member_number: Optional[str]
    direction: str
    access_type: str
    result: str
    timestamp: str

    class Config:
        from_attributes = True


class SalesReport(BaseModel):
    id: int
    sale_number: str
    member_name: Optional[str]
    total: float
    items_count: int
    payment_method: str
    created_at: str

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    today_access: int
    today_granted: int
    today_denied: int
    today_sales: float
    total_members: int
    active_members: int
    low_stock_products: int

    class Config:
        from_attributes = True


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())

    access_today = db.query(AccessLog).filter(
        AccessLog.timestamp >= today_start,
        AccessLog.timestamp <= today_end
    ).all()

    sales_today = db.query(Sale).filter(
        Sale.created_at >= today_start,
        Sale.created_at <= today_end,
        Sale.status == "completed"
    ).all()

    total_members = db.query(Member).count()
    active_members = db.query(Member).filter(Member.status == "active").count()
    low_stock = db.query(Product).filter(Product.stock <= Product.min_stock, Product.is_active == True).count()

    return DashboardStats(
        today_access=len(access_today),
        today_granted=sum(1 for a in access_today if a.result == "granted"),
        today_denied=sum(1 for a in access_today if a.result == "denied"),
        today_sales=sum(s.total for s in sales_today),
        total_members=total_members,
        active_members=active_members,
        low_stock_products=low_stock
    )


@router.get("/daily", response_model=List[DailyStats])
def get_daily_stats(
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    stats = []
    current = start_date

    while current <= end_date:
        day_start = datetime.combine(current, datetime.min.time())
        day_end = datetime.combine(current, datetime.max.time())

        access_day = db.query(AccessLog).filter(
            AccessLog.timestamp >= day_start,
            AccessLog.timestamp <= day_end
        ).all()

        sales_day = db.query(Sale).filter(
            Sale.created_at >= day_start,
            Sale.created_at <= day_end,
            Sale.status == "completed"
        ).all()

        new_members_day = db.query(Member).filter(
            Member.created_at >= day_start,
            Member.created_at <= day_end
        ).count()

        stats.append(DailyStats(
            date=current.isoformat(),
            access_count=len(access_day),
            access_granted=sum(1 for a in access_day if a.result == "granted"),
            access_denied=sum(1 for a in access_day if a.result == "denied"),
            sales_count=len(sales_day),
            sales_total=sum(s.total for s in sales_day),
            new_members=new_members_day
        ))

        current += timedelta(days=1)

    return stats


@router.get("/access", response_model=List[AccessReport])
def get_access_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    result: Optional[str] = None,
    member_id: Optional[int] = None,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(AccessLog)

    if start_date:
        query = query.filter(AccessLog.timestamp >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(AccessLog.timestamp <= datetime.fromisoformat(end_date))
    if result:
        query = query.filter(AccessLog.result == result)
    if member_id:
        query = query.filter(AccessLog.member_id == member_id)

    logs = query.order_by(AccessLog.timestamp.desc()).limit(limit).all()

    return [
        AccessReport(
            id=log.id,
            member_name=f"{log.member.first_name} {log.member.last_name}" if log.member else None,
            member_number=log.member.member_number if log.member else None,
            direction=log.direction,
            access_type=log.access_type,
            result=log.result,
            timestamp=log.timestamp.isoformat()
        ) for log in logs
    ]


@router.get("/sales", response_model=List[SalesReport])
def get_sales_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    payment_method: Optional[str] = None,
    member_id: Optional[int] = None,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(Sale)

    if start_date:
        query = query.filter(Sale.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Sale.created_at <= datetime.fromisoformat(end_date))
    if payment_method:
        query = query.filter(Sale.payment_method == payment_method)
    if member_id:
        query = query.filter(Sale.member_id == member_id)

    query = query.filter(Sale.status == "completed")
    sales = query.order_by(Sale.created_at.desc()).limit(limit).all()

    return [
        SalesReport(
            id=sale.id,
            sale_number=sale.sale_number or f"SALE-{sale.id}",
            member_name=f"{sale.member.first_name} {sale.member.last_name}" if sale.member else None,
            total=sale.total,
            items_count=len(sale.items),
            payment_method=sale.payment_method,
            created_at=sale.created_at.isoformat()
        ) for sale in sales
    ]


@router.get("/top-members", response_model=List[TopMember])
def get_top_members(
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    start_date = datetime.now() - timedelta(days=days)

    results = db.query(
        AccessLog.member_id,
        func.count(AccessLog.id).label("visits")
    ).filter(
        AccessLog.timestamp >= start_date,
        AccessLog.member_id.isnot(None)
    ).group_by(
        AccessLog.member_id
    ).order_by(
        func.count(AccessLog.id).desc()
    ).limit(limit).all()

    top = []
    for r in results:
        member = db.query(Member).get(r.member_id)
        if member:
            top.append(TopMember(
                member_id=member.id,
                member_name=f"{member.first_name} {member.last_name}",
                member_number=member.member_number,
                visits=r.visits
            ))

    return top


@router.get("/top-products", response_model=List[TopProduct])
def get_top_products(
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    start_date = datetime.now() - timedelta(days=days)

    results = db.query(
        SaleItem.product_id,
        SaleItem.product_name,
        func.sum(SaleItem.quantity).label("quantity_sold"),
        func.sum(SaleItem.total).label("total_sales")
    ).join(Sale).filter(
        Sale.created_at >= start_date,
        Sale.status == "completed"
    ).group_by(
        SaleItem.product_id
    ).order_by(
        func.sum(SaleItem.quantity).desc()
    ).limit(limit).all()

    return [
        TopProduct(
            product_id=r.product_id or 0,
            product_name=r.product_name,
            quantity_sold=int(r.quantity_sold or 0),
            total_sales=float(r.total_sales or 0)
        ) for r in results
    ]


@router.get("/summary")
def get_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Sale).filter(Sale.status == "completed")

    if start_date:
        query = query.filter(Sale.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Sale.created_at <= datetime.fromisoformat(end_date))

    sales = query.all()

    access_query = db.query(AccessLog)
    if start_date:
        access_query = access_query.filter(AccessLog.timestamp >= datetime.fromisoformat(start_date))
    if end_date:
        access_query = access_query.filter(AccessLog.timestamp <= datetime.fromisoformat(end_date))

    access_logs = access_query.all()

    return {
        "period": {
            "start": start_date or "Todos",
            "end": end_date or "Todos"
        },
        "access": {
            "total": len(access_logs),
            "granted": sum(1 for a in access_logs if a.result == "granted"),
            "denied": sum(1 for a in access_logs if a.result == "denied")
        },
        "sales": {
            "total": len(sales),
            "amount": sum(s.total for s in sales),
            "average": sum(s.total for s in sales) / len(sales) if sales else 0
        }
    }