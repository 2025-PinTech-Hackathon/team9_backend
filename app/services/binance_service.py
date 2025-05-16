import requests
from typing import Dict, Optional


class BinanceService:
    BASE_URL = "https://api.binance.com/api/v3"

    @staticmethod
    def get_current_price(symbol: str) -> Optional[float]:
        """현재 거래소의 특정 심볼 가격을 가져옵니다."""
        try:
            response = requests.get(
                f"{BinanceService.BASE_URL}/ticker/price", params={"symbol": symbol}
            )
            response.raise_for_status()
            data = response.json()
            return float(data["price"])
        except Exception as e:
            print(f"Error getting price for {symbol}: {str(e)}")
            return None

    @staticmethod
    def get_btc_price() -> Optional[float]:
        """현재 BTC/USDT 가격을 가져옵니다."""
        return BinanceService.get_current_price("BTCUSDT")
