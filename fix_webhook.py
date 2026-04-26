import requests
from requests.auth import HTTPDigestAuth

DEVICE_IP = "192.168.1.38"
SERVER_IP = "192.168.1.10"
SERVER_PORT = 8000

# XML simple y robusto
xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<HttpHostNotificationList version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
    <HttpHostNotification>
        <id>1</id>
        <url>http://{SERVER_IP}:{SERVER_PORT}/api/access/hikvision-webhook</url>
        <protocolType>HTTP</protocolType>
        <parameterFormatType>json</parameterFormatType>
        <addressingFormatType>ipaddress</addressingFormatType>
        <ipAddress>{SERVER_IP}</ipAddress>
        <portNo>{SERVER_PORT}</portNo>
    </HttpHostNotification>
</HttpHostNotificationList>"""

print(f"Configurando dispositivo {DEVICE_IP} -> {SERVER_IP}:{SERVER_PORT}")
try:
    r = requests.put(
        f"http://{DEVICE_IP}/ISAPI/Event/notification/httpHosts",
        data=xml.encode('utf-8'),
        auth=HTTPDigestAuth("admin", "acc12345"),
        headers={"Content-Type": "application/xml"},
        timeout=10
    )
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    print(f"Error: {e}")
