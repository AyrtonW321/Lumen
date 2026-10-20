"""Self-check with synthetic data. Run: python test_lumen.py"""
import random
from datetime import date, datetime, timedelta

import lumen

conn = lumen.connect(":memory:")
t0 = datetime(2026, 10, 19, 9, 30)  # Monday

# Repeated voicemail on the same person -> poor lead, "find another contact"
vm = lumen.add_lead(conn, "Test VM Warehouse", "Haneco", ["Lighting"], now=t0)
bob = lumen.add_contact(conn, vm, "Bob Test", "Plant Manager", now=t0)
for d in range(3):
    lumen.log_activity(conn, vm, "VM", contact_id=bob, now=t0 + timedelta(days=d))

# Open but busy -> good lead, top of the list
busy = lumen.add_lead(conn, "Test Busy Plant", "JWL", ["Solar", "BESS"], source="follow-up", now=t0)
amy = lumen.add_contact(conn, busy, "Amy Test", "Facilities Director", now=t0)
r = lumen.log_activity(conn, busy, "BUSY", contact_id=amy, callback_date="2026-10-22", note="busy till Thu",
                       now=t0 + timedelta(hours=5))
assert r["myphoner_comment"] == "BUSY 14:30 - Amy Test (Facilities Director) - call back 2026-10-22 - busy till Thu"

# Receptionist only, no decision-maker known
rcp = lumen.add_lead(conn, "Test Reception Co", "Exceledy", now=t0)
lumen.log_activity(conn, rcp, "RCP", now=t0)

# Email request marks preference
em = lumen.add_lead(conn, "Test Email Co", "Haneco", now=t0)
sue = lumen.add_contact(conn, em, "Sue Test", "Operations Manager", now=t0)
lumen.log_activity(conn, em, "EREQ", contact_id=sue, now=t0)

booked = lumen.add_lead(conn, "Test Booked Co", "Haneco", now=t0)
lumen.log_activity(conn, booked, "BKD", now=t0)

rows = {r["id"]: r for r in lumen.list_leads(conn, today=date(2026, 10, 23))}
assert any("Find another contact: Bob Test" in a for a in rows[vm]["advice"]), rows[vm]["advice"]
assert rows[busy]["advice"][0].startswith("Open to a meeting") and rows[busy]["tier"] == 1
assert rows[busy]["next_action_date"] == "2026-10-22" and rows[busy]["due"]
assert any("Contact receptionist first" in a for a in rows[rcp]["advice"])
dm_lead = lumen.add_lead(conn, "Test DM Known Co", "Haneco", now=t0)
lumen.add_contact(conn, dm_lead, "Dan Test", "Owner", now=t0)
lumen.log_activity(conn, dm_lead, "RCP", now=t0)
dm_advice = next(r["advice"] for r in lumen.list_leads(conn) if r["id"] == dm_lead)
assert any("ask for Dan Test" in a for a in dm_advice), dm_advice
assert "Sue Test prefers email" in rows[em]["advice"] and rows[em]["advice"][0] == "Send the email they asked for"
assert rows[booked]["closed"] == "BKD" and not rows[booked]["due"]
assert rows[busy]["tier"] < rows[vm]["tier"]

# Validation
for bad in [dict(lead_id=vm, outcome="CB"), dict(lead_id=vm, outcome="VM", contact_id=amy)]:
    try:
        lumen.log_activity(conn, **bad)
        raise AssertionError(f"accepted {bad}")
    except ValueError:
        pass
for bad in [dict(brand="Nope"), dict(products=["Wind"]), dict(label="great")]:
    try:
        lumen.update_lead(conn, vm, **bad)
        raise AssertionError(f"accepted {bad}")
    except ValueError:
        pass

# Lists: booked -> Winners, already has solution -> Losers, moving back reopens
assert lumen.load_all(conn)[booked]["source"] == "winner"
has = lumen.add_lead(conn, "Test Has LED Co", "JWL", now=t0)
lumen.log_activity(conn, has, "HAS", now=t0)
bad_no = lumen.add_lead(conn, "Test Bad Number Co", "JWL", now=t0)
lumen.log_activity(conn, bad_no, "BAD", now=t0)
leads = lumen.load_all(conn)
assert leads[has]["source"] == "loser" and leads[bad_no]["source"] == "new" and leads[bad_no]["closed"] == "BAD"
rows = {r["id"]: r for r in lumen.list_leads(conn, today=date(2027, 1, 1))}
assert not rows[booked]["open"] and not rows[booked]["due"] and rows[booked]["advice"] == ["Winner: meeting booked"]
assert not rows[has]["open"] and rows[has]["advice"] == ["Loser: already has a solution"]
lumen.update_lead(conn, booked, source="follow-up")
assert lumen.load_all(conn)[booked]["closed"] is None
assert {r["id"]: r for r in lumen.list_leads(conn)}[booked]["open"]
lumen.update_lead(conn, booked, source="winner")

# Reschedule only
lumen.update_lead(conn, rcp, next_action_date="2026-11-02")
assert lumen.load_all(conn)[rcp]["next_action_date"] == "2026-11-02"
for bad in [dict(next_action_date="next week"), dict(meeting_type="Carrier pigeon"), dict(appt_at="soon")]:
    try:
        lumen.update_lead(conn, rcp, **bad)
        raise AssertionError(f"accepted {bad}")
    except ValueError:
        pass

