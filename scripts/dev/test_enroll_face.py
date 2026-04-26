import requests
import json

BASE_URL = "http://localhost:8000/api/access"
MEMBER_ID = 1
DEVICE_IDS = "1" 

def test_enroll_face():
    # Probamos solo el enrolamiento facial por separado
    url = f"{BASE_URL}/enroll-face/{MEMBER_ID}"
    params = {
        "device_ids": DEVICE_IDS
    }
    
    print(f"Enrolando cara del Miembro {MEMBER_ID} en dispositivo {DEVICE_IDS}...")
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
    test_enroll_face()
