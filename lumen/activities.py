"""Logging a call or email against a lead."""
from datetime import date, datetime

from .config import OUTCOMES
from .timeutil import add_business_days, hour_block, stamp


def myphoner_comment(outcome, now, contact=None, callback_date=None, note=None):
    who = contact and (f"{contact['name']} ({contact['title']})" if contact["title"] else contact["name"])
    parts = [f"{outcome} {now:%H:%M}", who, callback_date and f"call back {callback_date}", note]
    return " - ".join(p for p in parts if p)


def log_activity(conn, lead_id, outcome, contact_id=None, note=None, caller=None, callback_date=None, now=None):
    if outcome not in OUTCOMES:
        raise ValueError(f"unknown outcome {outcome!r}")
    if outcome == "OTHER" and not (note or "").strip():
        raise ValueError("describe what happened in the call log for Other")
    if callback_date:
        date.fromisoformat(callback_date)
    if outcome == "CALLBACK" and not callback_date:
        raise ValueError("choose a callback date")
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
        if rule.get("move_to"):
            conn.execute("UPDATE leads SET source = ? WHERE id = ?", (rule["move_to"], lead_id))
        # A new callback explicitly reopens the lead; prior classifications stay in history.
        if outcome == "CALLBACK" or (callback_date and not rule.get("closes") and lead["source"] in ("winner", "loser")):
            conn.execute("UPDATE leads SET source = 'follow-up', closed = NULL WHERE id = ?", (lead_id,))
        elif rule.get("closes"):
            conn.execute("UPDATE leads SET closed = ? WHERE id = ?", (outcome, lead_id))
        if outcome == "EREQ" and contact_id:
            conn.execute("UPDATE contacts SET prefers_email = 1 WHERE id = ?", (contact_id,))
    return {"id": cur.lastrowid, "myphoner_comment": comment}
