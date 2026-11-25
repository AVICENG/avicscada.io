"""Persistent user point-view preferences and deterministic point-list queries."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Any

SORT_FIELDS = {"name", "data_type", "value", "unit", "quality", "native_identity"}
QUALITIES = {"GOOD", "UNCERTAIN", "BAD", "COMM_LOST", "STALE", "BAD_COMMUNICATION", "BAD_CONFIGURATION", "DISABLED"}


class PointViewService:
    def __init__(self, database: str | Path):
        self.database = str(database)
        Path(self.database).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS point_favorites (
                user_id TEXT NOT NULL, point_id TEXT NOT NULL, station_id TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(user_id, point_id))""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_point_favorites_station ON point_favorites(user_id, station_id)")

    def _connect(self):
        db = sqlite3.connect(self.database, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=15000")
        return db

    def add_favorite(self, point_id: str, *, user_id: str = "local-engineer", station_id: str | None = None) -> dict[str, Any]:
        if not point_id or not point_id.strip() or not user_id or not user_id.strip():
            raise ValueError("point_id и user_id обязательны")
        with self._connect() as db:
            db.execute("INSERT OR IGNORE INTO point_favorites(user_id,point_id,station_id) VALUES(?,?,?)",
                       (user_id, point_id, station_id))
        return {"point_id": point_id, "user_id": user_id, "station_id": station_id, "favorite": True}

    def remove_favorite(self, point_id: str, *, user_id: str = "local-engineer") -> dict[str, Any]:
        with self._connect() as db:
            db.execute("DELETE FROM point_favorites WHERE user_id=? AND point_id=?", (user_id, point_id))
        return {"point_id": point_id, "user_id": user_id, "favorite": False}

    def favorite_ids(self, *, user_id: str = "local-engineer", station_id: str | None = None) -> set[str]:
        sql = "SELECT point_id FROM point_favorites WHERE user_id=?"
        args: list[Any] = [user_id]
        if station_id is not None:
            sql += " AND station_id=?"; args.append(station_id)
        with self._connect() as db:
            return {r[0] for r in db.execute(sql, args).fetchall()}

    @staticmethod
    def query(records: list[dict[str, Any]], *, favorite_ids: set[str] | None = None,
              station_id: str | None = None, search: str | None = None,
              quality: str | None = None, favorites_only: bool = False,
              sort_by: str = "name", sort_dir: str = "asc", offset: int = 0,
              limit: int = 5000) -> dict[str, Any]:
        if sort_by not in SORT_FIELDS: raise ValueError(f"Недопустимое поле сортировки: {sort_by}")
        if sort_dir not in {"asc", "desc"}: raise ValueError("sort_dir должен быть asc или desc")
        if offset < 0 or not 1 <= limit <= 5000: raise ValueError("Некорректные offset/limit")
        if quality and quality.upper() not in QUALITIES: raise ValueError("Неизвестное качество точки")
        favs = favorite_ids or set(); q = (search or "").casefold(); normalized_quality = quality.upper() if quality else None
        filtered=[]
        for row in records:
            p=row.get("payload",{}); point_id=row.get("entity_id",row.get("id"))
            device=p.get("device",{}) if isinstance(p.get("device"),dict) else {}
            row_station=p.get("station_id") or device.get("station_id") or row.get("station_id")
            quality_value=getattr(p.get("quality"),"value",p.get("quality","UNCERTAIN"))
            quality_value=str(quality_value).upper()
            hay=" ".join(str(p.get(k,row.get(k,"")) or "") for k in ("name","engineering_description","source_ref","native_identity"))
            if station_id and row_station != station_id: continue
            if normalized_quality and quality_value != normalized_quality: continue
            if q and q not in (hay+" "+str(row.get("name",""))).casefold(): continue
            if favorites_only and point_id not in favs: continue
            item={"id":point_id,"name":row.get("name") or p.get("name"),"version":row.get("version"),
                  "station_id":row_station,"device_id":p.get("device_id"),"data_type":p.get("data_type"),"direction":getattr(p.get("direction", "input"), "value", p.get("direction", "input")),
                  "unit":p.get("unit"),"value":p.get("value"),"quality":quality_value,
                  "source_ref":p.get("source_ref"),"native_identity":p.get("native_identity"),
                  "object_type":p.get("object_type"),"protocol":device.get("protocol"),
                  "device_name":device.get("name"),"device_address":device.get("address"),
                  "device_manufacturer":device.get("manufacturer"),"device_model":device.get("model"),
                  "favorite":point_id in favs}
            filtered.append(item)
        total=len(filtered)
        def key(item):
            v=item.get(sort_by)
            if v is None: return (1, "")
            if isinstance(v,(int,float)): return (0,v)
            return (0,str(v).casefold())
        filtered.sort(key=key, reverse=sort_dir=="desc")
        return {"points":filtered[offset:offset+limit],"total":total,"offset":offset,"limit":limit,
                "sort_by":sort_by,"sort_dir":sort_dir,"favorite_count":sum(x["id"] in favs for x in filtered)}
