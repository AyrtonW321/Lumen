"""Lumen: local call logger. Stores calls in SQLite, syncs to Google Sheets on demand.

Run:  python lumen.py   then open http://127.0.0.1:8765
"""
import json
import os
import sqlite3
import threading
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent
DB_PATH = Path(os.environ.get("LUMEN_DB", ROOT / "data" / "lumen.db"))
PORT = int(os.environ.get("LUMEN_PORT", 8765))

# --- Tunables (CLAUDE.md 7.3, 7.6). Change here, nowhere else. ---
OUTCOMES = {  # locked codes, ordered by "furthest point reached"
    "VM": "Voicemail / no answer",
    "BAD": "Bad number",
    "GK": "Gatekeeper block",
    "WP": "Wrong person / left",
    "NI": "Not interested",
    "INT": "Interested",
    "BKD": "Meeting booked",
    "DNC": "Do not call",
}
RELEVANT = {"NI", "INT", "BKD"}
MARKETS = ["Ontario", "Other Canada", "Chicago"]
ROLES = ["owner", "facility/plant manager", "operations", "office admin", "other"]
OBJECTIONS = ["already upgraded", "leases", "no budget", "bad timing", "not decision-maker", "other"]
HOUR_BLOCKS = [(0, "before 9"), (9, "9-11"), (11, "11-13"), (13, "13-15"), (15, "15+")]
# Business days until next attempt. None = stop calling. NI wait is unconfirmed (Section 9, Q10).
RETRY_BUSINESS_DAYS = {"VM": 2, "GK": 1, "WP": 1, "INT": 2, "NI": 55, "BAD": None, "BKD": None, "DNC": None}
VM_FLAG_STREAK = 4   # flag: find new number/contact
VM_STOP_STREAK = 6   # cap attempts
VOICEMAIL_ON_ATTEMPTS = (1, 3)

SCHEMA = """
CREATE TABLE IF NOT EXISTS companies (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  market TEXT NOT NULL,
  list_name TEXT,
  dnc INTEGER NOT NULL DEFAULT 0,
  decision_maker_identified INTEGER NOT NULL DEFAULT 0,
  attempts INTEGER NOT NULL DEFAULT 0,
  vm_streak INTEGER NOT NULL DEFAULT 0,
  last_outcome TEXT,
  last_call_at TEXT,
  next_retry_date TEXT
);
CREATE TABLE IF NOT EXISTS calls (
  id INTEGER PRIMARY KEY,
  company_id INTEGER NOT NULL REFERENCES companies(id),
  contact_name TEXT,
  timestamp TEXT NOT NULL,
  weekday TEXT NOT NULL,
  hour_block TEXT NOT NULL,
  attempt_number INTEGER NOT NULL,
  days_since_last_attempt INTEGER,
  outcome TEXT NOT NULL,
  role_reached TEXT,
  objection TEXT,
  voicemail_left INTEGER NOT NULL DEFAULT 0,
  callback_date TEXT,
  gatekeeper_gave_name INTEGER NOT NULL DEFAULT 0,
  note TEXT,
  caller TEXT,
  source TEXT NOT NULL DEFAULT 'logger',
  myphoner_comment TEXT NOT NULL
);
"""


def connect(path=DB_PATH):
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def hour_block(dt):
    return [label for start, label in HOUR_BLOCKS if dt.hour >= start][-1]


def add_business_days(d, n):
    while n > 0:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def next_retry(outcome, now, callback_date, vm_streak):
    if outcome == "INT" and callback_date:
        return callback_date
    days = RETRY_BUSINESS_DAYS[outcome]
    if days is None or vm_streak >= VM_STOP_STREAK:
        return None
    return add_business_days(now.date(), days).isoformat()


def myphoner_comment(outcome, now, role=None, objection=None, contact=None, note=None, callback_date=None):
    parts = [f"{outcome} {now:%H:%M}"]
    parts += [p for p in (contact, role, objection) if p]
    if callback_date:
        parts.append(f"call back {callback_date}")
    if note:
        parts.append(note)
    return " - ".join(parts)


def add_company(conn, name, market, list_name=None):
    name = (name or "").strip()
    if not name or market not in MARKETS:
        raise ValueError("company needs a name and a valid market")
    cur = conn.execute("INSERT INTO companies (name, market, list_name) VALUES (?, ?, ?)", (name, market, list_name))
    conn.commit()
    return cur.lastrowid


