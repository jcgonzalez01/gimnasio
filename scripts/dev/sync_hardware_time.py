import sqlite3, requests, time
from requests.auth import HTTPDigestAuth
from datetime import datetime

# Configuración del dispositivo
conn = sqlite3.connect('backend/gimnasio.db')
cur = conn.cursor()
cur.execute("SELECT ip_address, port, username, password FROM hikvision_devices WHERE is_active = 1 LIMIT 1")
row = cur.fetchone()
conn.close()

if not row:
    print("No hay dispositivos activos.")
    exit()

ip, port, user, pwd = row

# Sincronizar a la hora local del PC (ISO format con offset si es posible, o simple)
now = datetime.now()
time_str = now.strftime("%Y-%m-%dT%H:%M:%S")

# XML para configurar la hora
xml_body = f"""<?xml version="1.0" encoding="UTF-8"?>
<Time version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
    <timeMode>manual</timeMode>
    <localTime>{time_str}</localTime>
</Time>"""

url = f"http://{ip}:{port}/ISAPI/System/time"

print(f"Sincronizando dispositivo {ip} a la hora del PC: {time_str}")
try:
    r = requests.put(url, data=xml_body.encode('utf-8'), 
                     auth=HTTPDigestAuth(user, pwd), 
                     headers={"Content-Type": "application/xml"},
                     timeout=10)
    print("Status:", r.status_code)
    print("Respuesta:", r.text)
except Exception as e:
    print("Error:", e)
