from __future__ import annotations
import json, sqlite3
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

class TimeManagementService:
    """Persistent station timezone policy and explicit per-device clock-sync authorization registry."""
    def __init__(self,database:str|Path):
        self.path=str(database); Path(self.path).parent.mkdir(parents=True,exist_ok=True)
        with self._db() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.executescript('''CREATE TABLE IF NOT EXISTS station_time_policy(station_id TEXT PRIMARY KEY,timezone_name TEXT NOT NULL,ntp_enabled INTEGER NOT NULL,ntp_servers_json TEXT NOT NULL,updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS device_time_permission(station_id TEXT NOT NULL,device_id TEXT NOT NULL,allowed INTEGER NOT NULL,approved_by TEXT NOT NULL,reason TEXT NOT NULL,updated_at TEXT NOT NULL,PRIMARY KEY(station_id,device_id));''')
    def _db(self):
        db=sqlite3.connect(self.path,timeout=15); db.row_factory=sqlite3.Row; db.execute('PRAGMA busy_timeout=15000'); return db
    def configure_station(self,station_id:str,timezone_name:str,*,ntp_enabled:bool=False,ntp_servers:list[str]|None=None)->dict:
        try: ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc: raise ValueError('Unknown IANA timezone') from exc
        servers=list(ntp_servers or [])
        if ntp_enabled and not servers: raise ValueError('NTP servers must be configured when NTP is enabled')
        item={'station_id':station_id,'timezone':timezone_name,'ntp_enabled':bool(ntp_enabled),'ntp_servers':servers,'updated_at':datetime.now(timezone.utc).isoformat()}
        with self._db() as db: db.execute('INSERT INTO station_time_policy VALUES(?,?,?,?,?) ON CONFLICT(station_id) DO UPDATE SET timezone_name=excluded.timezone_name,ntp_enabled=excluded.ntp_enabled,ntp_servers_json=excluded.ntp_servers_json,updated_at=excluded.updated_at',(station_id,timezone_name,int(ntp_enabled),json.dumps(servers),item['updated_at']))
        return item
    def station_time(self,station_id:str)->dict:
        with self._db() as db: row=db.execute('SELECT * FROM station_time_policy WHERE station_id=?',(station_id,)).fetchone()
        config={'station_id':station_id,'timezone':'UTC','ntp_enabled':False,'ntp_servers':[]} if row is None else {'station_id':station_id,'timezone':row['timezone_name'],'ntp_enabled':bool(row['ntp_enabled']),'ntp_servers':json.loads(row['ntp_servers_json']),'updated_at':row['updated_at']}
        now=datetime.now(timezone.utc); local=now.astimezone(ZoneInfo(config['timezone']))
        return {**config,'utc_now':now.isoformat(),'local_now':local.isoformat()}
    def set_device_sync_permission(self,station_id:str,device_id:str,allowed:bool,*,approved_by:str,reason:str)->dict:
        if not approved_by.strip() or not reason.strip(): raise ValueError('Approver and reason are required')
        item={'station_id':station_id,'device_id':device_id,'allowed':bool(allowed),'approved_by':approved_by,'reason':reason,'updated_at':datetime.now(timezone.utc).isoformat()}
        with self._db() as db: db.execute('INSERT INTO device_time_permission VALUES(?,?,?,?,?,?) ON CONFLICT(station_id,device_id) DO UPDATE SET allowed=excluded.allowed,approved_by=excluded.approved_by,reason=excluded.reason,updated_at=excluded.updated_at',(station_id,device_id,int(allowed),approved_by,reason,item['updated_at']))
        return item
    def device_sync_permission(self,station_id:str,device_id:str)->dict:
        with self._db() as db: row=db.execute('SELECT * FROM device_time_permission WHERE station_id=? AND device_id=?',(station_id,device_id)).fetchone()
        return {'station_id':station_id,'device_id':device_id,'allowed':False,'reason':'No explicit authorization'} if row is None else {'station_id':station_id,'device_id':device_id,'allowed':bool(row['allowed']),'approved_by':row['approved_by'],'reason':row['reason'],'updated_at':row['updated_at']}
    def authorize_sync(self,station_id:str,device_id:str)->bool: return bool(self.device_sync_permission(station_id,device_id)['allowed'])
