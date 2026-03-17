#!/usr/bin/env python3
"""Local proxy bridge: accepts unauthenticated requests on localhost,
forwards them to an upstream proxy with authentication.

Usage:
    python proxy_bridge.py --upstream http://user:pass@proxy.example.com:3120 --port 18080
"""
import argparse
import base64
import http.server
import select
import socket
import socketserver
import threading
import urllib.parse
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("proxy-bridge")


class ProxyBridge(http.server.BaseHTTPRequestHandler):
    upstream_host: str
    upstream_port: int
    proxy_auth: str | None  # Base64 encoded

    def log_message(self, format, *args):
        logger.debug(format, *args)

    def do_CONNECT(self):
        """Handle HTTPS CONNECT tunnels."""
        try:
            # Connect to upstream proxy
            upstream = socket.create_connection((self.upstream_host, self.upstream_port), timeout=15)

            # Send CONNECT to upstream with auth
            connect_line = f"CONNECT {self.path} HTTP/1.1\r\n"
            connect_line += f"Host: {self.path}\r\n"
            if self.proxy_auth:
                connect_line += f"Proxy-Authorization: Basic {self.proxy_auth}\r\n"
            connect_line += "\r\n"
            upstream.sendall(connect_line.encode())

            # Read upstream response
            response = b""
            while b"\r\n\r\n" not in response:
                chunk = upstream.recv(4096)
                if not chunk:
                    break
                response += chunk

            status_line = response.split(b"\r\n")[0]
            status_code = int(status_line.split(b" ")[1])

            if status_code == 200:
                self.send_response(200, "Connection Established")
                self.end_headers()
                self._tunnel(self.connection, upstream)
            else:
                self.send_error(502, f"Upstream proxy returned {status_code}")
                logger.warning("Upstream CONNECT failed: %s", status_line.decode(errors="replace"))

            upstream.close()
        except Exception as e:
            logger.error("CONNECT error: %s", e)
            try:
                self.send_error(502, str(e))
            except Exception:
                pass

    def do_GET(self):
        self._forward_request()

    def do_POST(self):
        self._forward_request()

    def do_PUT(self):
        self._forward_request()

    def do_DELETE(self):
        self._forward_request()

    def do_HEAD(self):
        self._forward_request()

    def _forward_request(self):
        """Forward HTTP (non-CONNECT) requests through upstream proxy."""
        try:
            upstream = socket.create_connection((self.upstream_host, self.upstream_port), timeout=15)

            # Build request to upstream
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else b""

            request_line = f"{self.command} {self.path} HTTP/1.1\r\n"
            headers = ""
            for key, value in self.headers.items():
                if key.lower() not in ("proxy-authorization",):
                    headers += f"{key}: {value}\r\n"
            if self.proxy_auth:
                headers += f"Proxy-Authorization: Basic {self.proxy_auth}\r\n"
            headers += "\r\n"

            upstream.sendall((request_line + headers).encode() + body)

            # Forward response back
            response = b""
            while True:
                chunk = upstream.recv(65536)
                if not chunk:
                    break
                response += chunk

            self.wfile.write(response)
            upstream.close()
        except Exception as e:
            logger.error("Forward error: %s", e)
            self.send_error(502, str(e))

    @staticmethod
    def _tunnel(client: socket.socket, upstream: socket.socket):
        """Bidirectional tunnel between client and upstream."""
        sockets = [client, upstream]
        timeout = 60
        while True:
            readable, _, errors = select.select(sockets, [], sockets, timeout)
            if errors:
                break
            if not readable:
                break
            for s in readable:
                other = upstream if s is client else client
                try:
                    data = s.recv(65536)
                    if not data:
                        return
                    other.sendall(data)
                except Exception:
                    return


class ThreadedProxy(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    parser = argparse.ArgumentParser(description="Local proxy bridge with auth")
    parser.add_argument("--upstream", required=True, help="Upstream proxy URL (http://user:pass@host:port)")
    parser.add_argument("--port", type=int, default=18080, help="Local listen port")
    args = parser.parse_args()

    parsed = urllib.parse.urlparse(args.upstream)
    upstream_host = parsed.hostname
    upstream_port = parsed.port or 3128

    proxy_auth = None
    if parsed.username:
        creds = f"{parsed.username}:{parsed.password or ''}"
        proxy_auth = base64.b64encode(creds.encode()).decode()

    ProxyBridge.upstream_host = upstream_host
    ProxyBridge.upstream_port = upstream_port
    ProxyBridge.proxy_auth = proxy_auth

    server = ThreadedProxy(("127.0.0.1", args.port), ProxyBridge)
    logger.info("Proxy bridge listening on 127.0.0.1:%d -> %s:%d (auth=%s)",
                args.port, upstream_host, upstream_port, "yes" if proxy_auth else "no")
    server.serve_forever()


if __name__ == "__main__":
    main()
