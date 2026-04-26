
import requests

def test_api():
    # URL del backend (asumiendo que corre en localhost:8000 o similar)
    # Segun Layout.tsx, intenta usar el host actual.
    url = "http://localhost:8000/api/access/devices/2/open-door"
    try:
        r = requests.post(url)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
