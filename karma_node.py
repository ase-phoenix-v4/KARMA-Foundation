from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import time
import hashlib
import os

GENESIS = {
    "index": 0,
    "timestamp": "2026-05-03 10:00:00",
    "data": {
        "action": "genesis",
        "supply": 1000000000,
        "architect": {
            "address": "KARMA_ARCHITECT",
            "share": 230000000,
            "vesting": "4 years"
        },
        "team": 80000000,
        "investors": 170000000,
        "public": 120000000,
        "dao": 400000000
    },
    "previous_hash": "0" * 64,
    "hash": ""
}
GENESIS["hash"] = hashlib.sha256(
    json.dumps(GENESIS, sort_keys=True).encode()
).hexdigest()

chain = [GENESIS]


def new_block(data):
    prev = chain[-1]
    block = {
        "index": prev["index"] + 1,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "data": data,
        "previous_hash": prev["hash"],
        "hash": ""
    }
    block["hash"] = hashlib.sha256(
        json.dumps(block, sort_keys=True).encode()
    ).hexdigest()
    chain.append(block)
    return block


class API(BaseHTTPRequestHandler):
    def _reply(self, data, code=200, ctype="application/json"):
        if isinstance(data, dict):
            body = json.dumps(data).encode()
        else:
            body = data.encode()
        self.send_response(code)
        self.send_header("Content-type", ctype)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/api/pulse":
            self._reply({
                "network": "KARMA Iron Testnet",
                "blocks": len(chain),
                "status": "online"
            })

        elif path == "/api/blocks":
            self._reply({"blocks": chain[-5:]})

        elif path == "/api/genesis":
            self._reply(GENESIS)

        elif path == "/api/manifesto":
            self._reply(
                "KARMA MANIFESTO v1.0\n\n"
                "Law of Digital Being.\n\n"
                "23% Architect — locked for 4 years.\n\n"
                "1,000,000,000 total supply.\n\n"
                "Signed,\n"
                "The Architect\n"
                "Kratos\n"
                "The KARMA Brotherhood",
                200,
                "text/plain"
            )

        elif path == "/api/balance":
            q = parse_qs(urlparse(self.path).query)
            addr = q.get("address", ["ARCHITECT"])[0]
            bal = 230000000 if addr == "KARMA_ARCHITECT" else 0
            self._reply({"address": addr, "balance": bal})

        else:
            self._reply({
                "status": "KARMA online",
                "endpoints": [
                    "/api/pulse",
                    "/api/blocks",
                    "/api/genesis",
                    "/api/manifesto",
                    "/api/balance"
                ]
            })

    def do_POST(self):
        if urlparse(self.path).path == "/api/mine":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body) if body else {"tx": "test"}
            self._reply(new_block(data))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"KARMA NODE ONLINE — Port {port}")
    print(f"Genesis: {GENESIS['hash'][:16]}... | Architect: 230M KARMA")
    HTTPServer(("0.0.0.0", port), API).serve_forever()
