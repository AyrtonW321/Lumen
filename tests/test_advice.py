from datetime import date, timedelta

from lumen.activities import log_activity
from lumen.contacts import add_contact
from lumen.leads import add_lead, list_leads
from tests.base import T0, DbTestCase


class AdviceTests(DbTestCase):
    def rows(self, today=date(2026, 10, 23)):
        return {r["id"]: r for r in list_leads(self.conn, today=today)}

    def test_repeated_voicemail_on_one_contact_says_find_another(self):
        lead = add_lead(self.conn, "Test VM Warehouse", "Haneco", ["Lighting"], now=T0)
        bob = add_contact(self.conn, lead, "Bob Test", "Plant Manager", now=T0)
        for d in range(3):
            log_activity(self.conn, lead, "VM", contact_id=bob, now=T0 + timedelta(days=d))
        advice = self.rows()[lead]["advice"]
        self.assertTrue(any("Find another contact: Bob Test" in a for a in advice), advice)

    def test_busy_lead_ranks_first_and_is_due(self):
        vm = add_lead(self.conn, "Test VM Warehouse", "Haneco", now=T0)
        bob = add_contact(self.conn, vm, "Bob Test", "Plant Manager", now=T0)
        for d in range(3):
            log_activity(self.conn, vm, "VM", contact_id=bob, now=T0 + timedelta(days=d))
        busy = add_lead(self.conn, "Test Busy Plant", "JWL", ["Solar", "BESS"], source="follow-up", now=T0)
        amy = add_contact(self.conn, busy, "Amy Test", "Facilities Director", now=T0)
        r = log_activity(self.conn, busy, "BUSY", contact_id=amy, callback_date="2026-10-22", note="busy till Thu",
                         now=T0 + timedelta(hours=5))
        self.assertEqual(r["myphoner_comment"],
                         "BUSY 14:30 - Amy Test (Facilities Director) - call back 2026-10-22 - busy till Thu")
        rows = self.rows()
        self.assertTrue(rows[busy]["advice"][0].startswith("Open to a meeting"))
        self.assertEqual(rows[busy]["tier"], 1)
        self.assertEqual(rows[busy]["next_action_date"], "2026-10-22")
        self.assertTrue(rows[busy]["due"])
        self.assertLess(rows[busy]["tier"], rows[vm]["tier"])

    def test_receptionist_without_decision_maker(self):
        lead = add_lead(self.conn, "Test Reception Co", "Exceledy", now=T0)
        log_activity(self.conn, lead, "RCP", now=T0)
        self.assertTrue(any("Contact receptionist first" in a for a in self.rows()[lead]["advice"]))

    def test_receptionist_with_known_decision_maker_names_them(self):
        lead = add_lead(self.conn, "Test DM Known Co", "Haneco", now=T0)
        add_contact(self.conn, lead, "Dan Test", "Owner", now=T0)
        log_activity(self.conn, lead, "RCP", now=T0)
        advice = self.rows()[lead]["advice"]
        self.assertTrue(any("ask for Dan Test" in a for a in advice), advice)

    def test_email_request_marks_contact_and_advises_sending(self):
        lead = add_lead(self.conn, "Test Email Co", "Haneco", now=T0)
        sue = add_contact(self.conn, lead, "Sue Test", "Operations Manager", now=T0)
        log_activity(self.conn, lead, "EREQ", contact_id=sue, now=T0)
        advice = self.rows()[lead]["advice"]
        self.assertIn("Sue Test prefers email", advice)
        self.assertEqual(advice[0], "Send the email they asked for")
