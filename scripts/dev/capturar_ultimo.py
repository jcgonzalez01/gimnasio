import requests, sqlite3, os
from requests.auth import HTTPDigestAuth
from datetime import datetime

def capturar_ultimo():
    # 1. Obtener datos del dispositivo activo
    db_path = "backend/gimnasio.db"
    if not os.path.exists(db_path):
        print("Error: No se encuentra la base de datos.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT ip_address, port, username, password, name FROM hikvision_devices WHERE is_active = 1 LIMIT 1")
    dev = cursor.fetchone()
    conn.close()

    if not dev:
        print("Error: No hay dispositivos activos configurados en el sistema.")
        return

    ip, port, user, pwd, name = dev
    auth = HTTPDigestAuth(user, pwd)

    print(f"Conectando a {name} ({ip})...")

    # 2. Consultar el último evento para saber quién fue el último
    try:
        payload = {
            "AcsEventCond": {
                "searchID": "last_capture",
                "searchResultPosition": 0,
                "maxResults": 1,
                "major": 0,
                "minor": 0
            }
        }
        r_ev = requests.post(f"http://{ip}:{port}/ISAPI/AccessControl/AcsEvent?format=json", 
                             json=payload, auth=auth, timeout=5)
        
        last_user = "Desconocido"
        if r_ev.status_code == 200:
            events = r_ev.json().get("AcsEvent", {}).get("InfoList", [])
            if events:
                last_user = events[0].get("employeeNoString", "N/A")
                print(f"Último usuario detectado: {last_user}")
        
        # 3. Tomar la foto ahora mismo
        print("Tomando captura de la cámara...")
        url_snap = f"http://{ip}:{port}/ISAPI/Streaming/channels/1/picture"
        r_snap = requests.get(url_snap, auth=auth, timeout=10)

        if r_snap.status_code == 200:
            os.makedirs("capturas_manuales", exist_ok=True)
            filename = f"capturas_manuales/ultimo_acceso_{last_user}_{datetime.now().strftime('%H%M%S')}.jpg"
            with open(filename, "wb") as f:
                f.write(r_snap.content)
            print(f"\n✅ ¡ÉXITO!")
            print(f"Foto guardada como: {filename}")
            print(f"Usuario asociado al evento: {last_user}")
        else:
            print(f"❌ No se pudo tomar la foto. El dispositivo respondió: {r_snap.status_code}")

    except Exception as e:
        print(f"❌ Error durante la operación: {e}")

if __name__ == "__main__":
    capturar_ultimo()
