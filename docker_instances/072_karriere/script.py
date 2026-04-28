"""Schlanker Einstiegspunkt zum Starten des lokalen HTTP-Servers."""

import os
from http.server import ThreadingHTTPServer

from config import DEFAULT_HOST, DEFAULT_PORT
from request_handler import JobRequestHandler


def run_server() -> None:
    """Startet den Threading-HTTP-Server mit konfigurierbarem Host und Port."""
    host = os.getenv("HOST", DEFAULT_HOST)
    port = int(os.getenv("PORT", str(DEFAULT_PORT)))
    server = ThreadingHTTPServer((host, port), JobRequestHandler)
    print(f"Serving on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
