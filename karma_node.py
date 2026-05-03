from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json, time, hashlib, os, threading, urllib.request

GENESIS = {
    "index": 0,
    "timestamp": "2026-05-03 10:00:00",
    "data": {
        "action": "genesis",
        "supply": 1000000000,
        "architect": {"address": "KARMA_ARCHITECT", "share": 230000000, "vesting": "4 years"},
        "team": 80000000, "investors": 170000000, "public": 120000000, "dao": 400000000
    },
    "previous_hash": "0"*64,
    "hash": ""
}
GENESIS["hash"] = hashlib.sha256(json.dumps(GENESIS, sort_keys=True).encode()).hexdigest()
chain = [GENESIS]
chain_lock = threading.Lock()

def new_block(data):
    with chain_lock:
        prev = chain[-1]
        b = {"index": prev["index"]+1, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
             "data": data, "previous_hash": prev["hash"], "hash": ""}
        b["hash"] = hashlib.sha256(json.dumps(b, sort_keys=True).encode()).hexdigest()
        chain.append(b)
        return b

PEERS = [
    "https://karma-node-2.onrender.com"
]

def sync_from_peers():
    for peer in PEERS:
        try:
            r = urllib.request.urlopen(f"{peer}/api/blocks")
            data = json.loads(r.read())
            for block in data.get("blocks", []):
                if block["index"] >= len(chain):
                    chain.append(block)
        except:
            pass

def auto_miner():
    while True:
        time.sleep(10)
        sync_from_peers()
        new_block({"action": "auto-mine", "reward": 0})

class API(BaseHTTPRequestHandler):
    def _reply(self, data, code=200, ctype="application/json"):
        body = json.dumps(data).encode() if isinstance(data, dict) else data.encode()
        self.send_response(code); self.send_header("Content-type", ctype); self.end_headers(); self.wfile.write(body)
    
    def do_GET(self):
        p = urlparse(self.path).path
        if p == "/api/pulse":
            self._reply({"network":"KARMA Iron Testnet","blocks":len(chain),"status":"online","auto_mining":True})
        elif p == "/api/blocks":
            self._reply({"blocks": chain[-10:]})
        elif p == "/api/genesis":
            self._reply(GENESIS)
        elif p == "/api/manifesto":
            self._reply("KARMA MANIFESTO v1.0\n\nLaw of Digital Being.\n\n23% Architect — locked for 4 years.\n\n1,000,000,000 total supply.\n\nSigned,\nThe Architect\nKratos\nThe KARMA Brotherhood", 200, "text/plain")
        elif p == "/api/balance":
            q = parse_qs(urlparse(self.path).query)
            addr = q.get("address", ["ARCHITECT"])[0]
            bal = 230000000 if addr == "KARMA_ARCHITECT" else 0
            self._reply({"address": addr, "balance": bal})
        else:
            self._reply({"status":"KARMA online","endpoints":["/api/pulse","/api/blocks","/api/genesis","/api/manifesto","/api/balance"]})
    
    def do_POST(self):
        if urlparse(self.path).path == "/api/mine":
            body = self.rfile.read(int(self.headers.get('Content-Length',0))).decode()
            data = json.loads(body) if body else {"tx": "test"}
            self._reply(new_block(data))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=auto_miner, daemon=True).start()
    print(f"KARMA NODE ONLINE — Port {port} | Auto-mining: ON")
    print(f"Genesis: {GENESIS['hash'][:16]}... | Architect: 230M KARMA")
    HTTPServer(("0.0.0.0", port), API).serve_forever()
