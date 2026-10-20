# Lumen: Change Plan (October 20, 2026)

This plan covers every change Ayrton requested on October 20, 2026, and the exact steps for making them.

**Status: built and verified on October 20, 2026.**

**Branch:** `docs/project-brief` (local; last commit `cd8dca8`, not pushed)
**Files touched:** `lumen.py`, `index.html`, `test_lumen.py`, `README.md`, `CLAUDE.md`
**Rule kept from CLAUDE.md:** fake data only until Haneco approves in writing. No real lead data in git.

---

## Summary of changes

| # | Change | Where |
|---|---|---|
| 1 | Fix sidebar overflow (no sideways scrolling) | `index.html` CSS |
| 2 | Make the UI pop: coloured buttons, chips, score pill, header | `index.html` CSS + markup |
| 3 | Lists as tabs: Leads, Follow-ups, Winners, Losers, All; close a lead | `lumen.py`, `index.html` |
| 4 | Mark winner / loser; move a lead to another list | `lumen.py`, `index.html` |
| 5 | Reschedule quick buttons, bigger date picker, "Reschedule only" | `lumen.py`, `index.html` |
| 6 | No browser autofill on any field | `index.html` |
| 7 | Copy buttons for company name and phone numbers | `index.html` |
| 8 | Contact phone: ext field and type (Direct / Mobile / Business); edit contacts | `lumen.py`, `index.html` |
| 9 | Lead details + "Copy appointment" text for calendar invites | `lumen.py`, `index.html` |
| 10 | Tests, docs, browser check, commit | `test_lumen.py`, `README.md`, `CLAUDE.md` |

---

## 1. Fix sidebar overflow

**Problem:** the three filter dropdowns and long lead rows are wider than the 360px sidebar. The sidebar grows and scrolls sideways.

**Steps:**
1. In `index.html` CSS, set `aside { overflow-x: hidden; min-width: 0; }`.
2. Make every control in the sidebar fill its cell: `aside select, aside input { width: 100%; min-width: 0; }`.
3. Change the filter grid to `grid-template-columns: repeat(3, minmax(0, 1fr))` so columns can shrink below their content width.
4. Let lead rows wrap: `.lead span, .lead small { overflow-wrap: anywhere; }`.
5. Put the "Due now / Show closed" row on its own wrapping line (`flex-wrap: wrap`).

**Check:** open at full screen and at 1024px wide. No horizontal scrollbar in the sidebar.

---

## 2. Make the UI pop

**Steps:**
1. Add colour tokens to `:root`:
   - `--primary` (blue) for main actions
   - `--success` (green) for winners
   - `--danger` (red) for losers
   - `--accent` (amber) for outcome hotkeys
   - one colour per brand: Haneco, JWL, Exceledy
   - one colour per product: Solar, Lighting, BESS
2. Add button classes:
   - `.btn-primary` (filled blue): **Save**, **Add lead**, **Add contact**, **Train AI**
   - `.btn-success` (filled green): **Mark winner**
   - `.btn-danger` (filled red): **Mark loser**
   - `.btn-ghost`: secondary actions such as Sync and copy buttons
3. Add a header bar across the top with the app name "Lumen" and the AI status.
4. Show brand and product as coloured chips in the lead list and the lead header.
5. Show the AI score as a pill: green at 60% or more, amber from 30% to 59%, grey below 30%.
6. Give the advice card a coloured left border and bold its first line.
7. Show outcome hotkeys as amber key caps, and highlight the selected one.

**Check:** take a screenshot. Save, Mark winner and Mark loser should be the most visible buttons on screen.

---

## 3. Lists as tabs

**Data:** the existing `leads.source` column holds the list. Values become:

| Value | Tab name |
|---|---|
| `new` | Leads |
| `follow-up` | Follow-ups |
| `winner` | Winners |
| `loser` | Losers |

No new column, and existing leads keep working.

**Steps in `lumen.py`:**
1. Change `SOURCES` to the four values above.
2. Add a helper `is_open(lead)`. A lead is open when its source is `new` or `follow-up` and `closed` is empty.
3. In `list_leads()`, only score open leads, and add `"open": is_open(lead)` to each row.
4. In `advice()`, return `["Winner: meeting booked"]` or `["Loser: already has a solution"]` (tier 99) for winners and losers.

**Steps in `index.html`:**
1. Add a tab bar at the top of the sidebar: **Leads · Follow-ups · Winners · Losers · All**, each with a live count.
2. Clicking a tab filters the list by `source`. **All** shows every lead.
3. Remove the old "All lists" dropdown, because the tabs replace it.
4. Make "Due now" start **unchecked**.
5. Add a **×** button on the lead header that clears the selection and returns to the list view.
6. Remember the last tab in `localStorage`, wrapped in try/catch.

