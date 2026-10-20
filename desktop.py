"""Lumen in its own desktop window. Run: py -3.12 desktop.py   (needs: py -3.12 -m pip install pywebview)

Starts the same local server on a free port and shows it in a native window (Windows' built-in Edge engine).
Closing the window stops Lumen. Same data as the browser version: data/lumen.db.
"""
import os
import threading

import webview

import lumen

server = lumen.make_server(port=0)
threading.Thread(target=server.serve_forever, daemon=True).start()

webview.create_window("Lumen", f"http://127.0.0.1:{server.server_port}", width=1400, height=900,
                      min_size=(900, 600), text_select=True)
# private_mode=False keeps the caller name and last tab between runs.
# Profile lives in %LOCALAPPDATA%, not OneDrive: OneDrive locks WebView2's files and the window fails to open.
webview.start(private_mode=False, storage_path=os.path.join(os.environ["LOCALAPPDATA"], "Lumen", "webview"))
server.shutdown()
