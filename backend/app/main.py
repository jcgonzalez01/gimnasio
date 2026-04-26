from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .core.config import settings
from .core.database import Base, engine
from .models import member, access, pos  # importar para crear tablas
from .api import members, access as access_router, pos as pos_router, reports as reports_router

# Crear tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="Sistema de Gestión de Gimnasio con Control de Acceso Hikvision y Punto de Venta",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Archivos estáticos (fotos de miembros)
os.makedirs("./uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="./uploads"), name="uploads")

# Routers
app.include_router(members.router, prefix="/api")
app.include_router(access_router.router, prefix="/api")
app.include_router(pos_router.router, prefix="/api")
app.include_router(reports_router.router, prefix="/api")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}


@app.on_event("startup")
async def startup_event():
    """Seed inicial si la BD está vacía."""
    from .core.database import SessionLocal
    from .models.member import MembershipPlan
    from .models.pos import ProductCategory, Product

    db = SessionLocal()
    try:
        # Planes por defecto
        if db.query(MembershipPlan).count() == 0:
            plans = [
                MembershipPlan(name="Mensual", duration_days=30, price=500.00,
                               description="Acceso ilimitado por 1 mes", color="#2196F3"),
                MembershipPlan(name="Trimestral", duration_days=90, price=1350.00,
                               description="Acceso ilimitado por 3 meses", color="#4CAF50"),
                MembershipPlan(name="Semestral", duration_days=180, price=2500.00,
                               description="Acceso ilimitado por 6 meses", color="#FF9800"),
                MembershipPlan(name="Anual", duration_days=365, price=4500.00,
                               description="Acceso ilimitado por 1 año", color="#9C27B0"),
                MembershipPlan(name="Diario", duration_days=1, price=80.00,
                               description="Acceso por 1 día", color="#607D8B"),
            ]
            db.add_all(plans)

        # Categorías por defecto
        if db.query(ProductCategory).count() == 0:
            cats = [
                ProductCategory(name="Suplementos", icon="💊"),
                ProductCategory(name="Bebidas", icon="🥤"),
                ProductCategory(name="Ropa y Accesorios", icon="👕"),
                ProductCategory(name="Servicios", icon="⚡"),
                ProductCategory(name="Equipamiento", icon="🏋️"),
            ]
            db.add_all(cats)
            db.flush()

            # Productos de ejemplo
            productos = [
                Product(name="Proteína Whey 1kg", price=650.00, cost=400.00,
                        stock=20, min_stock=3, category_id=1, sku="PROT-001"),
                Product(name="Creatina 300g", price=380.00, cost=220.00,
                        stock=15, min_stock=3, category_id=1, sku="CREA-001"),
                Product(name="Agua 600ml", price=20.00, cost=8.00,
                        stock=100, min_stock=20, category_id=2, sku="AGUA-001"),
                Product(name="Bebida Energética", price=45.00, cost=25.00,
                        stock=50, min_stock=10, category_id=2, sku="BEBE-001"),
                Product(name="Clase de Spinning", price=120.00, is_service=True,
                        stock=0, category_id=4, sku="SPIN-001"),
                Product(name="Clase Personal (1hr)", price=300.00, is_service=True,
                        stock=0, category_id=4, sku="PERS-001"),
                Product(name="Guantes de Box", price=280.00, cost=150.00,
                        stock=10, min_stock=2, category_id=3, sku="GUAN-001"),
            ]
            db.add_all(productos)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error en seed inicial: {e}")
    finally:
        db.close()
