from sqlalchemy import create_engine, text
engine = create_engine('sqlite:///backend/gimnasio.db')

with engine.connect() as conn:
    r = conn.execute(text('SELECT COUNT(*) FROM access_logs'))
    print('Total eventos:', r.scalar())

    r2 = conn.execute(text('SELECT * FROM access_logs ORDER BY id DESC LIMIT 3'))
    print('Ultimos eventos:')
    for row in r2:
        print(f'  ID={row[0]}, member_id={row[1]}, result={row[6]}, type={row[5]}')

    # Verificar si el enroll funciono
    r3 = conn.execute(text('SELECT face_enrolled FROM members WHERE id = 1'))
    row3 = r3.fetchone()
    print(f'Miembro 1 face_enrolled: {row3[0]}')