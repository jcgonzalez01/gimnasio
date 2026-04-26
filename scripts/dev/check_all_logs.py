import os
from sqlalchemy import create_engine, text

base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "backend", "gimnasio.db")
DB_URL = f"sqlite:///{db_path}"

def check_all_logs():
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        print("--- TODOS LOS REGISTROS EN LA DB ---")
        query = text("SELECT id, timestamp, member_id, result FROM access_logs ORDER BY timestamp DESC")
        rows = conn.execute(query).fetchall()
        for row in rows:
            print(row)

if __name__ == "__main__":
    check_all_logs()
