import requests
from requests.auth import HTTPDigestAuth

def delete_final_try():
    ip = "192.168.1.36"
    user = "admin"
    pwd = "acc12345"
    employee_no = "1"
    auth = HTTPDigestAuth(user, pwd)
    
    # Variante 3: UserInfoDetail/Delete (usada en modelos K1T)
    url = f"http://{ip}/ISAPI/AccessControl/UserInfoDetail/Delete?format=json"
    payload = {
        "UserInfoDetail": {
            "mode": "byEmployeeNo",
            "EmployeeNoList": [{"employeeNo": employee_no}]
        }
    }
    
    print("Intentando variante UserInfoDetail/Delete...")
    r = requests.put(url, auth=auth, json=payload)
    print(f"Status: {r.status_code}")
    print(r.text)

    # Variante 4: Busqueda primero para ver si existe
    print("\nVerificando si el usuario 1 existe en el dispositivo...")
    url_search = f"http://{ip}/ISAPI/AccessControl/UserInfo/Search?format=json"
    search_payload = {
        "UserInfoSearchCond": {
            "searchID": "1",
            "searchResultPosition": 0,
            "maxResults": 1,
            "EmployeeNoList": [{"employeeNo": employee_no}]
        }
    }
    r_search = requests.post(url_search, auth=auth, json=search_payload)
    print(f"Resultado busqueda: {r_search.status_code}")
    print(r_search.text)

if __name__ == "__main__":
    delete_final_try()
