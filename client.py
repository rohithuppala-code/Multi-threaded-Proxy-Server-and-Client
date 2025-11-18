#!/usr/bin/env python3
"""
Simple client for the multi-threaded proxy server.
Usage:
    python client.py <proxy_host> <proxy_port> <url>

The client sends the URL followed by newline, reads the 10-byte length header,
the 100-byte content-type header, then reads the body and saves it into a file.
The filename is derived from the URL and content type (defaults to .html).
"""

import socket
import sys
import os
import urllib.parse
from datetime import datetime

LENGTH_HEADER = 10
CTYPE_HEADER = 100
RECV_BUFSIZE = 4096

def safe_filename_from_url(url, ctype):
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.replace(':', '_') or 'page'
    path = parsed.path.rstrip('/')
    if path:
        last = os.path.basename(path)
        base = f"{host}_{last}"
    else:
        base = host
    # if query exists, include a short hash-like or timestamp
    if parsed.query:
        base += "_" + str(abs(hash(parsed.query)))[:8]
    # choose extension from content-type
    ext = ".html" if "html" in ctype.lower() or "text" in ctype.lower() else ""
    if not ext:
        # try to infer from ctype (e.g., text/plain -> .txt)
        if "plain" in ctype.lower():
            ext = ".txt"
        elif "json" in ctype.lower():
            ext = ".json"
        elif "xml" in ctype.lower():
            ext = ".xml"
        elif "javascript" in ctype.lower():
            ext = ".js"
        else:
            ext = ".bin"
    # timestamp to avoid collisions
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{base}_{ts}{ext}"
    # sanitize filename
    filename = "".join(c for c in filename if c.isalnum() or c in "._-")
    return filename

def recv_all(sock, n):
    data = b''
    while len(data) < n:
        chunk = sock.recv(min(n - len(data), RECV_BUFSIZE))
        if not chunk:
            break
        data += chunk
    return data

def fetch_via_proxy(proxy_host, proxy_port, url):
    with socket.create_connection((proxy_host, proxy_port), timeout=30) as s:
        # send URL followed by newline
        s.sendall((url + '\n').encode('utf-8'))

        # read length header
        length_header = recv_all(s, LENGTH_HEADER)
        if len(length_header) < LENGTH_HEADER:
            raise RuntimeError("Incomplete length header received")
        try:
            body_len = int(length_header.decode('ascii'))
        except Exception as e:
            raise RuntimeError("Invalid length header") from e

        # read content-type header
        ctype_raw = recv_all(s, CTYPE_HEADER)
        if len(ctype_raw) < CTYPE_HEADER:
            raise RuntimeError("Incomplete content-type header received")
        ctype = ctype_raw.rstrip(b' ').decode('utf-8', errors='replace')

        # read body
        body = recv_all(s, body_len)
        if len(body) < body_len:
            raise RuntimeError(f"Expected {body_len} bytes, got {len(body)} bytes")

        return body, ctype

def main():
    if len(sys.argv) < 4:
        print("Usage: python client.py <proxy_host> <proxy_port> <url>")
        print("Example: python client.py 127.0.0.1 8888 https://example.com/")
        sys.exit(1)
    proxy_host = sys.argv[1]
    proxy_port = int(sys.argv[2])
    url = sys.argv[3]
    try:
        body, ctype = fetch_via_proxy(proxy_host, proxy_port, url)
    except Exception as e:
        print("Error:", e)
        sys.exit(2)

    filename = safe_filename_from_url(url, ctype)
    with open(filename, 'wb') as f:
        f.write(body)
    print(f"Saved {len(body)} bytes to {filename} (Content-Type: {ctype})")

if __name__ == '__main__':
    main()
