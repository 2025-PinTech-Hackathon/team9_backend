from mongoengine import (
    Document,
    StringField,
    FloatField,
    DateTimeField,
    IntField,
)
from datetime import datetime


class FreqtradeHistory(Document):
    risk_level = StringField(required=True, choices=["low", "medium", "high"])
    real_profit_in_this_sell = FloatField(default=0.0)
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "freqtrade_history",
        "indexes": ["risk_level", "created_at"],
        "ordering": ["-created_at"],
    }
