# 🚀 Guía de Despliegue en VPS con Coolify

## Requisitos previos
- VPS con Ubuntu 22.04 o Debian 12 (mínimo 2 GB RAM, 20 GB disco)
- Coolify instalado en el VPS
- Dominio apuntando a la IP del VPS
- Repositorio Git (GitHub, GitLab, Gitea, etc.)

---

## Paso 1 — Subir el código a un repositorio Git

```bash
# En tu máquina local
cd "C:\Users\jcgon\OneDrive\Desktop\gimnasio"
git init
git add .
git commit -m "GymSystem Pro - Initial commit"

# Crear repo en GitHub/GitLab y conectar
git remote add origin https://github.com/TU_USUARIO/gym-system.git
git push -u origin main
```

---

## Paso 2 — Instalar Coolify en el VPS (si no está instalado)

```bash
# Conectar al VPS
ssh root@IP_DE_TU_VPS

# Instalar Coolify (1 comando)
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

Luego accede a: `http://IP_VPS:8000` para configurar Coolify.

---

## Paso 3 — Crear el proyecto en Coolify

### 3.1 Conectar el repositorio Git
1. En Coolify → **Sources** → Agregar tu GitHub/GitLab
2. Autorizar el acceso al repositorio del gimnasio

### 3.2 Crear nueva aplicación Docker Compose
1. **Projects** → New Project → "GymSystem Pro"
2. **New Resource** → **Docker Compose**
3. Seleccionar el repositorio y rama `main`
4. Coolify detectará automáticamente el `docker-compose.yml`

---

## Paso 4 — Configurar variables de entorno en Coolify

En la sección **Environment Variables** de la aplicación:

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `DOMAIN` | `gym.tudominio.com` | Tu dominio |
| `SECRET_KEY` | *(generar abajo)* | Clave JWT secreta |
| `FRONTEND_PORT` | `3000` | Puerto interno |

**Generar SECRET_KEY segura:**
```bash
openssl rand -hex 32
```

---

## Paso 5 — Configurar dominio y SSL

1. En Coolify → tu app → **Domains**
2. Agregar: `gym.tudominio.com`
3. Activar **Let's Encrypt SSL** ✓
4. Coolify configura Traefik automáticamente

> ⚠️ Asegúrate de que el DNS del dominio apunte a la IP del VPS antes de activar SSL.

---

## Paso 6 — Deploy

1. Click en **Deploy** en Coolify
2. Coolify construirá las imágenes Docker y levantará los contenedores
3. El proceso tarda ~3-5 minutos la primera vez

### Verificar que funciona:
```
https://gym.tudominio.com          → Frontend
https://gym.tudominio.com/api/docs → Documentación API
https://gym.tudominio.com/api/health → {"status": "ok"}
```

---

## Estructura de contenedores desplegados

```
VPS
└── Coolify (Traefik)
    ├── gym_frontend (Nginx:80) ← HTTPS externo
    │   ├── /           → React SPA
    │   ├── /api/       → proxy → backend:8000
    │   ├── /api/access/ws → WebSocket → backend:8000
    │   └── /uploads/   → proxy → backend:8000
    └── gym_backend (FastAPI:8000) ← solo red interna
        ├── Volume: gym_db_data    (SQLite)
        └── Volume: gym_uploads_data (fotos)
```

---

## Volúmenes persistentes (datos importantes)

| Volumen | Contenido | Ruta en contenedor |
|---------|-----------|-------------------|
| `gym_db_data` | Base de datos SQLite | `/app/data/gimnasio.db` |
| `gym_uploads_data` | Fotos de miembros | `/app/uploads/` |

> 💾 **Backup recomendado**: Hacer backup periódico de estos volúmenes.

```bash
# Backup de la base de datos
docker run --rm -v gym_db_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/gym_db_backup_$(date +%Y%m%d).tar.gz /data

# Backup de las fotos
docker run --rm -v gym_uploads_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/gym_uploads_backup_$(date +%Y%m%d).tar.gz /data
```

---

## Actualizar la aplicación

Cada push a la rama `main` puede disparar un re-deploy automático:
1. Coolify → App → **Webhooks** → Activar auto-deploy
2. O hacer deploy manual desde el panel

```bash
# Publicar cambios
git add .
git commit -m "feat: nueva funcionalidad"
git push origin main
# → Coolify detecta el push y hace deploy automático
```

---

## Configuración de Hikvision con el servidor en producción

Una vez desplegado, configura cada dispositivo Hikvision:

1. Acceder al dispositivo en `http://IP_DISPOSITIVO`
2. **Configuration → Network → Advanced Settings → Integration Protocol**
3. Activar **HTTP Listening** y configurar:
   - Listening Host IP: `IP_DEL_VPS`
   - Listening Host Port: `443`
   - Listening Host URL: `/api/access/hikvision-webhook`

---

## Solución de problemas

### Ver logs en tiempo real:
```bash
# Backend
docker logs -f gym_backend

# Frontend
docker logs -f gym_frontend
```

### Reiniciar servicios:
```bash
docker restart gym_backend gym_frontend
```

### Acceder a la base de datos:
```bash
docker exec -it gym_backend python -c "
from app.core.database import engine
from app.models import *
print('BD OK')
"
```
