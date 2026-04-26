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
    last_serial = 0
    print(f"--- MONITOR HIKVISION v7.0 (Serial Tracking) ---")
    print(f"Backend: {BACKEND_URL}")
    
    while True:
        dev = get_active_device()
        if not dev: time.sleep(5); continue
        
        try:
            # Traer los últimos 10 eventos. El serialNo es el ID único real.
            payload = {
                "AcsEventCond": {
                    "searchID": "s" + str(int(time.time()))[-5:],
                    "searchResultPosition": 0,
                    "maxResults": 10,
                    "major": 0, "minor": 0
                }
            }
            
            r = requests.post(
                f"http://{dev['ip']}:{dev['port']}/ISAPI/AccessControl/AcsEvent?format=json",
                json=payload, auth=HTTPDigestAuth(dev['user'], dev['pass']), timeout=5
            )
            
            if r.status_code == 200:
                events = r.json().get("AcsEvent", {}).get("InfoList", [])
                
                # Procesar eventos (vienen de más nuevo a más viejo)
                for ev in events:
                    serial = ev.get('serialNo', 0)
                    ev_time = ev.get("time")
                    emp_no = ev.get('employeeNoString') or ev.get('employeeNo')
                    full_name = ev.get('name') # Algunos modelos envian el nombre aqui
                    
                    # Si el serial es mayor al último procesado, es un evento NUEVO
                    if serial > last_serial:
                        if last_serial == 0:
                            last_serial = serial
                            print(f"[!] Monitor activo. Serial inicial: {serial}")
                            break
                        
                        display_id = emp_no or (f"Nombre: {full_name}" if full_name else "N/A")
                        print(f"[🔔] {ev_time} | ID: {display_id} | Serial: {serial}")
                        
                        # Enviar al backend
                        # Si no hay ID pero hay nombre, el backend intentará resolverlo
                        webhook_data = {"EventNotificationAlert": {"AccessControllerEvent": ev}}
                        try:
                            requests.post(BACKEND_URL, json=webhook_data, timeout=2)
                        except: pass
                        
                        last_serial = serial
            
        except Exception as e:
            print(f"Error: {e}")
            
        time.sleep(2)

if __name__ == "__main__":
    poll()
