from datetime import datetime
from mongoengine import Document, FloatField, DateTimeField, ReferenceField


class InvestmentTradeHistory(Document):
    profit_amount = FloatField(required=True)
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "investment_trade_histories",
        "indexes": ["created_at"],
    }

    def to_dict(self):
        return {
            "id": str(self.id),
            "profit_amount": self.profit_amount,
            "created_at": self.created_at.isoformat(),
        }
