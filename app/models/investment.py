from mongoengine import (
    Document,
    StringField,
    FloatField,
    DateTimeField,
    ReferenceField,
    ListField,
    DictField,
    IntField,
)
from datetime import datetime
from typing import Dict, Optional
from .investment_trade_history import InvestmentTradeHistory


class Investment(Document):
    name = StringField(required=True, description="Investment name/alias")
    coin_type = StringField(required=True, choices=["BTC", "ETH", "SOL"])
    risk_level = StringField(required=True, choices=["low", "medium", "high"])
    initial_amount = FloatField(required=True)
    entry_price_usdt = FloatField(required=True, description="Entry price in USDT")

    current_profit = FloatField(default=0.0)
    internal_position = IntField(required=True, description="Internal position number")
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    # 거래 내역 추가
    transactions = ListField(
        DictField(), default=list, description="투자 관련 거래 내역 (입금/출금)"
    )

    trade_history = ListField(ReferenceField(InvestmentTradeHistory))

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

        trade_histories = []
        for trade_history in self.trade_history:
            trade_history_copy = trade_history.to_dict()
            if isinstance(trade_history_copy.get("created_at"), datetime):
                trade_history_copy["created_at"] = trade_history_copy[
                    "created_at"
                ].isoformat()
            trade_histories.append(trade_history_copy)

        return {
            "id": str(self.id),
            "name": self.name,
            "coin_type": self.coin_type,
            "risk_level": self.risk_level,
            "initial_amount": self.initial_amount,
            "entry_price_usdt": self.entry_price_usdt,
            "current_profit": self.current_profit,
            "internal_position": self.internal_position,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "transactions": transactions,
            "trade_history": trade_histories,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Investment":
        investment = cls(
            name=data["name"],
            coin_type=data["coin_type"],
            risk_level=data["risk_level"],
            initial_amount=data["initial_amount"],
            entry_price_usdt=data["entry_price_usdt"],
            current_profit=data.get("current_profit", 0.0),
            internal_position=data["internal_position"],
        )
        investment.created_at = data.get("created_at", datetime.utcnow())
        investment.updated_at = data.get("updated_at", datetime.utcnow())
        investment.transactions = data.get("transactions", [])
        return investment
