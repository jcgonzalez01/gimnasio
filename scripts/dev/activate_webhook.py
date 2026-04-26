import requests
from requests.auth import HTTPDigestAuth

DEVICE_IP = "192.168.1.38"
USER = "admin"
PASS = "acc12345"

# Este XML activa el envío de eventos de acceso a través de la red (HTTP/ISAPI)
xml_linkage = """<?xml version="1.0" encoding="UTF-8"?>
<EventLogCfg version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
    <id>1</id>
    <linkage>
        <Linkage>
            <notificationList>
                <Notification>
                    <notificationMethod>http</notificationMethod>
                    <notificationHostID>1</notificationHostID>
                </Notification>
            </notificationList>
        </Linkage>
    </linkage>
</EventLogCfg>"""

# También probamos activar AcsEvent (Control de Acceso específico)
xml_acs = """<?xml version="1.0" encoding="UTF-8"?>
<AcsEventCfg version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
    <Linkage>
        <notificationList>
            <Notification>
                <notificationMethod>http</notificationMethod>
                <notificationHostID>1</notificationHostID>
            </Notification>
        </notificationList>
    </Linkage>
</AcsEventCfg>"""

def try_put(path, xml, label):
    print(f"Intentando {label}...")
    try:
        r = requests.put(
            f"http://{DEVICE_IP}{path}",
            data=xml.encode('utf-8'),
            auth=HTTPDigestAuth(USER, PASS),
            headers={"Content-Type": "application/xml"},
            timeout=10
        )
        print(f"Status: {r.status_code}, Response: {r.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

try_put("/ISAPI/Event/notification/httpHosts/1/linkage", xml_linkage, "Linkage General")
try_put("/ISAPI/AccessControl/AcsEvent/linkage", xml_acs, "Linkage Control Acceso")
