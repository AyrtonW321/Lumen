"""Calendar-invite text for a booked meeting."""
from datetime import datetime

from .config import PHONE_TYPES


def appointment_text(lead, contact=None, caller=None):
    """Lines with no value are left out entirely."""
    c = contact or {}
    phone = c.get("phone") or lead["phone"]
    if phone:
        ext = c.get("ext") if c.get("phone") else None
        kind = PHONE_TYPES.get(c.get("phone_type") if c.get("phone") else "business")
        phone = " ".join(p for p in (phone, ext and f"ext {ext}", kind and f"({kind})") if p)
    appt = None
    if lead["appt_at"]:
        t = datetime.fromisoformat(lead["appt_at"])
        appt = f"{t:%a %b} {t.day}, {t.year} at {t:%I:%M %p}".replace(" at 0", " at ")
    made = " ".join(p for p in ("Appt made", caller and f"by {caller}", appt and f"for {appt}") if p)
    lines = [
        ("Name", c.get("name")),
        ("Title", c.get("title")),
        ("Address", lead["address"]),
        ("Facility Size", lead["facility_size"]),
        ("Phone number", phone),
        ("Email", c.get("email")),
        ("Meeting Type", lead["meeting_type"]),
        ("Solar Reference", lead["solar_reference"]),
        ("Lighting Reference", lead["lighting_reference"]),
    ]
    out = [f"{k}: {v}" for k, v in lines if v]
    if caller or appt:
        out.append(made)
    return "\n".join(out)
