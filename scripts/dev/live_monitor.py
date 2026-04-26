import requests, time, json, sqlite3, os
from requests.auth import HTTPDigestAuth

DB_PATH = "backend/gimnasio.db"
BACKEND_URL = "http://127.0.0.1:8001/api/access/hikvision-webhook"

def get_active_device():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT ip_address, port, username, password FROM hikvision_devices WHERE is_active = 1 LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return {"ip": row[0], "port": row[1], "user": row[2], "pass": row[3]} if row else None
    except: return None

def poll():
    print("\n--- MONITOR DE TIEMPO REAL (ÚLTIMOS EVENTOS) ---")
    
    while True:
        dev = get_active_device()
        if not dev: time.sleep(5); continue
        
        try:
            # Primero preguntamos cuántos eventos hay en total
            total_payload = {"AcsEventCond": {"searchID": "count", "searchResultPosition": 0, "maxResults": 1, "major": 0, "minor": 0}}
            r_count = requests.post(f"http://{dev['ip']}:{dev['port']}/ISAPI/AccessControl/AcsEvent?format=json",
                                   json=total_payload, auth=HTTPDigestAuth(dev['user'], dev['pass']), timeout=5)
            
            if r_count.status_code == 200:
                total = r_count.json().get("AcsEvent", {}).get("totalMatches", 0)
                # Pedimos los últimos 5 empezando desde el final
                start_pos = max(0, total - 5)
                
                payload = {
                    "AcsEventCond": {
                        "searchID": "live" + str(int(time.time()))[-4:],
                        "searchResultPosition": start_pos,
                        "maxResults": 5,
                        "major": 0, "minor": 0
                    }
                }
                
                r = requests.post(f"http://{dev['ip']}:{dev['port']}/ISAPI/AccessControl/AcsEvent?format=json",
                                 json=payload, auth=HTTPDigestAuth(dev['user'], dev['pass']), timeout=5)
                
                if r.status_code == 200:
                    events = r.json().get("AcsEvent", {}).get("InfoList", [])
                    for ev in events:
                        emp_no = ev.get('employeeNoString') or ev.get('employeeNo', 'N/A')
                        ev_time = ev.get('time')
                        # Si detectamos un acceso con ID, lo mandamos al backend
                        if emp_no != 'N/A':
                            print(f"[🔔 OK] Detectado ID {emp_no} a las {ev_time}")
                            requests.post(BACKEND_URL, json={"EventNotificationAlert": {"AccessControllerEvent": ev}}, timeout=2)
                        else:
                            print(f"[.] Evento sin ID a las {ev_time}", end="\r")
            
        except Exception as e:
            print(f"Error: {e}")
            
        time.sleep(1.5)

if __name__ == "__main__":
    poll()
