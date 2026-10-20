"""Contact writes."""
from datetime import datetime

from .config import PHONE_TYPES
from .timeutil import stamp


def clean_contact(fields):
    fields = {k: (v.strip() or None) if isinstance(v, str) else v for k, v in fields.items()}
    if "name" in fields and not fields["name"]:
        raise ValueError("contact needs a name")
    if fields.get("phone_type") and fields["phone_type"] not in PHONE_TYPES:
        raise ValueError("phone type must be direct, mobile or business")
    return fields


def add_contact(conn, lead_id, name, title=None, phone=None, email=None, ext=None, phone_type=None, now=None):
    c = clean_contact(dict(name=name or "", title=title, phone=phone, email=email, ext=ext, phone_type=phone_type))
    if conn.execute("SELECT 1 FROM leads WHERE id = ?", (lead_id,)).fetchone() is None:
        raise ValueError("unknown lead")
    cur = conn.execute(
        """INSERT INTO contacts (lead_id, name, title, phone, email, ext, phone_type, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (lead_id, c["name"], c["title"], c["phone"], c["email"], c["ext"], c["phone_type"],
         stamp(now or datetime.now())))
    conn.commit()
    return cur.lastrowid


def update_contact(conn, contact_id, **fields):
    allowed = {"name", "title", "phone", "email", "ext", "phone_type"}
    if set(fields) - allowed:
        raise ValueError(f"cannot update {sorted(set(fields) - allowed)}")
    fields = clean_contact(fields)
    if conn.execute("SELECT 1 FROM contacts WHERE id = ?", (contact_id,)).fetchone() is None:
        raise ValueError("unknown contact")
    with conn:
        for key, value in fields.items():  # keys whitelisted above
            conn.execute(f"UPDATE contacts SET {key} = ? WHERE id = ?", (value, contact_id))
