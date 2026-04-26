import sqlite3, requests
from requests.auth import HTTPDigestAuth

conn = sqlite3.connect('backend/gimnasio.db')
cur = conn.cursor()
cur.execute("SELECT ip_address, port, username, password FROM hikvision_devices WHERE is_active = 1 LIMIT 1")
row = cur.fetchone()
conn.close()

if not row: exit()
ip, port, user, pwd = row

# Endpoint para borrar logs en Hikvision ISAPI
url = f"http://{ip}:{port}/ISAPI/AccessControl/AcsEvent/Delete"

print(f"Limpiando memoria de eventos en {ip}...")
try:
    # Algunos modelos usan DELETE, otros PUT con XML
    r = requests.put(url, auth=HTTPDigestAuth(user, pwd), timeout=10)
    print("Status:", r.status_code)
    print("Respuesta:", r.text)
    
    # Intentar también con el método alternativo si falla
    if r.status_code != 200:
        url_alt = f"http://{ip}:{port}/ISAPI/ContentMgmt/log/search/delete"
        r2 = requests.put(url_alt, auth=HTTPDigestAuth(user, pwd), timeout=10)
        print("Metodo alternativo:", r2.status_code)

except Exception as e:
    print("Error:", e)
