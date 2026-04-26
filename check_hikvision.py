from sqlalchemy import create_engine, text
import json
engine = create_engine('sqlite:///backend/gimnasio.db')

with engine.connect() as conn:
    r = conn.execute(text('SELECT raw_event FROM access_logs WHERE raw_event LIKE :pattern ORDER BY id DESC LIMIT 5'), {'pattern': '%EventNotificationAlert%'})
    print('Eventos del Hikvision:')
    for i, row in enumerate(r):
        if row[0]:
            data = json.loads(row[0])
            acs = data.get('AccessControllerEvent', {})
            print(f'  Evento {i+1}:')
            print(f'    employeeNoString: {acs.get("employeeNoString")}')
            print(f'    currentVerifyMode: {acs.get("currentVerifyMode")}')
            print(f'    status: {acs.get("status")}')
            print(f'    name: {acs.get("name")}')
            print()