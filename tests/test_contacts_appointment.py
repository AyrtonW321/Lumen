from lumen.appointment import appointment_text
from lumen.contacts import add_contact, update_contact
from lumen.leads import add_lead, lead_detail, update_lead
from tests.base import T0, DbTestCase


class ContactAndAppointmentTests(DbTestCase):
    def setUp(self):
        super().setUp()
        self.lead = add_lead(self.conn, "Test Reception Co", "Exceledy", now=T0)
        self.cid = add_contact(self.conn, self.lead, "John Doe", "Facility Manager", phone="123-245-2451",
                               ext="204", phone_type="direct", email="john.doe@example.com")

    def john(self):
        return next(c for c in lead_detail(self.conn, self.lead)["contacts"] if c["id"] == self.cid)

    def test_update_contact_rejects_bad_values(self):
        self.assertRejects(lambda **k: update_contact(self.conn, self.cid, **k),
                           dict(phone_type="pager"), dict(name=""), dict(colour="red"))

    def test_full_appointment_text(self):
        update_lead(self.conn, self.lead, address="123 Good Street", facility_size="40,000 sq ft",
                    meeting_type="Online", solar_reference="None", lighting_reference="Fluorescent",
                    appt_at="2026-10-27T10:00", phone="905-555-0000")
        text = appointment_text(lead_detail(self.conn, self.lead), self.john(), "Ayrton")
        self.assertEqual(text, """Name: John Doe
Title: Facility Manager
Address: 123 Good Street
Facility Size: 40,000 sq ft
Phone number: 123-245-2451 ext 204 (D)
Email: john.doe@example.com
Meeting Type: Online
Solar Reference: None
Lighting Reference: Fluorescent
Appt made by Ayrton for Tue Oct 27, 2026 at 10:00 AM""")

    def test_empty_lines_are_left_out(self):
        update_lead(self.conn, self.lead, address="", facility_size=None)
        sparse = appointment_text(lead_detail(self.conn, self.lead), {**self.john(), "email": None}, None)
        for key in ("Address:", "Email:", "Facility Size:", " by "):
            self.assertNotIn(key, sparse)

    def test_main_phone_counts_as_business(self):
        update_lead(self.conn, self.lead, phone="905-555-0000")
        self.assertIn("Phone number: 905-555-0000 (B)", appointment_text(lead_detail(self.conn, self.lead)))

    def test_contact_classification_and_order_persist(self):
        other = add_contact(self.conn, self.lead, "Sam", status="voicemail")
        update_contact(self.conn, self.cid, sort_order=2, status="decision-maker")
        update_contact(self.conn, other, sort_order=1)
        contacts = lead_detail(self.conn, self.lead)["contacts"]
        self.assertEqual([c["id"] for c in contacts], [other, self.cid])
        self.assertEqual(contacts[0]["status"], "voicemail")
        self.assertEqual(contacts[1]["status"], "decision-maker")
        with self.assertRaises(ValueError):
            update_contact(self.conn, self.cid, status="unknown")
