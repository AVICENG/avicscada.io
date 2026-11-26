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
    def __init__(self,database: str|Path, *, repository=None, point_usage_service=None):
        self.path=str(database); Path(self.path).parent.mkdir(parents=True,exist_ok=True)
        self.repository=repository; self.point_usage_service=point_usage_service
        with self._db() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.executescript('''CREATE TABLE IF NOT EXISTS history_samples(
            sample_id TEXT PRIMARY KEY, station_id TEXT NOT NULL, point_id TEXT NOT NULL,
            recorded_at TEXT NOT NULL, value_json TEXT NOT NULL, quality TEXT NOT NULL, source TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS idx_history_point_time ON history_samples(station_id,point_id,recorded_at);
            CREATE INDEX IF NOT EXISTS idx_history_time ON history_samples(recorded_at);
            CREATE TABLE IF NOT EXISTS history_bindings(
                station_id TEXT NOT NULL, point_id TEXT NOT NULL, enabled_at TEXT NOT NULL,
                PRIMARY KEY(station_id, point_id));''')
    def _db(self):
        db=sqlite3.connect(self.path,timeout=15); db.row_factory=sqlite3.Row; db.execute('PRAGMA busy_timeout=15000'); return db
    @staticmethod
    def _map(r): return HistorySample(r['sample_id'],r['station_id'],r['point_id'],r['recorded_at'],json.loads(r['value_json']),r['quality'],r['source'])
    def configured_points(self, station_id: str) -> list[str]:
        with self._db() as db:
            rows = db.execute(
                "SELECT point_id FROM history_bindings WHERE station_id=? ORDER BY point_id",
                (station_id,),
            ).fetchall()
        return [row["point_id"] for row in rows]

    def reconcile_point_usage(self) -> dict:
        """Rebuild Core Point usage from durable History bindings after startup.

        History and Core use separate SQLite databases, so this is an idempotent
        repair protocol rather than a cross-database ACID transaction.
        """
        if self.repository is None or self.point_usage_service is None:
            return {"reconciled": 0, "removed_invalid_bindings": [], "issues": []}

        with self._db() as db:
            bindings = db.execute(
                "SELECT station_id, point_id FROM history_bindings ORDER BY station_id, point_id"
            ).fetchall()

        desired_by_source: dict[str, set[str]] = {}
        invalid: list[tuple[str, str]] = []
        issues: list[dict] = []
        for row in bindings:
            station_id, point_id = row["station_id"], row["point_id"]
            try:
                point = self.repository.get_record(point_id)
                if point.get("entity_type") != "Point":
                    raise ValueError("reference is not a Point")
                device = self.repository.get_record(point.get("payload", {}).get("device_id"))
                if device.get("entity_type") != "Device":
                    raise ValueError("Point device reference is invalid")
                if device.get("payload", {}).get("station_id") != station_id:
                    raise ValueError("Point belongs to another station")
            except Exception as exc:
                invalid.append((station_id, point_id))
                issues.append({"station_id": station_id, "point_id": point_id,
                               "reason": f"{type(exc).__name__}: {exc}"})
                continue
            desired_by_source.setdefault(f"history:{station_id}", set()).add(point_id)

        if invalid:
            with self._db() as db:
                db.execute("BEGIN IMMEDIATE")
                db.executemany(
                    "DELETE FROM history_bindings WHERE station_id=? AND point_id=?",
                    invalid,
                )
                db.commit()

        # Include old Core keys with no remaining History binding, otherwise a
        # crash between the two SQLite commits could leave a phantom license slot.
        source_keys = set(desired_by_source)
        for record in self.repository.list_records(entity_type="Point"):
            for key in record.get("payload", {}).get("licensed_usage") or []:
                if isinstance(key, str) and key.startswith("history:"):
                    source_keys.add(key)

        for source_key in sorted(source_keys):
            self.point_usage_service.set_point_usage(
                source_key, sorted(desired_by_source.get(source_key, set()))
            )
        return {
            "reconciled": len(source_keys),
            "removed_invalid_bindings": [
                {"station_id": station_id, "point_id": point_id}
                for station_id, point_id in invalid
            ],
            "issues": issues,
        }

    def configure_point(self, station_id: str, point_id: str, *, enabled: bool = True) -> dict:
        """Enable/disable persistent history acquisition for one real engineering Point."""
        if self.repository is None:
            raise RuntimeError("Репозиторий точек не подключён")
        try:
            point = self.repository.get_record(point_id)
        except Exception as exc:
            raise ValueError("Точка архива не найдена") from exc
        if point.get("entity_type") != "Point":
            raise ValueError("В архив можно включать только инженерные точки")
        device_id = point.get("payload", {}).get("device_id")
        try:
            device = self.repository.get_record(device_id)
        except Exception as exc:
            raise ValueError("У точки отсутствует устройство") from exc
        if device.get("payload", {}).get("station_id") != station_id:
            raise ValueError("Точка принадлежит другой станции")

        previous = self.configured_points(station_id)
        desired = sorted(set(previous) | {point_id}) if enabled else sorted(set(previous) - {point_id})
        source_key = f"history:{station_id}"
        if enabled and self.point_usage_service is not None:
            # Check license capacity before persisting a new archive binding.
            self.point_usage_service.set_point_usage(source_key, desired)
        try:
            with self._db() as db:
                db.execute("BEGIN IMMEDIATE")
                if enabled:
                    db.execute(
                        "INSERT OR IGNORE INTO history_bindings(station_id,point_id,enabled_at) VALUES(?,?,?)",
                        (station_id, point_id, datetime.now(timezone.utc).isoformat()),
                    )
                else:
                    db.execute(
                        "DELETE FROM history_bindings WHERE station_id=? AND point_id=?",
                        (station_id, point_id),
                    )
                db.commit()
        except Exception:
            if enabled and self.point_usage_service is not None:
                self.point_usage_service.set_point_usage(source_key, previous)
            raise
        if not enabled and self.point_usage_service is not None:
            # Keep a conservative extra license reference if this update fails.
            self.point_usage_service.set_point_usage(source_key, desired)
        return {"station_id": station_id, "point_id": point_id, "enabled": bool(enabled),
                "configured_point_ids": desired}

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
