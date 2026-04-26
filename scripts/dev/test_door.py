
import requests
from requests.auth import HTTPDigestAuth
import sqlite3
import os

def test_door():
    db_path = r'C:\Users\jcgon\OneDrive\Documentos\gimnasio\backend\gimnasio.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT ip_address, port, username, password FROM hikvision_devices WHERE ip_address = '192.168.1.38'")
    row = cursor.fetchone()
    conn.close()

    if not row:
        print("Device not found in DB")
        return

    ip, port, user, pwd = row
    base_url = f"http://{ip}:{port}"
    auth = HTTPDigestAuth(user, pwd)
    url = f"{base_url}/ISAPI/AccessControl/RemoteControl/door/1"
    
    print(f"Testing door on {url}")

    # Method 1: Current XML (ver 2.0)
    xml_20 = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<RemoteControlDoor version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">'
        '<doorNo>1</doorNo>'
        '<cmd>open</cmd>'
        '</RemoteControlDoor>'
    )
    print("\nAttempt 1: XML ver 2.0")
    try:
        r = requests.put(url, data=xml_20, auth=auth, headers={"Content-Type": "application/xml"}, timeout=5)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

    # Method 2: JSON
    json_payload = {"RemoteControlDoor": {"cmd": "open"}}
    print("\nAttempt 2: JSON (cmd: open)")
    try:
        r = requests.put(url + "?format=json", json=json_payload, auth=auth, timeout=5)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

    # Method 3: JSON with doorNo
    json_payload_2 = {"RemoteControlDoor": {"doorNo": 1, "cmd": "open"}}
    print("\nAttempt 3: JSON (doorNo: 1, cmd: open)")
    try:
        r = requests.put(url + "?format=json", json=json_payload_2, auth=auth, timeout=5)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

    # Method 4: XML ver 1.0 (hikvision namespace)
    xml_10 = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<RemoteControlDoor version="1.0" xmlns="http://www.hikvision.com/ver10/XMLSchema">'
        '<doorNo>1</doorNo>'
        '<cmd>open</cmd>'
        '</RemoteControlDoor>'
    )
    print("\nAttempt 4: XML ver 1.0")
    try:
        r = requests.put(url, data=xml_10, auth=auth, headers={"Content-Type": "application/xml"}, timeout=5)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_door()
