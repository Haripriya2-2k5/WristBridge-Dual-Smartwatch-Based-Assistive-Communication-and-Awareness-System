# database.py
import sqlite3
import time

def init_db(db_path="wristbridge.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # sos table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts INTEGER NOT NULL,
        lat REAL NOT NULL,
        lon REAL NOT NULL,
        note TEXT
    )
    """)
    # user status (key-value)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_status (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TEXT
    )
    """)
    # log for simple watch notifications
    cur.execute("""
    CREATE TABLE IF NOT EXISTS log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT,
        value TEXT,
        updated_at TEXT
    )
    """)
    conn.commit()
    conn.close()

def add_sos_event(db_path, ts, lat, lon, note=""):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("INSERT INTO sos (ts, lat, lon, note) VALUES (?, ?, ?, ?)", (ts, lat, lon, note))
    conn.commit()
    conn.close()
    # also log
    add_log(db_path, "sos_sent", f"{ts}:{lat},{lon}:{note}")

def list_sos_events(db_path, limit=100):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id, ts, lat, lon, note FROM sos ORDER BY ts DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

def update_user_status(db_path, key, value):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    cur.execute("INSERT OR REPLACE INTO user_status (key, value, updated_at) VALUES (?, ?, ?)", (key, value, ts))
    conn.commit()
    conn.close()
    add_log(db_path, "status_update", f"{key}={value}")

def add_log(db_path, key, value):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    cur.execute("INSERT INTO log (key, value, updated_at) VALUES (?, ?, ?)", (key, value, ts))
    conn.commit()
    conn.close()
