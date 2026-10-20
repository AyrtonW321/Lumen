from datetime import date

from lumen.activities import log_activity
from lumen.leads import add_lead, list_leads, load_all, update_lead
from tests.base import T0, DbTestCase


class ValidationTests(DbTestCase):
    def setUp(self):
        super().setUp()
        self.lead = add_lead(self.conn, "Test Lead", "Haneco", now=T0)

    def test_log_activity_rejects_unknown_outcome_and_foreign_contact(self):
        other = add_lead(self.conn, "Other Co", "Haneco", now=T0)
        from lumen.contacts import add_contact
        stranger = add_contact(self.conn, other, "Amy Test", now=T0)
        self.assertRejects(lambda **k: log_activity(self.conn, **k),
                           dict(lead_id=self.lead, outcome="CB"),
                           dict(lead_id=self.lead, outcome="VM", contact_id=stranger))

    def test_update_lead_rejects_bad_values(self):
        self.assertRejects(lambda **k: update_lead(self.conn, self.lead, **k),
                           dict(brand="Nope"), dict(products=["Wind"]), dict(label="great"),
                           dict(next_action_date="next week"), dict(meeting_type="Carrier pigeon"),
                           dict(appt_at="soon"))


class ListTests(DbTestCase):
    def test_booked_goes_to_winners_and_has_goes_to_losers(self):
        booked = add_lead(self.conn, "Test Booked Co", "Haneco", now=T0)
        log_activity(self.conn, booked, "BKD", now=T0)
        has = add_lead(self.conn, "Test Has LED Co", "JWL", now=T0)
        log_activity(self.conn, has, "HAS", now=T0)
        bad = add_lead(self.conn, "Test Bad Number Co", "JWL", now=T0)
        log_activity(self.conn, bad, "BAD", now=T0)
        leads = load_all(self.conn)
        self.assertEqual(leads[booked]["source"], "winner")
        self.assertEqual(leads[has]["source"], "loser")
        self.assertEqual((leads[bad]["source"], leads[bad]["closed"]), ("new", "BAD"))

        rows = {r["id"]: r for r in list_leads(self.conn, today=date(2027, 1, 1))}
        self.assertEqual(rows[booked]["closed"], "BKD")
        self.assertFalse(rows[booked]["open"] or rows[booked]["due"])
        self.assertEqual(rows[booked]["advice"], ["Winner: meeting booked"])
        self.assertFalse(rows[has]["open"])
        self.assertEqual(rows[has]["advice"], ["Loser: already has a solution"])

    def test_moving_back_to_an_open_list_reopens(self):
        booked = add_lead(self.conn, "Test Booked Co", "Haneco", now=T0)
        log_activity(self.conn, booked, "BKD", now=T0)
        update_lead(self.conn, booked, source="follow-up")
        self.assertIsNone(load_all(self.conn)[booked]["closed"])
        self.assertTrue({r["id"]: r for r in list_leads(self.conn)}[booked]["open"])

    def test_reschedule_only_sets_the_date(self):
        lead = add_lead(self.conn, "Test Reception Co", "Exceledy", now=T0)
        update_lead(self.conn, lead, next_action_date="2026-11-02")
        self.assertEqual(load_all(self.conn)[lead]["next_action_date"], "2026-11-02")
