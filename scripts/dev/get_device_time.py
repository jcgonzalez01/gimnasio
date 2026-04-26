import os
import requests
from requests.auth import HTTPDigestAuth
from sqlalchemy import create_engine, text
import xml.etree.ElementTree as ET

# Configuración de DB
base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "backend", "gimnasio.db")
DB_URL = f"sqlite:///{db_path}"

def get_device_time():
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        device = conn.execute(text("SELECT ip_address, port, username, password, name FROM hikvision_devices WHERE is_active = 1")).fetchone()
        if not device:
            print("No hay dispositivos activos.")
            return

        print(f"Consultando fecha/hora de: {device.name} ({device.ip_address})")
        base_url = f"http://{device.ip_address}:{device.port}"
        auth = HTTPDigestAuth(device.username, device.password)
        
        try:
            # Endpoint ISAPI para tiempo del sistema
            r = requests.get(f"{base_url}/ISAPI/System/time", auth=auth, timeout=10)
            if r.status_code == 200:
                # El resultado suele ser un XML
                root = ET.fromstring(r.text)
                # Namespace común
                ns = {'ns': 'http://www.isapi.org/ver20/XMLSchema'}
                local_time = root.find('.//ns:localTime', ns)
                if local_time is not None:
                    print(f"\nFecha y Hora del Dispositivo: {local_time.text}")
                else:
                    # Intentar sin namespace
                    local_time = root.find('.//localTime')
                    print(f"\nFecha y Hora del Dispositivo: {local_time.text if local_time is not None else r.text}")
            else:
                print(f"Error al consultar el dispositivo: {r.status_code}")
                print(r.text)
        except Exception as e:
            print(f"Excepción: {e}")

if __name__ == "__main__":
    get_device_time()
