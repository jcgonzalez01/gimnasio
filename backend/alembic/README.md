# Migraciones (Alembic)

## Primera vez en una BD existente con datos

Si ya tienes datos en `gimnasio.db`, marca la BD como ya migrada (no re-crea las tablas):

```bash
cd backend
alembic stamp 0001
```

## BD nueva (vacía)

```bash
cd backend
alembic upgrade head
```

## Crear una nueva migración tras cambiar modelos

```bash
cd backend
alembic revision --autogenerate -m "descripción del cambio"
alembic upgrade head
```

> ⚠️ Revisa siempre el archivo generado en `alembic/versions/` antes de aplicarlo —
> autogenerate no detecta todos los cambios (renames, server defaults, etc.).

## En producción (Coolify / Docker)

Las migraciones se aplican al arrancar el contenedor del backend.
Ver `backend/Dockerfile` y el `command` del compose.
