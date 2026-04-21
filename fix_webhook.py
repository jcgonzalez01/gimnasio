import requests
from requests.auth import HTTPDigestAuth

def fix_webhook_communication():
    # Datos del dispositivo según tus logs
    device_ip = "192.168.1.38"
    pc_ip = "192.168.1.10"
    auth = HTTPDigestAuth('admin', 'acc12345')
    
    print(f"--- FORZANDO APERTURA DE COMUNICACIÓN WEBHOOK ---")
    
    # 1. Configuración del Host con parámetros de compatibilidad total
    url_host = f'http://{device_ip}:80/ISAPI/Event/notification/httpHosts'
    
    # Forzamos XML para la configuración inicial pero pedimos JSON para los eventos
    # Importante: incluimos <httpAuthenticationMethod> para que no intente usar contraseñas raras
    body = f"""<?xml version="1.0" encoding="UTF-8"?>
<HttpHostNotificationList version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
    <HttpHostNotification>
        <id>1</id>
        <url>http://{pc_ip}:8000/api/access/hikvision-webhook</url>
        <protocolType>HTTP</protocolType>
        <parameterFormatType>json</parameterFormatType>
        <addressingFormatType>ipaddress</addressingFormatType>
        <ipAddress>{pc_ip}</ipAddress>
        <portNo>8000</portNo>
        <httpAuthenticationMethod>none</httpAuthenticationMethod>
        <SubscribeEvent>
            <heartbeat>30</heartbeat>
            <eventMode>all</eventMode>
            <EventList>
                <Event>
                    <type>AccessControllerEvent</type>
                </Event>
            </EventList>
        </SubscribeEvent>
    </HttpHostNotification>
</HttpHostNotificationList>"""

    try:
        print(f"Configurando PC {pc_ip} como destino de eventos...")
        r = requests.put(url_host, auth=auth, data=body, headers={'Content-Type': 'application/xml'}, timeout=10)
        print(f"Resultado Configuración: {r.status_code}")
        
        # 2. ACTIVAR el servicio de eventos (fundamental)
        # Algunos dispositivos requieren activar el 'event upload' globalmente
        url_service = f'http://{device_ip}:80/ISAPI/Event/notification/httpHosts/1/activate'
        r_act = requests.put(url_service, auth=auth, timeout=5)
        print(f"Activación de canal: {r_act.status_code}")

        # 3. VERIFICAR si el dispositivo realmente nos ve
        r_verify = requests.get(url_host, auth=auth, timeout=5)
        if pc_ip in r_verify.text:
            print("\n✅ ÉXITO: El dispositivo tiene tu IP grabada correctamente.")
            print("👉 POR FAVOR: Escanea tu cara ahora y mira la consola negra.")
        else:
            print("\n❌ ERROR: El dispositivo no guardó la IP. Revisa si hay un firewall en tu PC.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_webhook_communication()
