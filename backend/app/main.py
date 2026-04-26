from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging
import sys

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .core.config import settings
from .core.database import Base, engine
from .core.security import get_current_user
from .models import member, access, pos, user, audit  # importar para crear tablas
from .api import (
    members, access as access_router, pos as pos_router,
    reports as reports_router, auth as auth_router,
    payments as payments_router,
)

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Validación de producción
config_errors = settings.validate_for_production()
if config_errors:
    for err in config_errors:
        logger.error(f"CONFIG: {err}")
    if settings.is_production:
        logger.critical("Configuración insegura en producción. Aborto el arranque.")
        sys.exit(1)

# Crear tablas (Alembic se encarga en producción; esto es por compatibilidad)
Base.metadata.create_all(bind=engine)

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(
    title=settings.APP_NAME,
    description="Sistema de Gestión de Gimnasio con Control de Acceso Hikvision y Punto de Venta",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Archivos estáticos (fotos de miembros)
os.makedirs("./uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="./uploads"), name="uploads")

_auth_dep = [Depends(get_current_user)]

# Auth router: público (login) y privado (me, users) — el dep está por endpoint
app.include_router(auth_router.router, prefix="/api")

# Webhooks de Hikvision — públicos (no se les puede pedir JWT)
app.include_router(access_router.public_router, prefix="/api")

# Endpoints protegidos
app.include_router(members.router,         prefix="/api", dependencies=_auth_dep)
app.include_router(access_router.router,   prefix="/api", dependencies=_auth_dep)
app.include_router(pos_router.router,      prefix="/api", dependencies=_auth_dep)
app.include_router(reports_router.router,  prefix="/api", dependencies=_auth_dep)
app.include_router(payments_router.router, prefix="/api", dependencies=_auth_dep)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}


@app.on_event("startup")
async def startup_event():
    """Seed inicial: planes/productos/admin si la BD está vacía."""
    from .core.database import SessionLocal
    from .core.security import hash_password
    from .models.member import MembershipPlan
    from .models.pos import ProductCategory, Product
    from .models.user import User, UserRole

    db = SessionLocal()
    try:
        # ── Usuario admin de bootstrap ────────────────────────────────────────
        if db.query(User).count() == 0:
            admin = User(
                username=settings.BOOTSTRAP_ADMIN_USERNAME,
                email=settings.BOOTSTRAP_ADMIN_EMAIL or None,
                full_name="Administrador",
                role=UserRole.ADMIN,
                is_active=True,
                hashed_password=hash_password(settings.BOOTSTRAP_ADMIN_PASSWORD),
            )
            db.add(admin)
            db.commit()
            logger.warning(
                f"Usuario admin creado: '{settings.BOOTSTRAP_ADMIN_USERNAME}' — "
                "cambia la contraseña tras el primer login."
            )

        # ── Planes por defecto ────────────────────────────────────────────────
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

        # ── Categorías y productos por defecto ────────────────────────────────
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
        logger.error(f"Error en seed inicial: {e}")
    finally:
        db.close()

    # ── Scheduler de notificaciones de vencimiento ────────────────────────────
    if settings.EMAIL_NOTIFICATIONS_ENABLED:
        try:
            from .services.notifications import start_scheduler
            start_scheduler()
            logger.info("Scheduler de notificaciones iniciado.")
        except Exception as exc:
            logger.error(f"No se pudo iniciar scheduler: {exc}")


@app.on_event("shutdown")
async def shutdown_event():
    try:
        from .services.notifications import stop_scheduler
        stop_scheduler()
    except Exception:
        pass
