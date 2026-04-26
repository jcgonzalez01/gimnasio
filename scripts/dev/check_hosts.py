import sqlite3, requests
from requests.auth import HTTPDigestAuth

conn = sqlite3.connect('backend/gimnasio.db')
cur = conn.cursor()
cur.execute("SELECT username, password, ip_address FROM hikvision_devices WHERE is_active = 1 LIMIT 1")
row = cur.fetchone()
conn.close()

if row:
    user, pwd, ip = row
    print(f"Probando con {user} en {ip}...")
    try:
        r = requests.get(f"http://{ip}/ISAPI/Event/notification/httpHosts", auth=HTTPDigestAuth(user, pwd), timeout=5)
        print("Status:", r.status_code)
        print("Body:", r.text)
    except Exception as e:
        print("Error:", e)
else:
    print("No hay dispositivos activos.")
