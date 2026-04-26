const express = require('express');
const Database = require('better-sqlite3');
const path = require('path');
const app = express();
const PORT = 8001;

const DB_PATH = path.join(__dirname, 'backend', 'gimnasio.db');

let db;

function initDatabase() {
  try {
    db = new Database(DB_PATH);
    console.log('Base de datos conectada:', DB_PATH);
    
    db.exec(`
      CREATE TABLE IF NOT EXISTS access_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        device_id INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        direction TEXT DEFAULT 'in',
        access_type TEXT DEFAULT 'face',
        result TEXT DEFAULT 'unknown',
        temperature REAL,
        raw_event TEXT,
        notes TEXT
      )
    `);
    
    console.log('Tabla access_logs verificada');
    return true;
  } catch (e) {
    console.error('Error inicializando BD:', e.message);
    return false;
  }
}

app.use(express.json({ type: 'application/json' }));
app.use(express.text({ type: 'application/xml' }));
app.use(express.raw({ type: 'application/xml' }));

const { getEventDescription } = require('./accessControlEvents');

const ACCESS_TYPE_MAP = {
  'face': 'face',
  'card': 'card',
  'fingerprint': 'fingerprint',
  'pin': 'pin',
  'password': 'pin',
  'faceandcard': 'face+card',
  'cardandface': 'face+card',
  'cardorfaceorfp': 'face+card',
  'faceorcard': 'face+card',
  'invalid': 'unknown',
  '': 'unknown'
};

function getAccessType(verifyMode) {
  if (!verifyMode) return 'unknown';
  return ACCESS_TYPE_MAP[verifyMode.toLowerCase()] || 'unknown';
}

function determineResult(major, minor, status) {
  // Basado en la lógica unificada de la reestructuración
  if (status === 'success' || status === 'OK') return 'granted';
  if (major === 5 && [1, 4, 38, 75, 104].includes(minor)) return 'granted';
  if (major === 3 && minor === 1) return 'granted';
  return 'denied';
}

function findMember(employeeNo) {
  if (!employeeNo || !db) return null;
  
  try {
    const member = db.prepare(`
      SELECT id, first_name, last_name, member_number 
      FROM members 
      WHERE hikvision_card_no = ? OR member_number = ? OR id = ?
      LIMIT 1
    `).get(employeeNo.toString(), employeeNo.toString(), employeeNo);
    
    return member;
  } catch (e) {
    console.error('Error buscando miembro:', e.message);
    return null;
  }
}

function saveAccessLog(data) {
  if (!db) return null;

  try {
    const stmt = db.prepare(`
      INSERT INTO access_logs (member_id, direction, access_type, result, temperature, raw_event, notes, timestamp)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `);

    const result = stmt.run(
      data.member_id,
      data.direction || 'in',
      data.access_type,
      data.result,
      data.temperature,
      data.raw_event,
      data.notes,
      data.timestamp || new Date().toISOString()
    );

    return result.lastInsertRowid;
  } catch (e) {
    console.error('Error guardando log:', e.message);
    return null;
  }
}
function parseHikvisionEvent(body) {
  let eventData = {};
  
  try {
    if (typeof body === 'string') {
      if (body.includes('EventNotificationAlert') || body.includes('AccessControllerEvent')) {
        const employeeMatch = body.match(/employeeNoString>(\d+)</);
        const majorMatch = body.match(/<major>(\d+)</);
        const minorMatch = body.match(/<minor>(\d+)</);
        const modeMatch = body.match(/currentVerifyMode>([^<]+)</);
        const statusMatch = body.match(/status>([^<]+)</);
        const timeMatch = body.match(/<time>([^<]+)/);
        const nameMatch = body.match(/<name>([^<]+)/);
        
        eventData = {
          employeeNoString: employeeMatch ? employeeMatch[1] : null,
          major: majorMatch ? parseInt(majorMatch[1]) : null,
          minor: minorMatch ? parseInt(minorMatch[1]) : null,
          currentVerifyMode: modeMatch ? modeMatch[1] : null,
          status: statusMatch ? statusMatch[1] : null,
          time: timeMatch ? timeMatch[1] : null,
          name: nameMatch ? nameMatch[1] : null
        };
      } else {
        eventData = JSON.parse(body);
      }
    } else if (typeof body === 'object') {
      eventData = body;
    }
  } catch (e) {
    console.error('Error parseando evento:', e.message);
  }
  
  return eventData;
}

