
import sys
import os

# Agregar el directorio backend al path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.hikvision import HikvisionISAPI
from app.core.database import SessionLocal
from app.models.access import HikvisionDevice

def debug():
    db = SessionLocal()
    d = db.query(HikvisionDevice).filter(HikvisionDevice.ip_address == '192.168.1.38').first()
    if not d:
        print("Device not found")
        return

    print(f"Testing device: {d.ip_address}")
    hik = HikvisionISAPI(d.ip_address, d.port, d.username, d.password)
    result = hik.open_door(door_no=1)
    print(f"Result type: {type(result)}")
    print(f"Result value: {result}")
    db.close()

if __name__ == "__main__":
    debug()
