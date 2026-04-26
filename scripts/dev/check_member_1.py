import sqlite3
import os

db_path = "backend/gimnasio.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- MIEMBROS ---")
cursor.execute("SELECT id, first_name, last_name FROM members WHERE id=1")
print(cursor.fetchone())

print("\n--- MEMBRESÍAS DEL ID 1 ---")
cursor.execute("SELECT id, plan_id, end_date, is_active FROM member_memberships WHERE member_id=1")
print(cursor.fetchall())

conn.close()
