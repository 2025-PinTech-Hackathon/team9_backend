from mongoengine import (
    Document,
    StringField,
    EmailField,
    DateTimeField,
    FloatField,
    ListField,
    DictField,
    ReferenceField,
    ObjectIdField,
)
from .investment import Investment
from datetime import datetime
from typing import Dict, Optional
from bson import ObjectId


class User(Document):
    _id = ObjectIdField(primary_key=True, default=ObjectId)
    user_id = StringField(required=True, unique=True)
    email = EmailField(required=True, unique=True)
    password = StringField(required=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    # USDT 잔액 필드
    usdt_balance = FloatField(default=0.0)

    # 가지고있는 Investment 목록
    investments = ListField(ReferenceField(Investment), default=list)

    # 거래 내역
    # transactions = ListField(DictField(), default=list)

    meta = {
        "collection": "users",
        "indexes": [
            {"fields": ["email"], "unique": True},
            {"fields": ["user_id"], "unique": True},
            {"fields": ["-created_at"]},
        ],
        "allow_inheritance": False,
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
            "usdt_balance": self.usdt_balance,
            "investments": [inv.to_dict() for inv in self.investments],
            # "transactions": self.transactions,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "User":
        user = cls(email=data["email"], password=data["password"])
        user.created_at = datetime.fromisoformat(data["created_at"])
        user.updated_at = datetime.fromisoformat(data["updated_at"])
        user.usdt_balance = data["usdt_balance"]
        user.investments = [Investment.from_dict(inv) for inv in data["investments"]]
        # user.transactions = data["transactions"]
        return user
