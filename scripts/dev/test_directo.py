import sqlite3
import requests
from requests.auth import HTTPDigestAuth

def check_everything():
    print("1. Verificando Miembro 1 en DB...")
    try:
        conn = sqlite3.connect("backend/gimnasio.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, first_name, photo_path FROM members WHERE id=1")
        row = cursor.fetchone()
        print(f"   Miembro: {row}")
        conn.close()
    except Exception as e:
        print(f"   Error DB: {e}")

    print("\n2. Verificando Dispositivo 1 en DB...")
    try:
        conn = sqlite3.connect("backend/gimnasio.db")
        cursor = conn.cursor()
        # Intentando con el nombre correcto de la tabla según los modelos
        cursor.execute("SELECT ip_address, port, username, password FROM hikvision_devices WHERE id=1")
        dev = cursor.fetchone()
        if dev:
            print(f"   Dispositivo: {dev[0]}:{dev[1]} (user: {dev[2]})")
            ip, port, user, pwd = dev
            print(f"\n3. Probando conexión directa al dispositivo {ip}...")
            url = f"http://{ip}:{port}/ISAPI/System/deviceInfo?format=json"
            r = requests.get(url, auth=HTTPDigestAuth(user, pwd), timeout=5)
            print(f"   Status Code: {r.status_code}")
            if r.status_code == 200:
                print("   ¡Conexión exitosa al dispositivo!")
            else:
                print(f"   Fallo: {r.text[:200]}")
        else:
            print("   No se encontró el dispositivo ID 1")
        conn.close()
    except Exception as e:
        print(f"   Error Dispositivo: {e}")

if __name__ == "__main__":
    check_everything()
