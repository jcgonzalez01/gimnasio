import requests
import json
import sys

def simulate_hikvision_webhook():
    url = "http://localhost:8000/api/access/hikvision-webhook"
    
    # Payload típico de Hikvision (JSON)
    payload = {
        "EventNotificationAlert": {
            "ipAddress": "192.168.1.38",
            "portNo": 80,
            "protocol": "HTTP",
            "macAddress": "00:00:00:00:00:00",
            "channelID": 1,
            "dateTime": "2026-04-21T10:00:00-04:00",
            "activePostCount": 1,
            "eventType": "access_control",
            "eventState": "active",
            "eventDescription": "Access Control Event",
            "AccessControllerEvent": {
                "deviceName": "acc1",
                "major": 5,
                "minor": 1,
                "time": "2026-04-21T10:00:00-04:00",
                "employeeNoString": "1",  # Suponiendo que el ID del miembro es 1
                "cardNo": "",
                "cardReaderNo": 1,
                "doorNo": 1,
                "currentVerifyMode": "face",
                "serialNo": 123,
                "type": 0,
                "mask": "no",
                "temperature": 36.5
            }
        }
    }

    print(f"Enviando simulación de webhook a {url}...")
    try:
        # Nota: La identificación por IP en el backend usa request.client.host
        # En una simulación local, la IP será 127.0.0.1
        response = requests.post(url, json=payload, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
        print("Asegúrate de que el backend esté corriendo (puerto 8000).")

if __name__ == "__main__":
    simulate_hikvision_webhook()
