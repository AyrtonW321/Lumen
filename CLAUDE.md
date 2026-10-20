# Haneco Call Logger and Lead Scoring Tool: Project Brief

Prepared for Claude Code. This file documents the full planning conversation (October 19, 2026), the PD11 technical report it builds on, the research brief, every concern and open question raised, and a proposed build plan.

**How to use this file in Claude Code:** put it at the root of a new repo (or rename it `CLAUDE.md`). Start by reading Section 9 (Open Questions). Several design decisions depend on answers that do not exist yet. Do not assume them. Ask Ayrton.

---

## Table of Contents

1. Project Summary
2. Background: Ayrton, Haneco, and the Current Workflow
3. Source Context: The PD11 Technical Report
4. Conversation History (Chronological)
5. Research Brief (Full Content)
6. Concerns and Risks
7. Proposed System Design
8. Phased Build Plan and Tasks
9. Open Questions (Must Be Answered Before Building)
10. Constraints and Rules for Claude Code
11. Glossary

---

## 1. Project Summary

**Goal:** a tool that lets Ayrton log cold calls faster than clicking through spreadsheet dropdowns, writes the results to the spreadsheet, and grades every lead (called or not) so he knows which leads deserve his time, how often to call and follow up on each one, and which leads tend to end in voicemail.

**Why it exists:** MyPhoner's three statuses (winner, loser, call back) hide why calls fail. Five of six real outcomes are logged as "call back." The spreadsheet tracker requires manual clicks for every call. Ayrton wants both faster logging and smarter prioritization to raise meetings booked per day.

**Core ideas Ayrton proposed:**
1. A logger: input lead/call info quickly, have it land in the spreadsheet.
2. A scoring model ("neural network or AI") trained on logged leads that grades each lead as worth pursuing or not.
3. Outputs to the spreadsheet or another app: which leads to prioritize, how often to call and follow up, which leads usually go to voicemail.
4. Use the entire MyPhoner dataset: several Ontario lists, a couple of Chicago lists, lists for other Canadian provinces, and two follow-up lists (Chicago and Canada, about 150 leads each), not only his own 600 calls.

**Current recommended direction (from the conversation):**
- Build the fast logger first. Clean data matters more than model choice.
- No neural network at current data volume. Use interpretable models (beta-binomial rates, penalized logistic regression).
- Biggest AI win: use an LLM to read historical free-text MyPhoner comments and tag each with an outcome code, contact role, and objection. This converts messy history into labeled training data.
- Score every lead on two axes: **Value** (how much the customer is worth) and **Ease** (how likely to book). Priority = Value × Ease.
- Treat Ontario and Chicago as different markets.
- Quickest win: rank the two follow-up lists (~300 leads with comment history) with simple rules before any model exists.

---

## 2. Background: Ayrton, Haneco, and the Current Workflow

### Ayrton
- Ayrton Wong, University of Waterloo, Applied Mathematics (concentration: Scientific Computing and Machine Learning). Previous academic term 2A.
- Fall 2026 co-op: Sales Representative / Energy Specialist at Haneco Lighting Canada Inc., 215 Shields Court, Unit 3, Markham, ON.
- Supervisor: Angela (Office Assistant), works closely with the team day to day.
- Team: two co-op students (Ayrton and one colleague) and two supervisors.

### Haneco and the sales motion
- Haneco Lighting Canada is the North American arm of a multinational LED lighting manufacturer (expanded from South Australia).
- Outreach team phones businesses to book **preliminary meetings** for **LED and solar energy audits**. The audit shows a business which rebates it may qualify for under Ontario's **Save on Energy** program (run by the IESO).
- The outreach role ends once a meeting is booked. Others handle the rest of the sales process.
- Role also includes: finding new contacts inside target companies, keeping a follow-up list, and calling back past clients who missed or declined earlier appointments.
- Markets: Ontario, other Canadian provinces, and Chicago.

### Current tools
- **MyPhoner** (dialer/CRM). Every call gets one status plus a free-text comment:
  - **Winner:** a preliminary meeting was booked.
  - **Loser:** company already has lighting, EV, and solar solutions. This is the only use of the loser status.
  - **Call back:** every other outcome (voicemail, gatekeeper, wrong person, decline, real interest).
- Comment histories for a single company get long because several people at one company are often called. They are hard to scan.
- Ayrton was told MyPhoner **cannot export** logs. The research found this is probably a permissions issue (see Section 5).
- **Daily lead tracker spreadsheet** and **follow-up list spreadsheet**, kept alongside MyPhoner. Ayrton manually clicks dropdown options for each call. Platform (Google Sheets vs Excel) is **unknown**.

### Call volume
- About 30 calls per day, about 150 per week, five working days.

---

## 3. Source Context: The PD11 Technical Report

**Title:** Identifying Reachable Decision-Makers in Cold-Call Outreach for LED and Solar Energy Audits
**Author:** Ayrton Wong. **Date:** October 9, 2026. **Course:** PD 11, University of Waterloo.
**Location:** Claude Docs artifact, https://claude.ai/code/artifact/84b4c075-612c-4627-9237-6d8202dfa45c

### Purpose
Measure how often cold calls fail because the caller cannot reach a relevant decision-maker, and recommend a simple tracking method to reduce those failures.

### Data and method
- Four weeks of one representative's calls in Fall 2026: about 600 calls.
- **37 meetings booked**, taken from MyPhoner's winner count (the only hard number).
- All other counts are **Ayrton's estimates**: about 23 of 30 daily calls go to voicemail, about 10 of every 150 end at a gatekeeper, about 2 of every 150 reach the wrong person or a contact who left. Of relevant people who did not book, about three quarters were not interested.
- MyPhoner comments could not be exported or bulk-analyzed.
- No statistical tests (estimates, single period).

### Outcome codes (Appendix A of the report)
Each call gets exactly one code. If a call involves several outcomes, use the furthest point reached (the lowest row in this table).

