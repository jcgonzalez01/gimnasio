import sqlite3, requests
from requests.auth import HTTPDigestAuth

# Configuración del servidor (Escuchador)
SERVER_IP = "192.168.1.10"
SERVER_PORT = 8001
WEBHOOK_PATH = "/api/access/hikvision-webhook"

# Obtener datos del equipo activo
conn = sqlite3.connect('backend/gimnasio.db')
cur = conn.cursor()
cur.execute("SELECT ip_address, port, username, password FROM hikvision_devices WHERE is_active = 1 LIMIT 1")
row = cur.fetchone()
conn.close()

if not row:
    print("Error: No hay dispositivos activos en la base de datos.")
    exit()

device_ip, device_port, user, pwd = row
url = f"http://{device_ip}:{device_port}/ISAPI/Event/notification/httpHosts/1"

# XML de configuración según especificación ISAPI
xml_body = f"""<?xml version="1.0" encoding="UTF-8"?>
<HttpHostNotification version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
    <id>1</id>
    <url>http://{SERVER_IP}:{SERVER_PORT}{WEBHOOK_PATH}</url>
    <protocolType>HTTP</protocolType>
    <parameterFormatType>json</parameterFormatType>
    <addressingFormatType>ipaddress</addressingFormatType>
    <ipAddress>{SERVER_IP}</ipAddress>
    <portNo>{SERVER_PORT}</portNo>
    <httpAuthenticationMethod>none</httpAuthenticationMethod>
</HttpHostNotification>"""

print(f"Configurando terminal {device_ip} para envío automático a {SERVER_IP}:{SERVER_PORT}...")

try:
    r = requests.put(
        url, 
        data=xml_body.encode('utf-8'),
        auth=HTTPDigestAuth(user, pwd),
        headers={"Content-Type": "application/xml"},
        timeout=10
    )
    
    if r.status_code == 200:
        print("✅ ÉXITO: El terminal ha sido vinculado correctamente.")
        print("A partir de ahora, los eventos llegarán al monitor sin demora.")
    else:
        print(f"❌ ERROR: El dispositivo respondió con estado {r.status_code}")
        print(r.text)

except Exception as e:
    print(f"❌ ERROR DE CONEXIÓN: {e}")
