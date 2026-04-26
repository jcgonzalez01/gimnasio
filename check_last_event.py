from sqlalchemy import create_engine, text
engine = create_engine('sqlite:///backend/gimnasio.db')
with engine.connect() as conn:
    r = conn.execute(text('SELECT * FROM members WHERE hikvision_card_no = :card'), {"card": "1"})
    row = r.fetchone()
    print('Miembro con hikvision_card_no=1:', row)

    r2 = conn.execute(text('SELECT * FROM access_logs ORDER BY id DESC LIMIT 1'))
    row2 = r2.fetchone()
    print('Ultimo log:', row2)