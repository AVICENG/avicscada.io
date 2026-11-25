from __future__ import annotations
import json, sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

@dataclass(frozen=True)
class EventRecord:
    event_id: str
    station_id: str | None
    event_type: str
    severity: str
    source_id: str | None
    occurred_at: str
    actor_id: str | None
    correlation_id: str | None
    message: str
    details: dict[str, Any]

class EventService:
    """Persistent operational event journal. It is deliberately separate from Audit and Alarm history."""
    SEVERITIES = {"DEBUG", "INFO", "NOTICE", "WARNING", "ERROR", "CRITICAL"}
    def __init__(self, database: str | Path):
        self.path = str(database); Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript('''CREATE TABLE IF NOT EXISTS events(
                event_id TEXT PRIMARY KEY, station_id TEXT, event_type TEXT NOT NULL,
                severity TEXT NOT NULL, source_id TEXT, occurred_at TEXT NOT NULL,
                actor_id TEXT, correlation_id TEXT, message TEXT NOT NULL, details_json TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS idx_events_time ON events(occurred_at DESC);
                CREATE INDEX IF NOT EXISTS idx_events_station_time ON events(station_id, occurred_at DESC);
                CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type, occurred_at DESC);''')
    def _db(self):
        db=sqlite3.connect(self.path, timeout=15); db.row_factory=sqlite3.Row; db.execute('PRAGMA busy_timeout=15000'); return db
    @staticmethod
    def _map(r): return EventRecord(r['event_id'],r['station_id'],r['event_type'],r['severity'],r['source_id'],r['occurred_at'],r['actor_id'],r['correlation_id'],r['message'],json.loads(r['details_json']))
    def record(self, event_type: str, message: str, *, station_id: str|None=None, severity: str='INFO', source_id: str|None=None, actor_id: str|None=None, correlation_id: str|None=None, details: dict|None=None, event_id: str|None=None) -> EventRecord:
        if not event_type.strip() or not message.strip(): raise ValueError('event_type and message are required')
        severity=severity.upper()
        if severity not in self.SEVERITIES: raise ValueError(f'Unsupported severity: {severity}')
        event=EventRecord(event_id or str(uuid4()),station_id,event_type,severity,source_id,datetime.now(timezone.utc).isoformat(),actor_id,correlation_id,message,details or {})
        with self._db() as db:
            existing=db.execute('SELECT * FROM events WHERE event_id=?',(event.event_id,)).fetchone()
            if existing is not None:
                stored=self._map(existing)
                if (stored.station_id,stored.event_type,stored.severity,stored.source_id,stored.actor_id,stored.correlation_id,stored.message,stored.details) != (event.station_id,event.event_type,event.severity,event.source_id,event.actor_id,event.correlation_id,event.message,event.details):
                    raise ValueError('Event idempotency key was reused with different event content')
                return stored
            db.execute('INSERT INTO events VALUES(?,?,?,?,?,?,?,?,?,?)',(event.event_id,event.station_id,event.event_type,event.severity,event.source_id,event.occurred_at,event.actor_id,event.correlation_id,event.message,json.dumps(event.details,ensure_ascii=False,sort_keys=True)))
        return event
    def list(self, *, station_id: str|None=None, event_type: str|None=None, severity: str|None=None, since: str|None=None, until: str|None=None, search: str|None=None, limit: int=200) -> list[EventRecord]:
        if not 1 <= limit <= 2000: raise ValueError('limit must be between 1 and 2000')
        clauses=[]; args=[]
        for col,val in [('station_id',station_id),('event_type',event_type),('severity',severity.upper() if severity else None)]:
            if val is not None: clauses.append(f'{col}=?'); args.append(val)
        if since: clauses.append('occurred_at>=?'); args.append(since)
        if until: clauses.append('occurred_at<=?'); args.append(until)
        if search: clauses.append('(message LIKE ? OR source_id LIKE ? OR event_type LIKE ?)'); args.extend([f'%{search}%']*3)
        sql='SELECT * FROM events'+(' WHERE '+' AND '.join(clauses) if clauses else '')+' ORDER BY occurred_at DESC LIMIT ?'; args.append(limit)
        with self._db() as db: return [self._map(r) for r in db.execute(sql,args).fetchall()]
    def purge_before(self, cutoff_iso: str) -> int:
        with self._db() as db: cur=db.execute('DELETE FROM events WHERE occurred_at<?',(cutoff_iso,)); return cur.rowcount