# Contacts: ext, phone type, edit
cid = lumen.add_contact(conn, rcp, "John Doe", "Facility Manager", phone="123-245-2451", ext="204",
                        phone_type="direct", email="john.doe@example.com")
lumen.update_contact(conn, cid, title="Facility Manager")
for bad in [dict(phone_type="pager"), dict(name=""), dict(colour="red")]:
    try:
        lumen.update_contact(conn, cid, **bad)
        raise AssertionError(f"accepted {bad}")
    except ValueError:
        pass

# Appointment text: full, sparse, no contact
lumen.update_lead(conn, rcp, address="123 Good Street", facility_size="40,000 sq ft", meeting_type="Online",
                  solar_reference="None", lighting_reference="Fluorescent", appt_at="2026-10-27T10:00",
                  phone="905-555-0000")
lead = lumen.lead_detail(conn, rcp)
john = next(c for c in lead["contacts"] if c["id"] == cid)
assert lumen.appointment_text(lead, john, "Ayrton") == """Name: John Doe
Title: Facility Manager
Address: 123 Good Street
Facility Size: 40,000 sq ft
Phone number: 123-245-2451 ext 204 (D)
Email: john.doe@example.com
Meeting Type: Online
Solar Reference: None
Lighting Reference: Fluorescent
Appt made by Ayrton for Tue Oct 27, 2026 at 10:00 AM"""
lumen.update_lead(conn, rcp, address="", facility_size=None)
sparse = lumen.appointment_text(lumen.lead_detail(conn, rcp), {**john, "email": None}, None)
assert not any(sparse.count(k) for k in ("Address:", "Email:", "Facility Size:", " by ")), sparse
assert "Phone number: 905-555-0000 (B)" in lumen.appointment_text(lumen.lead_detail(conn, rcp))

# Migration: an old database keeps its rows and gains the new columns
import os
import sqlite3
import tempfile
old = os.path.join(tempfile.mkdtemp(), "old.db")
raw = sqlite3.connect(old)
raw.executescript("""CREATE TABLE leads (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, brand TEXT NOT NULL,
  products TEXT NOT NULL DEFAULT '', source TEXT NOT NULL DEFAULT 'new', list_name TEXT, phone TEXT, label TEXT,
  closed TEXT, next_action_date TEXT, created_at TEXT NOT NULL);
  CREATE TABLE contacts (id INTEGER PRIMARY KEY, lead_id INTEGER NOT NULL, name TEXT NOT NULL, title TEXT,
  phone TEXT, email TEXT, prefers_email INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL);
  INSERT INTO leads (name, brand, created_at) VALUES ('Old Co', 'Haneco', '2026-10-01T09:00:00');""")
raw.commit()
raw.close()
migrated = lumen.connect(old)
row = migrated.execute("SELECT * FROM leads").fetchone()
assert row["name"] == "Old Co" and row["address"] is None
assert "phone_type" in {r["name"] for r in migrated.execute("PRAGMA table_info(contacts)")}
migrated.close()

# Winners count as good training examples
X, y, w, ids = lumen.training_examples({booked: lumen.load_all(conn)[booked]})
assert y[-1] == 1.0 and w[-1] == 3.0

# Training: features never see the call they predict
lead = lumen.load_all(conn)[busy]
X, y, w, ids = lumen.training_examples({busy: lead})
assert y == [1.0] and X[0]["positive_signals"] == 0 and X[0]["never_contacted"] == 1

try:
    import model
except ImportError:
    print("ok (torch not installed, model test skipped)")
    raise SystemExit

# Synthetic world: decision-makers who get reached say yes; voicemail streaks don't
random.seed(1)
for i in range(60):
    lid = lumen.add_lead(conn, f"Synth {i}", random.choice(list(lumen.BRANDS)), now=t0)
    good = i % 2 == 0
    cid = lumen.add_contact(conn, lid, f"Person {i}", "Facilities Manager" if good else "Clerk", now=t0)
    for d in range(4):
        outcome = random.choice(["BUSY", "EREQ", "RCP"]) if good else "VM"
        lumen.log_activity(conn, lid, outcome, contact_id=cid, now=t0 + timedelta(days=d, hours=1))
lumen.update_lead(conn, vm, label="poor")

scorer = model.Scorer.train(*lumen.training_examples(lumen.load_all(conn)))
assert scorer.metrics["beats_baseline"], scorer.metrics
rows = {r["id"]: r for r in lumen.list_leads(conn, scorer, today=date(2026, 10, 23))}
assert rows[busy]["score"] > rows[vm]["score"], (rows[busy]["score"], rows[vm]["score"])
assert rows[vm]["why"], "logistic model should explain its score"
assert "score" not in rows[booked]

import tempfile
from pathlib import Path
path = Path(tempfile.mkdtemp()) / "m.pt"
scorer.save(path)
assert model.Scorer.load(path).predict([lumen.features(lumen.load_all(conn)[vm], [], [], t0)])
print("ok", scorer.metrics)
