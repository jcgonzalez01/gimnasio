import os
from sqlalchemy import create_engine, text
from datetime import datetime

# URL de la base de datos con ruta absoluta
base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "backend", "gimnasio.db")

print(f"Usando DB en: {db_path}")
DB_URL = f"sqlite:///{db_path}"

def check_db():
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        print("\n--- DISPOSITIVOS ACTIVOS ---")
        try:
            result = conn.execute(text("SELECT id, name, ip_address, is_active FROM hikvision_devices WHERE is_active = 1"))
            for row in result:
                print(row)
        except Exception as e:
            print(f"Error consultando dispositivos: {e}")
            
        print("\n--- ÚLTIMOS 10 REGISTROS DE ACCESO ---")
        try:
            result = conn.execute(text("SELECT id, member_id, direction, result, timestamp FROM access_logs ORDER BY timestamp DESC LIMIT 10"))
            for row in result:
                print(row)
        except Exception as e:
            print(f"Error consultando logs: {e}")
            
        print("\n--- REGISTROS DE HOY ---")
        try:
            # En SQLite date('now') usa UTC. Si la zona horaria es distinta, usaremos un string directo.
            today = datetime.now().strftime('%Y-%m-%d')
            result = conn.execute(text(f"SELECT COUNT(*) FROM access_logs WHERE timestamp >= '{today}'"))
            print(f"Total hoy: {result.scalar()}")
        except Exception as e:
            print(f"Error consultando hoy: {e}")

if __name__ == "__main__":
    check_db()
