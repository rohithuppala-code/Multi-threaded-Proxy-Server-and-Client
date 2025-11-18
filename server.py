#!/usr/bin/env python3
"""
Multi-threaded proxy server.
Protocol (simple):
- Client sends a URL as a UTF-8 string terminated by newline ("\n").
- Server responds with a fixed 10-byte ASCII decimal length header (body length in bytes, zero-padded),
  followed by a fixed 100-byte ASCII Content-Type header (padded with spaces),
  then the raw response body bytes (length matches the 10-byte header).
If an error occurs while fetching, server returns a nonzero length and a short text error message
as the body (Content-Type: text/plain; charset=utf-8).
"""

import socket
import threading
import urllib.request
import urllib.error
import sys

HOST = '0.0.0.0'
PORT = 8888            # change if needed
LENGTH_HEADER = 10     # bytes for length
CTYPE_HEADER = 100     # bytes for content-type header
RECV_BUFSIZE = 4096

def fetch_url(url, timeout=15):
    req = urllib.request.Request(url, headers={'User-Agent': 'MiniProxy/1.0'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read()
        ctype = resp.getheader('Content-Type') or 'application/octet-stream'
        return body, ctype

def handle_client(conn, addr):
    try:
        conn.settimeout(30)
        # read until newline
        data = b''
        while b'\n' not in data:
            chunk = conn.recv(RECV_BUFSIZE)
            if not chunk:
                # connection closed before newline
                print(f"[{addr}] connection closed early")
                return
            data += chunk
            if len(data) > 8192:
                # too long input
                break
        url_line = data.split(b'\n', 1)[0].strip()
        try:
            url = url_line.decode('utf-8')
        except UnicodeDecodeError:
            send_error(conn, "Invalid URL encoding; expected UTF-8.")
            return
        if not url:
            send_error(conn, "No URL received.")
            return

        print(f"[{addr}] Fetching URL: {url}")

        try:
            body, ctype = fetch_url(url)
        except urllib.error.HTTPError as e:
            msg = f"HTTP error {e.code}: {getattr(e, 'reason', '')}"
            print(f"[{addr}] {msg}")
            send_error(conn, msg)
            return
        except urllib.error.URLError as e:
            msg = f"URL error: {e.reason}"
            print(f"[{addr}] {msg}")
            send_error(conn, msg)
            return
        except Exception as e:
            msg = f"Fetch failed: {e}"
            print(f"[{addr}] {msg}")
            send_error(conn, msg)
            return

        # prepare headers
        body_len = len(body)
        length_header = f"{body_len:0{LENGTH_HEADER}d}".encode('ascii')
        # content type padded/truncated to CTYPE_HEADER
        ctype_enc = str(ctype).encode('utf-8')
        if len(ctype_enc) > CTYPE_HEADER:
            ctype_enc = ctype_enc[:CTYPE_HEADER]
        ctype_enc = ctype_enc.ljust(CTYPE_HEADER, b' ')

        # send headers then body
        conn.sendall(length_header + ctype_enc)
        # send body in chunks to avoid huge memory spikes (body already in memory from fetch)
        offset = 0
        while offset < body_len:
            sent = conn.send(body[offset:offset+RECV_BUFSIZE])
            if sent == 0:
                raise RuntimeError("socket connection broken during send")
            offset += sent

        print(f"[{addr}] Sent {body_len} bytes, Content-Type: {ctype}")
    except socket.timeout:
        print(f"[{addr}] connection timed out.")
    except Exception as e:
        print(f"[{addr}] error: {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass

def send_error(conn, message):
    body = message.encode('utf-8')
    ctype = 'text/plain; charset=utf-8'
    body_len = len(body)
    length_header = f"{body_len:0{LENGTH_HEADER}d}".encode('ascii')
    ctype_enc = ctype.encode('utf-8').ljust(CTYPE_HEADER, b' ')
    try:
        conn.sendall(length_header + ctype_enc + body)
    except Exception:
        pass

def serve_forever(host=HOST, port=PORT):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(100)
    print(f"Proxy server listening on {host}:{port}")
    try:
        while True:
            conn, addr = sock.accept()
            print(f"Connection from {addr}")
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        sock.close()

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        PORT = int(sys.argv[1])
    serve_forever(HOST, PORT)
