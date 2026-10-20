"""Lead writes and reads."""
from datetime import date, datetime

from .advice import advice
from .config import BRANDS, MEETING_TYPES, OPEN_SOURCES, PRODUCTS, SOURCES
from .features import features
from .timeutil import stamp


def clean_products(products):
    products = products.split(",") if isinstance(products, str) else (products or [])
    bad = [p for p in products if p and p not in PRODUCTS]
    if bad:
        raise ValueError(f"unknown product {bad[0]!r}")
    return ",".join(p for p in PRODUCTS if p in products)


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
    allowed = {"name", "brand", "products", "source", "list_name", "phone", "label", "next_action_date", "address",
               "facility_size", "solar_reference", "lighting_reference", "meeting_type", "appt_at"}
    if set(fields) - allowed:
        raise ValueError(f"cannot update {sorted(set(fields) - allowed)}")
    fields = {k: (v.strip() or None) if isinstance(v, str) else v for k, v in fields.items()}
    if "brand" in fields and fields["brand"] not in BRANDS:
        raise ValueError("unknown brand")
    if "source" in fields and fields["source"] not in SOURCES:
        raise ValueError("unknown source")
    if "label" in fields and fields["label"] not in ("good", "poor", None):
        raise ValueError("label must be good, poor or empty")
    if fields.get("meeting_type") and fields["meeting_type"] not in MEETING_TYPES:
        raise ValueError("unknown meeting type")
    if fields.get("next_action_date"):
        date.fromisoformat(fields["next_action_date"])  # raises ValueError on a bad date
    if fields.get("appt_at"):
        datetime.fromisoformat(fields["appt_at"])
    if "products" in fields:
        fields["products"] = clean_products(fields["products"] or "")
    if fields.get("source") in OPEN_SOURCES:
        fields["closed"] = None  # moving back to Leads or Follow-ups reopens the lead
    with conn:
        for key, value in fields.items():  # keys whitelisted above
            conn.execute(f"UPDATE leads SET {key} = ? WHERE id = ?", (value, lead_id))


def load_all(conn):
    """All leads with their contacts and activities (oldest first), keyed by lead id."""
    leads = {r["id"]: {**dict(r), "contacts": [], "activities": []} for r in conn.execute("SELECT * FROM leads")}
    for r in conn.execute("SELECT * FROM contacts ORDER BY id"):
        leads[r["lead_id"]]["contacts"].append(dict(r))
    for r in conn.execute("SELECT * FROM activities ORDER BY timestamp, id"):
        leads[r["lead_id"]]["activities"].append(dict(r))
    return leads


def is_open(lead):
    return lead["source"] in OPEN_SOURCES and not lead["closed"]


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
            "open": is_open(lead),
            "due": is_open(lead) and (not acts or (lead["next_action_date"] or "9") <= today.isoformat()),
            "_features": features(lead, lead["contacts"], acts, now),
        })
    if scorer:
        open_rows = [r for r in rows if r["open"]]
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