---

## 4. Mark winner / loser; move a lead

**Steps in `lumen.py`:**
1. Add a `move_to` field to two outcomes:
   - `BKD` (Meeting booked): `move_to="winner"`
   - `HAS` (Already has solution): `move_to="loser"`
2. In `log_activity()`, when the outcome has `move_to`, set `leads.source` to that value in the same transaction.
3. In `update_lead()`, when `source` changes to `new` or `follow-up`, also clear `closed`, so moving a lead back reopens it.
4. Leave `BAD` and `DNC` closed but **not** moved to Losers. Losers is only for "already has a solution".
5. In `training_examples()`, treat a lead in Winners with no manual label as a **good** label (weight 3). Losers add no label, because "already has a solution" says nothing about how reachable a lead is.

**Steps in `index.html`:**
1. Add **Mark winner** (green) and **Mark loser** (red) buttons on the lead header. They call `POST /api/leads/<id>` with `{source: "winner"}` or `{source: "loser"}`.
2. Replace the source dropdown with a labelled **Move to list** dropdown that shows all four lists.
3. After a move, refresh the list and keep the lead open so you can see the change.

---

## 5. Reschedule

**Steps in `index.html`:**
1. Make the date picker bigger: about 44px tall, 16px font, wider calendar icon.
2. Add quick buttons under it: **+1 day · +2 days · +1 week · +1 month · Jan 1 next year · +1 year · +2 years**.
3. Add a small JS function `quickDate(kind)`:
   - Adds the period to today. "+1 month" keeps the same day of the month and clamps to the month's last day.
   - "Jan 1 next year" is January 1 of the next calendar year.
   - If the result falls on a Saturday or Sunday, it moves to the following Monday.
4. A quick button fills the **Callback date** field, which is used when you save a call.
5. Add a **Reschedule only** button. It saves the date as the lead's next action date without logging a call.

**Steps in `lumen.py`:**
1. Allow `next_action_date` in `update_lead()`, validated as an ISO date (`YYYY-MM-DD`) with `date.fromisoformat`.

---

## 6. No browser autofill

**Steps in `index.html`:**
1. Add `autocomplete="off"` to every `<form>` and every `<input>` and `<textarea>`: search, new lead, new contact, edit contact, lead details, call log notes, caller name.
2. Chrome sometimes ignores `off` on name, phone and email fields. For those, use a made-up token such as `autocomplete="lumen-contact-name"`, which Chrome has no saved entries for.

**Check:** type in each field twice across reloads. No suggestion dropdown appears.

---

## 7. Copy buttons

**Steps in `index.html`:**
1. Add a 📋 button next to the company name in the lead header. It copies the name.
2. Add a 📋 button next to the lead's main phone and next to each contact's phone. It copies the number only (no ext, no type), so it pastes cleanly into a dialer.
3. Use one helper, `copy(text, label)`, that calls `navigator.clipboard.writeText` and shows a "Copied company name" or "Copied phone" toast. If the clipboard is blocked, the toast shows the text instead.

---

## 8. Contact phone details and editing

**Data migration (keeps existing data):**
1. Add a `MIGRATIONS` list in `lumen.py`:
   ```python
   MIGRATIONS = [
       ("contacts", "ext", "TEXT"),
       ("contacts", "phone_type", "TEXT"),
       ("leads", "address", "TEXT"),
       ("leads", "facility_size", "TEXT"),
       ("leads", "solar_reference", "TEXT"),
       ("leads", "lighting_reference", "TEXT"),
       ("leads", "meeting_type", "TEXT"),
       ("leads", "appt_at", "TEXT"),
   ]
   ```
2. In `connect()`, after `CREATE TABLE IF NOT EXISTS`, read `PRAGMA table_info(<table>)` and run `ALTER TABLE ... ADD COLUMN` for any column that is missing. Existing rows get empty values. Nothing is deleted.
3. Add the new columns to `SCHEMA` too, so fresh databases match.

**Steps in `lumen.py`:**
1. Add `PHONE_TYPES = {"direct": "D", "mobile": "M", "business": "B"}`.
2. Extend `add_contact()` with `ext` and `phone_type`, and validate `phone_type`.
3. Add `update_contact(conn, contact_id, **fields)` with a whitelist: name, title, phone, ext, phone_type, email.
4. Add the route `POST /api/contacts/<id>` that calls `update_contact()`.

