"""SQLite demo persistence. Replace with a managed DB for durable Cloud hosting."""
import sqlite3, hashlib, hmac, secrets, json
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime
DB=Path(__file__).with_name('eventon.db')

@contextmanager
def connect():
    c=sqlite3.connect(DB,timeout=20)
    c.execute('PRAGMA foreign_keys=ON')
    c.executescript('''CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, salt TEXT NOT NULL, password TEXT NOT NULL, display_name TEXT NOT NULL, company TEXT NOT NULL DEFAULT '');
    CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY AUTOINCREMENT, owner TEXT NOT NULL REFERENCES users(username), title TEXT NOT NULL, data TEXT NOT NULL, updated TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner);''')
    c.commit()
    try:
        yield c
        c.commit()
    except Exception:
        c.rollback();raise
    finally:c.close()

def digest(password,salt):return hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),310000).hex()

def register(username,password,display_name):
    salt=secrets.token_hex(16)
    with connect() as c:c.execute('INSERT INTO users(username,salt,password,display_name) VALUES(?,?,?,?)',(username,salt,digest(password,salt),display_name))

def login(username,password):
    with connect() as c:row=c.execute('SELECT salt,password,display_name,company FROM users WHERE username=?',(username,)).fetchone()
    return {'username':username,'display_name':row[2],'company':row[3]} if row and hmac.compare_digest(row[1],digest(password,row[0])) else None

def profile(username):
    with connect() as c:r=c.execute('SELECT display_name,company FROM users WHERE username=?',(username,)).fetchone()
    return {'username':username,'display_name':r[0],'company':r[1]} if r else None

def save_project(owner,data,pid=None):
    encoded=json.dumps(data,ensure_ascii=False,default=str);now=datetime.now().isoformat(timespec='seconds')
    with connect() as c:
        if pid:
            cur=c.execute('UPDATE projects SET title=?,data=?,updated=? WHERE id=? AND owner=?',(data['name'],encoded,now,pid,owner))
            if cur.rowcount!=1:raise ValueError('프로젝트를 찾을 수 없습니다.')
            return pid
        cur=c.execute('INSERT INTO projects(owner,title,data,updated) VALUES(?,?,?,?)',(owner,data['name'],encoded,now));return cur.lastrowid

def list_projects(owner):
    with connect() as c:return c.execute('SELECT id,title,updated FROM projects WHERE owner=? ORDER BY updated DESC,id DESC',(owner,)).fetchall()

def load_project(owner,pid):
    with connect() as c:r=c.execute('SELECT data FROM projects WHERE owner=? AND id=?',(owner,pid)).fetchone()
    if not r:raise ValueError('프로젝트를 찾을 수 없습니다.')
    return json.loads(r[0])

def delete_project(owner,pid):
    with connect() as c:c.execute('DELETE FROM projects WHERE owner=? AND id=?',(owner,pid))

def update_profile(username,name,company):
    with connect() as c:c.execute('UPDATE users SET display_name=?,company=? WHERE username=?',(name,company,username))

def change_password(username,old,new):
    if not login(username,old):return False
    salt=secrets.token_hex(16)
    with connect() as c:c.execute('UPDATE users SET salt=?,password=? WHERE username=?',(salt,digest(new,salt),username))
    return True
