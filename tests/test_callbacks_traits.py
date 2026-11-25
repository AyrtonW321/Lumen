import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from lumen.activities import log_activity
from lumen.callbacks import callbacks
from lumen.contacts import add_contact
from lumen.db import connect
from lumen.leads import add_lead, lead_detail, list_leads, update_lead
from lumen.traits import add_trait, badges, catalog, delete_trait, update_trait
from tests.base import T0, DbTestCase


class CallbackTests(DbTestCase):
    def setUp(self):
        super().setUp()
        self.lead = add_lead(self.conn, "Test Callback Co", "Haneco", phone="555-0100", now=T0)
        self.amy = add_contact(self.conn, self.lead, "Amy Test", title="Owner", phone="555-0101", ext="12", now=T0)

    def sections(self, now):
        return {r["name"]: r["section"] for r in callbacks(self.conn, now)}

    def test_callback_time_lands_in_comment_and_sections_follow_the_date(self):
        r = log_activity(self.conn, self.lead, "CALLBACK", self.amy, callback_date="2026-10-21",
                         callback_time="14:00", note="Call after lunch", now=T0)
        self.assertIn("call back 2026-10-21 14:00", r["myphoner_comment"])
        self.assertEqual(self.sections(T0), {"Test Callback Co": "upcoming"})
        row = callbacks(self.conn, datetime(2026, 10, 21, 15))[0]
        self.assertEqual((row["section"], row["late"]), ("today", True))
        self.assertEqual((row["phone"], row["ext"], row["contact"]["name"]), ("555-0101", "12", "Amy Test"))
        self.assertEqual(row["last_note"], "Call after lunch")
        self.assertEqual(self.sections(datetime(2026, 10, 22, 9)), {"Test Callback Co": "overdue"})
        self.assertEqual(self.sections(T0 - timedelta(days=30)), {})  # beyond the upcoming window

    def test_retry_dates_are_not_callbacks_and_next_call_clears_one(self):
        log_activity(self.conn, self.lead, "VM", now=T0)
        self.assertEqual(callbacks(self.conn, T0 + timedelta(days=3)), [])
        log_activity(self.conn, self.lead, "BUSY", callback_date="2026-10-20", now=T0)
        self.assertEqual(len(callbacks(self.conn, T0)), 1)
        log_activity(self.conn, self.lead, "VM", now=T0)
        self.assertEqual(callbacks(self.conn, T0), [])

    def test_expecting_call_shows_until_next_call_and_counts_broken_promises(self):
        for _ in range(2):
            log_activity(self.conn, self.lead, "CALLBACK", self.amy, callback_date="2026-11-30",
                         expecting_call=True, now=T0)
            self.assertEqual(self.sections(T0), {"Test Callback Co": "expecting"})
            log_activity(self.conn, self.lead, "VM", self.amy, called_back=False, now=T0)
            self.assertEqual(callbacks(self.conn, T0), [])
        log_activity(self.conn, self.lead, "VM", self.amy, called_back=False, now=T0)  # not expecting: not counted
        calls = lead_detail(self.conn, self.lead)
        self.assertIn("Doesn't call back", calls["badges"])
        self.assertIn("Doesn't call back", calls["contacts"][0]["badges"])

    def test_bad_callback_inputs_are_rejected(self):
        self.assertRejects(lambda **k: log_activity(self.conn, self.lead, **k),
                           dict(outcome="VM", callback_time="14:00"),
                           dict(outcome="VM", expecting_call=True),
                           dict(outcome="CALLBACK", callback_date="2026-10-21", callback_time="2pm"))
        self.assertRejects(lambda **k: update_lead(self.conn, self.lead, **k), dict(callback_at="tomorrow"))

    def test_closed_leads_drop_out(self):
        log_activity(self.conn, self.lead, "CALLBACK", callback_date="2026-10-19", now=T0)
        log_activity(self.conn, self.lead, "DNC", now=T0)
        self.assertEqual(callbacks(self.conn, T0), [])


