# Lumen UI baseline and refurbishment

Baseline markup and styling are preserved in baseline.html and baseline.css. The incumbent UI used Nunito, a 212px fixed sidebar, 16px cards, pill controls, company avatars, emoji icons, and loosely separated lead rows. Contacts preceded activity logging; outcomes and callback shortcuts were button clusters.

The supplied reference guides the restrained blue and white workspace. The refurbishment keeps the existing TypeScript / Python architecture, with explicit separators, compact controls, a collapsible navigation rail, and a lead directory emphasizing company, products, lifecycle status, quality, originating list, and last contact. Status and quality are separate concepts.

Closed means a call outcome ended outreach (for example do not call or bad number). All statuses includes closed records; a specific Closed calls filter makes them discoverable. Updating a callback date without logging a call only changes the schedule.

Contact classification and sort order persist in SQLite via additive migrations. Existing title and main phone fields are reused. Appointment contact fields edit the selected contact. Other activity uses the call log for its explanation. History preserves newlines.

## Contrast and theme refinement

Added persistent light/dark mode, a slate top bar, shared surface tokens, rounded dropdowns (including the option picker where supported), labeled lead facts, and separated contact identity and reachability columns. Directory rows place lifecycle status at the top right and limit product tags to two plus an accessible +n label. Review screenshots in review/ use simulated companies and contacts, not production data. Checked desktop (1440px) and mobile (390px), both themes, theme persistence, and page errors. No horizontal page overflow was detected.

## Activity classifications

Winner, Loser, and Callback are recorded activities saved with the call note. Winner and Loser do not require a contact result. Callback reopens previously won or lost leads into Follow-ups while retaining their historical classifications. Existing Meeting booked and Already has solution records remain supported. Move to list is under Log activity; the compact lead header has a grey close icon at its top right. Activity review screenshots use simulated data.
