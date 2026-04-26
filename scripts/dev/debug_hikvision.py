import os
import requests
from requests.auth import HTTPDigestAuth
from sqlalchemy import create_engine, text
import json
from datetime import datetime, timedelta

# Configuración de DB
base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "backend", "gimnasio.db")
DB_URL = f"sqlite:///{db_path}"

def debug_hikvision_events():
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        device = conn.execute(text("SELECT ip_address, port, username, password, name FROM hikvision_devices WHERE is_active = 1")).fetchone()
        if not device:
            print("No hay dispositivos activos.")
            return

        print(f"DEBUG: Consultando dispositivo {device.name} ({device.ip_address})")
        base_url = f"http://{device.ip_address}:{device.port}"
        auth = HTTPDigestAuth(device.username, device.password)
        
        # 1. Consultar capacidades de eventos
        try:
            r = requests.get(f"{base_url}/ISAPI/AccessControl/AcsEvent/capabilities", auth=auth, timeout=10)
            print("\n--- CAPACIDADES ---")
            print(r.text[:500])
        except Exception as e:
            print(f"Error capacidades: {e}")

        # 2. Consultar conteo total de eventos (si el dispositivo lo soporta)
        try:
            # Algunos modelos usan este endpoint
            r = requests.get(f"{base_url}/ISAPI/AccessControl/AcsEvent/totalNum", auth=auth, timeout=10)
            print("\n--- TOTAL EVENTOS EN DISPOSITIVO ---")
            print(r.text)
        except Exception:
            pass

        # 3. Consultar ÚLTIMOS 5 eventos sin filtro de fecha
        print("\n--- ÚLTIMOS 5 EVENTOS (SIN FILTRO DE FECHA) ---")
        payload = {
            "AcsEventCond": {
                "searchID": "debug_last",
                "searchResultPosition": 0,
                "maxResults": 5,
                "major": 0,
                "minor": 0
            }
        }
        try:
            r = requests.post(f"{base_url}/ISAPI/AccessControl/AcsEvent?format=json", json=payload, auth=auth, timeout=10)
            if r.status_code == 200:
                events = r.json().get("AcsEvent", {}).get("InfoList", [])
                for ev in events:
                    print(f"ID: {ev.get('searchID')}, Time: {ev.get('time')}, Emp: {ev.get('employeeNoString')}, Major: {ev.get('major')}, Minor: {ev.get('minor')}")
            else:
                print(f"Error {r.status_code}: {r.text}")
        except Exception as e:
            print(f"Error consulta: {e}")

if __name__ == "__main__":
    debug_hikvision_events()
