"""Self-check with synthetic data. Run: python test_lumen.py"""
from datetime import date, datetime

import lumen

conn = lumen.connect(":memory:")
co = lumen.add_company(conn, "Acme Test Warehouse", "Ontario", "synthetic")

# Monday 14:05 voicemail
r = lumen.log_call(conn, co, "VM", now=datetime(2026, 10, 19, 14, 5), voicemail_left=True)
assert r["attempt_number"] == 1
assert r["myphoner_comment"] == "VM 14:05"
c = conn.execute("SELECT * FROM companies WHERE id = ?", (co,)).fetchone()
assert c["next_retry_date"] == "2026-10-21" and c["vm_streak"] == 1
k = conn.execute("SELECT * FROM calls").fetchone()
assert (k["weekday"], k["hour_block"], k["days_since_last_attempt"]) == ("Mon", "13-15", None)

# Friday retry skips weekend; days_since derived
r = lumen.log_call(conn, co, "GK", now=datetime(2026, 10, 23, 9, 30), gatekeeper_gave_name=True)
c = conn.execute("SELECT * FROM companies WHERE id = ?", (co,)).fetchone()
assert r["attempt_number"] == 2 and c["next_retry_date"] == "2026-10-26" and c["vm_streak"] == 0
assert conn.execute("SELECT days_since_last_attempt FROM calls WHERE id = 2").fetchone()[0] == 4

# INT with callback date uses it; relevant contact marks decision-maker
lumen.log_call(conn, co, "INT", now=datetime(2026, 10, 26, 10, 0), role_reached="owner",
               contact_name="J. Test", callback_date="2026-11-02")
c = conn.execute("SELECT * FROM companies WHERE id = ?", (co,)).fetchone()
assert c["next_retry_date"] == "2026-11-02" and c["decision_maker_identified"] == 1
assert conn.execute("SELECT myphoner_comment FROM calls WHERE id = 3").fetchone()[0] == \
    "INT 10:00 - J. Test - owner - call back 2026-11-02"

# VM streak: flag at 4, stop at 6
co2 = lumen.add_company(conn, "Beta Test Plant", "Chicago")
for day in range(1, 7):
    lumen.log_call(conn, co2, "VM", now=datetime(2026, 11, day + 1, 11, 0))
rows = {r["id"]: r for r in lumen.list_companies(conn, today=date(2026, 12, 1))}
assert rows[co2]["needs_new_contact"] and rows[co2]["next_retry_date"] is None and not rows[co2]["due"]
assert rows[co]["due"]

# DNC is never due
lumen.log_call(conn, co, "DNC", now=datetime(2026, 11, 3, 9, 0))
assert not {r["id"]: r for r in lumen.list_companies(conn, today=date(2027, 1, 1))}[co]["due"]

# Validation
for bad in [dict(outcome="CB"), dict(outcome="VM", role_reached="ceo"), dict(outcome="NI", objection="meh")]:
    try:
        lumen.log_call(conn, co, **bad)
        raise AssertionError(f"accepted {bad}")
    except ValueError:
        pass

print("ok")
