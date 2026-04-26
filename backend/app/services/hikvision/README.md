# Integración Hikvision ISAPI (Estructura Restructurada)

Esta carpeta contiene la lógica de integración con terminales de control de acceso Hikvision (MinMoe, etc.) utilizando el protocolo ISAPI.

## Estructura del Paquete

- `constants.py`: Contiene los namespaces y endpoints de ISAPI (Sistema, Acceso, Eventos, Rostros). Portado de `isapiEndpoints.js`.
- `events.py`: Mapeo exhaustivo de tipos de eventos (Major/Minor) y tipos de enlace. Portado de `accessControlEvents.js` y `accessControlLinkages.js`.
- `client.py`: `HikvisionClient` base que maneja la autenticación Digest, construcción de URLs y peticiones HTTP.
- `parser.py`: Lógica para procesar los payloads (JSON/XML) recibidos por webhooks o consultas de eventos.
- `__init__.py`: Expone la clase `HikvisionISAPI` (para compatibilidad) y las funciones principales.

## Uso en el Backend

```python
from app.services.hikvision import HikvisionISAPI, parse_event_payload

hik = HikvisionISAPI(ip, port, user, password)
hik.open_door(1)

# En el webhook
parsed_event = parse_event_payload(request_json)
print(parsed_event['description']) # "Valid Card Authentication Completed"
```

## Referencias

Para más detalles sobre los workflows soportados, consultar `isapi_cheatsheet.md` en la raíz del proyecto.
