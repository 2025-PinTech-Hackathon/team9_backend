from typing import Dict, Any
from app.models.user import User


class WalletService:
    def __init__(self):
        pass

    def record_deposit(
        self, user_id: str, coin_type: str, amount: float, tx_hash: str
    ) -> Dict[str, Any]:
        """Record a deposit for a user"""
        user = User.objects(id=user_id).first()
        if not user:
            raise ValueError("User not found")

        # Update user's balance
        balance_field = f"{coin_type}_balance"
        current_balance = getattr(user, balance_field, 0.0)
        setattr(user, balance_field, current_balance + amount)

        # Record transaction
        transaction = {
            "type": "deposit",
            "coin_type": coin_type,
            "amount": amount,
            "tx_hash": tx_hash,
            "status": "completed",
        }

        if not hasattr(user, "transactions"):
            user.transactions = []

        user.transactions.append(transaction)
        user.save()

        return {
            "user_id": str(user.id),
            "coin_type": coin_type,
            "amount": amount,
            "new_balance": getattr(user, balance_field),
        }

    def process_withdrawal(
        self, user_id: str, coin_type: str, amount: float, destination_address: str
    ) -> Dict[str, Any]:
        """Process a withdrawal for a user"""
        user = User.objects(id=user_id).first()
        if not user:
            raise ValueError("User not found")

        # Check balance
        balance_field = f"{coin_type}_balance"
        current_balance = getattr(user, balance_field, 0.0)
        if current_balance < amount:
            raise ValueError("Insufficient balance")

        # Update balance
        setattr(user, balance_field, current_balance - amount)

        # Record transaction
        transaction = {
            "type": "withdrawal",
            "coin_type": coin_type,
            "amount": amount,
            "destination_address": destination_address,
            "status": "completed",
        }

        if not hasattr(user, "transactions"):
            user.transactions = []

        user.transactions.append(transaction)
        user.save()

        return {
            "user_id": str(user.id),
            "coin_type": coin_type,
            "amount": amount,
            "new_balance": getattr(user, balance_field),
        }

    def get_balance(self, user_id: str, coin_type: str) -> float:
        """Get user's balance for a specific coin"""
        user = User.objects(id=user_id).first()
        if not user:
            raise ValueError("User not found")

        balance_field = f"{coin_type}_balance"
        return getattr(user, balance_field, 0.0)
