from __future__ import annotations
import json, sqlite3, statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

@dataclass(frozen=True)
class HistorySample:
    sample_id: str; station_id: str; point_id: str; recorded_at: str; value: Any; quality: str; source: str

class HistoryService:
    """On-change/interval sample store and query/rollup primitives. Acquisition is owned by Runtime/Drivers."""
    QUALITIES={'GOOD','UNCERTAIN','STALE','BAD','COMM_LOST','DISABLED'}
    def __init__(self,database: str|Path):
        self.path=str(database); Path(self.path).parent.mkdir(parents=True,exist_ok=True)
        with self._db() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.executescript('''CREATE TABLE IF NOT EXISTS history_samples(
            sample_id TEXT PRIMARY KEY, station_id TEXT NOT NULL, point_id TEXT NOT NULL,
            recorded_at TEXT NOT NULL, value_json TEXT NOT NULL, quality TEXT NOT NULL, source TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS idx_history_point_time ON history_samples(station_id,point_id,recorded_at);
            CREATE INDEX IF NOT EXISTS idx_history_time ON history_samples(recorded_at);''')
    def _db(self):
        db=sqlite3.connect(self.path,timeout=15); db.row_factory=sqlite3.Row; db.execute('PRAGMA busy_timeout=15000'); return db
    @staticmethod
    def _map(r): return HistorySample(r['sample_id'],r['station_id'],r['point_id'],r['recorded_at'],json.loads(r['value_json']),r['quality'],r['source'])
    def append(self,station_id:str,point_id:str,value:Any,*,quality:str='GOOD',recorded_at:str|None=None,source:str='runtime') -> HistorySample:
        q=quality.upper()
        if q not in self.QUALITIES: raise ValueError(f'Unsupported quality: {q}')
        ts=recorded_at or datetime.now(timezone.utc).isoformat()
        sample=HistorySample(str(uuid4()),station_id,point_id,ts,value,q,source)
        with self._db() as db: db.execute('INSERT INTO history_samples VALUES(?,?,?,?,?,?,?)',(sample.sample_id,station_id,point_id,ts,json.dumps(value,ensure_ascii=False,allow_nan=False),q,source))
        return sample
    def query(self,station_id:str,point_id:str,*,since:str|None=None,until:str|None=None,limit:int=5000,include_bad:bool=True)->list[HistorySample]:
        if not 1<=limit<=50000: raise ValueError('limit must be between 1 and 50000')
        clauses=['station_id=?','point_id=?']; args=[station_id,point_id]
        if since: clauses.append('recorded_at>=?'); args.append(since)
        if until: clauses.append('recorded_at<=?'); args.append(until)
        if not include_bad: clauses.append("quality IN ('GOOD','UNCERTAIN')")
        args.append(limit)
        with self._db() as db: rows=db.execute('SELECT * FROM history_samples WHERE '+' AND '.join(clauses)+' ORDER BY recorded_at LIMIT ?',args).fetchall()
        return [self._map(r) for r in rows]
    def rollup(self,station_id:str,point_id:str,*,since:str|None=None,until:str|None=None,method:str='average')->dict:
        samples=self.query(station_id,point_id,since=since,until=until,include_bad=False)
        values=[s.value for s in samples if isinstance(s.value,(int,float)) and not isinstance(s.value,bool)]
        if not values: result=None
        elif method=='average': result=statistics.fmean(values)
        elif method=='sum': result=sum(values)
        elif method=='min': result=min(values)
        elif method=='max': result=max(values)
        elif method=='median': result=statistics.median(values)
        elif method=='last': result=values[-1]
        elif method=='count': result=len(values)
        else: raise ValueError('method must be average, sum, min, max, median, last or count')
        return {'station_id':station_id,'point_id':point_id,'method':method,'sample_count':len(samples),'valid_numeric_count':len(values),'value':result}
    def purge_before(self,cutoff_iso:str)->int:
        with self._db() as db: return db.execute('DELETE FROM history_samples WHERE recorded_at<?',(cutoff_iso,)).rowcount
