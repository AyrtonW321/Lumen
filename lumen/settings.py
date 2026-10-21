"""Local preferences shared by browser and desktop sessions."""
import time


def caller_name(conn):
    row = conn.execute("SELECT value FROM settings WHERE key = 'caller_name'").fetchone()
    return row["value"] if row else None


def save_caller_name(conn, name, revision=None):
    if not isinstance(name, str):
        raise ValueError("caller name must be text")
    if revision is None:
        revision = time.time_ns() // 1_000_000
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
        raise ValueError("invalid settings revision")
    with conn:
        conn.execute("""INSERT INTO settings (key, value, revision) VALUES ('caller_name', ?, ?)
                        ON CONFLICT(key) DO UPDATE SET value = excluded.value, revision = excluded.revision
                        WHERE excluded.revision >= settings.revision""", (name, revision))
