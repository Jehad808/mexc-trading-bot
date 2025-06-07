import time
import hmac
import hashlib
import requests
import logging

logger = logging.getLogger(__name__)

class MEXC:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://contract.mexc.com"

    def _sign(self, params: dict) -> str:
        """توليد توقيع HMAC SHA256"""
        query = '&'.join(f"{key}={params[key]}" for key in sorted(params))
        return hmac.new(self.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()

    def _request(self, method: str, path: str, params: dict = None, private: bool = False):
        url = self.base_url + path
        headers = {}
        if params is None:
            params = {}
        if private:
            params["api_key"] = self.api_key
            params["req_time"] = int(time.time() * 1000)
            params["sign"] = self._sign(params)
        if method == "GET":
            response = requests.get(url, params=params, headers=headers)
        else:
            response = requests.post(url, data=params, headers=headers)
        return response.json()

    def get_balance(self) -> float:
        """جلب الرصيد المتاح"""
        result = self._request("GET", "/api/v1/private/account/assets", private=True)
        if result.get("success"):
            for asset in result["data"]:
                if asset["currency"] == "USDT":
                    return float(asset["availableBalance"])
        return 0.0

    def set_leverage(self, symbol: str, leverage: int):
        """تعيين الرافعة المالية"""
        return self._request("POST", "/api/v1/private/position/change-leverage", {
            "symbol": symbol,
            "leverage": leverage
        }, private=True)

    def create_order(self, symbol, entry_price, quantity, direction, leverage=100):
        """فتح صفقة"""
        side = 1 if direction.upper() == "LONG" else 2
        params = {
            "symbol": symbol.lower(),  # مثل btcusdt
            "price": entry_price,
            "vol": quantity,
            "side": side,  # 1 = Buy, 2 = Sell
            "leverage": leverage,
            "open_type": 1,  # Isolated
            "position_id": 0,
            "external_oid": str(int(time.time() * 1000)),
            "stop_loss_price": 0,
            "take_profit_price": 0,
            "position_mode": 1,  # Single Position Mode
            "reduce_only": False,
            "price_type": 1  # Limit Order
        }
        return self._request("POST", "/api/v1/private/order/submit", params, private=True)

    def open_position(self, symbol, direction, leverage, capital_percentage, entry_price=None, take_profit=None, stop_loss=None):
        try:
            balance = self.get_balance()
            if balance == 0:
                return {"status": "error", "message": "الرصيد غير متاح أو صفر"}

            quantity = round((balance * (capital_percentage / 100)) / entry_price, 3)

            set_leverage_result = self.set_leverage(symbol, leverage)
            logger.info(f"تعيين الرافعة المالية: {set_leverage_result}")

            order_result = self.create_order(
                symbol=symbol,
                entry_price=entry_price,
                quantity=quantity,
                direction=direction,
                leverage=leverage
            )
            logger.info(f"نتيجة فتح الصفقة: {order_result}")

            if order_result.get("success"):
                return {"status": "success", "message": "تم فتح الصفقة بنجاح"}
            else:
                return {"status": "error", "message": order_result.get("message", "فشل غير معروف")}
        except Exception as e:
            logger.error(f"خطأ أثناء فتح الصفقة: {e}")
            return {"status": "error", "message": str(e)}
