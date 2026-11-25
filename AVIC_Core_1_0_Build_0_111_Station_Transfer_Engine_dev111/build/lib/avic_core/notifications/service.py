from __future__ import annotations
import json, sqlite3
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4

class NotificationService:
    """Notification routing registry and durable delivery outbox; no transport sends without an adapter."""
    CHANNELS={'EMAIL','TELEGRAM','PUSH','WEBHOOK'}
    def __init__(self,database:str|Path):
        self.path=str(database); Path(self.path).parent.mkdir(parents=True,exist_ok=True)
        with self._db() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.executescript('''CREATE TABLE IF NOT EXISTS notification_routes(route_id TEXT PRIMARY KEY,name TEXT NOT NULL,channel TEXT NOT NULL,recipient TEXT NOT NULL,enabled INTEGER NOT NULL,filters_json TEXT NOT NULL,created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS notification_outbox(message_id TEXT PRIMARY KEY,route_id TEXT,event_ref TEXT,payload_json TEXT NOT NULL,status TEXT NOT NULL,attempts INTEGER NOT NULL,created_at TEXT NOT NULL,delivered_at TEXT,last_error TEXT);
            CREATE INDEX IF NOT EXISTS idx_notification_status ON notification_outbox(status,created_at);''')
    def _db(self):
        db=sqlite3.connect(self.path,timeout=15); db.row_factory=sqlite3.Row; db.execute('PRAGMA busy_timeout=15000'); return db
    def add_route(self,name:str,channel:str,recipient:str,*,filters:dict|None=None,enabled:bool=True)->dict:
        channel=channel.upper()
        if channel not in self.CHANNELS: raise ValueError('Unsupported channel')
        if not name.strip() or not recipient.strip(): raise ValueError('Route name and recipient are required')
        item={'route_id':str(uuid4()),'name':name,'channel':channel,'recipient':recipient,'enabled':bool(enabled),'filters':filters or {},'created_at':datetime.now(timezone.utc).isoformat()}
        with self._db() as db: db.execute('INSERT INTO notification_routes VALUES(?,?,?,?,?,?,?)',(item['route_id'],name,channel,recipient,int(enabled),json.dumps(item['filters'],ensure_ascii=False),item['created_at']))
        return item
    def list_routes(self)->list[dict]:
        with self._db() as db: rows=db.execute('SELECT * FROM notification_routes ORDER BY name').fetchall()
        return [{'route_id':r['route_id'],'name':r['name'],'channel':r['channel'],'recipient':r['recipient'],'enabled':bool(r['enabled']),'filters':json.loads(r['filters_json']),'created_at':r['created_at']} for r in rows]
    def enqueue(self,payload:dict,*,event_ref:str|None=None,route_id:str|None=None)->dict:
        if route_id:
            with self._db() as db: route=db.execute('SELECT enabled FROM notification_routes WHERE route_id=?',(route_id,)).fetchone()
            if route is None: raise ValueError('Notification route does not exist')
            if not route['enabled']: raise ValueError('Notification route is disabled')
        msg={'message_id':str(uuid4()),'route_id':route_id,'event_ref':event_ref,'payload':payload,'status':'PENDING','attempts':0,'created_at':datetime.now(timezone.utc).isoformat(),'transport_state':'QUEUED_NO_TRANSPORT'}
        with self._db() as db: db.execute('INSERT INTO notification_outbox(message_id,route_id,event_ref,payload_json,status,attempts,created_at) VALUES(?,?,?,?,?,?,?)',(msg['message_id'],route_id,event_ref,json.dumps(payload,ensure_ascii=False),msg['status'],0,msg['created_at']))
        return msg
    def list_outbox(self,limit:int=200)->list[dict]:
        if not 1<=limit<=2000: raise ValueError('limit must be between 1 and 2000')
        with self._db() as db: rows=db.execute('SELECT * FROM notification_outbox ORDER BY created_at DESC LIMIT ?',(limit,)).fetchall()
        return [{'message_id':r['message_id'],'route_id':r['route_id'],'event_ref':r['event_ref'],'payload':json.loads(r['payload_json']),'status':r['status'],'attempts':r['attempts'],'created_at':r['created_at'],'delivered_at':r['delivered_at'],'last_error':r['last_error']} for r in rows]
