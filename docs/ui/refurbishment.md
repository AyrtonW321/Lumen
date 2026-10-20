# Lumen UI baseline and refurbishment

Baseline markup and styling are preserved in baseline.html and baseline.css. The incumbent UI used Nunito, a 212px fixed sidebar, 16px cards, pill controls, company avatars, emoji icons, and loosely separated lead rows. Contacts preceded activity logging; outcomes and callback shortcuts were button clusters.

The supplied reference guides the restrained blue and white workspace. The refurbishment keeps the existing TypeScript / Python architecture, with explicit separators, compact controls, a collapsible navigation rail, and a lead directory emphasizing company, products, lifecycle status, quality, originating list, and last contact. Status and quality are separate concepts.

Closed means a call outcome ended outreach (for example do not call or bad number). All statuses includes closed records; a specific Closed calls filter makes them discoverable. Updating a callback date without logging a call only changes the schedule.

Contact classification and sort order persist in SQLite via additive migrations. Existing title and main phone fields are reused. Appointment contact fields edit the selected contact. Other activity uses the call log for its explanation. History preserves newlines.
