import sqlite3
import requests
import json
import base64
import os
from requests.auth import HTTPDigestAuth

def test_direct_enroll():
    # 1. Obtener datos del miembro
    conn = sqlite3.connect("backend/gimnasio.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, first_name, last_name, photo_path FROM members WHERE id=1")
    m_id, fname, lname, ppath = cursor.fetchone()
    
    # 2. Obtener datos del dispositivo
    cursor.execute("SELECT ip_address, port, username, password FROM hikvision_devices WHERE id=1")
    ip, port, user, pwd = cursor.fetchone()
    conn.close()

    print(f"--- PASO 1: Registrando Miembro {m_id} ({fname}) en {ip} ---")
    
    # Registrar UserInfo primero
    url_user = f"http://{ip}:{port}/ISAPI/AccessControl/UserInfo/Record?format=json"
    user_payload = {
        "UserInfo": {
            "employeeNo": str(m_id),
            "name": f"{fname} {lname}"[:32],
            "userType": "normal",
            "Valid": {
                "enable": True,
                "beginTime": "2020-01-01T00:00:00",
                "endTime": "2030-12-31T23:59:59",
                "timeType": "local"
            }
        }
    }
    
    auth = HTTPDigestAuth(user, pwd)
    r1 = requests.post(url_user, auth=auth, json=user_payload, timeout=5)
    print(f"Status UserInfo: {r1.status_code}")
    if r1.status_code not in (200, 201):
        # Intentar PUT si ya existe
        url_put = f"http://{ip}:{port}/ISAPI/AccessControl/UserInfo/Modify?format=json"
        r1 = requests.put(url_put, auth=auth, json=user_payload, timeout=5)
        print(f"Status UserInfo (Modify): {r1.status_code}")

    print(f"\n--- PASO 2: Enrolando cara para ID {m_id} ---")

    # 3. Preparar imagen
    full_ppath = os.path.join("backend", ppath.lstrip("/"))
    with open(full_ppath, "rb") as f:
        img_bytes = f.read()
    
    # 4. Enrolar usando el método Multipart (FaceDataRecord)
    url_face = f"http://{ip}:{port}/ISAPI/Intelligent/FDLib/FaceDataRecord?format=json"
    meta = {
        "faceLibType": "blackFD", 
        "FDID": "1", 
        "FPID": str(m_id)
    }
    
    files = {
        'FaceDataRecord': (None, json.dumps(meta), 'application/json'),
        'img': ("face.jpg", img_bytes, 'image/jpeg')
    }
    
    try:
        r2 = requests.post(url_face, auth=auth, files=files, timeout=10)
        print(f"Status FaceData: {r2.status_code}")
        print("Response Body:")
        print(r2.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_direct_enroll()
