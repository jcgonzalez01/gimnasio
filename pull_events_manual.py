import os
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Importar lógica del backend si es posible, o recrearla
# Recreamos lo mínimo necesario para no depender de imports complejos
base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "backend", "gimnasio.db")
DB_URL = f"sqlite:///{db_path}"

# Mock de lo que necesitamos de HikvisionISAPI
import requests
from requests.auth import HTTPDigestAuth

class HikvisionISAPI:
    def __init__(self, ip, port, user, password):
        self.base_url = f"http://{ip}:{port}"
        self.auth = HTTPDigestAuth(user, password)
        
    def get_access_events(self, start_time, end_time):
        payload = {
            "AcsEventCond": {
                "searchID": "manual_sync",
                "searchResultPosition": 0,
                "maxResults": 500,
                "major": 0,
                "minor": 0,
                "startTime": start_time.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "endTime": end_time.strftime("%Y-%m-%dT%H:%M:%S+00:00")
            }
        }
        r = requests.post(f"{self.base_url}/ISAPI/AccessControl/AcsEvent?format=json", 
                         json=payload, auth=self.auth, timeout=15)
        if r.status_code == 200:
            return r.json().get("AcsEvent", {}).get("InfoList", [])
        return []

def sync():
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        # 1. Obtener dispositivo activo
        device = conn.execute(text("SELECT id, ip_address, port, username, password, name FROM hikvision_devices WHERE is_active = 1")).fetchone()
        if not device:
            print("No hay dispositivos activos.")
            return

        print(f"Sincronizando desde: {device.name} ({device.ip_address})")
        hik = HikvisionISAPI(device.ip_address, device.port, device.username, device.password)
        
        # 2. Definir rango (Últimas 48 horas para asegurar el día 21)
        end_time = datetime.now() + timedelta(hours=12) # Un margen hacia el futuro por zonas horarias
        start_time = datetime.now() - timedelta(hours=48)
        
        print(f"Buscando eventos entre {start_time} y {end_time}...")
        events = hik.get_access_events(start_time, end_time)
        print(f"Eventos encontrados en dispositivo: {len(events)}")
        
        new_count = 0
        for ev in events:
            emp_no = ev.get("employeeNoString")
            t_str = ev.get("time")
            # Parsear con el offset -04:00 si existe
            # 2026-04-21T10:15:23-04:00
            ts_str = t_str.replace("Z", "+00:00")
            ts = datetime.fromisoformat(ts_str)
            
            # Verificar si existe por timestamp Y employeeNo
            exists = conn.execute(text("""
                SELECT id FROM access_logs 
                WHERE timestamp = :ts 
                AND (member_id = :m_id OR (member_id IS NULL AND :m_id IS NULL))
            """), {"ts": ts, "m_id": int(emp_no) if emp_no and emp_no.isdigit() else None}).fetchone()
            
            if not exists:
                # Buscar miembro
                member_id = None
                if emp_no and emp_no.isdigit():
                    member_id = conn.execute(text("SELECT id FROM members WHERE id = :id"), {"id": int(emp_no)}).scalar()
                
                major = ev.get("major", 0)
                minor = ev.get("minor", 0)
                result = "granted" if (major == 5 and minor == 1) else "denied"
                
                conn.execute(text("""
                    INSERT INTO access_logs (member_id, device_id, direction, access_type, result, timestamp, raw_event)
                    VALUES (:m_id, :d_id, :dir, :type, :res, :ts, :raw)
                """), {
                    "m_id": member_id,
                    "d_id": device.id,
                    "dir": "in" if ev.get("doorNo") == 1 else "out",
                    "type": "face" if major == 5 else "unknown",
                    "res": result,
                    "ts": ts,
                    "raw": json.dumps(ev)
                })
                new_count += 1
        
        conn.commit()
        print(f"Sincronización terminada. {new_count} nuevos eventos guardados.")

if __name__ == "__main__":
    sync()