| Tag | Outcome | Use when | Example comment | MyPhoner status today |
|---|---|---|---|---|
| VM | No answer or voicemail | Nobody answered or voicemail | "VM again, third try" | Call back |
| GK | Gatekeeper block | Receptionist/assistant would not transfer or give a name | "Reception won't put the call through" | Call back |
| WP | Wrong person or contact left | Contact left, or person cannot discuss audits | "He left in the summer, ask for facilities" | Call back |
| NI | Right person, not interested | Relevant person declined, no callback request | "Not interested right now" | Call back |
| INT | Right person, interested | Relevant person asked for a later call or showed interest | "Busy this week, call Thursday" | Call back |
| BKD | Meeting booked | Preliminary meeting set | "Booked for Oct 20" | Winner |

Loser is separate from these codes. Losers were not counted separately in the report and are included in call back totals.

### Results (estimated counts, 600 calls)

| Code | Calls | Per week | Per day | Share |
|---|---|---|---|---|
| VM | 460 | 115 | 23 | 76.7% |
| GK | 40 | 10 | 2 | 6.7% |
| WP | 8 | 2 | 0.4 | 1.3% |
| NI | 41 | 10.25 | 2.05 | 6.8% |
| INT | 14 | 3.5 | 0.7 | 2.3% |
| BKD | 37 | 9.25 | 1.85 | 6.2% |
| Total | 600 | 150 | 30 | 100% |

| Rate | Calculation | Result |
|---|---|---|
| Contact rate (someone answered) | 140 ÷ 600 | 23.3% |
| Relevant-contact rate | 92 ÷ 600 | 15.3% |
| Meeting rate | 37 ÷ 600 | 6.2% |
| Meetings per relevant contact | 37 ÷ 92 | 40.2% |
| Identification failure rate, all calls | 48 ÷ 600 | 8.0% |
| Identification failure rate, answered calls | 48 ÷ 140 | 34.3% |
| Voicemails among call back calls | 460 ÷ 563 | 81.7% |
| Identification failures among call back calls | 48 ÷ 563 | 8.5% |

### Key findings
- Most failed calls fail at voicemail, not at identification.
- Among answered calls, about one in three misses the relevant person.
- When a relevant person is reached, about 40% of conversations book a meeting.
- Each hidden outcome needs a different next step: VM needs another attempt at a different time; GK needs a name or direct line; WP needs a new contact at the same company; NI needs a longer wait. "Call back" treats them all the same.

### Success criteria for a tracking method (set in the report)
1. Each call can be placed in one outcome category from the existing comment, without extra tools.
2. Logging adds no more than about 10 seconds per call.
3. For any company, a rep can see which contacts were tried, what happened, and when to retry.

### Recommendations in the report
- From Tuesday, October 13, 2026: begin every MyPhoner comment with an outcome tag (VM, GK, WP, NI, INT, BKD) plus the hour of the call.
- Add a company sheet in the lead tracker, one row per company: company, contacts tried and roles, last outcome tag, whether a decision-maker has been identified, next retry date. Update at end of each day (about 10 minutes).
- First counted week ends Friday, October 16, 2026. Count tags every Friday and share rates with Angela.
- On Friday, November 13, 2026, compare with the Table 4 baseline. Keep the method if identification failure among answered calls drops at least 10 percentage points from 34.3%, or relevant-contact rate rises at least 3 points from 15.3%. Otherwise keep only the tags. If identification failures are below 10% of answered calls, drop the company sheet and focus on call timing.
- Future: recorded call times could show whether voicemail rates differ across the day.

### Literature cited in the report
Johnston & Bonoma (1981); Webster & Wind (1972); Cabanelas et al. (2023); González-Flores et al. (2025, B2B lead scoring with ML, found lead source and lead status most useful); Rapp et al. (2008); Moncrief & Marshall (2005); Caponi (2007, practitioner); Bain & Company (2020); IESO (2023).

**Relevance to this project:** the logger and scoring tool is a direct automation of the report's own recommendation, and the report's numbers are the baseline (the prior) for any model.

---

## 4. Conversation History (Chronological)

### 4.1 Can Claude see a document from another chat?
**Ayrton asked:** whether Claude can open a past chat (called "PD11") and see the document produced there.

**Answer given:**
- Claude can search past chats by topic and read what was written.
- Published artifacts and Claude Docs can be listed and read in full (more reliable than reading chat text).
- Files created as downloads in another chat (e.g., a .docx) cannot be opened from a new chat. Only conversation text is visible. Download and re-attach to use the actual file.
- Chats inside Projects can only be searched from inside that Project.

Claude then located the PD11 chat and read the full report from the Claude Docs artifact.

### 4.2 Idea 1: a faster call logger
**Ayrton's idea:** build software or a website to log calls more easily instead of manually clicking every option in the spreadsheet. Input call logs into the software, and it writes to the spreadsheet. Goal: higher productivity and more leads called per day.

**Claude's response:**
- The idea fits and essentially automates the PD11 recommendation:
  - One keypress per outcome (V = voicemail, etc.), time stamped automatically, spreadsheet row written for him.
  - Company view built automatically, removing the 10-minute end-of-day sheet.
  - Tool builds the tagged MyPhoner comment and copies it to the clipboard, so MyPhoner becomes one paste.
- **Blunt payoff assessment:**
  - Logging is not the main bottleneck; voicemail is (about 77% of calls).
  - If dropdown clicking takes about 45 seconds per call, that is roughly 20 minutes a day. Cutting to about 10 seconds buys a handful of extra dials, not double the leads. Ayrton should time himself to get a real number.
  - The bigger win is data: automatic timestamps let him test which hours get answered, which was the report's own next step.
- **Concern raised:** leads are Haneco's data. Get Angela's approval before the data goes into any app. Safest design keeps data inside the existing spreadsheet with no outside server.
- **Questions asked (still unanswered):**
  1. Where does the tracker live: Google Sheets, Excel online (OneDrive/SharePoint), or local Excel?
  2. What are the columns and dropdown options clicked per call? (Screenshot with company names blanked out.)
  3. Work computer: can he install anything, or browser only? Can he add scripts to the sheet (Apps Script / Office Scripts)?
  4. Users: just Ayrton, or the co-op colleague too?

### 4.3 Idea 2: AI lead grading
**Ayrton's idea:** the point beyond a spreadsheet is to input all lead information and use a neural network or AI, trained on his data, to grade each lead (good or not). The grade tells him whether to dig into a lead. Output to the spreadsheet or another app to track which leads to prioritize, how often to call and follow up, and which leads usually end in voicemail.