**Steps in `index.html`:**
1. Add **Ext** and **Phone type** (Direct / Mobile / Business) to the Add contact form.
2. Show each contact as: `Amy Test · Facilities Director · 📞 905-555-0123 ext 204 (D) 📋`.
3. Add an **Edit** button on each contact. It opens the same form, filled in, and saves through `POST /api/contacts/<id>`.
4. Treat the lead's main phone as its Business line.

---

## 9. Lead details and "Copy appointment"

**New lead fields** (added by the migration in step 8):
- Address (for the site visit)
- Facility size
- Solar reference (e.g. "None")
- Lighting reference (e.g. "Fluorescent" or "LEDs upgraded in 2020")
- Meeting type: In-person, Online or Phone
- Appointment date and time (`appt_at`)

**Steps in `lumen.py`:**
1. Add `MEETING_TYPES = ["In-person", "Online", "Phone"]`.
2. Allow the six new fields in `update_lead()`, validating `meeting_type` and `appt_at` (ISO date-time).
3. Add a pure function `appointment_text(lead, contact, caller)` that returns the text below. **Every line whose value is empty is skipped entirely.**
   ```
   Name: John Doe
   Title: Facility Manager
   Address: 123 Good Street
   Facility Size: 40,000 sq ft
   Phone number: 123-245-2451 ext 204 (D)
   Email: john.doe@google.com
   Meeting Type: Online
   Solar Reference: None
   Lighting Reference: Fluorescent
   Appt made by Ayrton for Tue Oct 27, 2026 at 10:00 AM
   ```
   - Name, Title, Phone and Email come from the chosen contact. If no contact is chosen, the lead's main phone is used, marked (B).
   - The phone line adds `ext <n>` when an ext exists, and `(D)`, `(M)` or `(B)` from the phone type.
   - The last line includes "for <date> at <time>" only when an appointment time is set, and "by <caller>" only when the caller name is filled in.
   - No "APPOINTMENT CONFIRMATION DETAILS" heading, to match Ayrton's sample. This is easy to add later.
4. Add the route `GET /api/leads/<id>/appointment?contact_id=<id>&caller=<name>`, which returns `{"text": ...}`.

**Steps in `index.html`:**
1. Add a collapsible **Lead details** section with the six fields and a **Save details** button (primary blue).
2. Add a **📋 Copy appointment** button (primary blue). It fetches the text for the selected contact and caller, then copies it.
3. When you pick the **Meeting booked** outcome, open the Lead details section automatically so you can fill in the appointment right away.

---

## 10. Tests, docs, browser check, commit

**New checks in `test_lumen.py`** (synthetic data only):
1. Logging `BKD` moves a lead to `winner`, and logging `HAS` moves it to `loser`.
2. Moving a winner back to `new` clears `closed` and makes it open again.
3. Winners and losers get no AI score and don't show as due.
4. `update_lead(next_action_date="2026-11-02")` works. A bad date raises `ValueError`.
5. The migration adds the new columns to an old-style database without losing rows. The test builds the old schema, inserts a lead, runs `connect()`, and checks that the row is still there with the new columns empty.
6. `add_contact()` and `update_contact()` accept `ext` and `phone_type`. An unknown phone type raises `ValueError`.
7. `appointment_text()`:
   - With every field filled, it matches the sample exactly.
   - With no address and no email, those lines are missing (not blank).
   - With no contact, it falls back to the main phone marked (B).
8. A winner with no manual label shows up as a good training example.

**Docs:**
1. Update `README.md`: tabs, winner/loser, reschedule buttons, copy buttons, the appointment format, contact ext and phone type.
2. Add a "Decisions (October 20, 2026)" block to `CLAUDE.md` listing the new lists, the auto-move rules, the migration, and the appointment format.

**Browser check** (run `py -3.12 lumen.py`, fake data):
1. No sideways scroll in the sidebar at full screen.
2. Tabs filter correctly and counts update after a move.
3. Logging Meeting booked moves the lead to Winners, and Mark loser moves it to Losers.
4. Each quick reschedule button fills the right date, and weekends move to Monday.
5. The copy buttons put the right text on the clipboard.
6. Copy appointment skips empty lines.
7. No autofill dropdowns appear.

**Commit:** one commit on `docs/project-brief`, for example "Add list tabs, winner/loser, reschedule, contact phone details and appointment copy". **Not pushed** until Ayrton says so.

---

## Defaults chosen (change any before building)

- Bad number and Do not call stay closed but are not moved to Losers.
- Winners count as good training examples; Losers add no label.
- The lead's main phone counts as a Business line.
- No heading on the copied appointment text.
- "Due now" starts unchecked.
- The Lead details section opens automatically when Meeting booked is picked.
