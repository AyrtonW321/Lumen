import sqlite3
import tempfile
import unittest
from pathlib import Path

from lumen.db import connect


class MigrationTests(unittest.TestCase):
    def test_old_database_keeps_rows_and_gains_new_columns(self):
        old = Path(tempfile.mkdtemp()) / "old.db"
        raw = sqlite3.connect(old)
        raw.executescript("""CREATE TABLE leads (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE,
          brand TEXT NOT NULL, products TEXT NOT NULL DEFAULT '', source TEXT NOT NULL DEFAULT 'new',
          list_name TEXT, phone TEXT, label TEXT, closed TEXT, next_action_date TEXT, created_at TEXT NOT NULL);
          CREATE TABLE contacts (id INTEGER PRIMARY KEY, lead_id INTEGER NOT NULL, name TEXT NOT NULL, title TEXT,
          phone TEXT, email TEXT, prefers_email INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL);
          INSERT INTO leads (name, brand, created_at) VALUES ('Old Co', 'Haneco', '2026-10-01T09:00:00');""")
        raw.commit()
        raw.close()
        migrated = connect(old)
        self.addCleanup(migrated.close)
        row = migrated.execute("SELECT * FROM leads").fetchone()
        self.assertEqual(row["name"], "Old Co")
        self.assertIsNone(row["address"])
        self.assertIn("phone_type", {r["name"] for r in migrated.execute("PRAGMA table_info(contacts)")})
