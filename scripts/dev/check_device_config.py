import sqlite3, requests
from requests.auth import HTTPDigestAuth
import xml.etree.ElementTree as ET

conn = sqlite3.connect('backend/gimnasio.db')
cur = conn.cursor()
cur.execute("SELECT ip_address, port, username, password FROM hikvision_devices WHERE is_active = 1 LIMIT 1")
row = cur.fetchone()
conn.close()

if not row:
    print("No hay dispositivos activos en la BD.")
    exit()

ip, port, user, pwd = row
url = f"http://{ip}:{port}/ISAPI/Event/notification/httpHosts"

try:
    r = requests.get(url, auth=HTTPDigestAuth(user, pwd), timeout=10)
    print(f"--- Configuración actual en dispositivo {ip} ---")
    print(r.text)
except Exception as e:
    print(f"Error al conectar con el dispositivo: {e}")
