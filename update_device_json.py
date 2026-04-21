import requests
from requests.auth import HTTPDigestAuth

def update_config():
    url = 'http://192.168.1.38:80/ISAPI/Event/notification/httpHosts'
    auth = HTTPDigestAuth('admin', 'acc12345')
    
    # XML para configurar JSON y suscripción de eventos
    body = """<?xml version="1.0" encoding="UTF-8"?>
<HttpHostNotificationList version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
    <HttpHostNotification>
        <id>1</id>
        <url>http://192.168.1.10:8000/api/access/hikvision-webhook</url>
        <protocolType>HTTP</protocolType>
        <parameterFormatType>json</parameterFormatType>
        <addressingFormatType>ipaddress</addressingFormatType>
        <ipAddress>192.168.1.10</ipAddress>
        <portNo>8000</portNo>
        <httpAuthenticationMethod>none</httpAuthenticationMethod>
        <SubscribeEvent>
            <heartbeat>30</heartbeat>
            <eventMode>all</eventMode>
            <EventList>
                <Event>
                    <type>AccessControllerEvent</type>
                </Event>
            </EventList>
        </SubscribeEvent>
    </HttpHostNotification>
</HttpHostNotificationList>"""

    try:
        r = requests.put(url, auth=auth, data=body, headers={'Content-Type': 'application/xml'}, timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_config()