app.post('/api/access/hikvision-webhook', (req, res) => {
  const rawBody = req.body;
  const clientIP = req.ip || req.connection?.remoteAddress || 'unknown';
  
  console.log(`\n=== Evento de ${clientIP} ===`);
  
  const event = parseHikvisionEvent(rawBody);
  const acs = event.EventNotificationAlert?.AccessControllerEvent || event;
  
  const employeeNo = acs.employeeNoString || acs.employeeNo;
  const major = acs.major || 0;
  const minor = acs.minor || 0;
  const verifyMode = acs.currentVerifyMode || 'unknown';
  const status = acs.status || 'unknown';
  const name = acs.name || 'N/A';
  
  const result = determineResult(major, minor, status);
  const description = getEventDescription(major, minor);
  const accessType = getAccessType(verifyMode);
  const member = findMember(employeeNo);
  const memberId = member ? member.id : null;
  const memberName = member ? `${member.first_name} ${member.last_name}` : name;

  const rawEvent = JSON.stringify(event);

  const logId = saveAccessLog({
    member_id: memberId,
    direction: 'in',
    access_type: accessType,
    result: result,
    temperature: acs.temperature || null,
    raw_event: rawEvent,
    notes: description,
    timestamp: acs.time
  });
  console.log('\n--- Resultado ---');
  console.log(`Empleado: ${employeeNo || 'N/A'}`);
  console.log(`Miembro: ${memberName}`);
  console.log(`Miembro ID: ${memberId}`);
  console.log(`Major: ${major}, Minor: ${minor}`);
  console.log(`Modo: ${verifyMode}`);
  console.log(`Resultado: ${result}`);
  console.log(`Tipo: ${accessType}`);
  console.log(`Log ID: ${logId}`);
  
  if (result === 'granted') {
    console.log(`\n✅ ACCESO CONCEDIDO - ${memberName}`);
  } else {
    console.log(`\n❌ ACCESO DENEGADO - ${memberName}`);
  }
  
  res.status(200).json({ 
    status: 'ok', 
    received: true,
    log_id: logId,
    member_id: memberId,
    member_name: memberName,
    result: result
  });
});

app.get('/api/access/logs', (req, res) => {
  const limit = parseInt(req.query.limit) || 50;
  const offset = parseInt(req.query.offset) || 0;
  
  try {
    const logs = db.prepare(`
      SELECT al.*, 
             m.first_name || ' ' || m.last_name as member_name,
             m.member_number
      FROM access_logs al
      LEFT JOIN members m ON al.member_id = m.id
      ORDER BY al.id DESC
      LIMIT ? OFFSET ?
    `).all(limit, offset);
    
    res.json(logs);
  } catch (e) {
    console.error('Error obteniendo logs:', e.message);
    res.status(500).json({ error: e.message });
  }
});

app.get('/api/access/stats', (req, res) => {
  try {
    const today = db.prepare(`
      SELECT COUNT(*) as total,
             SUM(CASE WHEN result = 'granted' THEN 1 ELSE 0 END) as granted,
             SUM(CASE WHEN result = 'denied' THEN 1 ELSE 0 END) as denied
      FROM access_logs 
      WHERE date(timestamp) = date('now')
    `).get();
    
    const total = db.prepare('SELECT COUNT(*) as count FROM access_logs').get();
    const withMember = db.prepare('SELECT COUNT(*) as count FROM access_logs WHERE member_id IS NOT NULL').get();
    
    res.json({
      today: today,
      total_events: total.count,
      events_with_member: withMember.count
    });
  } catch (e) {
    console.error('Error obtener stats:', e.message);
    res.status(500).json({ error: e.message });
  }
});

app.get('/health', (req, res) => {
  const dbOk = db ? true : false;
  res.json({ 
    status: 'ok', 
    service: 'Hikvision Event Server',
    database: dbOk ? 'connected' : 'disconnected',
    db_path: DB_PATH
  });
});

app.get('/', (req, res) => {
  res.send(`
    <html>
      <head><title>Hikvision Event Server</title></head>
      <body>
        <h1>Hikvision Event Server</h1>
        <p>Puerto: ${PORT}</p>
        <p>Base de datos: ${DB_PATH}</p>
        <h2>Endpoints:</h2>
        <ul>
          <li>POST /api/access/hikvision-webhook</li>
          <li>GET /api/access/logs</li>
          <li>GET /api/access/stats</li>
          <li>GET /health</li>
        </ul>
      </body>
    </html>
  `);
});

if (initDatabase()) {
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`\n🚀 Hikvision Event Server`);
    console.log(`   Puerto: ${PORT}`);
    console.log(`   BD: ${DB_PATH}`);
    console.log(`   Webhook: http://localhost:${PORT}/api/access/hikvision-webhook`);
    console.log(`   Logs: http://localhost:${PORT}/api/access/logs`);
    console.log(`   Stats: http://localhost:${PORT}/api/access/stats`);
    console.log(`\nEsperando eventos...\n`);
  });
} else {
  console.error('No se pudo inicializar la base de datos');
  process.exit(1);
}