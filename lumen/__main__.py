"""Run:  python -m lumen   then open http://127.0.0.1:8765"""
from .config import DB_PATH, PORT
from .server import make_server

server = make_server()
print(f"Lumen running at http://127.0.0.1:{PORT}  (data: {DB_PATH})")
server.serve_forever()
