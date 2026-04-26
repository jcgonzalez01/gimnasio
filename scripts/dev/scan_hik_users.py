import sqlite3, requests, json
from requests.auth import HTTPDigestAuth

# Configuración desde BD
conn = sqlite3.connect('backend/gimnasio.db')
cur = conn.cursor()
cur.execute("SELECT ip_address, port, username, password FROM hikvision_devices WHERE is_active = 1 LIMIT 1")
row = cur.fetchone()
conn.close()

if not row:
    print("No hay dispositivos activos.")
    exit()

ip, port, user, pwd = row
url = f"http://{ip}:{port}/ISAPI/AccessControl/UserInfo/Search?format=json"

payload = {
    "UserInfoSearchCond": {
        "searchID": "diag_users",
        "searchResultPosition": 0,
        "maxResults": 50
    }
}

print(f"--- Listando usuarios en terminal Hikvision ({ip}) ---")
try:
    r = requests.post(url, json=payload, auth=HTTPDigestAuth(user, pwd), timeout=15)
    if r.status_code == 200:
        data = r.json()
        users = data.get("UserInfoSearch", {}).get("UserInfo", [])
        if not users:
            print("No se encontraron usuarios en el terminal.")
        else:
            print(f"{'ID':<10} | {'Nombre':<25} | {'Tipo':<10}")
            print("-" * 50)
            for u in users:
                print(f"{u.get('employeeNo', 'N/A'):<10} | {u.get('name', 'N/A'):<25} | {u.get('userType', 'N/A'):<10}")
    else:
        print(f"Error del dispositivo: {r.status_code}")
        print(r.text)
except Exception as e:
    print(f"Error de conexión: {e}")
