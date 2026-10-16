import sqlite3, json, sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "seed_library.json"
DATA_HOME = Path.home() / ("AppData/Local/JASS/LandLawReadyReckoner" if sys.platform == "win32" else ".local/share/jass/land-law-ready-reckoner")
DATA_HOME.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_HOME / "ready_reckoner.sqlite3"

def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def initialize():
    con = connect()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS acts(id INTEGER PRIMARY KEY, title TEXT UNIQUE, category TEXT, jurisdiction TEXT, summary TEXT, source TEXT, status TEXT, pdf_url TEXT, local_file TEXT, source_note TEXT);
    CREATE TABLE IF NOT EXISTS cases(id INTEGER PRIMARY KEY, title TEXT UNIQUE, citation TEXT, court TEXT, year TEXT, topics TEXT, principle TEXT, caution TEXT, url TEXT);
    CREATE TABLE IF NOT EXISTS guides(id INTEGER PRIMARY KEY, title TEXT UNIQUE, category TEXT, when_text TEXT, checklist TEXT, research TEXT, cases TEXT, warning TEXT);
    CREATE TABLE IF NOT EXISTS notes(id INTEGER PRIMARY KEY, title TEXT, state TEXT, issue TEXT, stage TEXT, notes TEXT, created_at TEXT, updated_at TEXT);
    """)
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    # Add new columns safely when upgrading an existing local database.
    act_cols = {row[1] for row in con.execute("PRAGMA table_info(acts)").fetchall()}
    for col in ("pdf_url", "local_file", "source_note"):
        if col not in act_cols:
            con.execute(f"ALTER TABLE acts ADD COLUMN {col} TEXT")
    for r in seed["acts"]:
        con.execute("""INSERT INTO acts(title,category,jurisdiction,summary,source,status,pdf_url,local_file,source_note)
          VALUES(:title,:category,:jurisdiction,:summary,:source,:status,:pdf_url,:local_file,:source_note)
          ON CONFLICT(title) DO UPDATE SET category=excluded.category,jurisdiction=excluded.jurisdiction,
          summary=excluded.summary,source=excluded.source,status=excluded.status,pdf_url=excluded.pdf_url,
          local_file=excluded.local_file,source_note=excluded.source_note""", r)
    for r in seed["cases"]:
        con.execute("INSERT OR IGNORE INTO cases(title,citation,court,year,topics,principle,caution,url) VALUES(:title,:citation,:court,:year,:topics,:principle,:caution,:url)", r)
    for old in seed["guides"]:
        r = dict(old); r["when_text"] = r.pop("when")
        con.execute("INSERT OR IGNORE INTO guides(title,category,when_text,checklist,research,cases,warning) VALUES(:title,:category,:when_text,:checklist,:research,:cases,:warning)", r)
    con.commit(); con.close()

def query_all(table, search=""):
    cols = {"acts":"title category jurisdiction summary status", "cases":"title citation court topics principle caution", "guides":"title category when_text checklist research cases warning"}
    if table not in cols: raise ValueError("Unsupported table")
    con=connect(); fields=cols[table].split()
    if search.strip():
        where=" OR ".join(f"{f} LIKE ?" for f in fields)
        rows=con.execute(f"SELECT * FROM {table} WHERE {where} ORDER BY title", [f"%{search.strip()}%"]*len(fields)).fetchall()
    else: rows=con.execute(f"SELECT * FROM {table} ORDER BY title").fetchall()
    con.close(); return [dict(x) for x in rows]

def list_notes():
    con=connect(); rows=con.execute("SELECT * FROM notes ORDER BY updated_at DESC").fetchall(); con.close()
    return [dict(x) for x in rows]

def save_note(n, ident=None):
    con=connect(); now=datetime.now().isoformat(timespec="seconds")
    if ident:
        con.execute("UPDATE notes SET title=?,state=?,issue=?,stage=?,notes=?,updated_at=? WHERE id=?",
                    (n["title"],n["state"],n["issue"],n["stage"],n["notes"],now,ident))
    else:
        cur=con.execute("INSERT INTO notes(title,state,issue,stage,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                        (n["title"],n["state"],n["issue"],n["stage"],n["notes"],now,now)); ident=cur.lastrowid
    con.commit(); con.close(); return ident

def delete_note(ident):
    con=connect(); con.execute("DELETE FROM notes WHERE id=?",(ident,)); con.commit(); con.close()
