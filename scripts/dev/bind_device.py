import sqlite3, requests
from requests.auth import HTTPDigestAuth

# Datos según tu documento
SERVER_IP = "192.168.1.10"
SERVER_PORT = 8001 
PATH = "/api/events"

# Obtener credenciales
conn = sqlite3.connect('backend/gimnasio.db')
cur = conn.cursor()
cur.execute("SELECT username, password, ip_address FROM hikvision_devices WHERE is_active = 1 LIMIT 1")
row = cur.fetchone()
conn.close()

if not row:
    print("No hay dispositivos activos.")
    exit()

user, pwd, device_ip = row
# URL con /1 al final como indica tu documento
url = f"http://{device_ip}/ISAPI/Event/notification/httpHosts/1"

xml_body = f"""<?xml version="1.0" encoding="UTF-8"?>
<HttpHostNotification version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
    <id>1</id>
    <url>http://{SERVER_IP}:{SERVER_PORT}{PATH}</url>
    <protocolType>HTTP</protocolType>
    <parameterFormatType>xml</parameterFormatType>
    <addressingFormatType>ipaddress</addressingFormatType>
    <ipAddress>{SERVER_IP}</ipAddress>
    <portNo>{SERVER_PORT}</portNo>
    <httpAuthenticationMethod>none</httpAuthenticationMethod>
</HttpHostNotification>"""

print(f"Vinculando terminal a http://{SERVER_IP}:{SERVER_PORT}{PATH}...")
try:
    # Usamos PUT a /httpHosts/1
    r = requests.put(url, data=xml_body.encode('utf-8'), 
                     auth=HTTPDigestAuth(user, pwd), 
                     headers={"Content-Type": "application/xml"},
                     timeout=10)
    print("Status:", r.status_code)
    print("Respuesta del equipo:", r.text)
    
    if r.status_code == 200:
        print("\n✅ VINCULACIÓN EXITOSA.")
        print("👉 PRUEBA AHORA: Escanea tu rostro y el evento debería aparecer.")
except Exception as e:
    print("Error:", e)
