"""HTTP server: JSON API under /api, static files from web/."""
import json
import sqlite3
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from .activities import log_activity
from .appointment import appointment_text
from .config import (BRANDS, MEETING_TYPES, MODEL_PATH, OUTCOMES, PHONE_TYPES, PORT, PRODUCTS, SOURCES, WEB_DIR)
from .contacts import add_contact, update_contact
from .db import connect
from .features import training_examples
from .leads import add_lead, lead_detail, list_leads, load_all, update_lead
from .sheets import sync_to_sheets
from .settings import caller_name, save_caller_name

# Set explicitly: Windows reads these from the registry, and a wrong .js type stops ES modules loading.
CONTENT_TYPES = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
                 ".js": "text/javascript; charset=utf-8", ".svg": "image/svg+xml", ".ico": "image/x-icon",
                 ".woff2": "font/woff2"}


def load_scorer():
    if not MODEL_PATH.exists():
        return None
    try:
        from . import model
        return model.Scorer.load(MODEL_PATH)
    except ImportError:
        return None


class Handler(BaseHTTPRequestHandler):
    conn = None
    scorer = None
    lock = threading.Lock()  # one shared SQLite connection

    def _send(self, status, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        with self.lock:
            self._route(self._get)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        with self.lock:
            self._route(lambda: self._post(body))

    def _route(self, handler):
        try:
            handler()
        except (ValueError, TypeError, KeyError, sqlite3.IntegrityError) as e:
            self._send(400, {"error": str(e)})
        except Exception as e:  # sync/train failures (no creds, no torch, offline) must not crash the tracker
            self._send(500, {"error": f"{type(e).__name__}: {e}"})

    def _static(self, path):
        root = WEB_DIR.resolve()
        if not (root / "index.html").is_file():
            return self._send(503, {"error": "UI not built. Run: cd web && npm install && npm run build"})
        file = (root / (path.strip("/") or "index.html")).resolve()
        if root not in file.parents or not file.is_file():
            return self._send(404, {"error": "not found"})
        self._send(200, file.read_bytes(), CONTENT_TYPES.get(file.suffix, "application/octet-stream"))

    def _get(self):
        url = urlsplit(self.path)
        parts = url.path.strip("/").split("/")
        if parts[0] != "api":
            return self._static(url.path)
        if parts[:2] == ["api", "leads"] and parts[3:] == ["appointment"]:
            q = {k: v[0] for k, v in parse_qs(url.query).items()}
            lead = lead_detail(self.conn, int(parts[2]))
            contact = next((c for c in lead["contacts"] if str(c["id"]) == q.get("contact_id")), None)
            return self._send(200, {"text": appointment_text(lead, contact, q.get("caller"))})
        if url.path == "/api/config":
            return self._send(200, {"brands": BRANDS, "products": PRODUCTS, "sources": SOURCES, "outcomes": OUTCOMES,
                                    "phone_types": PHONE_TYPES, "meeting_types": MEETING_TYPES,
                                    "model": self.scorer.metrics if self.scorer else None,
                                    "caller_name": caller_name(self.conn)})
        if url.path == "/api/leads":
            return self._send(200, list_leads(self.conn, self.scorer))
        if parts[:2] == ["api", "leads"] and len(parts) == 3:
            return self._send(200, lead_detail(self.conn, int(parts[2])))
        self._send(404, {"error": "not found"})

    def _post(self, body):
        parts = self.path.strip("/").split("/")
        if self.path == "/api/settings/caller":
            save_caller_name(self.conn, body["name"], body.get("revision"))
            return self._send(200, {"ok": True})
        if self.path == "/api/leads":
            return self._send(201, {"id": add_lead(self.conn, **body)})
        if parts[:2] == ["api", "leads"] and len(parts) == 3:
            update_lead(self.conn, int(parts[2]), **body)
            return self._send(200, {"ok": True})
        if parts[:2] == ["api", "leads"] and parts[3:] == ["contacts"]:
            return self._send(201, {"id": add_contact(self.conn, int(parts[2]), **body)})
        if parts[:2] == ["api", "contacts"] and len(parts) == 3:
            update_contact(self.conn, int(parts[2]), **body)
            return self._send(200, {"ok": True})
        if self.path == "/api/activities":
            body.pop("now", None)
            return self._send(201, log_activity(self.conn, **body))
        if self.path == "/api/train":
            try:
                from . import model
            except ImportError:
                raise RuntimeError(f'PyTorch missing for this Python. Run: "{sys.executable}" -m pip install torch')
            Handler.scorer = model.Scorer.train(*training_examples(load_all(self.conn)))
            Handler.scorer.save(MODEL_PATH)
            return self._send(200, Handler.scorer.metrics)
        if self.path == "/api/sync":
            return self._send(200, sync_to_sheets(self.conn))
        self._send(404, {"error": "not found"})

    def log_message(self, *args):
        pass


def make_server(port=PORT):
    """Port 0 picks any free port. Threaded: browsers hold idle preconnect sockets that would block a single thread."""
    Handler.conn = connect()
    Handler.scorer = load_scorer()
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)