class BackfillTests(DbTestCase):
    def test_old_open_callbacks_are_recovered_from_comments(self):
        old = Path(tempfile.mkdtemp()) / "old.db"
        raw = sqlite3.connect(old)
        raw.executescript("""CREATE TABLE leads (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE,
          brand TEXT NOT NULL, products TEXT NOT NULL DEFAULT '', source TEXT NOT NULL DEFAULT 'new',
          list_name TEXT, phone TEXT, label TEXT, closed TEXT, next_action_date TEXT, created_at TEXT NOT NULL);
          CREATE TABLE activities (id INTEGER PRIMARY KEY, lead_id INTEGER NOT NULL, contact_id INTEGER,
          timestamp TEXT NOT NULL, weekday TEXT NOT NULL, hour_block TEXT NOT NULL, outcome TEXT NOT NULL,
          note TEXT, caller TEXT, myphoner_comment TEXT NOT NULL);
          INSERT INTO leads VALUES (1, 'Asked Co', 'Haneco', '', 'follow-up', NULL, NULL, NULL, NULL, '2026-10-23', 'x');
          INSERT INTO leads VALUES (2, 'Retry Co', 'Haneco', '', 'new', NULL, NULL, NULL, NULL, '2026-10-23', 'x');
          INSERT INTO activities VALUES (1, 1, NULL, '2026-10-19T09:00:00', 'Mon', '9-11', 'BUSY', NULL, NULL,
                                         'BUSY 09:00 - call back 2026-10-23');
          INSERT INTO activities VALUES (2, 2, NULL, '2026-10-19T09:00:00', 'Mon', '9-11', 'VM', NULL, NULL,
                                         'VM 09:00');""")
        raw.commit()
        raw.close()
        conn = connect(old)
        self.addCleanup(conn.close)
        got = {r["name"]: r["callback_at"] for r in conn.execute("SELECT name, callback_at FROM leads")}
        self.assertEqual(got, {"Asked Co": "2026-10-23", "Retry Co": None})


class TraitTests(DbTestCase):
    def setUp(self):
        super().setUp()
        self.lead = add_lead(self.conn, "Test Trait Co", "JWL", now=T0)
        self.other = add_lead(self.conn, "Other Trait Co", "JWL", now=T0)
        self.amy = add_contact(self.conn, self.lead, "Amy Test", now=T0)

    def test_presets_reuse_spelling_and_duplicates_update_the_note(self):
        first = add_trait(self.conn, self.lead, "  nice ", self.amy, note="Talks hockey", now=T0)
        again = add_trait(self.conn, self.lead, "NICE", self.amy, note="Loves hockey", now=T0)
        self.assertEqual(first, again)
        t = lead_detail(self.conn, self.lead)["contacts"][0]["traits"]
        self.assertEqual([(x["name"], x["note"], x["global"]) for x in t], [("Nice", "Loves hockey", 1)])

    def test_one_off_traits_stay_out_of_catalog_until_promoted(self):
        tid = add_trait(self.conn, self.lead, "Roofing construction", note="Done in spring", now=T0)
        self.assertNotIn("Roofing construction", catalog(self.conn)["company"])
        self.assertEqual(lead_detail(self.conn, self.lead)["traits"][0]["name"], "Roofing construction")
        update_trait(self.conn, tid, **{"global": True})
        self.assertIn("Roofing construction", catalog(self.conn)["company"])
        self.assertNotIn("Roofing construction", catalog(self.conn)["person"])
        add_trait(self.conn, self.other, "roofing CONSTRUCTION", now=T0)
        self.assertEqual(lead_detail(self.conn, self.other)["traits"][0]["name"], "Roofing construction")

    def test_saved_custom_trait_and_list_rows(self):
        add_trait(self.conn, self.lead, "Speaks French", self.amy, save=True, now=T0)
        add_trait(self.conn, self.lead, "Budget-tight", now=T0)
        self.assertIn("Speaks French", catalog(self.conn)["person"])
        row = next(r for r in list_leads(self.conn, today=T0.date()) if r["id"] == self.lead)
        self.assertEqual({(t["name"], t["person"]) for t in row["traits"]},
                         {("Speaks French", True), ("Budget-tight", False)})

    def test_delete_and_validation(self):
        tid = add_trait(self.conn, self.lead, "Rude", self.amy, now=T0)
        delete_trait(self.conn, tid)
        self.assertEqual(lead_detail(self.conn, self.lead)["contacts"][0]["traits"], [])
        stranger = add_contact(self.conn, self.other, "Bo Test", now=T0)
        self.assertRejects(lambda **k: add_trait(self.conn, self.lead, **k),
                           dict(name=" "), dict(name="x" * 41), dict(name="Nice", note="x" * 201),
                           dict(name="Nice", contact_id=stranger))
        self.assertRejects(lambda **k: delete_trait(self.conn, **k), dict(trait_id=999))
        self.assertRejects(lambda **k: update_trait(self.conn, tid, **k), dict(name="New"))


class BadgeTests(DbTestCase):
    def acts(self, *outcomes, contact_id=None):
        return [{"outcome": o, "contact_id": contact_id, "called_back": None} for o in outcomes]

    def test_rules(self):
        self.assertEqual(badges(self.acts("VM", "BUSY")), [])  # too few calls to judge
        self.assertEqual(badges(self.acts("VM", "BUSY", "RCP")), ["Responsive"])
        self.assertEqual(badges(self.acts("BUSY", "VM", "VM", "VM", "VM")), ["Hard to reach"])
        self.assertEqual(badges(self.acts("VM", "EMAILED", "VM", "WIN", "VM", "OTHER", "VM")), ["Hard to reach"])
        self.assertEqual(badges(self.acts("CALLBACK", "VM", "NI")), ["Responsive"])
