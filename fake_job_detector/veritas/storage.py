import sqlite3,json,os,uuid
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def db_path():return Path(os.environ.get('VERITAS_DB',str(ROOT/'runtime/history.sqlite3')))
@contextmanager
def connect():
    p=db_path();p.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(p,timeout=20);db.row_factory=sqlite3.Row
    db.execute('CREATE TABLE IF NOT EXISTS analyses (id TEXT PRIMARY KEY, created_at TEXT, title TEXT, company TEXT, level TEXT, score INTEGER, payload TEXT, review TEXT DEFAULT "Pending", note TEXT DEFAULT "", reviewed_at TEXT)')
    try:
      with db:yield db
    finally:db.close()

def save_many(results):
    with connect() as db:
      for result in results:
        ident=str(uuid.uuid4());now=datetime.now(timezone.utc).isoformat();result.update(id=ident,created_at=now,saved=True)
        db.execute('INSERT INTO analyses(id,created_at,title,company,level,score,payload) VALUES(?,?,?,?,?,?,?)',(ident,now,result['job']['title'],result['job'].get('company',''),result['risk_level'],result['risk_score'],json.dumps(result)))

def history():
    with connect() as db:
      return [dict(r) for r in db.execute('SELECT id,created_at,title,company,level,score,review,note,reviewed_at FROM analyses ORDER BY created_at DESC')]

def get(ident):
    with connect() as db:r=db.execute('SELECT * FROM analyses WHERE id=?',(ident,)).fetchone()
    if r is None:return None
    return json.loads(r['payload'])|{'review':r['review'],'note':r['note'],'reviewed_at':r['reviewed_at']}

def review(ident,decision,note):
    with connect() as db:
      row=db.execute('SELECT review FROM analyses WHERE id=?',(ident,)).fetchone()
      if row is None:raise KeyError('Record not found')
      if row['review']!='Pending':raise ValueError('This review is already completed.')
      now=datetime.now(timezone.utc).isoformat()
      changed=db.execute('UPDATE analyses SET review=?,note=?,reviewed_at=? WHERE id=? AND review="Pending"',(decision,note,now,ident)).rowcount
      if changed!=1:raise ValueError('This review is already completed.')
    return get(ident)