**Claude's response:**
- With about 600 calls and 37 meetings, a neural network is the wrong tool. Too little labeled data; it would memorize noise.
- A simple scoring model fits: logistic regression or a readable points-based score.
- Launched a research task on what works at this scale (full output in Section 5).

**Research summary given to Ayrton:**
- Build a fast logger first; leave the neural network out for now.
- Better call timing and retry rules will probably add more meetings than lead scoring, because 77% of dials hit voicemail.
- Phase 1 (weeks 1–2): Google Sheets logger with one-key codes, automatic timestamps and attempt counts.
- Phase 2 (after about 100+ meetings, roughly 8–12 weeks): two simple models, one for "will someone answer," one for "will a relevant contact book."
- Phase 3: complex models only if team data is pooled.
- MyPhoner documents an API, webhooks, and list exports, so "cannot export" is probably account permissions. Ask for an API key or weekly export.
- Written approval from Haneco needed.
- Most timing benchmarks are vendor data. Expect single-digit to low double-digit percentage gains, mostly from timing and retries.

### 4.4 Idea 3: use all MyPhoner data, not just 600 calls
**Ayrton's point:** use the entire MyPhoner dataset: about four Ontario lists, a couple of Chicago lists, a couple of lists for other provinces. Track and grade every lead in these lists, not just ones he called, based on how important the customer is and how easily it could be acquired. Also apply it to the 600 calls already made and the follow-up lists (about 150 leads each, one for Chicago, one for Canada) to see which follow-ups are best to contact.

**Claude's response:**
- **Key distinction:**
  - Leads you can **score** = every lead in every list, called or not. This works.
  - Leads you can **learn from** = only leads with a recorded outcome. More lists mean more leads to grade, not more training data.
- The real question is how many **calls with outcomes** exist in MyPhoner across every list, every rep, and all past work terms. If Haneco has years of history from many reps, there could be thousands of outcomes and the small-data problem mostly disappears. Check this first.
- **Where AI helps most:**
  - Reading old comments: an LLM tags each historical comment with VM/GK/WP/NI/INT, role reached, and objection. This turns messy logs into labeled data without recoding by hand. Strongest use of AI in the idea.
  - Scoring on top of tagged history.
- **Two scores:**
  - Value: facility size, building type, old lighting, solar fit.
  - Ease: past outcomes, whether a decision-maker was reached, region.
  - Priority = Value × Ease. A big hard-to-reach warehouse can outrank an easy small office.
- **Do not pool Chicago with Ontario blindly.** Save on Energy only exists in Ontario. Chicago uses different utility incentives (ComEd), a different pitch, different odds. Region must be a model input, or Chicago gets its own model.
- **Follow-up lists are the quickest win.** About 300 leads already have comment history. Simple rule-based ranking before any model:
  1. Interested, callback date due
  2. Gatekeeper gave a name or direct line
  3. Not interested, but long enough ago to retry
  4. Repeated voicemails with no contact (needs a new number or contact)
- **To find out before building:**
  1. How much history exists: total calls across all lists and reps, and how far back.
  2. Whether Angela can get a MyPhoner API key or a full export with comments.
- **Offer:** with an export of even one follow-up list, Claude can tag the comments and rank the list as a proof of concept.

### 4.5 This document
Ayrton asked for full documentation of the chat and the research artifact, in detail, including all questions and concerns, to hand to Claude Code.

---

## 5. Research Brief (Full Content)

*Design Brief: A Personal Lead-Scoring and Call-Logging Tool for B2B Energy-Audit Cold Calling. Produced by a research task during this conversation. Figures from vendors are marked as such.*

### 5.1 Bottom line
Build the fast logger first and leave the neural network out. With about 37 meetings, a neural network will overfit. Better time-of-day and retry rules will do more for meetings per day than lead grading, because 77% of dials go to voicemail.

### 5.2 Data volume
- Baseline: about 600 calls, 37 meetings (6.2%), about 15% of dials reach a relevant person; about 40% of relevant conversations book.
- At about 150 calls/week, roughly 9 meetings/week. A four-month term might yield about 2,400 calls and 140–150 meetings: enough for a small interpretable model, not deep learning.
- (Section 4.4 notes this changes if team-wide MyPhoner history is available.)

### 5.3 Model choice for small data

| Method | Fit for ~40–150 meetings | Why |
|---|---|---|
| Neural network | No | Needs over 10× the events per variable of logistic regression (van der Ploeg, Austin & Steyerberg, 2014, BMC Med Res Methodology). Will memorize. |
| Gradient boosting / random forest | Not yet | Random forests needed up to 850 events per variable in one cohort. González-Flores et al. (2025) found gradient boosting best, but with 4+ years of CRM data. |
| Naive Bayes | Ranking only | Handles tiny data; probabilities poorly calibrated. |
| Points / rules | Yes, from day one | Transparent; encodes domain knowledge before data exists (e.g., "already LED = disqualify"). |
| Beta-binomial segment rates | Yes, best starting point | Honest rates for small segments by shrinking toward overall average. |
| Penalized (L2/ridge) logistic regression | Yes, Phase 2 core | Interpretable, calibrated. 3–6 predictors once about 100+ events. |

**Evidence:**
- Logistic regression reached stable validated AUC at roughly 20–50 events per variable (van der Ploeg et al., 2014).
- Riley et al. (2019, Statistics in Medicine) replaced the "10 events per variable" rule with stricter criteria: global shrinkage ≥ 0.9, optimism in Nagelkerke R² ≤ 0.05, precise overall risk estimate.
- **Do not use SMOTE/oversampling/undersampling.** van den Goorbergh et al. (2022, JAMIA) found these left minority-class probabilities strongly overestimated without improving AUROC. A 6% base rate is fine; calibrated probabilities matter, not balanced classes.

**Beta-binomial example:** prior from overall rate, e.g., 6.2% booking with strength 20 pseudo-calls → Beta(1.2, 18.8). Segment "warehouses, owner-occupied" with 3 bookings in 20 calls: posterior mean (1.2+3)/(20+20) = 10.5%, not the raw 15%. Rank segments by posterior mean; use the posterior interval to see which are still too uncertain.

**Parameter budget:** each level of a categorical variable costs one parameter (8-level industry = 7). At 37 events, about 2–3 parameters. At about 150 events, perhaps 6–10. Collapse industry to 4–6 groups; use size bands.

