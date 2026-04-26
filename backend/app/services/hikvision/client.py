"""
Cliente core para ISAPI de Hikvision.
"""
import requests
import json
import logging
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any, List
from datetime import datetime
from requests.auth import HTTPDigestAuth

from .constants import ISAPI_NS, SYSTEM, ACCESS, FACE_LIB, STREAMING, parse_endpoint, DOOR_CMD

logger = logging.getLogger(__name__)

class HikvisionClient:
    """Cliente para la API ISAPI de dispositivos Hikvision."""

    def __init__(self, ip: str, port: int, username: str, password: str, timeout: int = 10):
        self.base_url = f"http://{ip}:{port}"
        self.auth = HTTPDigestAuth(username, password)
        self.timeout = timeout
        self.session = requests.Session()
        self.session.auth = self.auth

    def request(self, endpoint_tuple: str, body: Any = None, params: Optional[Dict] = None, 
                is_json: bool = True, **kwargs) -> requests.Response:
        """Realiza una petición genérica basada en las constantes de endpoints."""
        method, path = parse_endpoint(endpoint_tuple)
        
        # Reemplazar placeholders en el path si existen (ej: <doorID>)
        for key, value in kwargs.items():
            path = path.replace(f"<{key}>", str(value))
            
        url = f"{self.base_url}{path}"
        if is_json and "format=json" not in url:
            url += ("&" if "?" in url else "?") + "format=json"
            
        headers = {}
        if is_json:
            headers["Content-Type"] = "application/json"
        elif isinstance(body, (bytes, str)) and ("<?xml" in str(body) or "version=" in str(body)):
            headers["Content-Type"] = "application/xml"

        try:
            if method == "GET":
                return self.session.get(url, params=params, timeout=self.timeout)
            elif method == "POST":
                if is_json:
                    return self.session.post(url, json=body, params=params, timeout=self.timeout, headers=headers)
                else:
                    return self.session.post(url, data=body, params=params, timeout=self.timeout, headers=headers)
            elif method == "PUT":
                if is_json:
                    return self.session.put(url, json=body, params=params, timeout=self.timeout, headers=headers)
                else:
                    return self.session.put(url, data=body, params=params, timeout=self.timeout, headers=headers)
            elif method == "DELETE":
                return self.session.delete(url, params=params, timeout=self.timeout)
        except Exception as e:
            logger.error(f"Error en petición ISAPI {method} {path}: {e}")
            raise

    # --- High Level Methods ---

    def get_device_info(self) -> Optional[Dict]:
        try:
            r = self.request(SYSTEM["DEVICE_INFO"])
            if r.status_code == 200:
                if "json" in r.headers.get("Content-Type", ""):
                    return r.json().get("DeviceInfo")
                else:
                    root = ET.fromstring(r.text)
                    ns = {"hik": "http://www.hikvision.com/ver20/XMLSchema"}
                    info = {}
                    for tag in ["deviceName", "deviceID", "model", "serialNumber", "macAddress", "firmwareVersion"]:
                        el = root.find(f"hik:{tag}", ns) or root.find(tag)
                        if el is not None: info[tag] = el.text
                    return info
        except: pass
        return None

    def test_connection(self) -> bool:
        try:
            r = self.request(SYSTEM["DEVICE_INFO"])
            return r.status_code == 200
        except: return False

    def open_door(self, door_no: int = 1) -> bool:
        """Abre la puerta remotamente usando XML (mayor compatibilidad)."""
        try:
            xml_payload = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<RemoteControlDoor version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">'
                f'<doorNo>{door_no}</doorNo>'
                f'<cmd>{DOOR_CMD["OPEN"]}</cmd>'
                '</RemoteControlDoor>'
            )
            r = self.request(ACCESS["REMOTE_CONTROL"], body=xml_payload, is_json=False, doorID=door_no)
            return r.status_code in (200, 201)
        except Exception as e:
            logger.error(f"Error al abrir puerta {door_no}: {e}")
            return False

    def add_user(self, employee_no: str, name: str, enabled: bool = True, 
                 begin_time: str = None, end_time: str = None,
                 face_image_b64: str = None) -> bool:
        payload = {
            "UserInfo": {
                "employeeNo": str(employee_no),
                "name": name[:32],
                "userType": "normal",
                "doorRight": "1",
                "RightPlan": [{"doorNo": 1, "planTemplateNo": "1"}],
                "Valid": {
                    "enable": enabled,
                    "beginTime": begin_time or "2020-01-01T00:00:00",
                    "endTime": end_time or "2030-12-31T23:59:59",
                    "timeType": "local",
                },
            }
        }
        # Intentar Record (POST), si falla Modify (PUT)
        success = False
        try:
            r = self.request(ACCESS["USER_ADD"], body=payload)
            if r.status_code in (200, 201):
                success = True
            else:
                r = self.request(ACCESS["USER_MODIFY"], body=payload)
                if r.status_code in (200, 201):
                    success = True
            
            if success:
                self.request(ACCESS["PERMISSION_SET_UP"], body={})
                
                # Si se proporcionó una foto, enrolarla también
                if face_image_b64:
                    self.enroll_face(employee_no, face_image_b64)
                    
                return True
        except Exception as e:
            logger.error(f"Error en add_user: {e}")
        return False

    def enroll_face(self, employee_no: str, face_image: Any, face_lib_id: str = "1", 
                    face_image_b64: str = None) -> Dict[str, Any]:
        """
        Sube una imagen facial al dispositivo. 
        face_image puede ser bytes o un string base64.
        """
        import base64
        
        image_bytes = face_image
        if face_image_b64:
            image_bytes = base64.b64decode(face_image_b64)
        elif isinstance(face_image, str):
            # Si viene con el prefijo data:image/jpeg;base64,...
            if "," in face_image:
                face_image = face_image.split(",")[1]
            image_bytes = base64.b64decode(face_image)

        url = f"{self.base_url}/ISAPI/Intelligent/FDLib/FaceDataRecord?format=json"
        meta = {
            "faceLibType": "blackFD", 
            "FDID": face_lib_id, 
            "FPID": str(employee_no)
        }
        
        files = {
            'FaceDataRecord': (None, json.dumps(meta), 'application/json'),
            'img': ("face.jpg", image_bytes, 'image/jpeg')
        }
        
        try:
            r = self.session.post(url, files=files, timeout=self.timeout)
            if r.status_code in (200, 201):
                return {"success": True}
            
            # Intentar obtener error detallado del JSON de respuesta
            try:
                err_data = r.json()
                msg = err_data.get("ResponseStatus", {}).get("statusString", r.text)
                return {"success": False, "error": msg}
            except:
                return {"success": False, "error": f"Error HTTP {r.status_code}"}
        except Exception as e:
            logger.error(f"Error en enroll_face: {e}")
            return {"success": False, "error": str(e)}

    def delete_face(self, employee_no: str, face_lib_id: str = "1") -> bool:
        """Elimina la cara de un usuario."""
        try:
            # ISAPI/Intelligent/FDLib/FDSearch/Delete
            payload = {
                "FaceDataDeleteCond": {
                    "searchID": "1",
                    "FPID": [{"value": str(employee_no)}]
                }
            }
            # Usamos una URL directa ya que las constantes pueden variar
            url = f"{self.base_url}/ISAPI/Intelligent/FDLib/FDSearch/Delete?format=json&FDID={face_lib_id}&faceLibType=blackFD"
            r = self.session.put(url, json=payload, timeout=self.timeout)
            return r.status_code in (200, 201)
        except:
            return False

    def delete_user(self, employee_no: str) -> bool:
        """Elimina un usuario del dispositivo."""
        try:
            url = f"{self.base_url}/ISAPI/AccessControl/UserInfo/Delete?format=json"
            payload = {
                "UserInfoDelCond": {
                    "EmployeeNoList": [{"employeeNo": str(employee_no)}]
                }
            }
            r = self.session.put(url, json=payload, timeout=self.timeout)
            return r.status_code in (200, 201)
        except Exception as e:
            logger.error(f"Error eliminando usuario {employee_no}: {e}")
            return False

    def capture_face_photo(self, channel_id: int = 1) -> Optional[bytes]:
        """
        Captura una foto (snapshot) del dispositivo.
        Retorna los bytes de la imagen o None si falla.
        """
        try:
            # Intentar canal 1 (principal) o el especificado
            r = self.request(STREAMING["SNAPSHOT"], is_json=False, channelID=channel_id)
            if r.status_code == 200:
                return r.content
            
            # Algunos dispositivos usan canales 101, 102 para sub-streams
            if channel_id == 1:
                r = self.request(STREAMING["SNAPSHOT"], is_json=False, channelID=101)
                if r.status_code == 200:
                    return r.content
        except Exception as e:
            logger.error(f"Error capturando foto del dispositivo: {e}")
        return None
