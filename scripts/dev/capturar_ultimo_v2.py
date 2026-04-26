import requests, sqlite3, os
from requests.auth import HTTPDigestAuth
from datetime import datetime

def capturar_ultimo_v2():
    db_path = "backend/gimnasio.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT ip_address, port, username, password FROM hikvision_devices WHERE is_active = 1 LIMIT 1")
    dev = cursor.fetchone()
    conn.close()

    if not dev: return
    ip, port, user, pwd = dev
    auth = HTTPDigestAuth(user, pwd)

    # Rutas comunes para snapshots en Hikvision
    rutas = [
        f"http://{ip}:{port}/ISAPI/Streaming/channels/1/picture",
        f"http://{ip}:{port}/ISAPI/Streaming/channels/101/picture",
        f"http://{ip}:{port}/ISAPI/Streaming/channels/1/snapshot",
        f"http://{ip}:{port}/ISAPI/ContentMgmt/StreamingProxy/channels/1/picture"
    ]

    for url in rutas:
        print(f"Probando: {url}...")
        try:
            r = requests.get(url, auth=auth, timeout=5)
            if r.status_code == 200:
                os.makedirs("capturas_manuales", exist_ok=True)
                filename = f"capturas_manuales/snapshot_ok_{datetime.now().strftime('%H%M%S')}.jpg"
                with open(filename, "wb") as f:
                    f.write(r.content)
                print(f"✅ ¡Captura lograda con éxito en {url}!")
                print(f"Archivo: {filename}")
                return
            else:
                print(f"  Fallo ({r.status_code})")
        except:
            print("  Error de conexión")

    print("\n❌ No se pudo encontrar una ruta de imagen válida para este dispositivo.")

if __name__ == "__main__":
    capturar_ultimo_v2()
