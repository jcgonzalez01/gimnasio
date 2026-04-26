import sqlite3, requests
from requests.auth import HTTPDigestAuth

# Configuración destino
SERVER_IP = "192.168.1.10"
SERVER_PORT = 8001
PATH = "/api/access/hikvision-webhook"

# Obtener credenciales del dispositivo
conn = sqlite3.connect('backend/gimnasio.db')
cur = conn.cursor()
cur.execute("SELECT username, password, ip_address FROM hikvision_devices WHERE is_active = 1 LIMIT 1")
row = cur.fetchone()
conn.close()

if not row:
    print("No hay dispositivos activos.")
    exit()

user, pwd, device_ip = row
url = f"http://{device_ip}/ISAPI/Event/notification/httpHosts"
full_webhook_url = f"http://{SERVER_IP}:{SERVER_PORT}{PATH}"

xml_body = f"""<?xml version="1.0" encoding="UTF-8"?>
<HttpHostNotificationList version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
    <HttpHostNotification>
        <id>1</id>
        <url>{full_webhook_url}</url>
        <protocolType>HTTP</protocolType>
        <parameterFormatType>json</parameterFormatType>
        <addressingFormatType>ipaddress</addressingFormatType>
        <ipAddress>{SERVER_IP}</ipAddress>
        <portNo>{SERVER_PORT}</portNo>
        <httpAuthenticationMethod>none</httpAuthenticationMethod>
    </HttpHostNotification>
</HttpHostNotificationList>"""

print(f"Enviando nueva configuración a {device_ip}...")
try:
    r = requests.put(url, data=xml_body.encode('utf-8'), 
                     auth=HTTPDigestAuth(user, pwd), 
                     headers={"Content-Type": "application/xml"},
                     timeout=10)
    print("Status:", r.status_code)
    print("Response:", r.text)
except Exception as e:
    print("Error:", e)
