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
    elif p == "/api/swap":
        direction = q.get("direction", [""])[0]
        amount = float(q.get("amount", ["0"])[0])
        if direction == "karma_to_usdc" and amount > 0:
            out, price = swap_karma_for_usdc(amount)
            self._reply({"action": "swap", "in": f"{amount} KARMA", "out": f"{out} USDC", "new_price": f"{price} USDC/KARMA"})
        elif direction == "usdc_to_karma" and amount > 0:
            out, price = swap_usdc_for_karma(amount)
            self._reply({"action": "swap", "in": f"{amount} USDC", "out": f"{out} KARMA", "new_price": f"{price} USDC/KARMA"})
        else:
            self._reply({"error": "use direction=karma_to_usdc or usdc_to_karma and amount>0"}, 400)
    else:
        self._reply({"status":"KARMA online"})
