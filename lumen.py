"""Lumen: local lead tracker and call logger. SQLite storage, Google Sheets sync, PyTorch lead scoring.

Run:  python lumen.py   then open http://127.0.0.1:8765
"""
import json
import math
import os
import re
import sqlite3
import sys
import threading
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent
DB_PATH = Path(os.environ.get("LUMEN_DB", ROOT / "data" / "lumen.db"))
MODEL_PATH = Path(os.environ.get("LUMEN_MODEL", ROOT / "data" / "model.pt"))
PORT = int(os.environ.get("LUMEN_PORT", 8765))

# --- Tunables. Change here, nowhere else. ---
BRANDS = {"Haneco": "Canada", "JWL": "Chicago", "Exceledy": "Texas"}
PRODUCTS = ["Solar", "Lighting", "BESS"]
SOURCES = {"new": "New (MyPhoner list)", "follow-up": "Follow-up list"}
# key: hotkey | retry: business days to next action (None = stop) | human: reached a person
# positive: counts as a good result | closes: lead is done (excluded from ranking)
# PD11 mapping: RCP = GK, BUSY and EREQ = INT, HAS = MyPhoner loser.
OUTCOMES = {
    "VM":      dict(label="Voicemail / no answer", key="v", retry=2),
    "RCP":     dict(label="Receptionist", key="r", retry=1, human=True),
    "WP":      dict(label="Wrong person / left", key="w", retry=1, human=True),
    "EREQ":    dict(label="Requested email", key="m", retry=2, human=True, positive=True),
    "EMAILED": dict(label="Emailed", key="e", retry=2),
    "BUSY":    dict(label="Interested, busy", key="i", retry=2, human=True, positive=True),
    "NI":      dict(label="Not interested", key="n", retry=55, human=True),
    "BKD":     dict(label="Meeting booked", key="b", retry=None, human=True, positive=True, closes=True),
    "HAS":     dict(label="Already has solution", key="h", retry=None, human=True, closes=True),
    "BAD":     dict(label="Bad number", key="x", retry=None, closes=True),
    "DNC":     dict(label="Do not call", key="d", retry=None, human=True, closes=True),
}
DECISION_TITLES = re.compile(r"owner|president|ceo|manager|director|facilit|operations|plant|maintenance|vp", re.I)
CONTACT_VM_LIMIT = 3   # same person, voicemail N times in a row -> find another contact
LEAD_VM_LIMIT = 4      # whole lead, voicemail N times in a row -> new number / go through reception
HOUR_BLOCKS = [(0, "before 9"), (9, "9-11"), (11, "11-13"), (13, "13-15"), (15, "15+")]

SCHEMA = """
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
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS contacts (
  id INTEGER PRIMARY KEY,
  lead_id INTEGER NOT NULL REFERENCES leads(id),
  name TEXT NOT NULL,
  title TEXT,
  phone TEXT,
  email TEXT,
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
"""


def connect(path=DB_PATH):
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def stamp(dt):
    return dt.isoformat(timespec="seconds")


def hour_block(dt):
    return [label for start, label in HOUR_BLOCKS if dt.hour >= start][-1]


def add_business_days(d, n):
    while n > 0:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def clean_products(products):
    products = products.split(",") if isinstance(products, str) else (products or [])
    bad = [p for p in products if p and p not in PRODUCTS]
    if bad:
        raise ValueError(f"unknown product {bad[0]!r}")
    return ",".join(p for p in PRODUCTS if p in products)


# --- Writes ---

