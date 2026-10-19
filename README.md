# Lumen

Local call logger for Haneco cold calling. Keyboard-driven, stores calls in SQLite on your PC, syncs to Google Sheets on demand. Project brief: [CLAUDE.md](CLAUDE.md).

## Run

```bash
python lumen.py
```

Open http://127.0.0.1:8765. Needs Python 3.10+. No other installs needed to log calls.

Data lives in `data/lumen.db` (gitignored). Back it up. Only use synthetic data until Haneco approves in writing.

## Keys

| Key | Action |
|---|---|
| `/` | Search companies, Enter picks first match |
| `↑` `↓` | Move between companies |
| `V` `X` `G` `W` `N` `I` `B` `D` | Outcome: VM, BAD, GK, WP, NI, INT, BKD, DNC |
| `1`–`5` (`0` skip) | Role reached |
| `1`–`6` (`0` skip) | Objection (NI only) |
| `Enter` | Save, copy MyPhoner comment to clipboard |
| `Esc` | Reset |

Each save auto-fills timestamp, weekday, hour block, attempt number, days since last attempt, and next retry date. Companies with 4+ straight voicemails are flagged for a new contact. Calling stops after 6. Retry waits and hour blocks are set at the top of `lumen.py`.

## Google Sheets sync (optional)

1. `pip install gspread`
2. In a **company-owned** Google Cloud project, create a service account and download its JSON key. Keep the key outside this repo.
3. Share the tracker sheet with the service account's email (Editor).
4. Set environment variables, then start Lumen:
   ```bash
   set LUMEN_GOOGLE_CREDENTIALS=C:\path\to\key.json
   set LUMEN_SHEET_ID=<id from the sheet URL>
   ```
5. Click **Sync to Google Sheets**. This rewrites only the `Lumen Calls` and `Lumen Companies` tabs. Your existing tabs are left alone.

## Check

```bash
python test_lumen.py
```
