"""Shared test setup. All data is synthetic."""
import unittest
from datetime import datetime

from lumen.db import connect

T0 = datetime(2026, 10, 19, 9, 30)  # Monday


class DbTestCase(unittest.TestCase):
    def setUp(self):
        self.conn = connect(":memory:")
        self.addCleanup(self.conn.close)

    def assertRejects(self, fn, *cases):
        for kwargs in cases:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                fn(**kwargs)
