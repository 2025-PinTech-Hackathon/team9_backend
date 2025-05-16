# --- Do not remove these libs ---
from freqtrade.strategy import IStrategy
from pandas import DataFrame

# --------------------------------
# config007.json
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
import numpy as np
import requests


class config_high_risk_strategy(IStrategy):
    INTERFACE_VERSION: int = 3

    minimal_roi = {"0": 0.035}

    stoploss = -0.02
    timeframe = "1h"
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    order_types = {
        "entry": "market",
        "exit": "market",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    def populate_indicators(self, df: DataFrame, metadata: dict) -> DataFrame:
        df["rsi"] = ta.RSI(df, timeperiod=14)
        df["ema_fast"] = ta.EMA(df, timeperiod=9)
        df["ema_slow"] = ta.EMA(df, timeperiod=21)
        df["ema_trend"] = ta.EMA(df, timeperiod=50)
        df["mom"] = ta.MOM(df, timeperiod=5)
        df["cci"] = ta.CCI(df, timeperiod=14)
        df["adx"] = ta.ADX(df)

        tp = qtpylib.typical_price(df)
        bb = qtpylib.bollinger_bands(tp, window=20, stds=2)
        df["bb_lower"] = bb["lower"]
        df["bb_upper"] = bb["upper"]
        df["bb_mid"] = bb["mid"]

        return df

    def populate_entry_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        df["enter_long"] = (
            (df["ema_fast"] > df["ema_slow"])
            & (df["ema_slow"] > df["ema_trend"])
            & (df["adx"] > 20)
            & (df["rsi"] > 50)
            & (df["mom"] > 0)
        ).astype(int)
        return df

    def populate_exit_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        df["exit_long"] = (
            (df["rsi"] > 75) | (df["close"] > df["bb_upper"]) | (df["ema_fast"] < df["ema_slow"])
        ).astype(int)
        return df

    def custom_exit(self, pair: str, trade, current_time, current_rate, current_profit, **kwargs):
        try:
            profit_usd = round(trade.stake_amount * current_profit, 2)

            requests.get(
                "http://localhost:5000/trade/callback/sell",  # url
                params={
                    "risk_level": "high",
                    # "pair": pair,
                    "profit_usd": profit_usd,
                    "stake_amount": trade.stake_amount,
                },
            )
        except Exception as e:
            self.logger.warning(f"Sell callback error: {e}")

        return "exit"
