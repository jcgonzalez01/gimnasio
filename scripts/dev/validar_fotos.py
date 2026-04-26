import sqlite3
import os

db_path = "backend/gimnasio.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT id, first_name, last_name, photo_path FROM members")
rows = cursor.fetchall()

print("--- VALIDACIÓN DE FOTOS ---")
for row in rows:
    m_id, fname, lname, ppath = row
    if ppath:
        # El backend usa "." + ppath relativo a la carpeta 'backend'
        full_path = os.path.join("backend", ppath.lstrip("/"))
        if os.path.exists(full_path):
            print(f"[OK] Miembro {m_id} ({fname} {lname}): {ppath}")
        else:
            print(f"[ERROR] Miembro {m_id} ({fname} {lname}): ARCHIVO NO ENCONTRADO en {full_path}")
    else:
        print(f"[INFO] Miembro {m_id} ({fname} {lname}): Sin foto")

conn.close()
