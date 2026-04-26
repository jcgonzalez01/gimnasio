import requests
from requests.auth import HTTPDigestAuth
import json

def delete_from_hikvision():
    ip = "192.168.1.36"
    port = 80
    user = "admin"
    pwd = "acc12345"
    employee_no = "1"
    
    auth = HTTPDigestAuth(user, pwd)
    
    print(f"Intentando eliminar ID {employee_no} de {ip}...")

    # 1. Eliminar Cara
    url_face = f"http://{ip}:{port}/ISAPI/Intelligent/FDLib/FDSearch/Delete?format=json&FDID=1&faceLibType=blackFD"
    payload_face = {
        "FaceDataDeleteCond": {
            "searchID": "1",
            "FPID": [{"value": employee_no}]
        }
    }
    try:
        r_face = requests.put(url_face, auth=auth, json=payload_face, timeout=10)
        print(f"Resultado eliminar cara: {r_face.status_code}")
        print(r_face.text)
    except Exception as e:
        print(f"Error al eliminar cara: {e}")

    # 2. Eliminar Usuario
    url_user = f"http://{ip}:{port}/ISAPI/AccessControl/UserInfo/Delete?format=json"
    payload_user = {
        "UserInfoDetail": {
            "mode": "byEmployeeNo",
            "EmployeeNoList": [{"employeeNo": employee_no}]
        }
    }
    try:
        r_user = requests.put(url_user, auth=auth, json=payload_user, timeout=10)
        print(f"\nResultado eliminar usuario: {r_user.status_code}")
        print(r_user.text)
    except Exception as e:
        print(f"Error al eliminar usuario: {e}")

if __name__ == "__main__":
    delete_from_hikvision()
