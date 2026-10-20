"""Optional Google Sheets sync."""
import os


def sync_to_sheets(conn):
    """Rewrite the Lumen tabs. Leaves every other tab alone."""
    import gspread  # optional dependency; tracking works without it

    # ponytail: full rewrite each sync; switch to append-only if activities reach tens of thousands
    sheet = gspread.service_account(filename=os.environ["LUMEN_GOOGLE_CREDENTIALS"]).open_by_key(
        os.environ["LUMEN_SHEET_ID"])
    tabs = {
        "Lumen Leads": "SELECT * FROM leads ORDER BY name",
        "Lumen Contacts": "SELECT l.name AS lead, c.* FROM contacts c JOIN leads l ON l.id = c.lead_id ORDER BY l.name",
        "Lumen Activities": """SELECT l.name AS lead, c.name AS contact, c.title, a.* FROM activities a
                               JOIN leads l ON l.id = a.lead_id LEFT JOIN contacts c ON c.id = a.contact_id
                               ORDER BY a.timestamp""",
    }
    counts = {}
    for title, sql in tabs.items():
        cur = conn.execute(sql)
        rows = [[d[0] for d in cur.description]] + [["" if v is None else v for v in r] for r in cur]
        try:
            ws = sheet.worksheet(title)
        except gspread.WorksheetNotFound:
            ws = sheet.add_worksheet(title, rows=len(rows) + 100, cols=len(rows[0]))
        ws.clear()
        ws.update(rows)
        counts[title] = len(rows) - 1
    return counts
