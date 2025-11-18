# Multi-threaded Proxy Server

A simple HTTP proxy server with a custom binary protocol implementation in Python.

## Overview

This project implements a multi-threaded proxy server that fetches web content on behalf of clients using a custom fixed-format binary protocol.

## Files

- `server.py` - Multi-threaded proxy server
- `client.py` - Client application to fetch URLs through the proxy

## Requirements

- Python 3.6+
- No external dependencies

## Installation

```bash
git clone <repository-url>
cd <repository-name>
```

## Usage

**Start the server:**

```bash
python3 server.py
```

**Fetch a URL through the proxy:**

```bash
python3 client.py 127.0.0.1 8888 https://example.com/
```

## Protocol

The proxy uses a simple binary protocol:

1. Client sends UTF-8 URL terminated by `\n`
2. Server responds with:
   - 10-byte length header (zero-padded decimal)
   - 100-byte Content-Type header (space-padded)
   - Response body bytes

## Features

- Multi-threaded connection handling
- Custom binary protocol
- Automatic file naming
- Error handling for HTTP errors and timeouts

## Configuration

Default server settings:
- Host: `0.0.0.0`
- Port: `8888`
- Timeout: 15 seconds

To use a different port:

```bash
python3 proxy_server.py 9000
```

## Example

```bash
# Terminal 1
$ python3 proxy_server.py
Proxy server listening on 0.0.0.0:8888

# Terminal 2
$ python3 client.py 127.0.0.1 8888 https://example.com/
Saved 1256 bytes to example.com_20241118_143052.html
```