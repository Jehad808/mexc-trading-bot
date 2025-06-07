import hmac, hashlib, time, requests, logging

class MEXC:
    def __init__(self, api_key, api_secret):
        self.key = api_key
        self.secret = api_secret
        self.base = "https://contract.mexc.com"

    def _sign(self, params):
        query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return hmac.new(self.secret.encode(), query.encode(), hashlib.sha256).hexdigest()

    def _request(self, path, method="GET", params=None):
        if params is None:
            params = {}
        params.update({"api_key": self.key, "req_time": int(time.time() * 1000)})
        params["sign"] = self._sign(params)
        if method == "GET":
            return requests.get(self.base + path, params=params).json()
        else:
            return requests.post(self.base + path, data=params).json()

    def get_balance(self):
        res = self._request("/api/v1/private/account/asset/USDT")
        return float(res["data"]["availableBalance"]) if res.get("success") else 0.0

    def create_order(self, symbol, price, volume, side, leverage):
        params = {
            "symbol": symbol.lower(),
            "price": price,
            "vol": volume,
            "side": 1 if side.lower() == "long" else 2,
            "leverage": leverage,
            "category": 1,
            "trade_type": 1,
            "position_mode": 1,
            "price_type": 1
        }
        return self._request("/api/v1/private/order/submit", "POST", params)
