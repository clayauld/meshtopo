import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Type
from urllib.parse import parse_qs, urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RECEIVED_REPORTS = []


class MockHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path.endswith("/position/report"):
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8"))
                logger.info(f"Received report: {data}")
                RECEIVED_REPORTS.append(data)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid JSON")
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self) -> None:
        if self.path == "/reports":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(RECEIVED_REPORTS).encode("utf-8"))
        elif self.path == "/clear":
            RECEIVED_REPORTS.clear()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Cleared")
        elif "/api/v1/position/report" in self.path:
            # Parse query params
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)

            # Convert to dict where values are single items if possible
            report_data = {k: v[0] if len(v) == 1 else v for k, v in params.items()}
            logger.info(f"Received report via GET: {report_data}")

            RECEIVED_REPORTS.append(report_data)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()


def run(
    server_class: Type[HTTPServer] = HTTPServer,
    handler_class: Type[BaseHTTPRequestHandler] = MockHandler,
    port: int = 8080,
) -> None:
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    logger.info(f"Starting mock server on port {port}...")
    httpd.serve_forever()


if __name__ == "__main__":
    run()
