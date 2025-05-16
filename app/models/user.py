from mongoengine import (
    Document,
    StringField,
    EmailField,
    DateTimeField,
    FloatField,
    ListField,
    DictField,
)
from datetime import datetime
from typing import Dict, Optional


class User(Document):
    user_id = StringField(required=True, unique=True)
    email = EmailField(required=True, unique=True)
    password = StringField(required=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    # 지갑 잔액 필드
    bitcoin_balance = FloatField(default=0.0)
    ethereum_balance = FloatField(default=0.0)
    solana_balance = FloatField(default=0.0)

    # 거래 내역
    transactions = ListField(DictField(), default=list)

    meta = {
        "collection": "users",
        "indexes": [{"fields": ["email"], "unique": True}, {"fields": ["-created_at"]}],
    }

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super(User, self).save(*args, **kwargs)

    def to_dict(self) -> Dict:
        return {
            "user_id": str(self.user_id),
            "email": self.email,
            "password": self.password,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "bitcoin_balance": self.bitcoin_balance,
            "ethereum_balance": self.ethereum_balance,
            "solana_balance": self.solana_balance,
            "transactions": self.transactions,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "User":
        user = cls(email=data["email"], password=data["password"])
        user.created_at = datetime.fromisoformat(data["created_at"])
        user.updated_at = datetime.fromisoformat(data["updated_at"])
        user.bitcoin_balance = data["bitcoin_balance"]
        user.ethereum_balance = data["ethereum_balance"]
        user.solana_balance = data["solana_balance"]
        user.transactions = data["transactions"]
        return user
