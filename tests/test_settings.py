import tempfile
import unittest
from pathlib import Path

from lumen.db import connect
from lumen.settings import caller_name, save_caller_name


class CallerSettingsTests(unittest.TestCase):
    def test_name_survives_database_reopen_and_can_be_cleared(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.db"
            conn = connect(path)
            self.assertIsNone(caller_name(conn))
            save_caller_name(conn, "Alex Morgan", revision=10)
            conn.close()
            conn = connect(path)
            try:
                self.assertEqual(caller_name(conn), "Alex Morgan")
                save_caller_name(conn, "Old input", revision=9)
                self.assertEqual(caller_name(conn), "Alex Morgan")
                save_caller_name(conn, "", revision=11)
                self.assertEqual(caller_name(conn), "")
            finally:
                conn.close()
