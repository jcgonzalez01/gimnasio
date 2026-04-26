# Scripts de desarrollo / debugging

Utilidades sueltas usadas durante el desarrollo y debugging del proyecto.
**No son parte del runtime de producción.**

## Categorías

- `check_*.py` — inspección de estado (BD, eventos, dispositivos)
- `borrar_*.py`, `delete_events.py`, `limpieza_total.py` — limpieza de datos en dispositivos Hikvision
- `seed_*.py` — sembrado de datos de prueba
- `test_*.py` — pruebas manuales contra dispositivos reales
- `monitor_events.py`, `pull_events_manual.py` — captura manual de eventos
- `reconfigure_*.py`, `fix_*.py` — reconfiguración / correcciones puntuales
- `capturar_ultimo*.py` — captura de la última foto

Para ejecutarlos:

```bash
cd backend && source venv/bin/activate
python ../scripts/dev/check_db.py
```
