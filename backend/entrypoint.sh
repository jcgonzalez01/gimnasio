#!/bin/sh
set -e

echo "→ Aplicando migraciones Alembic…"

# Si la BD ya existe pero nunca fue migrada, marcarla con la baseline
if [ -f /app/data/gimnasio.db ] && ! alembic current 2>/dev/null | grep -q '0001'; then
    HAS_TABLES=$(python -c "
import sqlite3
c = sqlite3.connect('/app/data/gimnasio.db')
n = c.execute(\"select count(*) from sqlite_master where type='table' and name='members'\").fetchone()[0]
print(n)
")
    if [ "$HAS_TABLES" = "1" ]; then
        echo "  BD existente detectada — marcando como ya migrada (stamp 0001)"
        alembic stamp 0001
    fi
fi

alembic upgrade head

echo "→ Arrancando uvicorn"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
