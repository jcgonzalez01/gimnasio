import sqlite3
from datetime import datetime, timedelta
import os

DB_PATH = "backend/gimnasio.db"

def create_and_assign_membership():
    if not os.path.exists(DB_PATH):
        print(f"No se encuentra la DB en {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Crear el plan de entrenamiento si no existe
    plan_name = "Entrenamiento Especial"
    cursor.execute("SELECT id FROM membership_plans WHERE name = ?", (plan_name,))
    plan_row = cursor.fetchone()

    if not plan_row:
        print(f"Creando plan: {plan_name}")
        cursor.execute("""
            INSERT INTO membership_plans (name, description, duration_days, price, is_active, color)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (plan_name, "Plan de entrenamiento personalizado", 30, 1000.0, 1, "#3B82F6"))
        plan_id = cursor.lastrowid
    else:
        plan_id = plan_row[0]
        print(f"El plan {plan_name} ya existe con ID: {plan_id}")

    # 2. Asignar al miembro 5 (Juan Carlos Gonzalez)
    member_id = 5
    cursor.execute("SELECT id FROM members WHERE id = ?", (member_id,))
    if not cursor.fetchone():
        print(f"No se encontró al miembro con ID {member_id}")
        conn.close()
        return

    # Definir fechas
    start_date = datetime.now()
    end_date = start_date + timedelta(days=30)
    
    start_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
    end_str = end_date.strftime("%Y-%m-%d %H:%M:%S")

    print(f"Asignando membresía al miembro {member_id}...")
    cursor.execute("""
        INSERT INTO member_memberships (member_id, plan_id, start_date, end_date, price_paid, payment_method, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (member_id, plan_id, start_str, end_str, 1000.0, "cash", 1))

    conn.commit()
    print(f"¡Hecho! Membresía '{plan_name}' asignada correctamente.")
    print(f"Válida desde {start_str} hasta {end_str}")
    
    conn.close()

if __name__ == "__main__":
    create_and_assign_membership()