def log_call(conn, company_id, outcome, now=None, role_reached=None, objection=None, contact_name=None,
             voicemail_left=False, callback_date=None, gatekeeper_gave_name=False, note=None, caller=None):
    if outcome not in OUTCOMES:
        raise ValueError(f"unknown outcome {outcome!r}")
    if role_reached and role_reached not in ROLES:
        raise ValueError(f"unknown role {role_reached!r}")
    if objection and objection not in OBJECTIONS:
        raise ValueError(f"unknown objection {objection!r}")
    co = conn.execute("SELECT * FROM companies WHERE id = ?", (company_id,)).fetchone()
    if co is None:
        raise ValueError("unknown company")

    now = now or datetime.now()
    attempt = co["attempts"] + 1
    days_since = (now.date() - datetime.fromisoformat(co["last_call_at"]).date()).days if co["last_call_at"] else None
    vm_streak = co["vm_streak"] + 1 if outcome == "VM" else 0
    comment = myphoner_comment(outcome, now, role_reached, objection, contact_name, note, callback_date)

    with conn:
        cur = conn.execute(
            """INSERT INTO calls (company_id, contact_name, timestamp, weekday, hour_block, attempt_number,
               days_since_last_attempt, outcome, role_reached, objection, voicemail_left, callback_date,
               gatekeeper_gave_name, note, caller, myphoner_comment)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (company_id, contact_name, now.isoformat(timespec="seconds"), now.strftime("%a"), hour_block(now),
             attempt, days_since, outcome, role_reached, objection, int(voicemail_left), callback_date,
             int(gatekeeper_gave_name), note, caller, comment))
        conn.execute(
            """UPDATE companies SET attempts = ?, vm_streak = ?, last_outcome = ?, last_call_at = ?,
               next_retry_date = ?, dnc = dnc OR ?, decision_maker_identified = decision_maker_identified OR ?
               WHERE id = ?""",
            (attempt, vm_streak, outcome, now.isoformat(timespec="seconds"),
             next_retry(outcome, now, callback_date, vm_streak), outcome == "DNC", outcome in RELEVANT,
             company_id))
    return {"id": cur.lastrowid, "attempt_number": attempt, "myphoner_comment": comment}


def list_companies(conn, today=None):
    today = (today or date.today()).isoformat()
    rows = [dict(r) for r in conn.execute("SELECT * FROM companies ORDER BY name")]
    for r in rows:
        r["due"] = bool(not r["dnc"] and r["next_retry_date"] and r["next_retry_date"] <= today)
        r["needs_new_contact"] = r["vm_streak"] >= VM_FLAG_STREAK
        r["leave_voicemail_next"] = (r["attempts"] + 1) in VOICEMAIL_ON_ATTEMPTS
    return rows


def sync_to_sheets(conn):
    """Rewrite the 'Lumen Calls' and 'Lumen Companies' tabs. Leaves every other tab alone."""
    import gspread  # optional dependency; logging works without it

    # ponytail: full rewrite each sync; switch to append-only if calls reach tens of thousands
    sheet = gspread.service_account(filename=os.environ["LUMEN_GOOGLE_CREDENTIALS"]).open_by_key(
        os.environ["LUMEN_SHEET_ID"])
    tabs = {
        "Lumen Calls": "SELECT c.name AS company, k.* FROM calls k JOIN companies c ON c.id = k.company_id ORDER BY k.id",
        "Lumen Companies": "SELECT * FROM companies ORDER BY name",
    }
    counts = {}
    for title, sql in tabs.items():
        cur = conn.execute(sql)
        rows = [[d[0] for d in cur.description]] + [["" if v is None else v for v in r] for r in cur]
        try:
            ws = sheet.worksheet(title)
        except gspread.WorksheetNotFound:
            ws = sheet.add_worksheet(title, rows=len(rows) + 100, cols=len(rows[0]))
        ws.clear()
        ws.update(rows)
        counts[title] = len(rows) - 1
    return counts


class Handler(BaseHTTPRequestHandler):
    conn = None
    lock = threading.Lock()  # one shared SQLite connection

    def _send(self, status, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        with self.lock:
            self._get()

    def do_POST(self):
        with self.lock:
            self._post()

    def _get(self):
        if self.path == "/":
            return self._send(200, (ROOT / "index.html").read_bytes(), "text/html; charset=utf-8")
        if self.path == "/api/config":
            return self._send(200, {"outcomes": OUTCOMES, "markets": MARKETS, "roles": ROLES, "objections": OBJECTIONS})
        if self.path == "/api/companies":
            return self._send(200, list_companies(self.conn))
        if self.path.startswith("/api/companies/") and self.path.endswith("/calls"):
            cid = self.path.split("/")[3]
            rows = self.conn.execute("SELECT * FROM calls WHERE company_id = ? ORDER BY id DESC", (cid,))
            return self._send(200, [dict(r) for r in rows])
        self._send(404, {"error": "not found"})

    def _post(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        try:
            if self.path == "/api/companies":
                return self._send(201, {"id": add_company(self.conn, body.get("name"), body.get("market"), body.get("list_name"))})
            if self.path == "/api/calls":
                body.pop("now", None)
                return self._send(201, log_call(self.conn, **body))
            if self.path == "/api/sync":
                return self._send(200, sync_to_sheets(self.conn))
        except (ValueError, TypeError, sqlite3.IntegrityError) as e:
            return self._send(400, {"error": str(e)})
        except Exception as e:  # sync failures (no creds, offline) must not crash the logger
            return self._send(500, {"error": f"{type(e).__name__}: {e}"})
        self._send(404, {"error": "not found"})

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    Handler.conn = connect()
    print(f"Lumen running at http://127.0.0.1:{PORT}  (data: {DB_PATH})")
    # threaded: Chrome holds idle preconnect sockets that would block a single-threaded server
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
