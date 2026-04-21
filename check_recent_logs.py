import os
from sqlalchemy import create_engine, text

base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "backend", "gimnasio.db")
DB_URL = f"sqlite:///{db_path}"

def check_recent_logs():
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        print("--- ÚLTIMOS 10 EVENTOS ---")
        query = text("SELECT id, timestamp, member_id FROM access_logs ORDER BY timestamp DESC LIMIT 10")
        rows = conn.execute(query).fetchall()
        for row in rows:
            print(row)

if __name__ == "__main__":
    check_recent_logs()
