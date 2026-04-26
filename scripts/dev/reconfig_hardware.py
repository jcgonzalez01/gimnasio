import sqlite3, requests
from requests.auth import HTTPDigestAuth

SERVER_IP = "192.168.1.10"
SERVER_PORT = 8001

conn = sqlite3.connect('backend/gimnasio.db')
cur = conn.cursor()
cur.execute("SELECT ip_address, port, username, password FROM hikvision_devices WHERE is_active = 1 LIMIT 1")
row = cur.fetchone()
conn.close()

if not row:
    print("No hay dispositivos activos.")
    exit()

device_ip, device_port, user, pwd = row
# Usar el puerto del dispositivo obtenido de la BD
url = f"http://{device_ip}:{device_port}/ISAPI/Event/notification/httpHosts/1"

xml_body = f"""<?xml version="1.0" encoding="UTF-8"?>
<HttpHostNotification version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
    <id>1</id>
    <url>http://{SERVER_IP}:{SERVER_PORT}/api/access/hikvision-webhook</url>
    <protocolType>HTTP</protocolType>
    <parameterFormatType>json</parameterFormatType>
    <addressingFormatType>ipaddress</addressingFormatType>
    <ipAddress>{SERVER_IP}</ipAddress>
    <portNo>{SERVER_PORT}</portNo>
    <httpAuthenticationMethod>none</httpAuthenticationMethod>
</HttpHostNotification>"""

print(f"Configurando dispositivo {device_ip} ({device_port}) para enviar a {SERVER_IP}:{SERVER_PORT}...")
try:
    r = requests.put(url, data=xml_body.encode('utf-8'), 
                     auth=HTTPDigestAuth(user, pwd), 
                     headers={"Content-Type": "application/xml"},
                     timeout=10)
    print("Status:", r.status_code)
    print("Respuesta:", r.text)
except Exception as e:
    print("Error:", e)
