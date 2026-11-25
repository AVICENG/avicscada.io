from __future__ import annotations
import json, sqlite3, statistics
from pathlib import Path
from uuid import uuid4

class AnalyticsService:
    """Tag/hierarchy registry and deterministic aggregation primitives; no automatic control outputs."""
    def __init__(self,database:str|Path):
        self.path=str(database); Path(self.path).parent.mkdir(parents=True,exist_ok=True)
        with self._db() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.executescript('''CREATE TABLE IF NOT EXISTS point_tags(point_id TEXT NOT NULL,tag TEXT NOT NULL,dictionary TEXT NOT NULL,PRIMARY KEY(point_id,tag,dictionary));
            CREATE INDEX IF NOT EXISTS idx_point_tags_tag ON point_tags(dictionary,tag);
            CREATE TABLE IF NOT EXISTS point_hierarchy(point_id TEXT PRIMARY KEY,hierarchy_path TEXT NOT NULL,metadata_json TEXT NOT NULL);''')
    def _db(self):
        db=sqlite3.connect(self.path,timeout=15); db.row_factory=sqlite3.Row; db.execute('PRAGMA busy_timeout=15000'); return db
    def tag_point(self,point_id:str,tag:str,*,dictionary:str='AVIC',hierarchy_path:str|None=None,metadata:dict|None=None)->dict:
        if not point_id.strip() or not tag.strip() or not dictionary.strip(): raise ValueError('point_id, tag and dictionary are required')
        with self._db() as db:
            db.execute('INSERT OR IGNORE INTO point_tags VALUES(?,?,?)',(point_id,tag,dictionary))
            if hierarchy_path is not None: db.execute('INSERT INTO point_hierarchy VALUES(?,?,?) ON CONFLICT(point_id) DO UPDATE SET hierarchy_path=excluded.hierarchy_path,metadata_json=excluded.metadata_json',(point_id,hierarchy_path,json.dumps(metadata or {},ensure_ascii=False)))
        return {'point_id':point_id,'tag':tag,'dictionary':dictionary,'hierarchy_path':hierarchy_path}
    def find_points(self,tag:str,*,dictionary:str='AVIC',hierarchy_prefix:str|None=None)->list[str]:
        sql='SELECT t.point_id FROM point_tags t LEFT JOIN point_hierarchy h ON h.point_id=t.point_id WHERE t.tag=? AND t.dictionary=?'; args=[tag,dictionary]
        if hierarchy_prefix is not None: sql+=' AND h.hierarchy_path LIKE ?'; args.append(hierarchy_prefix.rstrip('/')+'%')
        sql+=' ORDER BY t.point_id'
        with self._db() as db: return [r['point_id'] for r in db.execute(sql,args).fetchall()]
    @staticmethod
    def aggregate(values:list[float|int|None],method:str='average',*,missing_strategy:str='ignore_point')->dict:
        if missing_strategy not in {'ignore_point','ignore_series','linear_interpolation'}: raise ValueError('Unsupported missing-data strategy')
        missing=any(v is None for v in values)
        if missing_strategy=='ignore_series' and missing: return {'value':None,'input_count':len(values),'valid_count':0,'missing_count':sum(v is None for v in values),'strategy':missing_strategy}
        clean=[float(v) for v in values if isinstance(v,(int,float)) and not isinstance(v,bool)]
        if missing_strategy=='linear_interpolation' and missing:
            clean_values=list(values)
            valid=[i for i,v in enumerate(clean_values) if isinstance(v,(int,float)) and not isinstance(v,bool)]
            for i,v in enumerate(clean_values):
                if v is not None: continue
                left=max((j for j in valid if j<i),default=None); right=min((j for j in valid if j>i),default=None)
                if left is not None and right is not None: clean_values[i]=float(clean_values[left])+(float(clean_values[right])-float(clean_values[left]))*(i-left)/(right-left)
            clean=[float(v) for v in clean_values if isinstance(v,(int,float)) and not isinstance(v,bool)]
        if not clean: result=None
        elif method=='sum': result=sum(clean)
        elif method=='average': result=statistics.fmean(clean)
        elif method=='min': result=min(clean)
        elif method=='max': result=max(clean)
        elif method=='median': result=statistics.median(clean)
        elif method=='count': result=len(clean)
        else: raise ValueError('method must be sum, average, min, max, median or count')
        return {'value':result,'input_count':len(values),'valid_count':len(clean),'missing_count':sum(v is None for v in values),'strategy':missing_strategy}