**Validation:**
- Repeated stratified k-fold or bootstrap optimism correction, not a single split.
- **Group folds by company** (multiple calls per company leak otherwise).
- Report Brier score, calibration plot, AUC with confidence interval.
- Must beat the trivial baseline (everyone gets the overall rate), or don't use it.

**Lead-scoring literature:** González-Flores et al. (2025, Frontiers in AI) compared 15 classifiers; gradient boosting best; "source" and "lead status" most important. Nygård & Mezei (2020, HICSS) found random forests could estimate purchase probability. Both used far larger datasets.

### 5.4 Two separate problems
- **Answering** depends mostly on time, day, attempt number, line type. More data available (about 140 non-voicemail outcomes already).
- **Booking** depends on company fit: facility type, size, ownership, existing lighting.
- Mixing them in one model blurs both.

### 5.5 Features to log

No peer-reviewed study exists on predictors for Ontario LED/solar audit cold calling. These come from program rules and building economics and must be tested.

**Company-level (once per company):**
- **Employee band** (≤50 / 51–200 / 200+). IESO's Small Business Program gives businesses with 50 or fewer employees no-cost upgrades, with lighting incentives up to $3,000. Changes the pitch and possibly conversion.
- **Facility type:** warehouse/distribution, manufacturing, retail, office, multi-unit residential, agricultural/greenhouse, other. Most standard lighting measures moved from the Retrofit program to Instant Discounts; horticultural lighting and networked lighting controls remain in Retrofit.
- **Owner-occupied vs leased.** Split-incentive problem: owner pays, tenant saves. Log "unknown" rather than guessing.
- **Current lighting status:** fluorescent / HID / mixed / LED / unknown. "Already has LED/EV/solar" (MyPhoner loser) is a disqualifier, not a model input.
- **Solar fit:** flat roof, owned building. Retrofit solar PV incentives: $1,000/kW-DC up to 10 kW; $860/kW-AC from >10 kW to 1 MW; capped at 50% of costs.
- **Region / local distribution company.** IESO regional adders double Retrofit incentives in named areas (e.g., Niagara, Kingston, Barrie/Muskoka).
- **Lead source / list name** (top feature in González-Flores et al.).
- **Line type:** main switchboard vs direct dial.

**Call-level (automatic where possible):**
- Timestamp, hour block, weekday
- Attempt number for this company
- Days since last attempt
- Outcome code
- Role reached: owner, facility/plant manager, operations, office admin, other
- Voicemail left (yes/no)
- Objection code: already upgraded, leases, no budget, bad timing, not decision-maker, other
- Callback date

**Benchmarks (vendor data, loose comparison only):**
- Cognism 2024 (with WHAM): 55,701 dials, 9,247 connects (16.6%), 5,265 conversations, 254 meetings; 4.82% meeting rate per conversation.
- Gong Labs (July 2024, 300M calls): average rep connects with 5.4% of prospects, top quartile 13.3%.
- Ayrton's ~23% non-voicemail and 6.2% booked per dial are well above these, suggesting well-targeted lists.

**Attempts before giving up:**
- InsideSales claims contact chance reaches 90% by the sixth call (inbound-lead vendor data).
- Cognism/WHAM 2024: 3 attempts optimal; Cognism 2025: 93% of conversations happen by the third call.
- Defensible approach: find, on his own data, the attempt number where marginal connect rate falls below average.

**Best time to call (weak evidence):**
- MIT/InsideSales study covered inbound web leads, not cold B2B. Found Wed/Thu and 4–6 pm best.
- Gong sources disagree: one favors Wed/Thu; Gong Engage benchmarks say Tue/Wed 9 am–12 pm.
- Treat as hypotheses to test.

### 5.6 Models and cadence engine
**Model A, P(answered) per call slot:** hour block × attempt number × line type, company as grouping variable. Start with beta-binomial rates per time block (4–5 blocks, pooled across days; 5×5 = 25 cells is too thin).

**Model B, P(book | relevant contact reached) per company:** facility type, employee band, ownership, lighting status, source. About 40% of relevant contacts book, so this outcome is not rare.

**Prioritization score:**
Expected meetings per dial ≈ P(answer at this time) × P(relevant person | answered) × P(book | relevant).
This gives both who to call and when.

**Thompson sampling for call timing:**
- Each time block is an arm with Beta(successes+1, failures+1) for answer rate.
- Each morning, sample from each block's distribution and favor highest draws for re-attempts.
- Asymptotically optimal for Bernoulli bandits (Kaufmann et al., 2012). Applied to call pickup timing in maternal-health outreach (arXiv 2410.21405, 2024). Patent US 11068304 describes a Thompson-sampling contextual bandit for best time to call sales leads.
- About 30 lines of Python or Apps Script.

**Retry heuristic until Model A has data:**
- Rotate time blocks after each voicemail.
- Space attempts 1–3 business days apart.
- Leave voicemail on attempts 1 and 3 only.
- Cap at about 6 attempts.
- Flag companies with 4+ consecutive voicemails and no gatekeeper contact; find a different number or contact.

### 5.7 Build options

| Option | Cost | Effort | Maintenance | Verdict |
|---|---|---|---|---|
| Google Sheets + Apps Script sidebar/web-app form (hotkeys, auto timestamp and attempt count) | $0 | 1–2 days | Low | Recommended if Haneco uses Google Workspace. Quotas: 6 min/execution; 90 min/day trigger runtime consumer (6 h Workspace); 20 triggers/script. |
| Excel + Office Scripts / Power Automate | Included in M365 business plans | 2–3 days | Low–medium | Equivalent if company runs Microsoft. |
| MyPhoner API/webhooks → Sheet | $0 direct or Zapier/Make plan | 2–4 days | Medium | Best data source. Webhooks on winner/loser/call_back/new_call. Rate limit 60 req/min, 300 per 5 min. Needs API key from account admin. Webhooks don't fire for changes made via API. |
| Local web app (Flask/Streamlit) | $0 | 3–5 days | Medium–high | Only if Sheets forms are too slow. Adds data-residency questions. |
| Python scoring script (pandas + scikit-learn LogisticRegression, L2) | $0 | 1 day | Low | Run weekly; write p_answer, p_book, next_best_slot, explore_flag back to the Sheet. |

