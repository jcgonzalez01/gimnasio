"""
Analizador de eventos Hikvision.
Transforma los payloads crudos (JSON/XML) en estructuras de datos limpias.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from .events import get_event_description

def parse_event_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parsea el payload de un evento Hikvision (EventNotificationAlert).
    Devuelve un diccionario estandarizado con la información clave.
    """
    alert = payload.get("EventNotificationAlert", {})
    acs_event = alert.get("AccessControllerEvent", payload) # Fallback al root si no hay EventNotificationAlert
    
    major = acs_event.get("major", 0)
    minor = acs_event.get("minor", 0)
    
    # Resolver descripción humana
    description = get_event_description(major, minor)
    
    # Determinar resultado (simplificado)
    # Según la lógica observada en access.py y hikvision-server.js
    result = "denied"
    
    # 0x5/0x1 (Otros/Valid Card Auth) es el éxito más común
    if major == 5 and minor in [1, 4, 38, 75, 104]:
        result = "granted"
    elif major == 3 and minor == 1: # Operación/Door Remotely Open? No, 0x3 es Operation. 
        # En access.py dice major=3, minor=1 -> granted. 
        # Mirando events.py: 0x3/0x400 es Remote Open.
        # Pero access.py dice major=3, minor=1 es granted. 
        # Es posible que dependa del modelo.
        result = "granted"
    elif acs_event.get("status") in ["success", "OK"]:
        result = "granted"

    # Mapeo de tipos de acceso
    verify_mode = acs_event.get("currentVerifyMode", "").lower()
    access_type = "unknown"
    if "face" in verify_mode:
        access_type = "face"
    elif "card" in verify_mode:
        access_type = "card"
    elif "fingerprint" in verify_mode:
        access_type = "fingerprint"
    elif "password" in verify_mode or "pin" in verify_mode:
        access_type = "pin"
        
    # Extraer tiempo
    event_time_str = acs_event.get("time")
    ts = datetime.now()
    if event_time_str:
        try:
            # Intentar parsear ISO format
            ts = datetime.fromisoformat(event_time_str.replace("Z", "+00:00")).replace(tzinfo=None)
        except:
            pass

    return {
        "employee_no": acs_event.get("employeeNoString") or acs_event.get("employeeNo"),
        "major": major,
        "minor": minor,
        "description": description,
        "result": result,
        "access_type": access_type,
        "timestamp": ts,
        "temperature": acs_event.get("temperature"),
        "door_no": acs_event.get("doorNo", 1),
        "status": acs_event.get("status")
    }
