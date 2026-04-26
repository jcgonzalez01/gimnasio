import requests, datetime
from requests.auth import HTTPDigestAuth

DEVICE_IP = "192.168.1.38"
USER = "admin"
PASS = "acc12345"

# Obtener hora actual en formato ISO8601 con zona horaria
now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S-04:00")

xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Time version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
    <timeMode>manual</timeMode>
    <localTime>{now}</localTime>
</Time>"""

print(f"Sincronizando hora {now} -> {DEVICE_IP}")
try:
    r = requests.put(
        f"http://{DEVICE_IP}/ISAPI/System/time",
        data=xml.encode('utf-8'),
        auth=HTTPDigestAuth(USER, PASS),
        headers={"Content-Type": "application/xml"},
        timeout=10
    )
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    print(f"Error: {e}")
