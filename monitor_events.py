import requests, time, json, sqlite3, os
from requests.auth import HTTPDigestAuth
from datetime import datetime, timedelta

# Configuración base
DB_PATH = "backend/gimnasio.db"
BACKEND_URL = "http://127.0.0.1:8000/api/access/hikvision-webhook"

def get_active_device():
    """Consulta la base de datos para obtener el dispositivo activo."""
    try:
        if not os.path.exists(DB_PATH):
            return None
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT ip_address, port, username, password, name FROM hikvision_devices WHERE is_active = 1 LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "ip": row[0], "port": row[1], "user": row[2], "pass": row[3], "name": row[4]
            }
    except Exception as e:
        print(f"\n[!] Error DB: {e}")
    return None

def poll_events():
    current_device = None
    last_processed_time = None
    
    print(f"--- Monitor de Accesos (Sincronizado con IDs) ---")
    
    while True:
        new_device = get_active_device()
        
        if not new_device:
            time.sleep(5)
            continue
            
        if current_device != new_device:
            print(f"\n[🛰️] Escuchando dispositivo: {new_device['name']} ({new_device['ip']})")
            current_device = new_device
            last_processed_time = None

        try:
            # Usar UTC para la búsqueda, es más robusto en Hikvision ISAPI
            now_utc = datetime.utcnow()
            start_time = (now_utc - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
            end_time = (now_utc + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
            
            payload = {
                "AcsEventCond": {
                    "searchID": "m" + str(int(time.time() * 1000))[-8:], 
                    "searchResultPosition": 0, "maxResults": 15,
                    "major": 0, "minor": 0,
                    "startTime": start_time, "endTime": end_time
                }
            }
            
            r = requests.post(
                f"http://{current_device['ip']}:{current_device['port']}/ISAPI/AccessControl/AcsEvent?format=json",
                json=payload,
                auth=HTTPDigestAuth(current_device['user'], current_device['pass']),
                timeout=5
            )
            
            if r.status_code == 200:
                events = r.json().get("AcsEvent", {}).get("InfoList", [])
                
                if not events:
                    print(".", end="", flush=True)
                
                for ev in reversed(events):
                    ev_time = ev.get("time")
                    emp_no = ev.get('employeeNoString', 'N/A')
                    
                    if last_processed_time is None or ev_time > last_processed_time:
                        print(f"\n[🔔 ACCESO] {ev_time} | ID Usuario: {emp_no}")
                        
                        # Enviar evento al Backend (el backend se encargará de buscar la foto por el ID)
                        webhook_data = {
                            "EventNotificationAlert": {"AccessControllerEvent": ev}
                        }
                        requests.post(BACKEND_URL, json=webhook_data, timeout=3)
                        
                        last_processed_time = ev_time
            
        except Exception as e:
            print(f"\n[!] Error: {e}")
            
        time.sleep(3)

if __name__ == "__main__":
    poll_events()
