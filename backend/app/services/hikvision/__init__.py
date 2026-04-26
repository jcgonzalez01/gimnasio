"""
Paquete de integración Hikvision ISAPI.
"""
import base64
from .client import HikvisionClient
from .parser import parse_event_payload
from .events import get_event_description, get_linkage_description
from .constants import ISAPI_NS, SYSTEM, ACCESS, EVENT, FACE_LIB, DOOR_CMD

def image_file_to_base64(file_path: str) -> str:
    with open(file_path, "rb") as f: return base64.b64encode(f.read()).decode("utf-8")

def image_bytes_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")

class HikvisionISAPI(HikvisionClient):
    """
    Clase de compatibilidad que mantiene la interfaz original 
    pero utiliza la nueva estructura restructurada.
    """
    def __init__(self, ip: str, port: int, username: str, password: str, timeout: int = 10):
        super().__init__(ip, port, username, password, timeout)

    # El resto de métodos específicos se pueden ir moviendo aquí 
    # o seguir usando los del padre si coinciden.
    
    def get_access_events(self, start_time, end_time, max_results=100):
        from .constants import ACCESS
        start_str = start_time.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        end_str = end_time.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        payload = {
            "AcsEventCond": {
                "searchID": "1",
                "searchResultPosition": 0,
                "maxResults": max_results,
                "major": 0,
                "minor": 0,
                "startTime": start_str,
                "endTime": end_str
            }
        }
        r = self.request(ACCESS["ACS_EVENT_SEARCH"], body=payload)
        if r.status_code == 200:
            return r.json().get("AcsEvent", {}).get("InfoList", [])
        return []

    def configure_http_host(self, server_ip: str, server_port: int, slot_id: int = 1, path: str = "/api/access/hikvision-webhook"):
        from .constants import EVENT
        xml_body = (f'<?xml version="1.0" encoding="UTF-8"?><HttpHostNotificationList version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">'
                    f'<HttpHostNotification><id>{slot_id}</id><url>http://{server_ip}:{server_port}{path}</url><protocolType>HTTP</protocolType>'
                    f'<parameterFormatType>json</parameterFormatType><addressingFormatType>ipaddress</addressingFormatType>'
                    f'<ipAddress>{server_ip}</ipAddress><portNo>{server_port}</portNo></HttpHostNotification></HttpHostNotificationList>')
        r = self.request(EVENT["HTTP_HOSTS_SET"], body=xml_body, is_json=False)
        return {"success": r.status_code in (200, 201)}
