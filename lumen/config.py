"""Paths and tunables. Change values here, nowhere else."""
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT / "web" / "dist"  # built by `npm run build` in web/
DB_PATH = Path(os.environ.get("LUMEN_DB", ROOT / "data" / "lumen.db"))
MODEL_PATH = Path(os.environ.get("LUMEN_MODEL", ROOT / "data" / "model.pt"))
PORT = int(os.environ.get("LUMEN_PORT", 8765))

BRANDS = {"Haneco": "Canada", "JWL": "Chicago", "Exceledy": "Texas"}
PRODUCTS = ["Solar", "Lighting", "BESS", "EV Charging"]
SOURCES = {"new": "Leads", "follow-up": "Follow-ups", "winner": "Winners", "loser": "Losers"}
OPEN_SOURCES = ("new", "follow-up")
PHONE_TYPES = {"direct": "D", "mobile": "M", "business": "B"}
MEETING_TYPES = ["In-person", "Online", "Phone"]
# key: hotkey | retry: business days to next action (None = stop) | human: reached a person
# positive: counts as a good result | closes: lead is done | move_to: list the lead moves to
# PD11 mapping: RCP = GK, BUSY and EREQ = INT, HAS = MyPhoner loser.
OUTCOMES = {
    "WIN":     dict(label="Winner", key="", retry=None, positive=True, closes=True, move_to="winner"),
    "LOST":    dict(label="Loser", key="", retry=None, closes=True, move_to="loser"),
    "CALLBACK": dict(label="Callback scheduled", key="", retry=1, move_to="follow-up"),
    "OTHER":   dict(label="Other — describe in call log", key="o", retry=1),
    "VM":      dict(label="Voicemail / no answer", key="v", retry=2),
    "RCP":     dict(label="Receptionist", key="r", retry=1, human=True),
    "WP":      dict(label="Wrong person / left", key="w", retry=1, human=True),
    "EREQ":    dict(label="Requested email", key="m", retry=2, human=True, positive=True),
    "EMAILED": dict(label="Emailed", key="e", retry=2),
    "BUSY":    dict(label="Interested, busy", key="i", retry=2, human=True, positive=True),
    "NI":      dict(label="Not interested", key="n", retry=55, human=True),
    "BKD":     dict(label="Meeting booked", key="b", retry=None, human=True, positive=True, closes=True, move_to="winner"),
    "HAS":     dict(label="Already has solution", key="h", retry=None, human=True, closes=True, move_to="loser"),
    "BAD":     dict(label="Bad number", key="x", retry=None, closes=True),
    "DNC":     dict(label="Do not call", key="d", retry=None, human=True, closes=True),
}
DECISION_TITLES = re.compile(r"owner|president|ceo|manager|director|facilit|operations|plant|maintenance|vp", re.I)
CONTACT_VM_LIMIT = 3   # same person, voicemail N times in a row -> find another contact
LEAD_VM_LIMIT = 4      # whole lead, voicemail N times in a row -> new number / go through reception
HOUR_BLOCKS = [(0, "before 9"), (9, "9-11"), (11, "11-13"), (13, "13-15"), (15, "15+")]

# Traits: presets always appear in the picker and filter. Custom traits join them once saved for reuse.
PERSON_TRAITS = ["Nice", "Rude", "Gatekeeper-friendly", "Decision-maker", "Prefers email", "Has concerns"]
COMPANY_TRAITS = ["Has concerns", "Construction/renovation underway", "Budget-tight", "Multi-site", "Owns building"]
WARNING_TRAITS = ["Has concerns", "Rude", "Doesn't call back", "Hard to reach"]  # shown first on compact chips
RESPONSIVE_WINDOW = 5      # look at the latest N calls
RESPONSIVE_MIN_CALLS = 3   # need at least this many calls to judge
BROKEN_PROMISE_LIMIT = 2   # said they'd call, didn't, N times -> "Doesn't call back"
UPCOMING_DAYS = 7          # callbacks dropdown looks this far ahead
