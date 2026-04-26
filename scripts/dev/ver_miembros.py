import sqlite3
import os

db_path = "backend/gimnasio.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- MIEMBROS ACTUALES EN DB ---")
cursor.execute("SELECT id, first_name, last_name FROM members")
rows = cursor.fetchall()
for row in rows:
    print(row)

conn.close()
