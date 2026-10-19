# Lumen

Local lead tracker and call logger for Haneco (Canada), JWL (Chicago) and Exceledy (Texas). It runs on your PC, stores everything in SQLite, ranks leads with a PyTorch model you teach, gives next-step advice, and syncs to Google Sheets. Project brief: [CLAUDE.md](CLAUDE.md).

## Run

This PC has several Pythons. Use the same one for installing and running:

```bash
py -3.12 -m pip install torch --index-url https://download.pytorch.org/whl/cpu
```

```bash
py -3.12 lumen.py
```

Open http://127.0.0.1:8765. Data lives in `data/lumen.db` and the model in `data/model.pt`. Both are gitignored, so back them up. Only use fake data until Haneco approves in writing.

## What it tracks

- **Lead:** company, brand (Haneco / JWL / Exceledy), products (Solar, Lighting, BESS, any mix), list (new MyPhoner lead or your follow-up list).
- **Contacts:** name, job title, direct line, email. Several per lead.
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
| `B` | Meeting booked | closes lead |
| `H` | Already has solution | closes lead |
| `X` | Bad number | closes lead |
| `D` | Do not call | closes lead |

Other keys: `/` search, `↑` `↓` move, `1`–`9` pick contact, `0` main line, `Enter` save (`Ctrl+Enter` inside notes), `Esc` reset. Every value above is set at the top of `lumen.py`.

## Advice

Rules read each lead's history and say what to do next, for example:
- "Find another contact: Bob hit voicemail 3 times in a row"
- "Contact receptionist first: ask for the facilities or operations manager by name"
- "Sue prefers email" / "Send the email they asked for"
- "Open to a meeting but busy: offer two specific times"

## The AI (PyTorch)

Read [model.py](model.py). It is commented step by step.

- **What it predicts:** the chance the next touch on a lead goes well (interested, email request, or booked).
- **What it learns from:** every logged call (what the lead looked like before the call, and how the call went), plus your **Good lead / Poor lead** buttons, which count 3×.
- **Model:** `HIDDEN = 0` is logistic regression, a one-layer neural net. It can explain each score ("+ decision maker known, - voicemail streak"). Set `HIDDEN = 16` to try a hidden layer once you have thousands of calls.
- **Honesty check:** training holds out every 5th lead and compares the model with "guess the average". The sidebar says whether it beats that. Don't trust the ranking until it does.

Click **Train AI** whenever you have logged more calls. Until a model is trained, leads are sorted by the advice rules.

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

## Check

```bash
py -3.12 test_lumen.py
```