**Logger design:**
- Single screen. Keys: V = voicemail, G = gatekeeper, W = wrong person, N = not interested, I = interested, B = booked.
- Second keystroke sets role and objection.
- Free text optional.
- Script derives timestamp, weekday, hour block, attempt number.
- Target under 10 seconds per call. Saving 30–45 s/call returns about 15–20 min/day at 30 calls (illustrative estimate).

**MyPhoner access (from public docs):**
- REST JSON API for users, lists, leads, calls, webhooks.
- Account-level API key (Manage → Configure → Integrations) and personal API key with the user's rights.
- Lists export to CSV/Excel via Manage → Lists → Export/Move; exports include `score` and `manual_rating`.
- Built-in lead score starts at 30 and adjusts with engagement. Check what it does before rebuilding it.
- Limitation: the API cannot access report data.

### 5.8 Privacy and workplace
- **PIPEDA** s. 4.01 excludes business contact information used solely to communicate with someone about their employment. Names, titles, work numbers used to call prospects are largely out of scope.
- Free-text notes about individuals, or use beyond contacting them, can fall outside the exemption. Keep notes business-focused.
- **CRTC:** National Do Not Call List rules do not apply to calls to businesses, but Telemarketing Rules still apply, the company must be registered, and it must honor its **internal** do-not-call list. Add a DNC outcome code.
- **Employer approval required.** Leads, outcomes, and any model trained on them are Haneco's confidential data. Build in a company-owned Google or Microsoft account, not personal Gmail. Never copy lead data to personal devices or public GitHub. Get written sign-off describing what will be built. Pitch it as a team asset (pooled team data is the only route to Phase 3).
- **Work term report:** anonymize company names; ask the co-op office and employer about confidentiality before including internal figures.
- Not legal advice. Confirm obligations with Haneco.

### 5.9 Realistic gains and pitfalls
**Where gains come from:**
- Faster logging: minutes a day, plus clean data.
- Timing and retry optimization targets the 77% voicemail rate. Illustrative: lifting non-voicemail from 23% to 26%, with proportional downstream conversion, raises meetings about 13% (about 1 more per week). Assumes extra answers are as valuable as current ones.
- Fit scoring mainly helps skip obvious non-fits sooner.

**Published evidence:**
- Velocify (2014): over 400 customers, 90 days; prioritization users made 49% more contact attempts and had 15% higher contact and conversion. Observational vendor data, likely selection bias, mostly B2C, measured queue prioritization not scoring.
- Parush et al. (2022, arXiv): randomized test at an online marketplace; causal uplift policy raised a delivery-rate proxy 22% relative (p = 0.026). A purely predictive model (AUC 0.849) showed no benefit in off-policy evaluation. Ranking by probability of success differs from ranking by where the call changes the outcome.
- Wu, Andreev & Benyoucef (2023): review of 44 studies; lead scoring positively affects sales performance, but no pooled effect size, and models are mostly built on low-quality or insufficient data.

**Pitfalls:**
- **Selective labels / feedback loop** (Lakkaraju et al., KDD 2017): if only high-scored leads get called, low-scored leads are never tested. Counter: spend 10–15% of daily dials on random lower-scored leads; log score at call time plus an `explore` flag; never delete leads because of score.
- **Leakage:** fields like "lead status" or "callback scheduled" are partly outcomes. Use only information known before the call.
- **Cold start:** points rules plus beta-binomial priors; the PD11 baseline is the prior.
- **Data quality:** inconsistent codes hurt more than algorithm choice. Lock codes; no new codes mid-term without a mapping.
- **Non-stationarity:** IESO programs change (e.g., Retrofit changes effective June 30, 2026). Refit monthly; weight recent data.

### 5.10 Research phased plan
**Phase 1, weeks 1–2:** manager approval; request API key or weekly export; Apps Script logger with hotkeys and derived fields (one row per call, plus company sheet with one row per company); lock codes VM, GK, WP, NI, INT, BKD, BAD (bad number), DNC; default cadence; points-based fit flag (+2 owner-occupied, +2 warehouse/manufacturing, +1 ≤50 employees, disqualify if already LED); weekly beta-binomial review of answer rate by hour block and booking rate by facility type.

**Phase 2, after about 100+ meetings and about 1,500+ calls (8–12 weeks):** Model A per-block answer rates with Thompson sampling; Model B ridge logistic regression, 3–6 pre-specified predictors, company-grouped repeated CV; keep only if it beats base rate on Brier and calibrates; write scores back; keep exploration share; A/B test by alternating days with and without score ordering, comparing meetings per dial.

**Phase 3, only with pooled team data and several hundred meetings:** gradient boosting vs logistic under the same validation; adopt only if clearly better. Skip neural networks unless thousands of events.

### 5.11 Research caveats
- Most timing/attempt statistics come from vendors (InsideSales, Gong, Cognism, Velocify), with inconsistent definitions, often inbound leads, not peer-reviewed.
- No study on Ontario energy-audit cold-call predictors; features are reasoned, not proven.
- MyPhoner capabilities come from public docs; account plan and role permissions may restrict them.

