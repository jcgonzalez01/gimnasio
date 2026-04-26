from sqlalchemy import create_engine, text
import json
engine = create_engine('sqlite:///backend/gimnasio.db')

with engine.connect() as conn:
    r = conn.execute(text('SELECT raw_event FROM access_logs ORDER BY id DESC LIMIT 1'))
    row = r.fetchone()
    if row and row[0]:
        data = json.loads(row[0])
        acs = data.get('AccessControllerEvent', {})
        print('Ultimo evento:')
        print('  employeeNoString:', acs.get('employeeNoString'))
        print('  currentVerifyMode:', acs.get('currentVerifyMode'))
        print('  status:', acs.get('status'))
        print('  name:', acs.get('name'))
        print('  major:', acs.get('major'))
        print('  minor:', acs.get('minor'))