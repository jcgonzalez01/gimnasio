import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine, text
from datetime import datetime

engine = create_engine('sqlite:///backend/gimnasio.db')

with engine.connect() as conn:
    r = conn.execute(text('SELECT COUNT(*) FROM access_logs'))
    print('Total logs before:', r.scalar())
    print('Last log:')
    r2 = conn.execute(text('SELECT * FROM access_logs ORDER BY id DESC LIMIT 1'))
    row = r2.fetchone()
    print(f'  id={row[0]}, member_id={row[1]}, result={row[6]}, access_type={row[5]}')
    print(f'  raw: {row[8][:200]}...' if row[8] and len(row[8]) > 200 else f'  raw: {row[8]}')

print('\nTesting direct DB insert...')
from backend.app.core.database import SessionLocal
from backend.app.models.access import AccessLog

db = SessionLocal()
log = AccessLog(
    member_id=1,
    direction='in',
    access_type='card',
    result='granted',
    raw_event='{"test": true}',
)
db.add(log)
db.commit()
print(f'Inserted log ID: {log.id}')

r = conn.execute(text('SELECT * FROM access_logs ORDER BY id DESC LIMIT 1'))
row = r.fetchone()
print(f'New last log: id={row[0]}, member_id={row[1]}, result={row[6]}, access_type={row[5]}')
db.close()