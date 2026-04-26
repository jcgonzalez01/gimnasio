import sqlite3
import time
import os
from datetime import datetime

DB_PATH = 'backend/gimnasio.db'

def get_last_logs(last_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        # Traer eventos nuevos desde el último ID visto
        cur.execute("""
            SELECT al.id, m.first_name, m.last_name, al.timestamp, al.result, al.access_type
            FROM access_logs al
            LEFT JOIN members m ON al.member_id = m.id
            WHERE al.id > ?
            ORDER BY al.id ASC
        """, (last_id,))
        rows = cur.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"Error leyendo DB: {e}")
        return []

def main():
    print("=" * 60)
    print("   🖥️  MONITOR DE EVENTOS DEL SERVIDOR (LIVE)  ")
    print("=" * 60)
    print(f"Vigilando: {os.path.abspath(DB_PATH)}")
    print("Esperando nuevos registros...\n")

    # Inicializar con el ID más alto actual
    try:
        conn = sqlite3.connect(DB_PATH)
        last_id = conn.execute("SELECT MAX(id) FROM access_logs").fetchone()[0] or 0
        conn.close()
    except:
        last_id = 0

    while True:
        new_logs = get_last_logs(last_id)
        for log in new_logs:
            id_val, fname, lname, ts, result, a_type = log
            name = f"{fname} {lname}" if fname else "Desconocido/Extraño"
            status = "✅ CONCEDIDO" if result == 'granted' else "❌ DENEGADO"
            
            print(f"[{ts}] {status} | {name:<25} | Tipo: {a_type}")
            last_id = id_val
        
        time.sleep(1)

if __name__ == "__main__":
    main()