def add_lead(conn, name, brand, products=(), source="new", list_name=None, phone=None, now=None):
    name = (name or "").strip()
    if not name or brand not in BRANDS or source not in SOURCES:
        raise ValueError("lead needs a name, a valid brand and a valid source")
    cur = conn.execute(
        "INSERT INTO leads (name, brand, products, source, list_name, phone, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (name, brand, clean_products(products), source, list_name, phone, stamp(now or datetime.now())))
    conn.commit()
    return cur.lastrowid


def update_lead(conn, lead_id, **fields):
    allowed = {"name", "brand", "products", "source", "list_name", "phone", "label"}
    if set(fields) - allowed:
        raise ValueError(f"cannot update {sorted(set(fields) - allowed)}")
    if "brand" in fields and fields["brand"] not in BRANDS:
        raise ValueError("unknown brand")
    if "source" in fields and fields["source"] not in SOURCES:
        raise ValueError("unknown source")
    if "label" in fields and fields["label"] not in ("good", "poor", None):
        raise ValueError("label must be good, poor or empty")
    if "products" in fields:
        fields["products"] = clean_products(fields["products"])
    for key, value in fields.items():  # keys whitelisted above
        conn.execute(f"UPDATE leads SET {key} = ? WHERE id = ?", (value, lead_id))
    conn.commit()


def add_contact(conn, lead_id, name, title=None, phone=None, email=None, now=None):
    name = (name or "").strip()
    if not name:
        raise ValueError("contact needs a name")
    if conn.execute("SELECT 1 FROM leads WHERE id = ?", (lead_id,)).fetchone() is None:
        raise ValueError("unknown lead")
    cur = conn.execute(
        "INSERT INTO contacts (lead_id, name, title, phone, email, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (lead_id, name, title, phone, email, stamp(now or datetime.now())))
    conn.commit()
    return cur.lastrowid


def myphoner_comment(outcome, now, contact=None, callback_date=None, note=None):
    who = contact and (f"{contact['name']} ({contact['title']})" if contact["title"] else contact["name"])
    parts = [f"{outcome} {now:%H:%M}", who, callback_date and f"call back {callback_date}", note]
    return " - ".join(p for p in parts if p)


def log_activity(conn, lead_id, outcome, contact_id=None, note=None, caller=None, callback_date=None, now=None):
    if outcome not in OUTCOMES:
        raise ValueError(f"unknown outcome {outcome!r}")
    lead = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    if lead is None:
        raise ValueError("unknown lead")
    contact = None
    if contact_id:
        contact = conn.execute("SELECT * FROM contacts WHERE id = ? AND lead_id = ?", (contact_id, lead_id)).fetchone()
        if contact is None:
            raise ValueError("contact does not belong to this lead")

    now = now or datetime.now()
    rule = OUTCOMES[outcome]
    comment = myphoner_comment(outcome, now, contact, callback_date, note)
    if callback_date:
        next_action = callback_date
    elif rule["retry"] is None:
        next_action = None
    else:
        next_action = add_business_days(now.date(), rule["retry"]).isoformat()

    with conn:
        cur = conn.execute(
            """INSERT INTO activities (lead_id, contact_id, timestamp, weekday, hour_block, outcome, note, caller,
               myphoner_comment) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (lead_id, contact_id, stamp(now), now.strftime("%a"), hour_block(now), outcome, note, caller, comment))
        conn.execute("UPDATE leads SET next_action_date = ?, closed = COALESCE(closed, ?) WHERE id = ?",
                     (next_action, outcome if rule.get("closes") else None, lead_id))
        if outcome == "EREQ" and contact_id:
            conn.execute("UPDATE contacts SET prefers_email = 1 WHERE id = ?", (contact_id,))
    return {"id": cur.lastrowid, "myphoner_comment": comment}


# --- Reads ---

def load_all(conn):
    """All leads with their contacts and activities (oldest first), keyed by lead id."""
    leads = {r["id"]: {**dict(r), "contacts": [], "activities": []} for r in conn.execute("SELECT * FROM leads")}
    for r in conn.execute("SELECT * FROM contacts ORDER BY id"):
        leads[r["lead_id"]]["contacts"].append(dict(r))
    for r in conn.execute("SELECT * FROM activities ORDER BY timestamp, id"):
        leads[r["lead_id"]]["activities"].append(dict(r))
    return leads


def trailing(acts, outcome, contact_id=...):
    n = 0
    for a in reversed(acts):
        if contact_id is not ... and a["contact_id"] != contact_id:
            continue
        if a["outcome"] != outcome:
            break
        n += 1
    return n


def features(lead, contacts, acts, now):
    """Numbers the model sees. Only uses what was known at `now`, so training never peeks at the answer."""
    calls = [a for a in acts if a["outcome"] != "EMAILED"]
    outcomes = {a["outcome"] for a in acts}
    last = datetime.fromisoformat(acts[-1]["timestamp"]) if acts else None
    f = {f"brand_{b}": float(lead["brand"] == b) for b in BRANDS}
    f |= {f"product_{p}": float(p in lead["products"].split(",")) for p in PRODUCTS}
    f |= {
        "follow_up_list": float(lead["source"] == "follow-up"),
        "attempts": min(len(calls), 10) / 10,
        "reached_a_person": float(any(OUTCOMES[o].get("human") for o in outcomes)),
        "reached_receptionist": float("RCP" in outcomes),
        "positive_signals": min(sum(OUTCOMES[a["outcome"]].get("positive", False) for a in acts), 3) / 3,
        "said_not_interested": float("NI" in outcomes),
        "wrong_person": float("WP" in outcomes),
        "voicemail_streak": min(trailing(calls, "VM"), 6) / 6,
        "same_contact_voicemail_streak": min(max([trailing(calls, "VM", c["id"]) for c in contacts] or [0]), 6) / 6,
        "prefers_email": float("EREQ" in outcomes),
        "emailed": float("EMAILED" in outcomes),
        "contacts_known": min(len(contacts), 5) / 5,
        "decision_maker_known": float(any(DECISION_TITLES.search(c["title"] or "") for c in contacts)),
        "days_since_last_touch": min((now - last).days, 60) / 60 if last else 1.0,
        "never_contacted": float(not acts),
    }
    return f


def advice(lead, contacts, acts):
    """Plain-language next steps, plus a tier (lower = call sooner) used when no model is trained."""
    if lead["closed"]:
        return [f"Closed: {OUTCOMES[lead['closed']]['label']}"], 99
    tips, tier = [], 5
    if not acts:
        tips.append("New lead: make the first call")
        tier = 3
    for c in contacts:
        n = trailing([a for a in acts if a["outcome"] != "EMAILED"], "VM", c["id"])
        if n >= CONTACT_VM_LIMIT:
            tips.append(f"Find another contact: {c['name']} hit voicemail {n} times in a row")
            tier = max(tier, 6)
        if c["prefers_email"]:
            tips.append(f"{c['name']} prefers email")
    if trailing([a for a in acts if a["outcome"] != "EMAILED"], "VM") >= LEAD_VM_LIMIT:
        tips.append(f"{LEAD_VM_LIMIT}+ voicemails in a row: try another number or go through reception")
        tier = max(tier, 7)
    has_dm = any(DECISION_TITLES.search(c["title"] or "") for c in contacts)
    if any(a["outcome"] in ("RCP", "WP") for a in acts) and not has_dm:
        tips.append("Contact receptionist first: ask for the facilities or operations manager by name")
    elif contacts and not has_dm:
        tips.append("No decision-maker on file: find the owner, facilities or operations manager")
    if acts:
        last = acts[-1]["outcome"]
        if last == "BUSY":
            tips.insert(0, "Open to a meeting but busy: offer two specific times")
            tier = 1
        elif last == "EREQ":
            tips.insert(0, "Send the email they asked for")
            tier = 2
        elif last == "EMAILED":
            tips.insert(0, "Call to follow up on the email")
            tier = 2
        elif last == "NI":
            tips.append("Said not interested: wait before retrying")
            tier = 8
        elif last == "WP":
            tips.append("Wrong person: ask who handles facilities or energy costs")
            tier = 4
        elif last in ("VM", "RCP"):
            tier = max(tier, 4)
            dm = next((c for c in reversed(contacts) if DECISION_TITLES.search(c["title"] or "")), None)
            if last == "RCP" and dm:
                tips.append(f"Reached reception last time: ask for {dm['name']} by name or a direct line")
    return tips, tier


def training_examples(leads):
    """One example per call: features before the call -> was the call positive. Plus your Good/Poor labels."""
    X, y, w, ids = [], [], [], []
    for lead in leads.values():
        acts = lead["activities"]
        for i, a in enumerate(acts):
            if a["outcome"] == "EMAILED":
                continue
            t = datetime.fromisoformat(a["timestamp"])
            known = [c for c in lead["contacts"] if c["created_at"] <= a["timestamp"]]
            X.append(features(lead, known, acts[:i], t))
            y.append(float(OUTCOMES[a["outcome"]].get("positive", False)))
            w.append(1.0)
            ids.append(lead["id"])
        if lead["label"]:
            X.append(features(lead, lead["contacts"], acts, datetime.now()))
            y.append(float(lead["label"] == "good"))
            w.append(3.0)  # your judgement counts more than a single call
            ids.append(lead["id"])
    return X, y, w, ids


def list_leads(conn, scorer=None, today=None):
    today = today or date.today()
    now = datetime.combine(today, datetime.now().time())
    leads = load_all(conn)
    rows = []
    for lead in leads.values():
        tips, tier = advice(lead, lead["contacts"], lead["activities"])
        acts = lead["activities"]
        rows.append({
            **{k: lead[k] for k in ("id", "name", "brand", "products", "source", "list_name", "label", "closed",
                                    "next_action_date")},
            "last_outcome": acts[-1]["outcome"] if acts else None,
            "attempts": len(acts),
            "advice": tips,
            "tier": tier,
            "due": not lead["closed"] and (not acts or (lead["next_action_date"] or "9") <= today.isoformat()),
            "_features": features(lead, lead["contacts"], acts, now),
        })
    if scorer:
        open_rows = [r for r in rows if not r["closed"]]
        for r, (p, why) in zip(open_rows, scorer.predict([r["_features"] for r in open_rows])):
            r["score"], r["why"] = p, why
    for r in rows:
        del r["_features"]
    return rows


def lead_detail(conn, lead_id):
    lead = load_all(conn).get(lead_id)
    if lead is None:
        raise ValueError("unknown lead")
    lead["activities"].reverse()
    return lead


def sync_to_sheets(conn):
    """Rewrite the Lumen tabs. Leaves every other tab alone."""
    import gspread  # optional dependency; tracking works without it

    # ponytail: full rewrite each sync; switch to append-only if activities reach tens of thousands
    sheet = gspread.service_account(filename=os.environ["LUMEN_GOOGLE_CREDENTIALS"]).open_by_key(
        os.environ["LUMEN_SHEET_ID"])
    tabs = {
        "Lumen Leads": "SELECT * FROM leads ORDER BY name",
        "Lumen Contacts": "SELECT l.name AS lead, c.* FROM contacts c JOIN leads l ON l.id = c.lead_id ORDER BY l.name",
        "Lumen Activities": """SELECT l.name AS lead, c.name AS contact, c.title, a.* FROM activities a
                               JOIN leads l ON l.id = a.lead_id LEFT JOIN contacts c ON c.id = a.contact_id
                               ORDER BY a.timestamp""",
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


def load_scorer():
    if not MODEL_PATH.exists():
        return None
    try:
        import model
        return model.Scorer.load(MODEL_PATH)
    except ImportError:
        return None


class Handler(BaseHTTPRequestHandler):
    conn = None
    scorer = None
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
            self._route(self._get)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        with self.lock:
            self._route(lambda: self._post(body))

    def _route(self, handler):
        try:
            handler()
        except (ValueError, TypeError, KeyError, sqlite3.IntegrityError) as e:
            self._send(400, {"error": str(e)})
        except Exception as e:  # sync/train failures (no creds, no torch, offline) must not crash the tracker
            self._send(500, {"error": f"{type(e).__name__}: {e}"})

    def _get(self):
        parts = self.path.strip("/").split("/")
        if self.path == "/":
            return self._send(200, (ROOT / "index.html").read_bytes(), "text/html; charset=utf-8")
        if self.path == "/api/config":
            return self._send(200, {"brands": BRANDS, "products": PRODUCTS, "sources": SOURCES, "outcomes": OUTCOMES,
                                    "model": self.scorer.metrics if self.scorer else None})
        if self.path == "/api/leads":
            return self._send(200, list_leads(self.conn, self.scorer))
        if parts[:2] == ["api", "leads"] and len(parts) == 3:
            return self._send(200, lead_detail(self.conn, int(parts[2])))
        self._send(404, {"error": "not found"})

    def _post(self, body):
        parts = self.path.strip("/").split("/")
        if self.path == "/api/leads":
            return self._send(201, {"id": add_lead(self.conn, **body)})
        if parts[:2] == ["api", "leads"] and len(parts) == 3:
            update_lead(self.conn, int(parts[2]), **body)
            return self._send(200, {"ok": True})
        if parts[:2] == ["api", "leads"] and parts[3:] == ["contacts"]:
            return self._send(201, {"id": add_contact(self.conn, int(parts[2]), **body)})
        if self.path == "/api/activities":
            body.pop("now", None)
            return self._send(201, log_activity(self.conn, **body))
        if self.path == "/api/train":
            try:
                import model
            except ImportError:
                raise RuntimeError(f'PyTorch missing for this Python. Run: "{sys.executable}" -m pip install torch')
            Handler.scorer = model.Scorer.train(*training_examples(load_all(self.conn)))
            Handler.scorer.save(MODEL_PATH)
            return self._send(200, Handler.scorer.metrics)
        if self.path == "/api/sync":
            return self._send(200, sync_to_sheets(self.conn))
        self._send(404, {"error": "not found"})

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    Handler.conn = connect()
    Handler.scorer = load_scorer()
    print(f"Lumen running at http://127.0.0.1:{PORT}  (data: {DB_PATH})")
    # threaded: Chrome holds idle preconnect sockets that would block a single-threaded server
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
