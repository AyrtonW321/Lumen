"""Model inputs. Only uses what was known at the time, so training never peeks at the answer."""
from datetime import datetime

from .config import BRANDS, DECISION_TITLES, OUTCOMES, PRODUCTS


def trailing(acts, outcome, contact_id=...):
    """How many of the latest activities in a row have this outcome (optionally for one contact)."""
    n = 0
    for a in reversed(acts):
        if contact_id is not ... and a["contact_id"] != contact_id:
            continue
        if a["outcome"] != outcome:
            break
        n += 1
    return n


def features(lead, contacts, acts, now):
    """Numbers the model sees, each between 0 and 1."""
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
        label = lead["label"] or ("good" if lead["source"] == "winner" else None)
        if label:
            X.append(features(lead, lead["contacts"], acts, datetime.now()))
            y.append(float(label == "good"))
            w.append(3.0)  # your judgement counts more than a single call
            ids.append(lead["id"])
    return X, y, w, ids
