import sqlite3, requests
from requests.auth import HTTPDigestAuth
from datetime import datetime

conn = sqlite3.connect('backend/gimnasio.db')
cur = conn.cursor()
cur.execute("SELECT ip_address, port, username, password FROM hikvision_devices WHERE is_active = 1 LIMIT 1")
row = cur.fetchone()
conn.close()

if not row: exit()
ip, port, user, pwd = row

# 1. Configurar Zona Horaria a GMT-4 (asumiendo tu ubicación por los logs)
# El formato de Hikvision para TimeZone a veces es confuso: 
# 'CST-4:00:00' suele significar GMT-4 en algunos modelos.
# Intentaremos con un formato estándar.

now = datetime.now()
time_str = now.strftime("%Y-%m-%dT%H:%M:%S")

xml_body = f"""<?xml version="1.0" encoding="UTF-8"?>
<Time version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
    <timeMode>manual</timeMode>
    <localTime>{time_str}</localTime>
    <timeZone>GMT-04:00</timeZone>
</Time>"""

url = f"http://{ip}:{port}/ISAPI/System/time"

print(f"Corrigiendo Zona Horaria y Hora: {time_str} (GMT-04:00)")
try:
    r = requests.put(url, data=xml_body.encode('utf-8'), 
                     auth=HTTPDigestAuth(user, pwd), 
                     headers={"Content-Type": "application/xml"},
                     timeout=10)
    print("Status:", r.status_code)
    print("Respuesta:", r.text)
except Exception as e:
    print("Error:", e)
