# Cambios v1.1 — Hardening + features de producción

Implementación completa del listado P0/P1/P2 (excepto captura de foto por webcam).

## 🔐 P0 — Bloqueantes para producción

### Autenticación JWT
- Modelo `User` con roles (admin / manager / cashier / reception) — [models/user.py](backend/app/models/user.py)
- Endpoints `/api/auth/login`, `/auth/me`, `/auth/users` (CRUD admin), `/auth/change-password` — [api/auth.py](backend/app/api/auth.py)
- Hashing bcrypt + JWT con `SECRET_KEY` validado en producción — [core/security.py](backend/app/core/security.py)
- Bootstrap admin automático en primer arranque (`BOOTSTRAP_ADMIN_USERNAME`/`_PASSWORD`)
- **Frontend**: AuthContext, página de login, axios interceptor, ProtectedRoute con roles
- Webhooks Hikvision quedan en `public_router` (no requieren auth)
- WebSocket exige token JWT en producción

### Migraciones Alembic
- `backend/alembic/` configurado, `env.py` enlazado con la app — [alembic/env.py](backend/alembic/env.py)
- Migración baseline `0001_initial_schema.py` con todas las tablas
- `entrypoint.sh` aplica migraciones automáticamente y stampa BDs existentes — [backend/entrypoint.sh](backend/entrypoint.sh)

### Limpieza de repo
- `.gitignore` ampliado (logs, zips, capturas, build artefactos)
- `webhook_raw_debug.log`, `files*.zip`, `capturas_manuales/` desversionados
- Scripts de dev movidos a `scripts/dev/` (47 archivos)

## 🟠 P1 — Funcionalidades de negocio

### Notificaciones de vencimiento
- `services/notifications.py` con APScheduler — recordatorios a N días antes (configurable)
- Marca automática de miembros expirados a las 00:30 UTC
- Templates HTML profesionales por email
- Endpoint manual: `POST /api/auth/notifications/run-expiry-check` (admin)

### Recibos PDF
- `services/receipts.py` — formato POS 80mm con reportlab
- Endpoint: `GET /api/pos/sales/{id}/receipt`
- Botón "Imprimir / descargar PDF" en `Sales.tsx`

### Roles aplicados a endpoints
- `delete_member`, `delete_plan`, `update_plan`, `delete_product` → manager+
- `delete_device`, gestión de usuarios → admin only
- Frontend filtra menú según rol; rutas protegidas con `<ProtectedRoute roles={['admin']}>`

## 🟡 P2 — Mejoras avanzadas

### Auditoría
- Modelo `AuditLog` (user, action, entity_type, entity_id, summary, IP, timestamp)
- Servicio `services/audit.py` con `log_action(...)` no-throwing
- Eventos registrados: login, login_failed, delete (member/plan/product/device/user), open_door
- Endpoint admin: `GET /api/auth/audit?action=&user_id=`
- Página `Auditoría` en frontend con filtros

### Pasarela de pago
- Interfaz `PaymentProvider` (base.py) — soporta múltiples providers
- Implementación `ManualProvider` (default) y `MercadoPagoProvider` (Checkout Pro)
- Endpoints: `/api/payments/create`, `/payments/{id}/status`, `/payments/{id}/refund`
- Configuración: `PAYMENT_PROVIDER=manual|mercadopago` + `MERCADOPAGO_ACCESS_TOKEN`

### Tests
- **Backend**: pytest + fixtures en memoria (`tests/conftest.py`)
  - `test_auth.py`: login, permisos, usuarios inactivos
  - `test_members.py`: CRUD, duplicados, autorización
  - `test_pos.py`: ventas, recibo PDF, restricciones de cajero
- **Frontend**: vitest + jsdom + testing-library
  - `auth.test.tsx`: AuthContext con token storage

### Mejoras técnicas
- CORS ahora desde `CORS_ORIGINS` env var (rechaza `*` en producción)
- Rate limiter (slowapi) configurado con `100/minute` global
- Validación al arranque: aborta si producción tiene SECRET_KEY débil o CORS=`*`
- Logging estructurado (`logger` en lugar de `print`)
- Archivo de log webhook eliminado del código

## 🚀 Arranque

### Primer setup
```bash
cd backend
pip install -r requirements.txt
alembic upgrade head     # aplica migraciones
uvicorn app.main:app --reload
```

### Producción (Coolify)
Las migraciones se aplican automáticamente al iniciar el contenedor. Configura
todas las variables del `.env.production` antes del primer deploy.

## 🧪 Tests

```bash
# Backend
cd backend
pytest -v

# Frontend
cd frontend
npm install   # tras pull, hay nuevas devDependencies
npm test
```

## ⚠️ Cambios incompatibles

- **TODOS** los endpoints (excepto `/api/health`, `/api/auth/login`, webhooks Hikvision) ahora requieren JWT.
- Frontend redirige a `/login` ante 401.
- En producción (`ENV=production`), el sistema **no arrancará** si `SECRET_KEY` es la default o `CORS_ORIGINS="*"`.
- Primer login: usuario `admin`, password `admin123` — **cámbialo inmediatamente**.
