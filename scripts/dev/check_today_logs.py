import os
from sqlalchemy import create_engine, text
from datetime import datetime

base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "backend", "gimnasio.db")
DB_URL = f"sqlite:///{db_path}"

def check_today_logs():
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        print("--- EVENTOS DEL DÍA 21 DE ABRIL (TODOS) ---")
        # Buscamos por el string de la fecha para evitar problemas de tipos
        query = text("""
            SELECT id, member_id, direction, result, timestamp 
            FROM access_logs 
            WHERE timestamp LIKE '2026-04-21%'
            ORDER BY timestamp DESC
        """)
        rows = conn.execute(query).fetchall()
        print(f"Total encontrados: {len(rows)}")
        for row in rows:
            print(row)

if __name__ == "__main__":
    check_today_logs()
