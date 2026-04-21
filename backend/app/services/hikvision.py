"""
Servicio de integración con dispositivos Hikvision via ISAPI (HTTP REST).
Soporta: MinMoe, DS-K1T320EFX, DS-K1T671, DS-K1T804, y otros terminales con reconocimiento facial.
"""
import requests
import base64
import json
import time
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
from requests.auth import HTTPDigestAuth

logger = logging.getLogger(__name__)


class HikvisionISAPI:
    """Cliente para la API ISAPI de dispositivos Hikvision."""

    def __init__(self, ip: str, port: int, username: str, password: str, timeout: int = 10):
        self.base_url = f"http://{ip}:{port}"
        self.auth = HTTPDigestAuth(username, password)
        self.timeout = timeout
        self.session = requests.Session()
        self.session.auth = self.auth

    def _get(self, path: str) -> requests.Response:
        url = f"{self.base_url}{path}"
        return self.session.get(url, timeout=self.timeout)

    def _post(self, path: str, data: Any, content_type: str = "application/json") -> requests.Response:
        url = f"{self.base_url}{path}"
        if content_type == "application/json":
            return self.session.post(url, json=data, timeout=self.timeout,
                                     headers={"Content-Type": content_type})
        else:
            return self.session.post(url, data=data, timeout=self.timeout,
                                     headers={"Content-Type": content_type})

    def _put(self, path: str, data: Any) -> requests.Response:
        url = f"{self.base_url}{path}"
        return self.session.put(url, json=data, timeout=self.timeout,
                                headers={"Content-Type": "application/json"})

    def _delete(self, path: str) -> requests.Response:
        url = f"{self.base_url}{path}"
        return self.session.delete(url, timeout=self.timeout)

    def get_device_info(self) -> Optional[Dict]:
        """Obtiene información básica del dispositivo."""
        try:
            r = self._get("/ISAPI/System/deviceInfo")
            if r.status_code == 200:
                root = ET.fromstring(r.text)
                ns = {"hik": "http://www.hikvision.com/ver20/XMLSchema"}
                info = {}
                for tag in ["deviceName", "deviceID", "model", "serialNumber",
                            "macAddress", "firmwareVersion", "deviceType"]:
                    el = root.find(f"hik:{tag}", ns) or root.find(tag)
                    if el is not None:
                        info[tag] = el.text
                return info
        except Exception as e:
            logger.error(f"Error obteniendo info del dispositivo: {e}")
        return None

    def test_connection(self) -> bool:
        """Prueba la conexión con el dispositivo."""
        try:
            r = self._get("/ISAPI/System/deviceInfo")
            return r.status_code == 200
        except Exception:
            return False

    def get_user_list(self) -> List[Dict]:
        """Lista usuarios registrados en el dispositivo."""
        try:
            r = self._get("/ISAPI/AccessControl/UserInfo/Search?format=json")
            if r.status_code == 200:
                data = r.json()
                return data.get("UserInfoSearch", {}).get("UserInfo", [])
        except Exception as e:
            logger.error(f"Error listando usuarios: {e}")
        return []

    def add_user(self, employee_no: str, name: str, user_type: str = "normal",
                 begin_time: Optional[str] = None,
                 end_time: Optional[str] = None,
                 enabled: bool = True,
                 face_image_b64: Optional[str] = None) -> bool:
        """
        Crea o actualiza un usuario en el dispositivo.
        Optimizado para aplicar permisos y fotos de forma inmediata.
        """
        emp = str(employee_no)
        safe_name = name[:32]
        bt = begin_time or "2020-01-01T00:00:00"
        et = end_time or "2030-12-31T23:59:59"

        # Procesar imagen con alta calidad para biometría Hikvision
        if face_image_b64:
            try:
                import base64 as _b64, io as _io
                face_bytes = _b64.b64decode(face_image_b64)
                from PIL import Image as _PILImg
                _pil = _PILImg.open(_io.BytesIO(face_bytes)).convert("RGB")
                if _pil.width > 480 or _pil.height > 640:
                    _pil.thumbnail((480, 640), _PILImg.LANCZOS)
                _buf = _io.BytesIO()
                _pil.save(_buf, format="JPEG", quality=90, optimize=True)
                face_image_b64 = _b64.b64encode(_buf.getvalue()).decode("utf-8")
            except Exception as _re:
                logger.warning(f"add_user image optimization error: {_re}")

        payload: Dict = {
            "UserInfo": {
                "employeeNo": emp,
                "name": safe_name,
                "userType": user_type,
                "doorRight": "1",
                "RightPlan": [{"doorNo": 1, "planTemplateNo": "1"}],
                "Valid": {
                    "enable": enabled,
                    "beginTime": bt,
                    "endTime": et,
                    "timeType": "local",
                },
            }
        }

        user_ok = False
        # Intentar Record (POST)
        try:
            r = self._post("/ISAPI/AccessControl/UserInfo/Record?format=json", payload)
            if r.status_code in (200, 201):
                user_ok = True
        except Exception:
            pass

        # Si falla, intentar Modify (PUT)
        if not user_ok:
            try:
                r2 = self._put("/ISAPI/AccessControl/UserInfo/Modify?format=json", payload)
                if r2.status_code in (200, 201):
                    user_ok = True
            except Exception:
                pass

        # Si el usuario es OK, subir la cara si existe
        if user_ok and face_image_b64:
            self.enroll_face(emp, face_image_b64)

        # SIEMPRE forzar la aplicación de permisos para que las fechas surtan efecto
        self.apply_permissions()

        return user_ok

    def enroll_face(self, employee_no: str, face_image_b64: str,
                    face_lib_id: str = "1") -> Dict:
        """
        Enrola la imagen facial con el método de alta compatibilidad (Multipart JSON).
        Optimizado para ser rápido y eficaz.
        """
        import base64 as _b64, io as _io
        emp = str(employee_no)

        try:
            face_bytes = _b64.b64decode(face_image_b64)
            from PIL import Image as _PILImg
            _pil = _PILImg.open(_io.BytesIO(face_bytes)).convert("RGB")
            if _pil.width > 480 or _pil.height > 640:
                _pil.thumbnail((480, 640), _PILImg.LANCZOS)
            _buf = _io.BytesIO()
            _pil.save(_buf, format="JPEG", quality=90)
            img_bytes = _buf.getvalue()
        except Exception:
            return {"success": False, "error": "Image process error"}

        try:
            url = f"{self.base_url}/ISAPI/Intelligent/FDLib/FaceDataRecord?format=json"
            meta = {"faceLibType": "blackFD", "FDID": face_lib_id, "FPID": emp}
            files = {
                'FaceDataRecord': ("FaceDataRecord.json", json.dumps(meta), 'application/json'),
                'img': ("FaceImage.jpg", img_bytes, 'image/jpeg')
            }
            r = self.session.post(url, files=files, timeout=self.timeout)
            return {"success": r.status_code in (200, 201), "status": r.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def apply_permissions(self) -> bool:
        """Fuerza al dispositivo a aplicar cambios de permisos y fechas."""
        try:
            r = self._put("/ISAPI/AccessControl/Permission/SetUp", {})
            return r.status_code in (200, 201)
        except Exception:
            return False

    def capture_face_photo(self) -> Optional[bytes]:
        """Captura una foto JPEG desde la cámara del dispositivo."""
        endpoints = ["/ISAPI/Streaming/channels/1/picture", "/ISAPI/Streaming/channels/101/picture"]
        for ep in endpoints:
            try:
                r = self._get(ep)
                if r.status_code == 200 and r.content and r.content[:2] == b'\xff\xd8':
                    return r.content
            except Exception:
                continue
        return None

    def delete_user(self, employee_no: str) -> bool:
        """Elimina un usuario del dispositivo."""
        payload = {"UserInfoDelCond": {"EmployeeNoList": [{"employeeNo": str(employee_no)}]}}
        try:
            r = self._put("/ISAPI/AccessControl/UserInfo/Delete?format=json", payload)
            return r.status_code == 200
        except Exception:
            return False

    def update_user_validity(self, employee_no: str, end_date: datetime) -> bool:
        """Actualiza la fecha de vencimiento."""
        payload = {
            "UserInfo": {
                "employeeNo": str(employee_no),
                "Valid": {
                    "enable": True,
                    "beginTime": "2020-01-01T00:00:00",
                    "endTime": end_date.strftime("%Y-%m-%dT%H:%M:%S"),
                    "timeType": "local",
                }
            }
        }
        try:
            r = self._put("/ISAPI/AccessControl/UserInfo/Modify?format=json", payload)
            self.apply_permissions()
            return r.status_code == 200
        except Exception:
            return False

    def get_face_libs(self) -> List[Dict[str, str]]:
        """Lee las librerías faciales del dispositivo."""
        try:
            r = self._get("/ISAPI/Intelligent/FDLib?format=json")
            if r.status_code == 200:
                data = r.json()
                raw = data.get("FDLib") or []
                if isinstance(raw, list):
                    return [{"FDID": str(lib.get("FDID", "")), "faceLibType": lib.get("faceLibType", "")} for lib in raw]
        except Exception:
            pass
        return []

    def delete_face(self, employee_no: str, face_lib_id: str = "1") -> bool:
        """Elimina datos faciales."""
        real_libs = self.get_face_libs() or [{"FDID": face_lib_id, "faceLibType": "blackFD"}]
        for lib in real_libs:
            try:
                r = self._put("/ISAPI/Intelligent/FDLib/FaceDataRecord/delete?format=json",
                               {"FaceDataDelCond": {"FDID": lib["FDID"], "EmployeeNoList": [{"employeeNo": str(employee_no)}]}})
                if r.status_code == 200: return True
            except Exception:
                pass
        return False

    def get_face_list(self, face_lib_id: str = "1") -> List[Dict]:
        """Lista las caras enroladas."""
        try:
            r = self._post("/ISAPI/Intelligent/FDLib/FDSearch?format=json",
                            {"FaceDataSearchCond": {"searchID": "1", "searchResultPosition": 0, "maxResults": 100, "FDID": face_lib_id}})
            if r.status_code == 200:
                return r.json().get("FaceDataSearchResult", {}).get("FaceMatching", [])
        except Exception:
            pass
        return []

    def get_access_events(self, start_time: datetime, end_time: datetime, max_results: int = 100) -> List[Dict]:
        """Consulta eventos de acceso."""
        # Hikvision requiere formato ISO8601 con zona horaria o 'Z'
        # Usamos +00:00 para asegurar compatibilidad
        start_str = start_time.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        end_str = end_time.strftime("%Y-%m-%dT%H:%M:%S+00:00")

        payload = {
            "AcsEventCond": {
                "searchID": "1", 
                "searchResultPosition": 0, 
                "maxResults": max_results, 
                "major": 0, # 0 = Todos los eventos (incluye alarmas, fallos, etc)
                "minor": 0,
                "startTime": start_str, 
                "endTime": end_str
            }
        }

        print(f"[Hikvision] Consultando eventos desde {start_str} hasta {end_str}...", flush=True)

        try:
            r = self._post("/ISAPI/AccessControl/AcsEvent?format=json", payload)
            if r.status_code == 200:
                data = r.json()
                events = data.get("AcsEvent", {}).get("InfoList", [])
                print(f"[Hikvision] Se obtuvieron {len(events)} eventos del dispositivo.", flush=True)
                return events
            else:
                print(f"[Hikvision] Error consultando eventos: {r.status_code} - {r.text}", flush=True)
        except Exception as e:
            print(f"[Hikvision] Excepción consultando eventos: {e}", flush=True)
        return []
    def open_door(self, door_no: int = 1) -> dict:
        """Abre la puerta manualmente."""
        url = f"{self.base_url}/ISAPI/AccessControl/RemoteControl/door/{door_no}"
        try:
            r = self.session.put(url + "?format=json", json={"RemoteControlDoor": {"doorNo": door_no, "cmd": "open"}}, timeout=self.timeout)
            if r.status_code in (200, 201): return {"success": True}
        except Exception:
            pass
        return {"success": False}

    def configure_http_host(self, server_ip: str, server_port: int, slot_id: int = 1, path: str = "/api/access/hikvision-webhook") -> Dict:
        """Configura el dispositivo para eventos HTTP."""
        # Intentamos configurar para que envíe JSON si es posible, aunque muchos dispositivos
        # solo envían XML. Si envían XML, el backend deberá procesarlo.
        xml_body = (f'<?xml version="1.0" encoding="UTF-8"?><HttpHostNotificationList version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">'
                    f'<HttpHostNotification><id>{slot_id}</id><url>http://{server_ip}:{server_port}{path}</url><protocolType>HTTP</protocolType>'
                    f'<parameterFormatType>json</parameterFormatType><addressingFormatType>ipaddress</addressingFormatType>'
                    f'<ipAddress>{server_ip}</ipAddress><portNo>{server_port}</portNo></HttpHostNotification></HttpHostNotificationList>')
        try:
            r = self.session.put(f"{self.base_url}/ISAPI/Event/notification/httpHosts", data=xml_body.encode("utf-8"), headers={"Content-Type": "application/xml"}, timeout=self.timeout)
            return {"success": r.status_code in (200, 201)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_door_status(self) -> Optional[Dict]:
        """Obtiene el estado de la puerta."""
        try:
            r = self._get("/ISAPI/AccessControl/Door/Status/1")
            if r.status_code == 200: return r.json()
        except Exception:
            pass
        return None


def image_file_to_base64(file_path: str) -> str:
    with open(file_path, "rb") as f: return base64.b64encode(f.read()).decode("utf-8")

def image_bytes_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")
