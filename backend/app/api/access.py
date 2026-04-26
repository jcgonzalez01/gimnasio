from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta
import asyncio, threading, json, logging
import xml.etree.ElementTree as ET

from ..core.database import get_db, SessionLocal
from ..core.security import require_admin, get_current_user
from ..models.user import User
from ..models.access import HikvisionDevice, AccessLog
from ..models.member import Member
from ..schemas.access import (
    HikvisionDeviceCreate, HikvisionDeviceUpdate, HikvisionDeviceOut,
    AccessLogCreate, AccessLogOut, AccessEventWS
)
from ..services.hikvision import HikvisionISAPI, image_file_to_base64
from ..services.hikvision.parser import parse_event_payload
from ..services.websocket_manager import ws_manager
from ..services.audit import log_action
from ..services.deletion import assess_device, to_409_payload

router = APIRouter(prefix="/access", tags=["Control de Acceso"])
# Router público (sin auth) para webhooks de Hikvision y WebSocket
public_router = APIRouter(prefix="/access", tags=["Webhooks Hikvision"])
logger = logging.getLogger(__name__)


# ── Dispositivos Hikvision ────────────────────────────────────────────────────

@router.get("/devices", response_model=List[HikvisionDeviceOut])
def list_devices(db: Session = Depends(get_db)):
    return db.query(HikvisionDevice).all()


@router.post("/devices", response_model=HikvisionDeviceOut, status_code=201,
             dependencies=[Depends(require_admin)])
def create_device(device: HikvisionDeviceCreate, db: Session = Depends(get_db)):
    db_dev = HikvisionDevice(**device.model_dump())
    db.add(db_dev)
    db.commit()
    db.refresh(db_dev)
    return db_dev


@router.put("/devices/{device_id}", response_model=HikvisionDeviceOut,
            dependencies=[Depends(require_admin)])
