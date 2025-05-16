from mongoengine import (
    Document,
    StringField,
    FloatField,
    DateTimeField,
    IntField,
)
from datetime import datetime


class FreqtradeHistory(Document):
    profit_closed_coin = FloatField(default=0.0)
    profit_closed_percent_mean = FloatField(default=0.0)
    profit_closed_ratio_mean = FloatField(default=0.0)
    profit_closed_percent_sum = FloatField(default=0.0)
    profit_closed_ratio_sum = FloatField(default=0.0)
    profit_closed_percent = FloatField(default=0.0)
    profit_closed_ratio = FloatField(default=0.0)
    profit_closed_fiat = FloatField(default=0.0)
    profit_all_coin = FloatField(default=0.0)
    profit_all_percent_mean = FloatField(default=0.0)
    profit_all_ratio_mean = FloatField(default=0.0)
    profit_all_percent_sum = FloatField(default=0.0)
    profit_all_ratio_sum = FloatField(default=0.0)
    profit_all_percent = FloatField(default=0.0)
    profit_all_ratio = FloatField(default=0.0)
    profit_all_fiat = FloatField(default=0.0)
    trade_count = IntField(default=0)
    closed_trade_count = IntField(default=0)
    first_trade_date = StringField(default="")
    first_trade_humanized = StringField(default="")
    first_trade_timestamp = IntField(default=0)
    latest_trade_date = StringField(default="")
    latest_trade_humanized = StringField(default="")
    latest_trade_timestamp = IntField(default=0)
    avg_duration = StringField(default="0:00:00")
    best_pair = StringField(default="")
    best_rate = FloatField(default=0.0)
    best_pair_profit_ratio = FloatField(default=0.0)
    best_pair_profit_abs = FloatField(default=0.0)
    winning_trades = IntField(default=0)
    losing_trades = IntField(default=0)
    profit_factor = FloatField(default=None)
    winrate = FloatField(default=0.0)
    expectancy = FloatField(default=0.0)
    expectancy_ratio = FloatField(default=100.0)
    max_drawdown = FloatField(default=0.0)
    max_drawdown_abs = FloatField(default=0.0)
    max_drawdown_start = StringField(default="")
    max_drawdown_start_timestamp = IntField(default=0)
    max_drawdown_end = StringField(default="")
    max_drawdown_end_timestamp = IntField(default=0)
    trading_volume = FloatField(default=0.0)
    bot_start_timestamp = IntField(default=0)
    bot_start_date = StringField(default="")
    risk_level = StringField(required=True, choices=["low", "medium", "high"])
    real_profit_in_this_sell = FloatField(default=0.0)
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "freqtrade_history",
        "indexes": ["risk_level", "created_at"],
        "ordering": ["-created_at"],
    }