### 5.12 Research sources
- van der Ploeg et al. (2014): https://bmcmedresmethodol.biomedcentral.com/articles/10.1186/1471-2288-14-137
- Riley et al. (2019): https://onlinelibrary.wiley.com/doi/full/10.1002/sim.7992
- van den Goorbergh et al. (2022): https://arxiv.org/abs/2202.09101
- MIT/InsideSales lead response study: https://25649.fs1.hubspotusercontent-na2.net/hub/25649/file-13535879-pdf/docs/mit_study.pdf
- Gong cold call guide: https://www.gong.io/files/gong-guide-9-secret-elements-of-cold-calls.pdf
- Gong Engage benchmarks: https://help.gong.io/docs/engage-analytics-benchmarks-and-best-practices
- MyPhoner API: https://www.myphoner.com/docs/api/
- MyPhoner export/import: https://www.myphoner.com/blog/howto-bulk-update-leads-using-export-import/
- MyPhoner lead scoring: https://myphoner.help/en/articles/11022029-understanding-the-lead-scoring-system
- MyPhoner API FAQ: https://myphoner.help/en/articles/5832836-does-myphoner-have-an-api
- Velocify (2014): https://www.prnewswire.com/news-releases/velocify-study-shows-automatic-prioritization-significantly-increases-sales-lead-conversion-267326571.html
- Wu et al. (2023): https://www.researchgate.net/publication/367962051_The_state_of_lead_scoring_models_and_their_impact_on_sales_performance
- González-Flores et al. (2025): https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1554325/full
- Nygård & Mezei (2020): https://scholarspace.manoa.hawaii.edu/items/575bb293-482c-4ffa-8be9-b177feba5f57
- IESO energy efficiency for business: https://www.ieso.ca/Get-Involved/Energy-Efficiency/Energy-Efficiency-for-Business
- Save on Energy Retrofit update: https://www.saveonenergy.ca/en/For-Business-and-Industry/Programs-and-incentives/Retrofit-Program/Retrofit-Program-Update
- Cognism state of cold calling: https://www.cognism.com/state-of-cold-calling
- InsideSales lead response: https://www.insidesales.com/lead-response-management-infographic/
- Agrawal & Goyal (Thompson sampling): http://proceedings.mlr.press/v23/agrawal12/agrawal12.pdf
- Bandit call-timing (2024): https://arxiv.org/pdf/2410.21405
- Patent US 11068304: https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11068304
- Apps Script quotas: https://developers.google.com/apps-script/guides/services/quotas
- PIPEDA finding: https://www.priv.gc.ca/en/opc-actions-and-decisions/investigations/investigations-into-businesses/2019/pipeda-2019-006/
- CRTC telemarketing registration: https://crtc.gc.ca/eng/phone/telemarketing/tobligations/register-inscrire.htm
- CRTC business calls: https://crtc.gc.ca/eng/phone/telemarketing/biz.htm
- Parush et al. (2022): https://arxiv.org/pdf/2207.01722
- Lakkaraju et al. (2017): https://www.semanticscholar.org/paper/The-Selective-Labels-Problem:-Evaluating-in-the-of-Lakkaraju-Kleinberg/47c3d413056fe8538cb5ce2d6adc860e70062bf6

---

## 6. Concerns and Risks

| # | Concern | Why it matters | Mitigation |
|---|---|---|---|
| 1 | **Small labeled dataset** (600 calls, 37 meetings for Ayrton alone) | Neural networks and complex models overfit | Interpretable models; pull team-wide history; LLM-tag old comments to create labels |
| 2 | **Voicemail is the real bottleneck** (~77%) | Faster logging alone gives modest gains | Timestamp everything; optimize call timing and retries |
| 3 | **Logging time savings unmeasured** | Payoff estimate (~20 min/day) is a guess | Ayrton times himself on several calls |
| 4 | **Data belongs to Haneco** | Using it in personal tools without approval is a workplace and confidentiality problem | Written approval from Angela; company-owned accounts; no data in personal Gmail, devices, or public repos |
| 5 | **Privacy / telemarketing rules** | PIPEDA scope, CRTC registration, internal DNC list | Business-focused notes; DNC code; confirm with Haneco |
| 6 | **MyPhoner "cannot export"** | Blocks bulk analysis | Docs show API, webhooks, list export; likely a permissions issue. Request API key or export |
| 7 | **Scoring vs learning confusion** | More lists add leads to grade, not training labels | Count historical calls with outcomes across all lists and reps |
| 8 | **Chicago vs Ontario** | Different incentive programs (Save on Energy vs ComEd), pitch, and odds | Region as a feature, or separate models |
| 9 | **Feedback loop / selective labels** | Low-scored leads never get called, so the model never learns it was wrong | 10–15% exploration; log score and explore flag at call time; never delete leads by score |
| 10 | **Leakage** | Outcome-derived fields inflate model accuracy | Only pre-call information as features |
| 11 | **Label quality from LLM tagging** | Wrong tags poison the model | Hand-check a sample of tagged comments; measure agreement before trusting |
| 12 | **Historical selection bias** | Past calls weren't random; lists were chosen and ordered by people | Note it; use exploration going forward |
| 13 | **Non-stationarity** | IESO programs change (Retrofit changes June 30, 2026) | Monthly refits; weight recent data |
| 14 | **Weak benchmark evidence** | Vendor stats use inconsistent definitions | Trust own data after a few weeks |
| 15 | **PD11 numbers are estimates** | Only 37 meetings is a hard count | Replace with counted values once tagging/logging runs |
| 16 | **MyPhoner duplicate entry** | Logger plus MyPhoner means two systems | Clipboard comment generation now; webhooks/API sync later |

---

## 7. Proposed System Design

This is a starting design. Platform choices depend on Section 9 answers.

### 7.1 Components
1. **Call Logger (UI):** keyboard-driven form. One key for outcome, one for role, one for objection, optional note. Writes a call row, updates the company row, generates a tagged MyPhoner comment and copies it to the clipboard.
2. **Data Store:** the existing spreadsheet (Google Sheets or Excel), extended with structured tabs. No outside server unless approved.
3. **MyPhoner Importer:** pulls lists, leads, and call history (with comments) via API or CSV/Excel export.
4. **Comment Tagger (LLM):** reads historical free-text comments and outputs structured fields (outcome code, role reached, objection, callback date, gatekeeper gave name yes/no). Includes a human review step on a sample.
5. **Follow-Up Ranker (rules):** ranks follow-up list leads with deterministic rules (Section 7.5). No model needed.
6. **Scoring Engine (Python, later):** Value score, Ease score (Model A answer, Model B booking), Priority. Writes scores back to the sheet.
7. **Cadence Engine:** retry heuristic now, Thompson sampling over time blocks later. Outputs next best call slot per lead.
8. **Weekly Report:** rates from PD11 Section 3.4 (contact rate, relevant-contact rate, meeting rate, identification failure rate), answer rate by hour block, booking rate by segment.

### 7.2 Data model (proposed)

