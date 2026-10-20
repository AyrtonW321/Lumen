import random
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from lumen.activities import log_activity
from lumen.config import BRANDS
from lumen.contacts import add_contact
from lumen.features import features, training_examples
from lumen.leads import add_lead, list_leads, load_all, update_lead
from tests.base import T0, DbTestCase


class TrainingExampleTests(DbTestCase):
    def test_winners_count_as_good_examples(self):
        booked = add_lead(self.conn, "Test Booked Co", "Haneco", now=T0)
        log_activity(self.conn, booked, "BKD", now=T0)
        X, y, w, ids = training_examples({booked: load_all(self.conn)[booked]})
        self.assertEqual((y[-1], w[-1]), (1.0, 3.0))

    def test_features_never_see_the_call_they_predict(self):
        busy = add_lead(self.conn, "Test Busy Plant", "JWL", source="follow-up", now=T0)
        amy = add_contact(self.conn, busy, "Amy Test", "Facilities Director", now=T0)
        log_activity(self.conn, busy, "BUSY", contact_id=amy, now=T0)
        X, y, w, ids = training_examples({busy: load_all(self.conn)[busy]})
        self.assertEqual(y, [1.0])
        self.assertEqual((X[0]["positive_signals"], X[0]["never_contacted"]), (0, 1))


class ScorerTests(DbTestCase):
    def setUp(self):
        super().setUp()
        try:
            from lumen import model
        except ImportError:
            self.skipTest("torch not installed")
        self.model = model
        random.seed(1)
        # Synthetic world: decision-makers who get reached say yes; voicemail streaks don't.
        self.good_ids, self.poor_ids = [], []
        for i in range(60):
            lid = add_lead(self.conn, f"Synth {i}", random.choice(list(BRANDS)), now=T0)
            good = i % 2 == 0
            cid = add_contact(self.conn, lid, f"Person {i}", "Facilities Manager" if good else "Clerk", now=T0)
            for d in range(4):
                outcome = random.choice(["BUSY", "EREQ", "RCP"]) if good else "VM"
                log_activity(self.conn, lid, outcome, contact_id=cid, now=T0 + timedelta(days=d, hours=1))
            (self.good_ids if good else self.poor_ids).append(lid)

    def test_model_beats_baseline_ranks_good_above_poor_and_explains(self):
        scorer = self.model.Scorer.train(*training_examples(load_all(self.conn)))
        self.assertTrue(scorer.metrics["beats_baseline"], scorer.metrics)
        rows = {r["id"]: r for r in list_leads(self.conn, scorer, today=date(2026, 10, 23))}
        self.assertGreater(rows[self.good_ids[0]]["score"], rows[self.poor_ids[0]]["score"])
        self.assertTrue(rows[self.poor_ids[0]]["why"], "logistic model should explain its score")

    def test_closed_leads_get_no_score(self):
        booked = add_lead(self.conn, "Test Booked Co", "Haneco", now=T0)
        log_activity(self.conn, booked, "BKD", now=T0)
        scorer = self.model.Scorer.train(*training_examples(load_all(self.conn)))
        self.assertNotIn("score", {r["id"]: r for r in list_leads(self.conn, scorer)}[booked])

    def test_save_and_load_round_trip(self):
        scorer = self.model.Scorer.train(*training_examples(load_all(self.conn)))
        path = Path(tempfile.mkdtemp()) / "m.pt"
        scorer.save(path)
        lead = load_all(self.conn)[self.poor_ids[0]]
        row = features(lead, [], [], T0)
        self.assertEqual(self.model.Scorer.load(path).predict([row]), scorer.predict([row]))


if __name__ == "__main__":
    unittest.main()
