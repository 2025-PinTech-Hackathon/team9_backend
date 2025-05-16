from mongoengine import (
    Document,
    StringField,
    FloatField,
    DateTimeField,
    ReferenceField,
    ObjectIdField,
)
from datetime import datetime
from typing import Dict
from bson import ObjectId
from .user import User


class USDTTransaction(Document):
    _id = ObjectIdField(primary_key=True, default=ObjectId)
    user = ReferenceField(User, required=True)
    amount = FloatField(required=True)  # 양수면 입금, 음수면 출금
    transaction_type = StringField(required=True, choices=["deposit", "withdraw"])
    status = StringField(
        required=True, choices=["completed", "pending", "failed"], default="completed"
    )
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "usdt_transactions",
        "indexes": [
            {"fields": ["user"]},
            {"fields": ["-created_at"]},
        ],
    }

    def to_dict(self) -> Dict:
        return {
            "id": str(self._id),
            "user_id": str(self.user.id),
            "amount": self.amount,
            "transaction_type": self.transaction_type,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }
