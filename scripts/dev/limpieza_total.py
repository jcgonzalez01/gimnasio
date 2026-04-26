import sqlite3

def final_cleanup():
    db_path = "backend/gimnasio.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Limpiando tablas adicionales...")
    try:
        # En ventas (sales), ponemos el member_id a NULL en lugar de borrar la venta 
        # para no alterar la contabilidad del gimnasio.
        cursor.execute("UPDATE sales SET member_id = NULL WHERE member_id = 1")
        
        # Por si quedaron logs sin borrar
        cursor.execute("DELETE FROM access_logs WHERE member_id = 1")
        cursor.execute("DELETE FROM member_memberships WHERE member_id = 1")
        cursor.execute("DELETE FROM members WHERE id = 1")
        
        conn.commit()
        print("   ¡Limpieza de base de datos completada!")
    except Exception as e:
        print(f"   Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    final_cleanup()
