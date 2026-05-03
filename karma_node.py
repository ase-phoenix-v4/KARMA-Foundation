from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json, time, hashlib, os, threading, urllib.request, random, string

# --- 1. БЛОКЧЕЙН ---
GENESIS = {
    "index": 0, "timestamp": "2026-05-03 10:00:00",
    "data": {"action": "genesis", "supply": 1000000000, "architect": {"address": "KARMA_ARCHITECT", "share": 230000000}},
    "previous_hash": "0"*64, "hash": ""
}
GENESIS["hash"] = hashlib.sha256(json.dumps(GENESIS, sort_keys=True).encode()).hexdigest()
chain = [GENESIS]
chain_lock = threading.Lock()

# Состояния смарт-контрактов
balances = {"KARMA_ARCHITECT": 230000000}
vesting_contracts = {}
conditional_payments = {}

def execute_smart_contract(tx):
    t = tx.get("type")
    if t == "transfer":
        f, to, amt = tx["from"], tx["to"], int(tx["amount"])
        if balances.get(f, 0) >= amt:
            balances[f] -= amt
            balances[to] = balances.get(to, 0) + amt
            return {"status": "executed", "from": f, "to": to, "amount": amt}
        return {"status": "failed", "reason": "insufficient funds"}
    elif t == "vesting":
        cid = tx["contract_id"]
        vesting_contracts[cid] = {"beneficiary": tx["beneficiary"], "total": int(tx["amount"]), "start": time.time(), "duration": int(tx["duration_sec"])}
        return {"status": "vesting_created", "contract_id": cid}
    elif t == "conditional":
        cid = tx["contract_id"]
        conditional_payments[cid] = {"from": tx["from"], "to": tx["to"], "amount": int(tx["amount"]), "condition": tx["condition"]}
        return {"status": "conditional_created", "contract_id": cid}
    return {"status": "unknown_type"}

def process_pending_contracts():
    now = time.time()
    for cid, c in list(vesting_contracts.items()):
        if now - c["start"] >= c["duration"]:
            if balances.get("KARMA_ARCHITECT", 0) >= c["total"]:
                balances["KARMA_ARCHITECT"] -= c["total"]
                balances[c["beneficiary"]] = balances.get(c["beneficiary"], 0) + c["total"]
            del vesting_contracts[cid]

def new_block(data):
    with chain_lock:
        execute_smart_contract(data)
        process_pending_contracts()
        prev = chain[-1]
        b = {"index": prev["index"]+1, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
             "data": data, "previous_hash": prev["hash"], "hash": ""}
        b["hash"] = hashlib.sha256(json.dumps(b, sort_keys=True).encode()).hexdigest()
        chain.append(b)
        return b

# --- 2. СТРЕСС-ТЕСТ ---
stress_running = False
def stress_test(duration=30, rate=20):
    global stress_running
    stress_running = True
    start = time.time()
    count = 0
    while time.time() - start < duration:
        tx = {"type": "transfer", "from": "KARMA_ARCHITECT", "to": "".join(random.choices(string.ascii_uppercase, k=8)), "amount": str(random.randint(1, 100))}
        new_block(tx)
        count += 1
        time.sleep(1.0 / rate)
    stress_running = False
    return count

# --- 3. API ---
class API(BaseHTTPRequestHandler):
    def _reply(self, data, code=200, ctype="application/json"):
        body = json.dumps(data).encode() if isinstance(data, dict) else data.encode()
        self.send_response(code); self.send_header("Content-type", ctype); self.end_headers(); self.wfile.write(body)
    
    def do_GET(self):
        p = urlparse(self.path).path
        q = parse_qs(urlparse(self.path).query)
        if p == "/api/pulse":
            self._reply({"network":"KARMA Iron Testnet","blocks":len(chain),"status":"online", "stress_test_running": stress_running})
        elif p == "/api/blocks": self._reply({"blocks": chain[-20:]})
        elif p == "/api/genesis": self._reply(GENESIS)
        elif p == "/api/manifesto": self._reply("KARMA MANIFESTO v1.0 – The Law of Digital Being. 23% Architect locked.", 200, "text/plain")
        elif p == "/api/balance":
            addr = q.get("address", ["KARMA_ARCHITECT"])[0]
            self._reply({"address": addr, "balance": balances.get(addr, 0)})
        elif p == "/api/stress_start":
            threading.Thread(target=stress_test, daemon=True).start()
            self._reply({"status": "stress test started", "duration_sec": 30})
        else: self._reply({"status":"KARMA online"})
    
    def do_POST(self):
        if urlparse(self.path).path == "/api/mine":
            body = self.rfile.read(int(self.headers.get('Content-Length',0))).decode()
            self._reply(new_block(json.loads(body) if body else {"tx":"test"}))

# --- 4. СЕТЕВОЙ СЛОЙ ---
PEERS = ["https://karma-node2.onrender.com", "https://karma-node-3.onrender.com"]
def sync_from_peers():
    for peer in PEERS:
        try:
            r = urllib.request.urlopen(f"{peer}/api/blocks")
            for block in json.loads(r.read()).get("blocks", []):
                if block["index"] >= len(chain): chain.append(block)
        except: pass

def auto_miner():
    while True:
        time.sleep(10)
        sync_from_peers()
        new_block({"action": "auto-mine"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=auto_miner, daemon=True).start()
    print(f"KARMA NODE – Port {port} | SC Engine: ON | Stress Test: READY")
    HTTPServer(("0.0.0.0", port), API).serve_forever()
