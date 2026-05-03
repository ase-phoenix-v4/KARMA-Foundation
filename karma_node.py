from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json, time, hashlib, os, threading, socket, struct

# --- GENESIS ---
GENESIS = {
    "index": 0, "timestamp": "2026-05-03 10:00:00",
    "data": {"action": "genesis", "supply": 1000000000, "architect": {"address": "KARMA_ARCHITECT", "share": 230000000}},
    "previous_hash": "0"*64, "hash": ""
}
GENESIS["hash"] = hashlib.sha256(json.dumps(GENESIS, sort_keys=True).encode()).hexdigest()
chain = [GENESIS]
chain_lock = threading.Lock()
balances = {"KARMA_ARCHITECT": 230000000}

pool_usdc = {"karma": 1000000.0, "token": 1000.0, "k": 1000000.0*1000.0, "fee_percent": 0.3}
pool_pol = {"karma": 2000000.0, "token": 5000.0, "k": 2000000.0*5000.0, "fee_percent": 0.3}

def swap_karma_for_token(pool, amount_in):
    fee = amount_in * pool["fee_percent"] / 100
    net = amount_in - fee
    out = pool["token"] - (pool["k"] / (pool["karma"] + net))
    pool["karma"] += amount_in
    pool["token"] -= out
    pool["k"] = pool["karma"] * pool["token"]
    return round(out, 6), round(pool["token"] / pool["karma"], 6)

def swap_token_for_karma(pool, amount_in):
    fee = amount_in * pool["fee_percent"] / 100
    net = amount_in - fee
    out = pool["karma"] - (pool["k"] / (pool["token"] + net))
    pool["token"] += amount_in
    pool["karma"] -= out
    pool["k"] = pool["karma"] * pool["token"]
    return round(out, 6), round(pool["token"] / pool["karma"], 6)

def new_block(data):
    with chain_lock:
        prev = chain[-1]
        b = {"index": prev["index"]+1, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
             "data": data, "previous_hash": prev["hash"], "hash": ""}
        b["hash"] = hashlib.sha256(json.dumps(b, sort_keys=True).encode()).hexdigest()
        chain.append(b)
        return b

# --- HTTP API ---
class API(BaseHTTPRequestHandler):
    def _reply(self, data, code=200, ctype="application/json"):
        body = json.dumps(data).encode() if isinstance(data, dict) else data.encode()
        self.send_response(code); self.send_header("Content-type", ctype); self.send_header("Access-Control-Allow-Origin", "*"); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        p = urlparse(self.path).path; q = parse_qs(urlparse(self.path).query)
        if p == "/api/pulse": self._reply({"network":"KARMA Iron Testnet","blocks":len(chain),"status":"online"})
        elif p == "/api/pool": self._reply({"pool":"KARMA/USDC","karma":pool_usdc["karma"],"usdc":pool_usdc["token"],"price":round(pool_usdc["token"]/pool_usdc["karma"],6)})
        elif p == "/api/pool/pol": self._reply({"pool":"KARMA/POL","karma":pool_pol["karma"],"pol":pool_pol["token"],"price":round(pool_pol["token"]/pool_pol["karma"],6)})
        elif p == "/api/swap":
            d = q.get("direction",[""])[0]; a = float(q.get("amount",["0"])[0])
            if d == "karma_to_usdc" and a > 0: out, price = swap_karma_for_token(pool_usdc, a); self._reply({"swap":f"{a} KARMA -> {out} USDC","new_price":price})
            elif d == "usdc_to_karma" and a > 0: out, price = swap_token_for_karma(pool_usdc, a); self._reply({"swap":f"{a} USDC -> {out} KARMA","new_price":price})
            else: self._reply({"error":"direction?"}, 400)
        elif p == "/api/swap/pol":
            d = q.get("direction",[""])[0]; a = float(q.get("amount",["0"])[0])
            if d == "karma_to_pol" and a > 0: out, price = swap_karma_for_token(pool_pol, a); self._reply({"swap":f"{a} KARMA -> {out} POL","new_price":price})
            elif d == "pol_to_karma" and a > 0: out, price = swap_token_for_karma(pool_pol, a); self._reply({"swap":f"{a} POL -> {out} KARMA","new_price":price})
            else: self._reply({"error":"direction?"}, 400)
        elif p == "/api/last_block":
            self._reply(chain[-1])
        else: self._reply({"status":"KARMA online"})

def auto_miner():
    while True:
        time.sleep(10)
        new_block({"action":"auto-mine"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=auto_miner, daemon=True).start()
    print(f"KARMA NODE – Port {port}")
    HTTPServer(("0.0.0.0", port), API).serve_forever()
