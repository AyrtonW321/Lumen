"""SQLite schema, migrations and connection."""
import sqlite3
from pathlib import Path

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS leads (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  brand TEXT NOT NULL,
  products TEXT NOT NULL DEFAULT '',
  source TEXT NOT NULL DEFAULT 'new',
  list_name TEXT,
  phone TEXT,
  label TEXT,
  closed TEXT,
  next_action_date TEXT,
  created_at TEXT NOT NULL,
  address TEXT,
  facility_size TEXT,
  solar_reference TEXT,
  lighting_reference TEXT,
  meeting_type TEXT,
  appt_at TEXT
);
CREATE TABLE IF NOT EXISTS contacts (
  id INTEGER PRIMARY KEY,
  lead_id INTEGER NOT NULL REFERENCES leads(id),
  name TEXT NOT NULL,
  title TEXT,
  phone TEXT,
  email TEXT,
  ext TEXT,
  phone_type TEXT,
  prefers_email INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS activities (
  id INTEGER PRIMARY KEY,
  lead_id INTEGER NOT NULL REFERENCES leads(id),
  contact_id INTEGER REFERENCES contacts(id),
  timestamp TEXT NOT NULL,
  weekday TEXT NOT NULL,
  hour_block TEXT NOT NULL,
  outcome TEXT NOT NULL,
  note TEXT,
  caller TEXT,
  myphoner_comment TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS traits (
  id INTEGER PRIMARY KEY,
  lead_id INTEGER NOT NULL REFERENCES leads(id),
  contact_id INTEGER REFERENCES contacts(id),
  name TEXT NOT NULL,
  note TEXT,
  global INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);
"""
# Columns added after the first release. connect() adds any that an older database is missing.
MIGRATIONS = [
    ("contacts", "status", "TEXT"),
    ("contacts", "sort_order", "INTEGER NOT NULL DEFAULT 0"),
    ("contacts", "ext", "TEXT"),
    ("contacts", "phone_type", "TEXT"),
    ("leads", "address", "TEXT"),
    ("leads", "facility_size", "TEXT"),
    ("leads", "solar_reference", "TEXT"),
    ("leads", "lighting_reference", "TEXT"),
    ("leads", "meeting_type", "TEXT"),
    ("leads", "appt_at", "TEXT"),
    ("leads", "callback_at", "TEXT"),
    ("leads", "expecting_call", "INTEGER NOT NULL DEFAULT 0"),
    ("activities", "called_back", "INTEGER"),
    ("leads", "main_contact_id", "INTEGER"),
]
# Older databases only knew callbacks from the comment. Recover open ones when callback_at first appears.
BACKFILL = {("leads", "callback_at"): """
    UPDATE leads SET callback_at = next_action_date
    WHERE next_action_date IS NOT NULL AND closed IS NULL AND EXISTS (
      SELECT 1 FROM activities a WHERE a.id = (SELECT id FROM activities b WHERE b.lead_id = leads.id
                                               ORDER BY timestamp DESC, id DESC LIMIT 1)
        AND (a.outcome = 'CALLBACK' OR a.myphoner_comment LIKE '%call back ' || leads.next_action_date || '%'))"""}


def connect(path=DB_PATH):
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    for table, column, kind in MIGRATIONS:
        if column not in {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {kind}")
            if (table, column) in BACKFILL:
                conn.execute(BACKFILL[(table, column)])
    conn.commit()
    return conn
