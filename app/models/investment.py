from mongoengine import (
    Document,
    StringField,
    FloatField,
    DateTimeField,
    ReferenceField,
    ListField,
    DictField,
)
from datetime import datetime
from typing import Dict, Optional


class Investment(Document):
    name = StringField(required=True, description="Investment name/alias")
    coin_type = StringField(required=True, choices=["BTC", "ETH", "SOL"])
    risk_level = StringField(required=True, choices=["low", "medium", "high"])
    initial_amount = FloatField(required=True)

    current_profit = FloatField(default=0.0)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    # 거래 내역 추가
    transactions = ListField(
        DictField(), default=list, description="투자 관련 거래 내역 (입금/출금)"
    )

    meta = {
        "collection": "investments",
        "indexes": ["coin_type", "name", "risk_level"],
        "ordering": ["-created_at"],
    }

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super(Investment, self).save(*args, **kwargs)

    def to_dict(self) -> Dict:
        # transactions의 datetime 객체도 문자열로 변환
        transactions = []
        for transaction in self.transactions:
            transaction_copy = transaction.copy()
            if isinstance(transaction_copy.get("created_at"), datetime):
                transaction_copy["created_at"] = transaction_copy[
                    "created_at"
                ].isoformat()
            transactions.append(transaction_copy)

        return {
            "id": str(self.id),
            "name": self.name,
            "coin_type": self.coin_type,
            "risk_level": self.risk_level,
            "initial_amount": self.initial_amount,
            "current_profit": self.current_profit,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "transactions": transactions,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Investment":
        investment = cls(
            name=data["name"],
            coin_type=data["coin_type"],
            risk_level=data["risk_level"],
            initial_amount=data["initial_amount"],
            current_profit=data.get("current_profit", 0.0),
        )
        investment.created_at = data.get("created_at", datetime.utcnow())
        investment.updated_at = data.get("updated_at", datetime.utcnow())
        investment.transactions = data.get("transactions", [])
        return investment
