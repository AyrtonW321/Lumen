"""Rule-based next steps for a lead."""
from .config import CONTACT_VM_LIMIT, DECISION_TITLES, LEAD_VM_LIMIT, OUTCOMES
from .features import trailing


def advice(lead, contacts, acts):
    """Plain-language next steps, plus a tier (lower = call sooner) used when no model is trained."""
    if lead["source"] == "winner":
        return ["Winner: meeting booked" if lead["closed"] == "BKD" else "Classified as winner; see call history for details"], 99
    if lead["source"] == "loser":
        return ["Loser: already has a solution" if lead["closed"] == "HAS" else "Classified as loser; see call history for details"], 99
    if lead["closed"]:
        return [f"Closed: {OUTCOMES[lead['closed']]['label']}"], 99
    tips, tier = [], 5
    if not acts:
        tips.append("New lead: make the first call")
        tier = 3
    for c in contacts:
        n = trailing([a for a in acts if a["outcome"] != "EMAILED"], "VM", c["id"])
        if n >= CONTACT_VM_LIMIT:
            tips.append(f"Find another contact: {c['name']} hit voicemail {n} times in a row")
            tier = max(tier, 6)
        if c["prefers_email"]:
            tips.append(f"{c['name']} prefers email")
    if trailing([a for a in acts if a["outcome"] != "EMAILED"], "VM") >= LEAD_VM_LIMIT:
        tips.append(f"{LEAD_VM_LIMIT}+ voicemails in a row: try another number or go through reception")
        tier = max(tier, 7)
    has_dm = any(DECISION_TITLES.search(c["title"] or "") for c in contacts)
    if any(a["outcome"] in ("RCP", "WP") for a in acts) and not has_dm:
        tips.append("Contact receptionist first: ask for the facilities or operations manager by name")
    elif contacts and not has_dm:
        tips.append("No decision-maker on file: find the owner, facilities or operations manager")
    if acts:
        last = acts[-1]["outcome"]
        if last == "BUSY":
            tips.insert(0, "Open to a meeting but busy: offer two specific times")
            tier = 1
        elif last == "EREQ":
            tips.insert(0, "Send the email they asked for")
            tier = 2
        elif last == "EMAILED":
            tips.insert(0, "Call to follow up on the email")
            tier = 2
        elif last == "NI":
            tips.append("Said not interested: wait before retrying")
            tier = 8
        elif last == "WP":
            tips.append("Wrong person: ask who handles facilities or energy costs")
            tier = 4
        elif last in ("VM", "RCP"):
            tier = max(tier, 4)
            dm = next((c for c in reversed(contacts) if DECISION_TITLES.search(c["title"] or "")), None)
            if last == "RCP" and dm:
                tips.append(f"Reached reception last time: ask for {dm['name']} by name or a direct line")
    return tips, tier
