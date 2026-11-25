"""Callbacks dropdown: callbacks you owe, plus leads you're expecting a call from."""
from datetime import datetime, timedelta

from .config import UPCOMING_DAYS
from .leads import load_all
from .traits import badges

SECTIONS = ["expecting", "overdue", "today", "upcoming"]


def _who(lead):
    """The contact you last spoke to, else the first one on file."""
    by_id = {c["id"]: c for c in lead["contacts"]}
    last = next((a["contact_id"] for a in reversed(lead["activities"]) if a["contact_id"] in by_id), None)
    return by_id.get(last) or (lead["contacts"][0] if lead["contacts"] else None)


def callbacks(conn, now=None):
    now = now or datetime.now()
    today, horizon = now.date().isoformat(), (now.date() + timedelta(days=UPCOMING_DAYS)).isoformat()
    rows = []
    for lead in load_all(conn).values():
        at = lead["callback_at"]
        if lead["closed"] or not (at or lead["expecting_call"]):
            continue
        day = (at or "")[:10]
        section = ("expecting" if lead["expecting_call"] else "overdue" if day < today
                   else "today" if day == today else "upcoming" if day <= horizon else None)
        if section is None:
            continue
        c = _who(lead)
        phone = c["phone"] if c and c["phone"] else lead["phone"]
        ext = c["ext"] if c and c["phone"] else None
        rows.append({
            "id": lead["id"], "name": lead["name"], "brand": lead["brand"], "section": section, "callback_at": at,
            "late": bool(at and len(at) > 10 and datetime.fromisoformat(at) < now),
            "contact": c and {"name": c["name"], "title": c["title"]},
            "phone": phone, "ext": ext,
            "last_note": next((a["note"] for a in reversed(lead["activities"]) if a["note"]), None),
            "traits": [{"name": t["name"], "note": t["note"], "person": t["contact_id"] is not None}
                       for t in lead["traits"]],
            "badges": badges(lead["activities"]),
        })
    # Timed callbacks sort before untimed ones on the same day.
    rows.sort(key=lambda r: (SECTIONS.index(r["section"]), (r["callback_at"] or "")[:10],
                             (r["callback_at"] or "")[11:] or "99", r["name"]))
    return rows
