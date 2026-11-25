from __future__ import annotations
import json, sqlite3
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

@dataclass(frozen=True)
class DependencyEdge:
    edge_id:str; dependent_id:str; dependency_id:str; relation_type:str; station_id:str|None; metadata:dict

class DependencyService:
    """Explicit dependency graph. Deletion preview is advisory; destructive actions must consume it."""
    def __init__(self,database:str|Path):
        self.path=str(database); Path(self.path).parent.mkdir(parents=True,exist_ok=True)
        with self._db() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.executescript('''CREATE TABLE IF NOT EXISTS dependencies(edge_id TEXT PRIMARY KEY,dependent_id TEXT NOT NULL,dependency_id TEXT NOT NULL,relation_type TEXT NOT NULL,station_id TEXT,metadata_json TEXT NOT NULL,UNIQUE(dependent_id,dependency_id,relation_type)); CREATE INDEX IF NOT EXISTS idx_dep_target ON dependencies(dependency_id); CREATE INDEX IF NOT EXISTS idx_dep_source ON dependencies(dependent_id);''')
    def _db(self):
        db=sqlite3.connect(self.path,timeout=15); db.row_factory=sqlite3.Row; db.execute('PRAGMA busy_timeout=15000'); return db
    @staticmethod
    def _map(r): return DependencyEdge(r['edge_id'],r['dependent_id'],r['dependency_id'],r['relation_type'],r['station_id'],json.loads(r['metadata_json']))
    def add(self,dependent_id:str,dependency_id:str,relation_type:str,*,station_id:str|None=None,metadata:dict|None=None)->DependencyEdge:
        if dependent_id==dependency_id: raise ValueError('Self-dependency is not allowed')
        if not all(x.strip() for x in (dependent_id,dependency_id,relation_type)): raise ValueError('Dependency identifiers are required')
        edge=DependencyEdge(str(uuid4()),dependent_id,dependency_id,relation_type,station_id,metadata or {})
        with self._db() as db:
            db.execute('INSERT INTO dependencies VALUES(?,?,?,?,?,?) ON CONFLICT(dependent_id,dependency_id,relation_type) DO UPDATE SET station_id=excluded.station_id,metadata_json=excluded.metadata_json',(edge.edge_id,dependent_id,dependency_id,relation_type,station_id,json.dumps(edge.metadata,ensure_ascii=False,sort_keys=True)))
            row=db.execute('SELECT * FROM dependencies WHERE dependent_id=? AND dependency_id=? AND relation_type=?',(dependent_id,dependency_id,relation_type)).fetchone()
        return self._map(row)
    def list_for(self,object_id:str)->list[DependencyEdge]:
        with self._db() as db: rows=db.execute('SELECT * FROM dependencies WHERE dependent_id=? OR dependency_id=? ORDER BY relation_type',(object_id,object_id)).fetchall()
        return [self._map(r) for r in rows]
    def delete_preview(self,object_id:str)->dict:
        edges=self.list_for(object_id)
        dependents=[e for e in edges if e.dependency_id==object_id]
        dependencies=[e for e in edges if e.dependent_id==object_id]
        return {'object_id':object_id,'safe_to_delete':not dependents,'blocking_dependents':[{'object_id':e.dependent_id,'relation_type':e.relation_type,'metadata':e.metadata} for e in dependents],'outgoing_dependencies':[{'object_id':e.dependency_id,'relation_type':e.relation_type} for e in dependencies],'edge_count':len(edges)}
    def remove_object_edges(self,object_id:str)->int:
        with self._db() as db: return db.execute('DELETE FROM dependencies WHERE dependent_id=? OR dependency_id=?',(object_id,object_id)).rowcount
