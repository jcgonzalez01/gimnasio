import sqlite3
import requests
import datetime
from requests.auth import HTTPDigestAuth
import os

DB_PATH = "backend/gimnasio.db"

def sync_active_device():
    if not os.path.exists(DB_PATH):
        print(f"No se encuentra la DB en {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT ip_address, port, username, password, name FROM hikvision_devices WHERE is_active = 1 LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if not row:
        print("No hay dispositivos activos configurados.")
        return

    ip, port, user, pw, name = row
    
    # Obtener hora actual con desfase -04:00 (basado en lo que vimos antes)
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S-04:00")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Time version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
    <timeMode>manual</timeMode>
    <localTime>{now}</localTime>
</Time>"""

    print(f"Sincronizando {name} ({ip}) con hora {now}...")
    try:
        url = f"http://{ip}:{port}/ISAPI/System/time"
        r = requests.put(
            url,
            data=xml.encode('utf-8'),
            auth=HTTPDigestAuth(user, pw),
            headers={"Content-Type": "application/xml"},
            timeout=10
        )
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print("Sincronización exitosa.")
        else:
            print(f"Error: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    sync_active_device()
