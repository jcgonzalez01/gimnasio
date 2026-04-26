import sqlite3, requests
from requests.auth import HTTPDigestAuth
from datetime import datetime

conn = sqlite3.connect('backend/gimnasio.db')
cur = conn.cursor()
cur.execute("SELECT ip_address, port, username, password FROM hikvision_devices WHERE is_active = 1 LIMIT 1")
row = cur.fetchone()
conn.close()

if not row:
    print("No hay dispositivos activos.")
    exit()

ip, port, user, pwd = row
url = f"http://{ip}:{port}/ISAPI/System/time"

try:
    print(f"Hora actual PC: {datetime.now()}")
    print(f"Hora UTC PC:    {datetime.utcnow()}")
    r = requests.get(url, auth=HTTPDigestAuth(user, pwd), timeout=10)
    print("\n--- Hora en dispositivo Hikvision ---")
    print(r.text)
except Exception as e:
    print(f"Error: {e}")
