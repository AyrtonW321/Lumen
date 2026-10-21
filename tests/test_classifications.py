from datetime import datetime

from lumen.activities import log_activity
from lumen.leads import add_lead, lead_detail, list_leads
from tests.base import DbTestCase, T0


class ClassificationTests(DbTestCase):
    def setUp(self):
        super().setUp()
        self.lead = add_lead(self.conn, "Classification Test", "Haneco", now=T0)

    def test_classifications_keep_notes_and_can_be_reopened(self):
        for outcome, source in (("WIN", "winner"), ("LOST", "loser")):
            with self.subTest(outcome=outcome):
                self.lead = add_lead(self.conn, f"Test {outcome}", "Haneco", now=T0)
                log_activity(self.conn, self.lead, outcome, note="Spoke with the owner.\nDiscussed the project.", now=T0)
                lead = lead_detail(self.conn, self.lead)
                self.assertEqual((lead["source"], lead["closed"]), (source, outcome))
                self.assertEqual(lead["activities"][0]["note"], "Spoke with the owner.\nDiscussed the project.")
                log_activity(self.conn, self.lead, "CALLBACK", callback_date="2026-10-23", note="Follow up on revised plans", now=datetime(2026, 10, 20, 10))
                lead = lead_detail(self.conn, self.lead)
                self.assertEqual((lead["source"], lead["closed"]), ("follow-up", None))
                self.assertEqual(lead["next_action_date"], "2026-10-23")
                self.assertEqual(lead["activities"][0]["outcome"], "CALLBACK")
                self.assertTrue(any(a["outcome"] == outcome for a in lead["activities"]))
                self.assertTrue(next(row for row in list_leads(self.conn) if row["id"] == self.lead)["open"])

    def test_existing_booked_lead_can_have_a_callback(self):
        log_activity(self.conn, self.lead, "BKD", now=T0)
        log_activity(self.conn, self.lead, "VM", callback_date="2026-10-23", now=T0)
        self.assertEqual(lead_detail(self.conn, self.lead)["source"], "follow-up")
        self.assertIsNone(lead_detail(self.conn, self.lead)["closed"])

    def test_callback_validation_does_not_write_activity(self):
        for date in (None, "invalid"):
            with self.subTest(date=date), self.assertRaises(ValueError):
                log_activity(self.conn, self.lead, "CALLBACK", callback_date=date, now=T0)
        self.assertEqual(lead_detail(self.conn, self.lead)["activities"], [])
