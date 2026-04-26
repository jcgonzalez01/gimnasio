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
    print("--- MONITOR DE ALTA SENSIBILIDAD ACTIVADO ---")
    
    while True:
        dev = get_active_device()
        if not dev: time.sleep(5); continue
        
        try:
            # Pedir los últimos 5 eventos de cualquier tipo
            payload = {"AcsEventCond": {"searchID": "final"+str(int(time.time()))[-4:], "searchResultPosition": 0, "maxResults": 5}}
            r = requests.post(f"http://{dev['ip']}:{dev['port']}/ISAPI/AccessControl/AcsEvent?format=json",
                             json=payload, auth=HTTPDigestAuth(dev['user'], dev['pass']), timeout=5)
            
            if r.status_code == 200:
                events = r.json().get("AcsEvent", {}).get("InfoList", [])
                for ev in events:
                    serial = ev.get('serialNo', 0)
                    if serial > last_serial:
                        if last_serial == 0: last_serial = serial; break
                        
                        emp_no = ev.get('employeeNoString') or ev.get('employeeNo', 'N/A')
                        print(f"[*] Detectado Serial {serial} | ID: {emp_no} | Maj: {ev.get('major')}")
                        
                        # ENVIAR AL BACKEND Y FORZAR PROCESAMIENTO
                        webhook_data = {"EventNotificationAlert": {"AccessControllerEvent": ev}}
                        try:
                            res = requests.post(BACKEND_URL, json=webhook_data, timeout=3)
                            print(f"    -> Backend: {res.status_code}")
                        except: print("    -> Error enviando al backend")
                        
                        last_serial = serial
            
        except Exception as e:
            print(f"Error: {e}")
            
        time.sleep(1) # Escaneo ultra-rápido cada 1 segundo

if __name__ == "__main__":
    poll()