**`companies`** (one row per company)
| Field | Type | Notes |
|---|---|---|
| company_id | string | Stable key (MyPhoner lead/company ID if available) |
| company_name | string | |
| list_name | string | Source list (lead source feature) |
| market | enum | Ontario, Other Canada, Chicago |
| region / LDC | string | For IESO regional adders |
| facility_type | enum | warehouse, manufacturing, retail, office, multi-unit residential, agricultural/greenhouse, other, unknown |
| employee_band | enum | ≤50, 51–200, 200+, unknown |
| ownership | enum | owner-occupied, leased, unknown |
| lighting_status | enum | fluorescent, HID, mixed, LED, unknown |
| solar_fit | enum | yes, no, unknown |
| decision_maker_identified | bool | |
| last_outcome | enum | Outcome code |
| last_call_at | datetime | |
| attempts | int | |
| next_retry_date | date | |
| value_score | float | |
| ease_score | float | |
| priority | float | |
| disqualified | bool | e.g., already LED/solar (MyPhoner loser) |
| dnc | bool | Internal do-not-call |

**`contacts`** (one row per person at a company)
| Field | Notes |
|---|---|
| contact_id, company_id | |
| name, title | Business contact info only |
| role | owner, facility/plant manager, operations, office admin, other |
| phone, line_type | switchboard vs direct dial |
| status | active, left company, wrong person |

**`calls`** (one row per call)
| Field | Notes |
|---|---|
| call_id, company_id, contact_id | |
| timestamp | Auto |
| weekday, hour_block | Auto-derived |
| attempt_number | Auto-derived per company |
| days_since_last_attempt | Auto-derived |
| outcome | VM, GK, WP, NI, INT, BKD, BAD, DNC |
| role_reached | |
| objection | already upgraded, leases, no budget, bad timing, not decision-maker, other |
| voicemail_left | bool |
| callback_date | |
| gatekeeper_gave_name | bool |
| note | Optional free text, business-focused only |
| caller | Ayrton or colleague |
| score_at_call_time | For feedback-loop tracking |
| explore_flag | True if picked by random exploration |
| source | logger, myphoner_import, llm_tagged |
| tag_confidence | For LLM-tagged rows |

### 7.3 Outcome codes (locked)
VM, GK, WP, NI, INT, BKD (from PD11), plus BAD (bad number) and DNC (do not call). Precedence: furthest point reached. Do not add codes without a mapping.

### 7.4 Scores
- **Value:** points from facility_type, employee_band, lighting_status, solar_fit, ownership. Start rule-based; Ayrton and Angela should set weights.
- **Ease:** start with beta-binomial segment rates (prior from PD11 baseline). Later: Model A (answer) × P(relevant | answered) × Model B (book | relevant).
- **Priority = Value × Ease.**
- Disqualified and DNC leads are excluded, not scored low.

### 7.5 Follow-up ranking rules (Phase 1 proof of concept)
1. INT with callback date due or past due
2. GK where a name or direct line was obtained
3. NI where enough time has passed to retry (threshold to be set; e.g., 60–90 days, unconfirmed)
4. Repeated VM (4+) with no human contact → flag for new number/contact, not another dial
Within each tier, sort by Value score, then by days since last attempt.

### 7.6 Cadence defaults
Rotate time blocks after each VM; 1–3 business days between attempts; voicemail on attempts 1 and 3 only; cap about 6 attempts; flag 4+ consecutive VMs.

### 7.7 Market handling
`market` is a required field. Either include it as a model feature or train separate Ease models per market. Chicago value scoring must not use Save on Energy assumptions.

---

## 8. Phased Build Plan and Tasks

### Phase 0: Prerequisites (Ayrton, not code)
- [ ] Written approval from Angela/Haneco describing the tool and data use
- [ ] Find out spreadsheet platform and get a screenshot of current columns/dropdowns
- [ ] Ask for MyPhoner personal API key or full list exports (with comments) for all lists, especially the two follow-up lists
- [ ] Find out how much history exists: total calls across all lists and reps, date range
- [ ] Time current logging per call on several calls
- [ ] Confirm work computer permissions (installs, scripts)
- [ ] Confirm whether the colleague will use the tool

### Phase 1: Proof of concept on one follow-up list
**Input:** one exported follow-up list with comments (about 150 leads).
1. Write a parser for the MyPhoner export format.
2. Build the LLM comment tagger. Output structured fields per comment with confidence.
3. Hand-review a random sample (e.g., 30 comments). Report agreement rate.
4. Apply follow-up ranking rules (Section 7.5).
5. Output a ranked list back to a sheet/CSV.
**Done when:** Ayrton can call down the ranked list, and tag agreement on the sample is acceptable to him.

### Phase 2: Fast logger
1. Build the logger on the confirmed platform (Apps Script sidebar for Google Sheets, or Office Scripts / local page for Excel).
2. Hotkeys for outcome, role, objection; auto timestamp, weekday, hour block, attempt number.
3. Write call row, update company row, compute next retry date.
4. Generate tagged MyPhoner comment and copy to clipboard.
**Done when:** logging takes under 10 seconds per call and every PD11 success criterion is met.

### Phase 3: Full history import and baseline
1. Import all lists and all call history via API or exports.
2. Run the comment tagger over all history; spot-check by market.
3. Build the weekly report (PD11 rates, answer rate by hour block, booking rate by segment, by market).
4. Replace PD11 estimates with counted values.

### Phase 4: Scoring
1. Value score (rules, weights agreed with Ayrton/Angela).
2. Ease via beta-binomial segment rates.
3. If enough labeled outcomes exist: Model A and Model B (ridge logistic regression, 3–6 predictors, company-grouped repeated CV, Brier, calibration, AUC with CI, must beat base rate).
4. Write scores and next best slot back to the sheet.
5. Exploration: 10–15% random lower-scored leads; log score_at_call_time and explore_flag.

### Phase 5: Cadence optimization and evaluation
1. Thompson sampling over time blocks for re-attempts.
2. A/B test: alternate days with and without score ordering; compare meetings per dial.
3. Monthly refit.

### Phase 6 (only if data supports it)
Gradient boosting vs logistic regression under identical validation. Neural networks only with thousands of events.

---

## 9. Open Questions (Must Be Answered Before Building)

