from lumen.contacts import add_contact
from lumen.leads import add_lead, lead_detail, list_leads, update_lead
from lumen.traits import add_trait
from tests.base import T0, DbTestCase


class MainContactTests(DbTestCase):
    def setUp(self):
        super().setUp()
        self.lead = add_lead(self.conn, "Test Main Co", "Haneco", now=T0)

    def main(self):
        return list_leads(self.conn, today=T0.date())[0]["main_contact"]

    def test_no_contacts_means_no_main_contact(self):
        self.assertIsNone(self.main())

    def test_default_skips_reception_and_prefers_decision_maker(self):
        add_contact(self.conn, self.lead, "Rita Test", title="Reception", status="reception", now=T0)
        bob = add_contact(self.conn, self.lead, "Bob Test", title="Ops", now=T0)
        self.assertEqual(self.main()["id"], bob)
        dana = add_contact(self.conn, self.lead, "Dana Test", title="Owner", now=T0)
        add_trait(self.conn, self.lead, "Decision-maker", dana)
        self.assertEqual(self.main(), {"id": dana, "name": "Dana Test", "title": "Owner", "pinned": False})

    def test_pin_wins_and_can_be_cleared(self):
        add_contact(self.conn, self.lead, "Dana Test", status="decision-maker", now=T0)
        bob = add_contact(self.conn, self.lead, "Bob Test", now=T0)
        update_lead(self.conn, self.lead, main_contact_id=bob)
        self.assertEqual((self.main()["id"], self.main()["pinned"]), (bob, True))
        self.assertTrue(lead_detail(self.conn, self.lead)["main_contact"]["pinned"])
        update_lead(self.conn, self.lead, main_contact_id=None)
        self.assertEqual(self.main()["name"], "Dana Test")

    def test_cannot_pin_another_leads_contact(self):
        other = add_lead(self.conn, "Test Other Co", "JWL", now=T0)
        stranger = add_contact(self.conn, other, "Sam Test", now=T0)
        with self.assertRaises(ValueError):
            update_lead(self.conn, self.lead, main_contact_id=stranger)
