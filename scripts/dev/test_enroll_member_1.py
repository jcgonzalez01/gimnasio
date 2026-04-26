import requests
import json

BASE_URL = "http://localhost:8000/api/access"
MEMBER_ID = 1
DEVICE_IDS = "1" 

def test_enroll():
    url = f"{BASE_URL}/register-and-enroll/{MEMBER_ID}"
    params = {
        "device_ids": DEVICE_IDS
    }
    
    print(f"Enviando Miembro {MEMBER_ID} al dispositivo {DEVICE_IDS}...")
    try:
        response = requests.post(url, params=params)
        print(f"Status Code: {response.status_code}")
        try:
            print("Response JSON:")
            print(json.dumps(response.json(), indent=2))
        except:
            print("Response Text (not JSON):")
            print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_enroll()
