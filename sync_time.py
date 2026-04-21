import requests
from requests.auth import HTTPDigestAuth
from datetime import datetime

def sync_time():
    url = 'http://192.168.1.38:80/ISAPI/System/time'
    auth = HTTPDigestAuth('admin', 'acc12345')
    
    # Obtener hora actual del PC
    now = datetime.now()
    # Formato: 2026-04-21T10:15:23-04:00 (ajustado a tu zona)
    time_str = now.strftime("%Y-%m-%dT%H:%M:%S-04:00")
    
    body = f"""<?xml version="1.0" encoding="UTF-8"?>
<Time version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
    <timeMode>manual</timeMode>
    <localTime>{time_str}</localTime>
    <timeZone>CST-4:00:00</timeZone>
</Time>"""

    try:
        r = requests.put(url, auth=auth, data=body, headers={'Content-Type': 'application/xml'}, timeout=10)
        print(f"Sincronizando hora a: {time_str}")
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    sync_time()
