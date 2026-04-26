import requests
from requests.auth import HTTPDigestAuth

def delete_user_xml():
    ip = "192.168.1.36"
    user = "admin"
    pwd = "acc12345"
    employee_no = "1"
    
    auth = HTTPDigestAuth(user, pwd)
    url = f"http://{ip}/ISAPI/AccessControl/UserInfo/Delete?format=json" # El formato json se pide en la URL pero a veces el body debe ser estructurado
    
    # Intentando de nuevo con el formato JSON corregido segun documentacion estricta
    payload = {
        "UserInfoDetail": {
            "mode": "byEmployeeNo",
            "EmployeeNoList": [
                {
                    "employeeNo": employee_no
                }
            ]
        }
    }
    
    print(f"Re-intentando eliminar ID {employee_no} con JSON estructurado...")
    r = requests.put(url, auth=auth, json=payload)
    print(f"Status: {r.status_code}")
    print(r.text)

    if r.status_code != 200:
        print("\nIntentando con metodo XML...")
        url_xml = f"http://{ip}/ISAPI/AccessControl/UserInfo/Delete"
        xml_payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<UserInfoDetail version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
    <mode>byEmployeeNo</mode>
    <EmployeeNoList>
        <EmployeeNoItem>
            <employeeNo>{employee_no}</employeeNo>
        </EmployeeNoItem>
    </EmployeeNoList>
</UserInfoDetail>"""
        r2 = requests.put(url_xml, auth=auth, data=xml_payload, headers={'Content-Type': 'application/xml'})
        print(f"Status XML: {r2.status_code}")
        print(r2.text)

if __name__ == "__main__":
    delete_user_xml()
