import os
from sqlalchemy import create_engine, text

# URL de la base de datos con ruta absoluta
base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "backend", "gimnasio.db")
DB_URL = f"sqlite:///{db_path}"

def delete_events():
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        # Primero listamos para confirmar lo que vamos a borrar
        query_find = text("""
            SELECT id, member_id, direction, result, timestamp 
            FROM access_logs 
            WHERE timestamp >= '2026-04-21 04:00:00' 
              AND timestamp <= '2026-04-21 04:59:59'
        """)
        
        print("--- EVENTOS ENCONTRADOS PARA EL 21 DE ABRIL A LAS 4:00 AM ---")
        rows = conn.execute(query_find).fetchall()
        ids_to_delete = [row[0] for row in rows]
        
        for row in rows:
            print(row)
            
        if not ids_to_delete:
            print("No se encontraron eventos en ese horario.")
            return

        # Procedemos a borrar
        print(f"\nBorrando {len(ids_to_delete)} eventos...")
        delete_query = text(f"DELETE FROM access_logs WHERE id IN ({','.join(map(str, ids_to_delete))})")
        conn.execute(delete_query)
        conn.commit()
        print("Eliminación completada con éxito.")

if __name__ == "__main__":
    delete_events()
