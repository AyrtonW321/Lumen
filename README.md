# Lumen

Local lead tracker and call logger for Haneco (Canada), JWL (Chicago) and Exceledy (Texas). It runs on your PC, stores everything in SQLite, ranks leads with a PyTorch model you teach, gives next-step advice, and syncs to Google Sheets. Project brief: [CLAUDE.md](CLAUDE.md).

## Run

The UI is TypeScript + Tailwind, so build it once (needs Node 20+). `Lumen.bat` does this for you the first time.

```bash
cd web
npm install
npm run build
```

This PC has several Pythons. Use the same one for installing and running:

```bash
py -3.12 -m pip install torch --index-url https://download.pytorch.org/whl/cpu
```

```bash
py -3.12 -m lumen
```

Open http://127.0.0.1:8765. After updating the code, stop the running copy (`Ctrl+C`) and start it again. Older databases are upgraded automatically on start. Data lives in `data/lumen.db` and the model in `data/model.pt`. Both are gitignored, so back them up. Only use fake data until Haneco approves in writing.

### Desktop window (optional)

Run Lumen in its own window instead of a browser tab:

```bash
py -3.12 -m pip install pywebview
```

Then double-click **`Lumen.bat`**, or run `py -3.12 -m lumen.desktop`. For a desktop icon, right-click `Lumen.bat` → Show more options → Send to → Desktop (create shortcut). Closing the window stops Lumen. It uses the same `data/lumen.db` as the browser version, so don't run both at once. The window's settings (caller name, last tab) are kept in `%LOCALAPPDATA%\Lumen`, outside OneDrive, because OneDrive locks those files.

## Project layout

```
lumen/            Python package (run with python -m lumen)
  config.py       paths and tunables: brands, outcomes, limits
  db.py           schema, migrations, connect()
  leads.py        lead writes, load_all, list_leads, lead_detail
  contacts.py     contact writes
  activities.py   log_activity, MyPhoner comment
  advice.py       rule-based next steps
  features.py     model inputs and training examples
  model.py        PyTorch scorer
  appointment.py  calendar-invite text
  sheets.py       Google Sheets sync
  server.py       HTTP API + static files
  desktop.py      pywebview window
web/              browser UI: TypeScript + Tailwind CSS v4, built by Vite into web/dist
  index.html      page shell (Tailwind utilities)
  src/            types.ts, state.ts, render.ts, actions.ts, events.ts, main.ts, styles.css, ...
tests/            Python unittests (synthetic data only)
docs/PLAN.md      build plan for the October 20 changes
```

Dependency direction: `config` <- `db`/`timeutil` <- `features` <- `advice` <- `leads` <- `server`. No module imports `server`.

## What it tracks

- **Lead:** company, brand (Haneco / JWL / Exceledy), products (Solar, Lighting, BESS, any mix), main phone, and details for appointments (address, facility size, solar and lighting reference, meeting type, appointment time).
- **Lists (tabs):** Leads, Follow-ups, Winners, Losers, All. Use **Mark winner**, **Mark loser** or **Move to list** on any lead. Moving a lead back to Leads or Follow-ups reopens it. Click **✕** to close a lead.
- **Contacts:** name, job title, phone, ext, phone type (Direct / Mobile / Business), email. Several per lead, and each can be edited (✎).
- **Activities:** outcome, who you spoke to, callback date, free-text call log. A MyPhoner comment is built and copied to the clipboard.

| Key | Outcome | Next action |
|---|---|---|
| `V` | Voicemail / no answer | 2 business days |
| `R` | Receptionist | 1 |
| `W` | Wrong person / left | 1 |
| `M` | Requested email (marks contact as prefers email) | 2 |
| `E` | Emailed | 2 |
| `I` | Interested, busy | callback date or 2 |
| `N` | Not interested | 55 |
| `B` | Meeting booked | moves lead to Winners, opens appointment details |
| `H` | Already has solution | moves lead to Losers |
| `X` | Bad number | closes lead |
| `D` | Do not call | closes lead |

**Rescheduling:** quick buttons fill the next-call date: +1 day, +2 days, +1 week, +1 month, Jan 1 next year, +1 year, +2 years. A date that lands on a weekend moves to Monday. **Reschedule only** sets the date without logging a call.

**Copy buttons (📋):** company name, main phone, each contact's phone.

**Copy appointment:** in "Lead details & appointment". It builds calendar-invite text from the lead and the contact you picked. Empty fields are left out:

```
Name: John Doe
Title: Facility Manager
Address: 123 Good Street
Phone number: 123-245-2451 ext 204 (D)
Email: john.doe@example.com
Meeting Type: Online
Solar Reference: None
Appt made by Ayrton for Tue Oct 27, 2026 at 10:00 AM
```

Browser autofill is turned off on every field.

Other keys: `/` search, `↑` `↓` move, `1`–`9` pick contact, `0` main line, `Enter` save (`Ctrl+Enter` inside notes), `Esc` reset. Every value above is set in `lumen/config.py`.

## Advice

Rules read each lead's history and say what to do next, for example:
- "Find another contact: Bob hit voicemail 3 times in a row"
- "Contact receptionist first: ask for the facilities or operations manager by name"
- "Sue prefers email" / "Send the email they asked for"
- "Open to a meeting but busy: offer two specific times"

## The AI (PyTorch)

Read [lumen/model.py](lumen/model.py). It is commented step by step.

- **What it predicts:** the chance the next touch on a lead goes well (interested, email request, or booked).
- **What it learns from:** every logged call (what the lead looked like before the call, and how the call went), plus your **Good lead / Poor lead** buttons, which count 3×.
- **Model:** `HIDDEN = 0` is logistic regression, a one-layer neural net. It can explain each score ("+ decision maker known, - voicemail streak"). Set `HIDDEN = 16` to try a hidden layer once you have thousands of calls.
- **Honesty check:** training holds out every 5th lead and compares the model with "guess the average". The sidebar says whether it beats that. Don't trust the ranking until it does.

Leads in Winners also count as good examples. Click **Train AI** whenever you have logged more calls. Until a model is trained, leads are sorted by the advice rules.

## Google Sheets sync (optional)

1. `py -3.12 -m pip install gspread`
2. In a **company-owned** Google Cloud project, create a service account and download its JSON key. Keep the key outside this repo.
3. Share the tracker sheet with the service account's email (Editor).
4. Set environment variables, then start Lumen:
   ```bash
   set LUMEN_GOOGLE_CREDENTIALS=C:\path\to\key.json
   set LUMEN_SHEET_ID=<id from the sheet URL>
   ```
5. Click **Sync to Sheets**. It rewrites only the `Lumen Leads`, `Lumen Contacts` and `Lumen Activities` tabs. Your existing tabs are left alone. Mapping onto your current tracker's columns waits on a screenshot of them (CLAUDE.md, Section 9, Q2).

## Develop the UI

```bash
py -3.12 -m lumen          # API on :8765
cd web && npm run dev      # hot-reloading UI on :5173, /api proxied to :8765
```

After changing `web/src`, run `npm run build` again so the Python server (and the desktop window) serves the new version. `web/dist` and `web/node_modules` are gitignored.

## Check

```bash
py -3.12 -m unittest discover -s tests -t .
cd web && npm run typecheck && npm test
```
