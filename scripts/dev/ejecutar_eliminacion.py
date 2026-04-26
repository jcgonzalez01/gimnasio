import sqlite3
import requests
from requests.auth import HTTPDigestAuth
import json

def delete_member_1():
    db_path = "backend/gimnasio.db"
    
    # 1. Obtener datos del dispositivo
    print("Obteniendo datos del dispositivo...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT ip_address, port, username, password FROM hikvision_devices WHERE id=1")
    dev = cursor.fetchone()
    
    if dev:
        ip, port, user, pwd = dev
        auth = HTTPDigestAuth(user, pwd)
        
        print(f"Eliminando ID 1 del dispositivo {ip}...")
        
        # Eliminar cara primero (opcional, pero recomendado)
        url_face = f"http://{ip}:{port}/ISAPI/Intelligent/FDLib/FDSearch/Delete?format=json&FDID=1&faceLibType=blackFD"
        payload_face = {
            "FaceDataDeleteCond": {
                "searchID": "1",
                "FPID": [{"value": "1"}]
            }
        }
        try:
            r_face = requests.put(url_face, auth=auth, json=payload_face, timeout=5)
            print(f"   Status Delete Face: {r_face.status_code}")
        except:
            print("   Error eliminando cara")

        # Eliminar Usuario
        url_user = f"http://{ip}:{port}/ISAPI/AccessControl/UserInfo/Delete?format=json"
        payload_user = {
            "UserInfoDetail": {
                "mode": "byEmployeeNo",
                "EmployeeNoList": [{"employeeNo": "1"}]
            }
        }
        try:
            r_user = requests.put(url_user, auth=auth, json=payload_user, timeout=5)
            print(f"   Status Delete User: {r_user.status_code}")
        except:
            print("   Error eliminando usuario")
    
    print("\nEliminando Miembro 1 de la Base de Datos...")
    try:
        # Desactivar restricciones de FK temporalmente si es necesario, 
        # pero SQLite suele manejarlo si está configurado.
        cursor.execute("DELETE FROM member_memberships WHERE member_id = 1")
        cursor.execute("DELETE FROM access_logs WHERE member_id = 1")
        cursor.execute("DELETE FROM members WHERE id = 1")
        conn.commit()
        print("   ¡Miembro 1 y sus datos relacionados eliminados con éxito!")
    except Exception as e:
        print(f"   Error DB: {e}")
        conn.rollback()
    
    conn.close()

if __name__ == "__main__":
    delete_member_1()