def update_device(device_id: int, device: HikvisionDeviceUpdate,
                  db: Session = Depends(get_db)):
    d = db.query(HikvisionDevice).filter(HikvisionDevice.id == device_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    for k, v in device.model_dump(exclude_none=True).items():
        setattr(d, k, v)
    db.commit()
    db.refresh(d)
    return d


@router.delete("/devices/{device_id}", dependencies=[Depends(require_admin)])
def delete_device(device_id: int,
                  request: Request,
                  force: bool = False,
                  user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    d = db.query(HikvisionDevice).filter(HikvisionDevice.id == device_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")

    impact = assess_device(db, d)
    if impact["history"] and not force:
        raise HTTPException(status_code=409,
                            detail=to_409_payload("El dispositivo", impact))

    # Si force, desvincular logs antes de borrar para preservar el historial
    if impact["history"]:
        db.query(AccessLog).filter(AccessLog.device_id == device_id).update(
            {"device_id": None}, synchronize_session=False
        )

    name = d.name
    db.delete(d)
    db.commit()
    log_action(db, user, "delete", entity_type="device", entity_id=device_id,
               summary=f"Eliminó dispositivo '{name}'" + (" (forzado)" if force else ""),
               request=request)
    return {"message": "Dispositivo eliminado"}


@router.post("/devices/{device_id}/test")
def test_device_connection(device_id: int, db: Session = Depends(get_db)):
    d = db.query(HikvisionDevice).filter(HikvisionDevice.id == device_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    hik = HikvisionISAPI(d.ip_address, d.port, d.username, d.password)
    ok = hik.test_connection()
    if ok:
        info = hik.get_device_info() or {}
        d.last_heartbeat = datetime.utcnow()
        d.serial_number = info.get("serialNumber")
        d.model = info.get("model")
        d.firmware = info.get("firmwareVersion")
        db.commit()
        return {"status": "online", "info": info}
    return {"status": "offline", "info": {}}


@router.post("/devices/{device_id}/open-door")
def open_door(device_id: int,
              request: Request,
              door_no: int = 1,
              user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    d = db.query(HikvisionDevice).filter(HikvisionDevice.id == device_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    hik = HikvisionISAPI(d.ip_address, d.port, d.username, d.password)
    result = hik.open_door(door_no=door_no)
    log_action(db, user, "open_door", entity_type="device", entity_id=device_id,
               summary=f"Apertura manual puerta {door_no} en '{d.name}'", request=request)
    logger.info(f"open_door {d.name} → {result}")
    return result


@router.post("/devices/{device_id}/sync-members")
def sync_members_to_device(device_id: int, db: Session = Depends(get_db)):
    """
    Registra TODOS los miembros activos en el dispositivo.
    - Sin membresía activa → enabled=False (registrado pero sin acceso)
    - Con membresía activa → enabled=True con fechas reales
    Útil para sincronizar un dispositivo nuevo o recargar tras un reset de fábrica.
    """
    d = db.query(HikvisionDevice).filter(HikvisionDevice.id == device_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")

    hik = HikvisionISAPI(d.ip_address, d.port, d.username, d.password)

    members = db.query(Member).filter(Member.status != "deleted").all()
    now = datetime.utcnow()

    results = []
    ok_count = 0
    fail_count = 0

    for m in members:
        # Determinar si tiene membresía activa
        active_mem = None
        for mem in m.memberships:
            if mem.is_active and mem.start_date <= now and mem.end_date >= now:
                active_mem = mem
                break

        has_access = active_mem is not None
        begin_time = active_mem.start_date.strftime("%Y-%m-%dT%H:%M:%S") if active_mem else "2020-01-01T00:00:00"
        end_time   = active_mem.end_date.strftime("%Y-%m-%dT%H:%M:%S")   if active_mem else "2030-12-31T23:59:59"

        ok = hik.add_user(
            employee_no=str(m.id),
            name=m.full_name,
            begin_time=begin_time,
            end_time=end_time,
            enabled=has_access,
        )

        # Guardar hikvision_card_no si aún no tiene
        if ok and not m.hikvision_card_no:
            m.hikvision_card_no = str(m.id)

        result_entry = {
            "member_id":   m.id,
            "member_no":   m.member_number,
            "name":        m.full_name,
            "has_access":  has_access,
            "registered":  ok,
        }
        results.append(result_entry)
        if ok:
            ok_count += 1
        else:
            fail_count += 1

        print(f"[sync_members] {m.full_name} (#{m.id}) → enabled={has_access} | {'OK' if ok else 'FAIL'}", flush=True)

    db.commit()

    return {
        "device":     d.name,
        "total":      len(members),
        "ok":         ok_count,
        "failed":     fail_count,
        "results":    results,
    }


@router.get("/devices/{device_id}/http-hosts")
def get_http_hosts(device_id: int, db: Session = Depends(get_db)):
    """Lee los destinos HTTP push configurados en el dispositivo."""
    d = db.query(HikvisionDevice).filter(HikvisionDevice.id == device_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    hik = HikvisionISAPI(d.ip_address, d.port, d.username, d.password)
    return hik.get_http_hosts()


@router.post("/devices/{device_id}/configure-events")
def configure_device_events(
    device_id: int,
    server_ip: str,
    server_port: int = 8001,
    slot_id: int = 1,
    db: Session = Depends(get_db),
):
    """
    Configura el dispositivo Hikvision para enviar eventos en tiempo real
    al backend via HTTP push (POST a /api/access/hikvision-webhook).

    Parámetros:
      server_ip:   IP de esta PC en la red local (ej: 192.168.1.10)
      server_port: Puerto del backend (por defecto 8001)
      slot_id:     Ranura 1-8 del dispositivo (por defecto 1)
    """
    d = db.query(HikvisionDevice).filter(HikvisionDevice.id == device_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    hik = HikvisionISAPI(d.ip_address, d.port, d.username, d.password)
    result = hik.configure_http_host(
        server_ip=server_ip,
        server_port=server_port,
        slot_id=slot_id,
    )
    return result


@router.get("/devices/{device_id}/debug-door")
def debug_door(device_id: int, door_no: int = 1, db: Session = Depends(get_db)):
    """
    Endpoint de diagnóstico: prueba TODOS los payloads posibles contra el
    dispositivo y devuelve la respuesta exacta de cada uno.
    """
    import requests as req_lib
    from requests.auth import HTTPDigestAuth

    d = db.query(HikvisionDevice).filter(HikvisionDevice.id == device_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")

    base = f"http://{d.ip_address}:{d.port}"
    auth = HTTPDigestAuth(d.username, d.password)
    url  = f"{base}/ISAPI/AccessControl/RemoteControl/door/{door_no}"
    results = []

    def mk_xml(ns: str, ver: str, body: str) -> bytes:
        if ns:
            tag = f'<RemoteControlDoor version="{ver}" xmlns="{ns}">'
        else:
            tag = "<RemoteControlDoor>"
        return f'<?xml version="1.0" encoding="UTF-8"?>{tag}{body}</RemoteControlDoor>'.encode()

    # errorMsg=cmd → el dispositivo usa <cmd> no <controlType>
    body_cmd      = f"<doorNo>{door_no}</doorNo><cmd>open</cmd>"
    body_cmd_user = f"<doorNo>{door_no}</doorNo><cmd>open</cmd><userType>normal</userType><employeeNo></employeeNo>"
    body_ctrl     = f"<doorNo>{door_no}</doorNo><controlType>open</controlType><userType>normal</userType><employeeNo></employeeNo>"

    xml_attempts = [
        ("xml | ver10 + cmd",          mk_xml("http://www.hikvision.com/ver10/XMLSchema", "1.0", body_cmd)),
        ("xml | ver10 + cmd + user",   mk_xml("http://www.hikvision.com/ver10/XMLSchema", "1.0", body_cmd_user)),
        ("xml | bare  + cmd",          mk_xml("", "", body_cmd)),
        ("xml | ver10 + controlType",  mk_xml("http://www.hikvision.com/ver10/XMLSchema", "1.0", body_ctrl)),
    ]
    for label, data in xml_attempts:
        try:
            r = req_lib.put(url, data=data, auth=auth, timeout=6,
                            headers={"Content-Type": "application/xml"})
            results.append({"label": label, "status": r.status_code,
                            "body": r.text[:400], "success": r.status_code in (200, 201)})
            if r.status_code in (200, 201):
                break
        except Exception as e:
            results.append({"label": label, "error": str(e), "success": False})

    json_attempts = [
        ("json | cmd",         {"RemoteControlDoor": {"doorNo": door_no, "cmd": "open"}}),
        ("json | cmd+user",    {"RemoteControlDoor": {"doorNo": door_no, "cmd": "open", "userType": "normal", "employeeNo": ""}}),
        ("json | controlType", {"RemoteControlDoor": {"doorNo": door_no, "controlType": "open", "userType": "normal", "employeeNo": ""}}),
    ]
    for label, payload in json_attempts:
        try:
            r = req_lib.put(url + "?format=json", json=payload, auth=auth, timeout=6,
                            headers={"Content-Type": "application/json"})
            results.append({"label": label, "status": r.status_code,
                            "body": r.text[:400], "success": r.status_code in (200, 201)})
            if r.status_code in (200, 201):
                break
        except Exception as e:
            results.append({"label": label, "error": str(e), "success": False})

    # También intentar GET capabilities para ver qué soporta el dispositivo
    try:
        cap = req_lib.get(
            f"{base}/ISAPI/AccessControl/RemoteControl/door/capabilities",
            auth=auth, timeout=6,
        )
        capabilities = cap.text[:800]
    except Exception as e:
        capabilities = str(e)

    return {"device": d.name, "url": url, "results": results, "capabilities": capabilities}


# ── Log de diagnóstico enfocado del dispositivo ───────────────────────────────

@router.get("/devices/{device_id}/comms-log")
def comms_log(device_id: int,
              member_id: Optional[int] = None,
              db: Session = Depends(get_db)):
    """
    Diagnóstico enfocado — máx. 7 peticiones HTTP para no saturar el dispositivo.

    Secciones:
      A. Info del dispositivo + librerías faciales (2 requests)
      B. Estado del miembro en el dispositivo (2 requests, solo si member_id)
      C. Prueba de subida de foto (2-3 requests, solo si member_id + tiene foto)
    """
    import requests as req_lib
    from requests.auth import HTTPDigestAuth
    import time, json as _json, base64 as _b64

    d = db.query(HikvisionDevice).filter(HikvisionDevice.id == device_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")

    base = f"http://{d.ip_address}:{d.port}"
    auth = HTTPDigestAuth(d.username, d.password)
    log: list = []

    # ─────────────────────────────────────────────────────────────────────────
    # Helper: realiza una petición JSON/XML y la agrega al log
    # ─────────────────────────────────────────────────────────────────────────
    def call(method: str, path: str, body=None, is_json: bool = True,
             label: str = "", section: str = "") -> dict:
        url = base + path
        t0 = time.time()

        # Ocultar datos base64 largos en el log para legibilidad
        def _sanitize_body(b) -> str:
            raw = _json.dumps(b, ensure_ascii=False) if not isinstance(b, str) else b
            import re
            return re.sub(
                r'"faceData"\s*:\s*"[A-Za-z0-9+/=]{80,}"',
                lambda m: f'"faceData": "[JPEG ~{len(m.group())//1365}KB base64]"',
                raw
            )[:800]

        entry = {
            "label":    label or f"{method} {path}",
            "method":   method,
            "url":      url,
            "req_body": "",
            "status":   None,
            "res_body": "",
            "ms":       0,
            "ok":       False,
            "section":  section,
        }
        try:
            if body is not None:
                if is_json:
                    entry["req_body"] = _sanitize_body(body)
                else:
                    entry["req_body"] = body[:600] if isinstance(body, str) else repr(body)[:200]

            headers = {"Content-Type": "application/json" if is_json else "application/xml"}
            kwargs  = dict(auth=auth, timeout=10, headers=headers)
            if body is None:
                r = getattr(req_lib, method.lower())(url, **kwargs)
            elif is_json:
                r = getattr(req_lib, method.lower())(url, json=body, **kwargs)
            else:
                r = getattr(req_lib, method.lower())(url, data=body, **kwargs)

            entry["status"]   = r.status_code
            entry["res_body"] = r.text[:2000]
            entry["ms"]       = round((time.time() - t0) * 1000)
            entry["ok"]       = r.status_code in (200, 201)
        except Exception as exc:
            entry["res_body"] = f"[EXCEPTION] {exc}"
            entry["ms"]       = round((time.time() - t0) * 1000)
        log.append(entry)
        return entry

    def call_multipart(label: str, path: str, meta_xml: str, img_bytes: bytes,
                       section: str = "C") -> dict:
        """pictureUpload multipart/form-data — método principal DS-K1T320EFX."""
        url = base + path
        t0  = time.time()
        entry = {
            "label":    label,
            "method":   "POST",
            "url":      url,
            "req_body": f"[multipart] XML: {meta_xml[:300]}  +  [JPEG ~{len(img_bytes)//1024}KB]",
            "status":   None,
            "res_body": "",
            "ms":       0,
            "ok":       False,
            "section":  section,
        }
        try:
            files = [
                ("FaceDataRecord", ("FaceDataRecord",
                                    meta_xml.encode("utf-8"), "application/xml")),
                ("img", ("face.jpg", img_bytes, "image/jpeg")),
            ]
            r = req_lib.post(url, files=files, auth=auth, timeout=20)
            entry["status"]   = r.status_code
            entry["res_body"] = r.text[:2000]
            entry["ms"]       = round((time.time() - t0) * 1000)
            entry["ok"]       = r.status_code in (200, 201)
        except Exception as exc:
            entry["res_body"] = f"[EXCEPTION] {exc}"
            entry["ms"]       = round((time.time() - t0) * 1000)
        log.append(entry)
        return entry

    # ════════════════════════════════════════════════════════════════════════
    # SECCIÓN A — Info del dispositivo + librerías faciales
    # ════════════════════════════════════════════════════════════════════════

    call("GET", "/ISAPI/System/deviceInfo",
         label="A1 · Información del dispositivo",
         section="A")

    e_fdlib = call("GET", "/ISAPI/Intelligent/FDLib?format=json",
                   label="A2 · Librerías faciales del dispositivo",
                   section="A")

    # ── Extraer FDID + faceLibType de la respuesta ───────────────────────────
    _real_libs: list = []
    try:
        _data = _json.loads(e_fdlib.get("res_body", "{}"))
        _raw  = _data.get("FDLib") or _data.get("FDLibList") or []
        if isinstance(_raw, list):
            for _lib in _raw:
                _fid = str(_lib.get("FDID") or "")
                _ft  = _lib.get("faceLibType", "")
                if _fid:
                    _real_libs.append({"FDID": _fid, "faceLibType": _ft})
        elif isinstance(_raw, dict) and _raw.get("FDID"):
            _real_libs.append({"FDID": str(_raw["FDID"]),
                                "faceLibType": _raw.get("faceLibType", "")})
    except Exception:
        pass
    if not _real_libs:
        _real_libs = [{"FDID": d.face_lib_id, "faceLibType": "blackFD"}]

    _first_fdid  = _real_libs[0]["FDID"]
    _first_ftype = _real_libs[0]["faceLibType"]

    # ════════════════════════════════════════════════════════════════════════
    # SECCIÓN B — Estado del miembro en el dispositivo
    # ════════════════════════════════════════════════════════════════════════
    member_status = {
        "employee_no":        None,
        "member_registered":  False,   # ¿existe UserInfo en el device?
        "member_has_face":    False,   # ¿hay dato facial (FDSearch o similar)?
        "user_info":          None,    # payload devuelto por el device
        "has_photo":          False,   # ¿tiene foto en la BD?
    }

    _face_bytes: Optional[bytes] = None
    _face_b64:   str = ""

    if member_id:
        employee_no = str(member_id)
        member_status["employee_no"] = employee_no

        # B1 — ¿Está registrado el usuario en el dispositivo?
        e_user = call(
            "POST", "/ISAPI/AccessControl/UserInfo/Search?format=json",
            body={"UserInfoSearchCond": {
                "searchID":             "diag_b1",
                "searchResultPosition": 0,
                "maxResults":           1,
                "EmployeeNoList":       [{"employeeNo": employee_no}],
            }},
            label=f"B1 · Buscar usuario #{member_id} en dispositivo",
            section="B",
        )
        try:
            _u = _json.loads(e_user.get("res_body", "{}"))
            _uinfo = (
                _u.get("UserInfoSearch", {}).get("UserInfo")
                or _u.get("UserInfo")
                or []
            )
            if isinstance(_uinfo, list) and len(_uinfo) > 0:
                member_status["member_registered"] = True
                member_status["user_info"] = _uinfo[0]
            elif isinstance(_uinfo, dict) and _uinfo:
                member_status["member_registered"] = True
                member_status["user_info"] = _uinfo
        except Exception:
            pass

        # B2 — ¿Tiene foto facial en la librería? (puede dar 400 en DS-K1T320EFX)
        call(
            "POST", "/ISAPI/Intelligent/FDLib/FDSearch?format=json",
            body={"FaceDataSearchCond": {
                "searchID":             "diag_b2",
                "searchResultPosition": 0,
                "maxResults":           1,
                "FDID":                 _first_fdid,
                "faceLibType":          _first_ftype,
            }},
            label=f"B2 · Buscar foto facial de #{member_id} (FDID={_first_fdid})",
            section="B",
        )

        # ── Cargar foto del miembro desde la BD ──────────────────────────────
        _member = db.query(Member).filter(Member.id == member_id).first()
        if _member and _member.photo_path:
            member_status["has_photo"] = True
            try:
                import io as _io
                with open("." + _member.photo_path, "rb") as _f:
                    _raw = _f.read()
                if _raw[:2] != b'\xff\xd8':
                    from PIL import Image as _PImgB
                    _img = _PImgB.open(_io.BytesIO(_raw)).convert("RGB")
                    _buf = _io.BytesIO()
                    _img.save(_buf, format="JPEG", quality=90)
                    _raw = _buf.getvalue()
                # Reducir a 300×300
                from PIL import Image as _PImgC
                _pil = _PImgC.open(_io.BytesIO(_raw)).convert("RGB")
                if _pil.width > 300 or _pil.height > 300:
                    _pil.thumbnail((300, 300), _PImgC.LANCZOS)
                _buf2 = _io.BytesIO()
                _pil.save(_buf2, format="JPEG", quality=80)
                _face_bytes = _buf2.getvalue()
                _face_b64   = _b64.b64encode(_face_bytes).decode("utf-8")
            except Exception as _pe:
                logger.warning(f"comms_log: no se pudo cargar foto: {_pe}")

        # ════════════════════════════════════════════════════════════════════
        # SECCIÓN C — Pruebas de subida de foto (solo si el miembro tiene foto)
        # ════════════════════════════════════════════════════════════════════
        if _face_b64:
            # C1 — PUT UserInfo/Modify + faceDataList (método actual de enroll_face)
            call(
                "PUT", "/ISAPI/AccessControl/UserInfo/Modify?format=json",
                body={"UserInfo": {
                    "employeeNo": employee_no,
                    "faceDataList": [{"faceData": _face_b64}],
                }},
                label=f"C1 · PUT UserInfo/Modify faceDataList (método actual enroll_face)",
                section="C",
            )

            # C2 — pictureUpload multipart XML (método nativo DS-K1T320EFX)
            if _face_bytes:
                _pu_xml = (
                    '<?xml version="1.0" encoding="UTF-8"?>'
                    f'<FaceDataRecord>'
                    f'<faceLibType>{_first_ftype}</faceLibType>'
                    f'<FDID>{_first_fdid}</FDID>'
                    f'<FPID>{employee_no}</FPID>'
                    f'</FaceDataRecord>'
                )
                call_multipart(
                    label=f"C2 · pictureUpload multipart FPID={employee_no} FDID={_first_fdid} (DS-K1T320EFX)",
                    path="/ISAPI/Intelligent/FDLib/pictureUpload",
                    meta_xml=_pu_xml,
                    img_bytes=_face_bytes,
                    section="C",
                )

                # C3 — pictureUpload con employeeNo en lugar de FPID
                call_multipart(
                    label=f"C3 · pictureUpload multipart employeeNo={employee_no} (variante)",
                    path="/ISAPI/Intelligent/FDLib/pictureUpload",
                    meta_xml=(
                        '<?xml version="1.0" encoding="UTF-8"?>'
                        f'<FaceDataRecord>'
                        f'<faceLibType>{_first_ftype}</faceLibType>'
                        f'<FDID>{_first_fdid}</FDID>'
                        f'<employeeNo>{employee_no}</employeeNo>'
                        f'</FaceDataRecord>'
                    ),
                    img_bytes=_face_bytes,
                    section="C",
                )

        elif member_id:
            log.append({
                "label":   f"C · Sin foto — el miembro #{member_id} no tiene foto en la BD",
                "method":  "–", "url": "–", "req_body": "", "status": None,
                "res_body": "Sube una foto primero desde MemberDetail",
                "ms": 0, "ok": False, "section": "C",
            })

    return {
        "device":         d.name,
        "ip":             d.ip_address,
        "port":           d.port,
        "face_lib":       d.face_lib_id,
        "real_libs":      _real_libs,
        "member_status":  member_status,
        "log":            log,
        "timestamp":      datetime.utcnow().isoformat(),
    }


# ── Captura de foto desde cámara del dispositivo ─────────────────────────────

@router.post("/devices/{device_id}/capture-photo/{member_id}")
async def capture_photo_from_device(device_id: int, member_id: int,
                                    db: Session = Depends(get_db)):
    """
    Captura una foto desde la cámara del dispositivo Hikvision
    y la asigna como foto del miembro.
    """
    device = db.query(HikvisionDevice).filter(HikvisionDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")

    hik = HikvisionISAPI(device.ip_address, device.port, device.username, device.password)
    photo_bytes = hik.capture_face_photo()

    if not photo_bytes:
        raise HTTPException(status_code=502,
                            detail="No se pudo capturar foto del dispositivo. "
                                   "Verifique que la cámara esté disponible.")

    import uuid, os
    from ..core.config import settings

    filename = f"member_{member_id}_dev_{device_id}_{uuid.uuid4().hex}.jpg"
    path = os.path.join(settings.FACES_DIR, filename)
    with open(path, "wb") as f:
        f.write(photo_bytes)

    if member.photo_path:
        old = "." + member.photo_path
        if os.path.exists(old):
            os.remove(old)

    member.photo_path = f"/uploads/faces/{filename}"
    db.commit()
    return {"photo_path": member.photo_path, "device": device.name}


# ── Registro + Enrolamiento en un solo paso ───────────────────────────────

@router.post("/register-and-enroll/{member_id}")
async def register_and_enroll(
    member_id: int,
    begin_date: Optional[str] = None,
    end_date: Optional[str] = None,
    device_ids: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Registra al usuario Y sube la foto facial en un solo paso.
    """
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")
    if not member.photo_path:
        raise HTTPException(status_code=400, detail="El miembro no tiene foto")

    q = db.query(HikvisionDevice).filter(
        HikvisionDevice.is_active == True,
        HikvisionDevice.device_type == "access_control",
    )
    if device_ids:
        ids = [int(x) for x in device_ids.split(",") if x.strip().isdigit()]
        q = q.filter(HikvisionDevice.id.in_(ids))
    devices = q.all()

    if not devices:
        raise HTTPException(status_code=400, detail="No hay dispositivos activos configurados")

    employee_no = str(member.id)
    bt = begin_date or "2020-01-01T00:00:00"
    et = end_date or "2030-12-31T23:59:59"

    # Cargar foto
    photo_fs_path = "." + member.photo_path
    try:
        import base64 as _b64
        with open(photo_fs_path, "rb") as _f:
            _raw = _f.read()
        if not (_raw[:2] == b'\xff\xd8'):
            from PIL import Image
            import io as _io
            img = Image.open(_io.BytesIO(_raw)).convert("RGB")
            buf = _io.BytesIO()
            img.save(buf, format="JPEG", quality=90)
            _raw = buf.getvalue()
        face_b64 = _b64.b64encode(_raw).decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando foto: {e}")

    results = []
    all_ok = True

    for device in devices:
        hik = HikvisionISAPI(device.ip_address, device.port, device.username, device.password)
        
        # El método add_user ahora maneja internamente el registro Y el enrolamiento facial
        # utilizando el método Multipart de alta compatibilidad que confirmamos que funciona.
        user_ok = hik.add_user(
            employee_no=employee_no,
            name=member.full_name,
            begin_time=bt,
            end_time=et,
            enabled=True,
            face_image_b64=face_b64,
        )
        
        results.append({"device": device.name, "user_added": user_ok, "face_enrolled": user_ok})
        if not user_ok:
            all_ok = False

    if all_ok or any(r["user_added"] for r in results):
        member.hikvision_card_no = employee_no
        member.face_enrolled = True
        db.commit()

    return {"success": all_ok, "results": results, "employee_no": employee_no}


# ── Registro de usuario en dispositivo (sin foto) ─────────────────────────────

@router.post("/register-user/{member_id}")
async def register_user_on_devices(
    member_id: int,
    begin_date: Optional[str] = None,   # "2024-01-01T00:00:00"
    end_date:   Optional[str] = None,   # "2024-12-31T23:59:59"
    device_ids: Optional[str] = None,   # "1,2,3"  (vacío = todos)
    db: Session = Depends(get_db),
):
    """
    Paso 1: Registra al usuario en el/los dispositivos (sin foto).
    Crea el UserInfo con nombre, employeeNo y rango de fechas de acceso.
    Marca hikvision_card_no en la BD si al menos un dispositivo responde OK.
    """
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")

    q = db.query(HikvisionDevice).filter(
        HikvisionDevice.is_active == True,
        HikvisionDevice.device_type == "access_control",
    )
    if device_ids:
        ids = [int(x) for x in device_ids.split(",") if x.strip().isdigit()]
        q = q.filter(HikvisionDevice.id.in_(ids))
    devices = q.all()

    if not devices:
        raise HTTPException(status_code=400, detail="No hay dispositivos activos configurados")

    employee_no = str(member.id)
    results = []
    all_ok = True

    for device in devices:
        hik = HikvisionISAPI(device.ip_address, device.port, device.username, device.password)
        user_ok = hik.add_user(
            employee_no=employee_no,
            name=member.full_name,
            begin_time=begin_date,
            end_time=end_date,
            enabled=bool(begin_date and end_date),
        )
        results.append({"device": device.name, "user_added": user_ok})
        if not user_ok:
            all_ok = False

    if any(r["user_added"] for r in results):
        member.hikvision_card_no = employee_no
        db.commit()

    return {"success": all_ok, "results": results, "employee_no": employee_no}


# ── Enrolamiento facial (solo foto, usuario debe existir ya) ──────────────────

@router.post("/enroll-face/{member_id}")
async def enroll_face(
    member_id: int,
    begin_date: Optional[str] = None,   # reservado — ya no se usa aquí
    end_date:   Optional[str] = None,
    device_ids: Optional[str] = None,   # "1,2,3"  (vacío = todos)
    db: Session = Depends(get_db),
):
    """
    Paso 2: Sube la foto facial del miembro al/los dispositivos.
    El usuario debe haber sido registrado previamente con /register-user.
    Solo envía la imagen; no crea ni modifica el UserInfo.
    """
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")
    if not member.photo_path:
        raise HTTPException(status_code=400, detail="El miembro no tiene foto")

    photo_fs_path = "." + member.photo_path

    q = db.query(HikvisionDevice).filter(
        HikvisionDevice.is_active == True,
        HikvisionDevice.device_type == "access_control",
    )
    if device_ids:
        ids = [int(x) for x in device_ids.split(",") if x.strip().isdigit()]
        q = q.filter(HikvisionDevice.id.in_(ids))
    devices = q.all()

    if not devices:
        raise HTTPException(status_code=400, detail="No hay dispositivos activos configurados")

    results = []
    all_ok = True
    employee_no = str(member.id)

    try:
        import base64 as _b64, io as _io
        with open(photo_fs_path, "rb") as _f:
            _raw = _f.read()
        # Convertir a JPEG si no lo es (PNG, WebP, etc.)
        if not (_raw[:2] == b'\xff\xd8'):
            from PIL import Image
            img = Image.open(_io.BytesIO(_raw)).convert("RGB")
            buf = _io.BytesIO()
            img.save(buf, format="JPEG", quality=90)
            _raw = buf.getvalue()
        face_b64 = _b64.b64encode(_raw).decode("utf-8")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archivo de foto no encontrado")
    except Exception as _e:
        raise HTTPException(status_code=500, detail=f"Error procesando foto: {_e}")

    for device in devices:
        hik = HikvisionISAPI(device.ip_address, device.port, device.username, device.password)

        face_result = hik.enroll_face(
            employee_no=employee_no,
            face_image_b64=face_b64,
            face_lib_id=device.face_lib_id,
        )

        face_ok = face_result.get("success", False)
        results.append({
            "device":        device.name,
            "face_enrolled": face_ok,
            "variant":       face_result.get("variant"),
            "error":         face_result.get("error"),
            "attempts":      face_result.get("attempts", []),
        })

        if not face_ok:
            all_ok = False

    if all_ok or any(r["face_enrolled"] for r in results):
        member.face_enrolled = True
        if not member.hikvision_card_no:
            member.hikvision_card_no = employee_no
        db.commit()

    return {"success": all_ok, "results": results, "employee_no": employee_no}


@router.delete("/unenroll-face/{member_id}")
async def unenroll_face(member_id: int, db: Session = Depends(get_db)):
    """Elimina los datos faciales y el usuario del miembro de todos los dispositivos."""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")

    devices = db.query(HikvisionDevice).filter(HikvisionDevice.is_active == True).all()
    employee_no = str(member.id)
    results = []

    for device in devices:
        hik = HikvisionISAPI(device.ip_address, device.port, device.username, device.password)
        # Intentar borrar cara y luego usuario
        face_ok = hik.delete_face(employee_no, device.face_lib_id)
        user_ok = hik.delete_user(employee_no)
        results.append({"device": device.name, "face_deleted": face_ok, "user_deleted": user_ok})

    member.face_enrolled = False
    member.hikvision_card_no = None # Limpiar vinculación con hardware
    db.commit()
    return {"success": True, "results": results}


# ── Logs de acceso ────────────────────────────────────────────────────────────

@router.get("/recent-faces")
def get_recent_faces(db: Session = Depends(get_db)):
    """Obtiene el último acceso exitoso de cada miembro ocurrido en la última hora, sin duplicados por ID."""
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)
    
    # 1. Obtener todos los registros exitosos de la última hora ordenados por tiempo (nuevos primero)
    logs = (
        db.query(AccessLog)
        .filter(AccessLog.timestamp >= one_hour_ago)
        .filter(AccessLog.result == "granted")
        .filter(AccessLog.member_id.isnot(None))
        .order_by(AccessLog.timestamp.desc())
        .all()
    )
    
    # 2. Filtrar para dejar solo uno por ID (el más reciente)
    seen_ids = set()
    recent = []
    
    for log in logs:
        if log.member_id not in seen_ids:
            member = log.member
            if member:
                recent.append({
                    "id": log.id,
                    "member_id": member.id,
                    "name": f"{member.first_name} {member.last_name}",
                    "photo_path": member.photo_path,
                    "capture_path": log.capture_path,
                    "timestamp": log.timestamp,
                    "access_type": log.access_type
                })
                seen_ids.add(log.member_id)
    
    return recent


@router.get("/logs", response_model=List[AccessLogOut])
def get_access_logs(
    member_id: Optional[int] = None,
    device_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    q = db.query(AccessLog).order_by(desc(AccessLog.timestamp))
    if member_id:
        q = q.filter(AccessLog.member_id == member_id)
    if device_id:
        q = q.filter(AccessLog.device_id == device_id)
    if start_date:
        q = q.filter(AccessLog.timestamp >= start_date)
    if end_date:
        q = q.filter(AccessLog.timestamp <= end_date)
    logs = q.offset(skip).limit(limit).all()

    result = []
    for log in logs:
        result.append(AccessLogOut(
            id=log.id,
            member_id=log.member_id,
            device_id=log.device_id,
            direction=log.direction,
            access_type=log.access_type,
            result=log.result,
            temperature=log.temperature,
            notes=log.notes,
            timestamp=log.timestamp,
            member_name=log.member.full_name if log.member else None,
            device_name=log.device.name if log.device else None,
        ))
    return result


@router.post("/logs", response_model=AccessLogOut, status_code=201)
async def create_access_log(log_data: AccessLogCreate, db: Session = Depends(get_db)):
    """Registra manualmente un evento de acceso y notifica via WebSocket."""
    log = AccessLog(**log_data.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)

    # Broadcast WebSocket
    member = db.query(Member).filter(Member.id == log.member_id).first() if log.member_id else None
    device = db.query(HikvisionDevice).filter(HikvisionDevice.id == log.device_id).first() if log.device_id else None

    event = AccessEventWS(
        log_id=log.id,
        member_id=log.member_id,
        member_name=member.full_name if member else None,
        member_number=member.member_number if member else None,
        photo_path=member.photo_path if member else None,
        device_name=device.name if device else None,
        device_location=device.location if device else None,
        direction=log.direction,
        result=log.result,
        access_type=log.access_type,
        temperature=log.temperature,
        timestamp=log.timestamp.isoformat(),
    )
    await ws_manager.broadcast(event.model_dump())

    return AccessLogOut(
        id=log.id,
        member_id=log.member_id,
        device_id=log.device_id,
        direction=log.direction,
        access_type=log.access_type,
        result=log.result,
        temperature=log.temperature,
        notes=log.notes,
        timestamp=log.timestamp,
        member_name=member.full_name if member else None,
        device_name=device.name if device else None,
    )


@router.post("/devices/{device_id}/pull-events")
async def pull_device_events(
    device_id: int,
    hours: int = Query(24, description="Número de horas hacia atrás para consultar"),
    db: Session = Depends(get_db)
):
    """
    Consulta manualmente los eventos históricos del dispositivo y los guarda en la BD.
    Útil si el webhook falló o si el dispositivo estuvo offline.
    """
    d = db.query(HikvisionDevice).filter(HikvisionDevice.id == device_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")

    hik = HikvisionISAPI(d.ip_address, d.port, d.username, d.password)
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    events = hik.get_access_events(start_time, end_time, max_results=100)
    
    new_logs_count = 0
    for ev in events:
        employee_no = ev.get("employeeNoString")
        event_time_str = ev.get("time")
        
        # Intentar parsear fecha del dispositivo
        try:
            ts = datetime.fromisoformat(event_time_str.replace("Z", "+00:00"))
        except:
            ts = datetime.utcnow()

        # Evitar duplicados
        exists = db.query(AccessLog).filter(
            AccessLog.timestamp == ts,
            AccessLog.member_id == (int(employee_no) if employee_no and employee_no.isdigit() else None)
        ).first()
        
        if exists: continue

        member = None
        if employee_no:
            try: member = db.query(Member).filter(Member.id == int(employee_no)).first()
            except: pass
        
        # Mapeo por major/minor de Hikvision
        major = ev.get("major", 0)
        minor = ev.get("minor", 0)

        # Ignorar eventos que no son lecturas del lector (major 1=alarma, 2=puerta)
        if major not in (3, 5):
            continue

        # 5 = Access Control, 1 = Legal (Exitoso)
        result = "granted" if (major == 5 and minor == 1) else "denied"

        access_type = "face" if major == 5 else "unknown"
        if minor == 2: access_type = "card"
        if minor == 3: access_type = "fingerprint"
        
        log = AccessLog(
            member_id=member.id if member else None,
            device_id=d.id,
            direction="in" if ev.get("doorNo") == 1 else "out",
            access_type=access_type,
            result=result,
            raw_event=json.dumps(ev),
            timestamp=ts
        )
        db.add(log)
        db.flush() # Para obtener el ID del log antes del commit si fuera necesario

        # Broadcast por WebSocket para actualizar el monitor en vivo durante la sincronización
        try:
            ws_event = AccessEventWS(
                event_type="access",
                log_id=0, # Temporal
                member_id=member.id if member else None,
member_name=f"{member.first_name} {member.last_name}" if member else (f"#{employee_no}" if employee_no else "Desconocido"),
                member_number=member.member_number if member else None,
                photo_path=member.photo_path if member else None,
                device_name=d.name,
                device_location=d.location,
                direction=log.direction,
                result=result,
                access_type=access_type,
                timestamp=ts.isoformat(),
            )
            # await ws_manager.broadcast(ws_event.model_dump()) # Comentado para no saturar si son muchos
        except: pass
        
        new_logs_count += 1
    
    if new_logs_count > 0:
        db.commit()
        
    return {"status": "ok", "events_retrieved": len(events), "new_logs_saved": new_logs_count}


# ── Webhook para eventos de Hikvision ─────────────────────────────────────────

@public_router.post("/events")
@public_router.post("/hikvision-webhook")
@public_router.post("/ISAPI/Event/notification/httpHosts") # Ruta por defecto de algunos firmwares
@public_router.post("/ISAPI/AccessControl/AcsEvent")
async def hikvision_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint para recibir eventos push de dispositivos Hikvision.
    Soporta JSON y XML. Mapeo actualizado según docs: 0x3/0x1 = Granted.
    """
    client_host = request.client.host
    body = await request.body()

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Webhook from {client_host}: {body[:500]!r}")

    request_data = {}
    
    # 1. Intentar parsear como JSON
    try:
        request_data = json.loads(body)
    except:
        # 2. Intentar parsear como XML (Muy común en modo 0x3/0x1)
        try:
            root = ET.fromstring(body)
            acs = root.find(".//{*}AccessControllerEvent")
            if acs is not None:
                request_data = {
                    "AccessControllerEvent": {
                        "employeeNoString": acs.findtext("{*}employeeNoString") or acs.findtext(".//{*}employeeNoString"),
                        "major": int(acs.findtext("{*}major") or 0),
                        "minor": int(acs.findtext("{*}minor") or 0),
                        "currentVerifyMode": acs.findtext("{*}currentVerifyMode") or "face",
                        "status": acs.findtext("{*}status") or "success",
                        "time": acs.findtext("{*}time"),
                        "temperature": acs.findtext("{*}temperature"),
                    }
                }
        except: pass

    if not request_data:
        return {"status": "unsupported_format"}

    try:
        # Recuperar capture_path si viene del monitor local
        capture_path = request_data.get("capture_path")
        
        # Log para debug
        if capture_path:
            logger.info(f"Recibida captura de foto: {capture_path}")
        
        parsed = parse_event_payload(request_data)
        
        employee_no = parsed["employee_no"]
        major = parsed["major"]
        minor = parsed["minor"]
        result = parsed["result"]
        description = parsed["description"]
        access_type = parsed["access_type"]
        ts = parsed["timestamp"]
        temperature = parsed["temperature"]
        
        # Ignorar eventos que no son lecturas (majors 3 y 5 son los de interés para acceso)
        if major not in (3, 5):
            logger.info(f"Evento ignorado: {description} (Maj={major}, Min={minor})")
            return {"status": "ok"}

        logger.info(f"Evento procesado: {description} -> Resultado: {result}")
        
        # Buscar miembro
        member = None
        if employee_no:
            emp_str = str(employee_no)
            member = db.query(Member).filter(
                (Member.hikvision_card_no == emp_str) | 
                (Member.member_number == emp_str) |
                (Member.id == (int(employee_no) if employee_no.isdigit() else -1))
            ).first()
        
        # Identificar dispositivo
        device = db.query(HikvisionDevice).filter(HikvisionDevice.ip_address == client_host).first()
        if not device:
            device = db.query(HikvisionDevice).filter(HikvisionDevice.is_active == True).first()
        
        # Guardar en BD
        log = AccessLog(
            member_id=member.id if member else None,
            device_id=device.id if device else None,
            direction="in",
            access_type=access_type,
            result=result,
            temperature=temperature,
            raw_event=json.dumps(request_data),
            capture_path=capture_path,
            timestamp=ts
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        
        # Enviar por WebSocket
        ws_payload = AccessEventWS(
            event_type="access",
            log_id=log.id,
            member_id=member.id if member else None,
            member_name=member.full_name if member else (f"#{employee_no}" if employee_no else "Desconocido"),
            member_number=member.member_number if member else None,
            photo_path=member.photo_path if member else None,
            device_name=device.name if device else "Dispositivo Hikvision",
            device_location=device.location if device and device.location else "Entrada",
            direction="in",
            result=result,
            access_type=access_type,
            temperature=temperature,
            timestamp=ts.strftime("%Y-%m-%dT%H:%M:%S")
        )
        
        await ws_manager.broadcast(ws_payload.model_dump())

    except Exception as e:
        logger.error(f"Error procesando webhook Hikvision: {e}")
        return {"status": "ok"}

    return {"status": "ok"}


# ── WebSocket ─────────────────────────────────────────────────────────────────

@public_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = Query(None)):
    """WS con auth por query param: /ws?token=<jwt>. Token requerido en producción."""
    from ..core.security import decode_token
    from ..core.config import settings
    from jose import JWTError

    # En producción, exigir token válido
    if settings.is_production:
        if not token:
            await websocket.close(code=4401)
            return
        try:
            decode_token(token)
        except JWTError:
            await websocket.close(code=4401)
            return

    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
