import sqlite3
try:
    conn = sqlite3.connect('backend/gimnasio.db')
    cur = conn.cursor()
    query = """
    SELECT 
        al.id, 
        IFNULL(m.first_name || ' ' || m.last_name, 'Desconocido') as nombre, 
        al.timestamp, 
        al.result, 
        al.access_type 
    FROM access_logs al 
    LEFT JOIN members m ON al.member_id = m.id 
    ORDER BY al.id DESC 
    LIMIT 20
    """
    rows = cur.execute(query).fetchall()
    print("-" * 100)
    print(f"{'ID':<5} | {'Miembro':<25} | {'Fecha/Hora':<20} | {'Resultado':<10} | {'Tipo':<10}")
    print("-" * 100)
    for r in rows:
        print(f"{r[0]:<5} | {r[1]:<25} | {r[2]:<20} | {r[3]:<10} | {r[4]:<10}")
    print("-" * 100)
    conn.close()
except Exception as e:
    print(f"Error: {e}")
