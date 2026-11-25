"""Person and company traits, plus badges worked out from call history."""
from datetime import datetime

from .config import (BROKEN_PROMISE_LIMIT, COMPANY_TRAITS, LEAD_VM_LIMIT, OUTCOMES, PERSON_TRAITS,
                     RESPONSIVE_MIN_CALLS, RESPONSIVE_WINDOW)
from .features import trailing
from .timeutil import stamp

NAME_MAX, NOTE_MAX = 40, 200
NOT_CALLS = {"EMAILED", "WIN", "LOST", "OTHER"}  # classifications and emails say nothing about picking up


def catalog(conn):
    """Traits offered in the picker and filter: presets plus custom traits saved for reuse."""
    out = {"person": list(PERSON_TRAITS), "company": list(COMPANY_TRAITS)}
    for r in conn.execute("SELECT name, contact_id IS NOT NULL AS person FROM traits WHERE global = 1 ORDER BY name"):
        names = out["person" if r["person"] else "company"]
        if r["name"].lower() not in {n.lower() for n in names}:
            names.append(r["name"])
    return out


def _target(conn, lead_id, contact_id):
    if conn.execute("SELECT 1 FROM leads WHERE id = ?", (lead_id,)).fetchone() is None:
        raise ValueError("unknown lead")
    if contact_id and conn.execute("SELECT 1 FROM contacts WHERE id = ? AND lead_id = ?",
                                   (contact_id, lead_id)).fetchone() is None:
        raise ValueError("contact does not belong to this lead")


def _clean(name, note):
    name, note = (name or "").strip(), (note or "").strip() or None
    if not name or len(name) > NAME_MAX:
        raise ValueError(f"trait needs a name of 1-{NAME_MAX} characters")
    if note and len(note) > NOTE_MAX:
        raise ValueError(f"trait note is limited to {NOTE_MAX} characters")
    return name, note


def add_trait(conn, lead_id, name, contact_id=None, note=None, save=False, now=None):
    """Adds a trait, or updates its note if this person or company already has it. Returns the trait id."""
    name, note = _clean(name, note)
    _target(conn, lead_id, contact_id)
    known = {n.lower(): n for n in catalog(conn)["person" if contact_id else "company"]}
    if name.lower() in known:  # reuse the existing spelling, so filters never split
        name, save = known[name.lower()], True
    same = conn.execute("SELECT id FROM traits WHERE lead_id = ? AND contact_id IS ? AND lower(name) = ?",
                        (lead_id, contact_id or None, name.lower())).fetchone()
    with conn:
        if same:
            conn.execute("UPDATE traits SET note = ? WHERE id = ?", (note, same["id"]))
            return same["id"]
        return conn.execute(
            "INSERT INTO traits (lead_id, contact_id, name, note, global, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (lead_id, contact_id or None, name, note, int(bool(save)), stamp(now or datetime.now()))).lastrowid


def update_trait(conn, trait_id, **fields):
    if set(fields) - {"note", "global"}:
        raise ValueError(f"cannot update {sorted(set(fields) - {'note', 'global'})}")
    row = conn.execute("SELECT * FROM traits WHERE id = ?", (trait_id,)).fetchone()
    if row is None:
        raise ValueError("unknown trait")
    _, note = _clean(row["name"], fields.get("note", row["note"]))
    with conn:
        conn.execute("UPDATE traits SET note = ?, global = ? WHERE id = ?",
                     (note, int(bool(fields.get("global", row["global"]))), trait_id))


def delete_trait(conn, trait_id):
    with conn:
        if conn.execute("DELETE FROM traits WHERE id = ?", (trait_id,)).rowcount == 0:
            raise ValueError("unknown trait")


def badges(acts):
    """Automatic badges from calls (oldest first). Pass one contact's calls for a person, all for a company."""
    calls = [a for a in acts if a["outcome"] not in NOT_CALLS]
    recent = calls[-RESPONSIVE_WINDOW:]
    picked = sum(1 for a in recent if OUTCOMES[a["outcome"]].get("human") or a["outcome"] == "CALLBACK")
    out = []
    if len(recent) >= RESPONSIVE_MIN_CALLS and picked * 2 >= len(recent):
        out.append("Responsive")
    if trailing(calls, "VM") >= LEAD_VM_LIMIT:
        out.append("Hard to reach")
    if sum(1 for a in acts if a.get("called_back") == 0) >= BROKEN_PROMISE_LIMIT:
        out.append("Doesn't call back")
    return out
