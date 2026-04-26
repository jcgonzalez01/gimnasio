import os
from sqlalchemy import create_engine, text

base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "backend", "gimnasio.db")
DB_URL = f"sqlite:///{db_path}"

def get_creds():
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT username, password FROM hikvision_devices WHERE id=2")).fetchone()
        print(f"USER: {res[0]}, PASS: {res[1]}")

if __name__ == "__main__":
    get_creds()
