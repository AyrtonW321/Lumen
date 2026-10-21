import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

from lumen import server
from lumen.db import connect


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Fake built UI, so tests do not need npm.
        cls.tmp = Path(tempfile.mkdtemp())
        web = cls.tmp / "dist"
        (web / "assets").mkdir(parents=True)
        (web / "index.html").write_text("<!doctype html>")
        (web / "assets" / "app.css").write_text("a{}")
        (web / "assets" / "app.js").write_text("1")
        (cls.tmp / "secret.txt").write_text("secret")
        web_patch = mock.patch.object(server, "WEB_DIR", web)
        web_patch.start()
        cls.addClassCleanup(web_patch.stop)
        with mock.patch.object(server, "connect", lambda: connect(":memory:")), \
                mock.patch.object(server, "load_scorer", lambda: None):
            cls.httpd = server.make_server(port=0)
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.httpd.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def get(self, path):
        with urllib.request.urlopen(self.base + path) as r:
            return r.status, r.headers["Content-Type"], r.read()

    def test_serves_page_css_and_js_with_right_types(self):
        self.assertIn("text/html", self.get("/")[1])
        self.assertIn("text/css", self.get("/assets/app.css")[1])
        self.assertIn("text/javascript", self.get("/assets/app.js")[1])

    def test_caller_setting_is_returned_in_config(self):
        req = urllib.request.Request(self.base + "/api/settings/caller", method="POST",
                                     data=json.dumps({"name": "Test Caller", "revision": 1}).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as response:
            self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(self.get("/api/config")[2])["caller_name"], "Test Caller")

    def test_static_route_blocks_path_traversal(self):
        for path in ("/../secret.txt", "/..%2Fsecret.txt", "/assets/../../secret.txt"):
            with self.subTest(path=path), self.assertRaises(urllib.error.HTTPError) as ctx:
                self.get(path)
            self.assertEqual(ctx.exception.code, 404)

    def test_missing_build_says_how_to_build(self):
        with mock.patch.object(server, "WEB_DIR", self.tmp / "nope"), self.assertRaises(urllib.error.HTTPError) as ctx:
            self.get("/")
        self.assertEqual(ctx.exception.code, 503)
        self.assertIn("npm run build", json.loads(ctx.exception.read())["error"])

    def test_config_and_create_lead(self):
        cfg = json.loads(self.get("/api/config")[2])
        self.assertIn("Haneco", cfg["brands"])
        req = urllib.request.Request(self.base + "/api/leads", method="POST",
                                     data=json.dumps({"name": "Test Co", "brand": "Haneco"}).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as r:
            self.assertEqual(r.status, 201)
        names = [row["name"] for row in json.loads(self.get("/api/leads")[2])]
        self.assertEqual(names, ["Test Co"])


if __name__ == "__main__":
    unittest.main()