| # | Question | Blocks |
|---|---|---|
| 1 | Is the lead tracker Google Sheets, Excel online (OneDrive/SharePoint), or local Excel? | Platform for logger and data store |
| 2 | What columns and dropdown options exist in the tracker and follow-up lists? | Data model mapping |
| 3 | Can Ayrton install software on the work computer, or browser only? Can scripts be added to the sheet? | Logger implementation |
| 4 | Just Ayrton, or the co-op colleague too? | Multi-user design, caller field |
| 5 | Has Haneco/Angela approved the tool and data use, in writing? | Everything |
| 6 | Can Ayrton get a MyPhoner API key or full exports with comments? | Importer, history, tagger |
| 7 | How many calls with outcomes exist in MyPhoner across all lists, reps, and terms? How far back? | Model choice and phase timing |
| 8 | How long does logging currently take per call? | Payoff measurement |
| 9 | Which LLM/API is approved for tagging comments, and can company data be sent to it? | Comment tagger |
| 10 | What retry wait should apply after NI? | Follow-up rules |
| 11 | Value score weights: which facility types and sizes are worth most to Haneco? | Value score |
| 12 | What does the Chicago pitch and incentive structure look like? | Chicago scoring |
| 13 | What fields does a MyPhoner export actually contain? | Parser |

### Answers so far (October 19, 2026)
- **Q1:** Tracker is Google Sheets. Ayrton wants a separate app or website to enter lead info. It either tracks leads itself or pushes them into Sheets.
- **Q3:** Can install software on the work computer.
- **Q5:** Not approved yet. Use synthetic data only until written approval.
- **Q6:** Unknown. Ayrton will ask for an API key or list export.

### Decisions (October 19, 2026)
- **External app:** Lumen is a local web app (`lumen.py` + `index.html`). It tracks leads itself (SQLite) and syncs to Google Sheets when possible.
- **Brands replace markets:** Haneco (Canada), JWL (Chicago), Exceledy (Texas, coming later).
- **Products:** Solar, Lighting, BESS. Set per lead, multi-select.
- **Lists:** each lead is either "new" (MyPhoner list) or "follow-up" (Ayrton's follow-up list).
- **Outcome codes, expanded with a mapping** (supersedes 7.3): VM; RCP = GK; WP; EREQ (requested email) and BUSY (interested, busy) = INT; EMAILED (an action, not a call); NI; BKD; HAS = MyPhoner loser; BAD; DNC.
- **Contacts:** several per lead, with name and job title. Voicemail streaks are tracked per contact.
- **Advice:** rule-based next steps in `advice()` (find another contact, go through reception, prefers email, offer times).
- **Model:** Ayrton wants to learn PyTorch. `model.py` uses PyTorch with `HIDDEN = 0` (logistic regression as a one-layer net), so scores stay explainable on small data. A hidden layer is one constant away. Training teaches from every call (features before the call predict whether it went well) plus Good/Poor labels (3× weight). Holdout is grouped by lead, and the sidebar reports whether the model beats the base rate.

### Decisions (October 20, 2026)
Built from [PLAN.md](PLAN.md).
- **Lists:** `leads.source` is one of `new` (Leads), `follow-up`, `winner`, `loser`. Only Leads and Follow-ups are open, ranked and due.
- **Auto-moves:** BKD moves a lead to Winners, and HAS moves it to Losers. BAD and DNC close the lead but stay in their list. Moving back to Leads or Follow-ups clears `closed`.
- **Migration:** `MIGRATIONS` in `lumen.py` adds new columns to older databases on start without touching existing rows.
- **Contacts:** added `ext` and `phone_type` (direct / mobile / business). The lead's main phone counts as Business.
- **Appointment text:** `appointment_text()` builds calendar-invite text and skips empty lines. There is no heading.
- **Training:** Winners without a manual label count as good examples (3x). Losers add no label.
- **No browser autofill** on any input.

---

## 10. Constraints and Rules for Claude Code

- **Never commit real lead data** (company names, contacts, phone numbers, comments) to any repository. Use synthetic sample data for development and tests. Add data folders to `.gitignore`.
- **No secrets in code.** MyPhoner API keys and LLM keys go in environment variables or the platform's secret store.
- **Company-owned accounts only** for deployed tools and data storage.
- **Keep data inside the existing spreadsheet ecosystem** unless Ayrton confirms approval for anything else.
- **Respect MyPhoner rate limits:** 60 requests/minute, 300 per 5 minutes.
- **Only pre-call information as model features** (no leakage).
- **Always log score_at_call_time and explore_flag** once scoring is live.
- **DNC and disqualified leads are excluded**, never just scored low.
- **Locked outcome codes:** VM, GK, WP, NI, INT, BKD, BAD, DNC.
- **Interpretable models first.** No neural networks unless data volume justifies it and validation shows a clear win.
- **Every model must beat the base-rate baseline** under company-grouped cross-validation, or it does not ship.
- **Ask Ayrton** when a Section 9 question blocks a decision. Do not guess platform, fields, or weights.
- Code style preferences from Ayrton (apply where relevant): keep comments minimal and only where needed; be explicit about steps; no skipped steps without explanation.

---

## 11. Glossary

- **MyPhoner:** the dialer/CRM Haneco uses. Statuses: winner, loser, call back.
- **Winner:** meeting booked. **Loser:** company already has lighting, EV, and solar solutions. **Call back:** everything else.
- **VM / GK / WP / NI / INT / BKD:** outcome codes from PD11 (voicemail, gatekeeper, wrong person, not interested, interested, booked). **BAD:** bad number. **DNC:** do not call.
- **Relevant contact:** a person able to discuss an energy audit (NI, INT, or BKD).
- **Identification failure:** GK or WP.
- **Save on Energy:** Ontario energy-efficiency incentive program run by the IESO.
- **IESO:** Independent Electricity System Operator (Ontario).
- **ComEd:** Chicago-area utility with its own incentive programs.
- **Beta-binomial:** Bayesian method for estimating a rate from small counts by shrinking toward an overall prior.
- **Ridge (L2) logistic regression:** logistic regression with a penalty that limits overfitting.
- **Thompson sampling:** method that picks options (e.g., call time blocks) by sampling from each option's estimated success distribution, balancing exploration and exploitation.
- **Brier score:** mean squared error of predicted probabilities; lower is better.
- **Calibration:** whether predicted probabilities match observed rates.
- **Selective labels / feedback loop:** a model only learns from leads it chose to call, so it never sees whether skipped leads were good.
- **Leakage:** using information in features that would not be known before the call.
- **Value × Ease:** priority formula; Value = customer worth, Ease = likelihood of booking.
