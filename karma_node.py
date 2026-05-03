from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json, time, hashlib, os, threading, random, string, math

# --- 1. БЛОКЧЕЙН ---
GENESIS = {
    "index": 0, "timestamp": "2026-05-03 10:00:00",
    "data": {"action": "genesis", "supply": 1000000000, "architect": {"address": "KARMA_ARCHITECT", "share": 230000000}},
    "previous_hash": "0"*64, "hash": ""
}
GENESIS["hash"] = hashlib.sha256(json.dumps(GENESIS, sort_keys=True).encode()).hexdigest()
chain = [GENESIS]
chain_lock = threading.Lock()

balances = {"KARMA_ARCHITECT": 230000000}

# --- 2. AMM ПУЛ ЛИКВИДНОСТИ ---
# Начальные резервы: 1,000,000 KARMA и 1,000 USDC
pool = {
    "karma": 1_000_000.0,
    "usdc": 1_000.0,
    "k": 1_000_000.0 * 1_000.0,  # constant product
    "fee_percent": 0.3  # комиссия пула 0.3%
}

def swap_karma_for_usdc(amount_karma_in):
    """Обменять KARMA на USDC. Возвращает (usdc_out, новая_цена)"""
    fee = amount_karma_in * pool["fee_percent"] / 100
    karma_in_after_fee = amount_karma_in - fee
    usdc_out = pool["usdc"] - (pool["k"] / (pool["karma"] + karma_in_after_fee))
    pool["karma"] += amount_karma_in
    pool["usdc"] -= usdc_out
    pool["k"] = pool["karma"] * pool["usdc"]
    price = pool["usdc"] / pool["karma"]
    return round(usdc_out, 6), round(price, 6)

def swap_usdc_for_karma(amount_usdc_in):
    """Обменять USDC на KARMA. Возвращает (karma_out, новая_цена)"""
    fee = amount_usdc_in * pool["fee_percent"] / 100
    usdc_in_after_fee = amount_usdc_in - fee
    karma_out = pool["karma"] - (pool["k"] / (pool["usdc"] + usdc_in_after_fee))
    pool["usdc"] += amount_usdc_in
    pool["karma"] -= karma_out
    pool["k"] = pool["karma"] * pool["usdc"]
    price = pool["usdc"] / pool["karma"]
    return round(karma_out, 6), round(price, 6)

def new_block(data):
    with chain_lock:
        prev = chain[-1]
        b = {"index": prev["index"]+1, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
             "data": data, "previous_hash": prev["hash"], "hash": ""}
        b["hash"] = hashlib.sha256(json.dumps(b, sort_keys=True).encode()).hexdigest()
        chain.append(b)
        return b

# --- 3. API ---
class API(BaseHTTPRequestHandler):
    def _reply(self, data, code=200, ctype="application/json"):
        body = json.dumps(data).encode() if isinstance(data, dict) else data.encode()
        self.send_response(code); self.send_header("Content-type", ctype); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        p = urlparse(self.path).path
        q = parse_qs(urlparse(self.path).query)
        if p == "/api/pulse":
            self._reply({"network":"KARMA Iron Testnet","blocks":len(chain),"status":"online"})
        elif p == "/api/blocks":
            self._reply({"blocks": chain[-10:]})
        elif p == "/api/genesis":
            self._reply(GENESIS)
        elif p == "/api/manifesto":
            self._reply("KARMA MANIFESTO v1.0 – The Law of Digital Being. 23% Architect locked.", 200, "text/plain")
        elif p == "/api/balance":
            addr = q.get("address", ["KARMA_ARCHITECT"])[0]
            self._reply({"address": addr, "balance": balances.get(addr, 0)})
        elif p == "/api/pool":
            self._reply({
                "pool": "KARMA/USDC",
                "karma_reserve": pool["karma"],
                "usdc_reserve": pool["usdc"],
                "constant_k": round(pool["k"], 2),
                "price_karma_per_usdc": round(pool["usdc"] / pool["karma"], 6),
                "fee_percent": pool["fee_percent"]
            })
        else:
            self._reply({"status":"KARMA online"})

    def do_POST(self):
        p = urlparse(self.path).path
        body = self.rfile.read(int(self.headers.get('Content-Length',0))).decode()
        data = json.loads(body) if body else {}
        if p == "/api/mine":
            self._reply(new_block(data))
        elif p == "/api/swap":
            direction = data.get("direction")
            amount = float(data.get("amount", 0))
            if direction == "karma_to_usdc":
                out, price = swap_karma_for_usdc(amount)
                self._reply({"action": "swap", "in": f"{amount} KARMA", "out": f"{out} USDC", "new_price": f"{price} USDC/KARMA"})
            elif direction == "usdc_to_karma":
                out, price = swap_usdc_for_karma(amount)
                self._reply({"action": "swap", "in": f"{amount} USDC", "out": f"{out} KARMA", "new_price": f"{price} USDC/KARMA"})
            else:
                self._reply({"error": "use direction: karma_to_usdc or usdc_to_karma"}, 400)

def auto_miner():
    while True:
        time.sleep(10)
        new_block({"action": "auto-mine"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=auto_miner, daemon=True).start()
    print(f"KARMA NODE + AMM POOL – Port {port} | Pool: 1M KARMA / 1K USDC")
    HTTPServer(("0.0.0.0", port), API).serve_forever()
