from flask import Blueprint, jsonify, request
from flask_restx import Resource, Api
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.config.wallet_addresses import WALLET_ADDRESSES
from app.models.user import User
from datetime import datetime

wallet_bp = Blueprint("wallet", __name__)
api = Api(
    wallet_bp,
    version="1.0",
    title="Crypto Wallet API",
    description="API for managing cryptocurrency wallets",
)


def init_wallet_routes(schemas):
    @api.route("/addresses")
    class WalletAddresses(Resource):
        @api.doc(security="Bearer Auth")
        @api.response(200, "Wallet addresses retrieved successfully")
        @api.response(401, "Unauthorized", schemas["error_response"])
        @jwt_required()
        def get(self):
            """Get fixed wallet addresses for deposits"""
            return {
                "addresses": WALLET_ADDRESSES,
                "message": "Wallet addresses retrieved successfully",
            }, 200

    @api.route("/deposit/<string:coin_type>")
    class Deposit(Resource):
        @api.doc(security="Bearer Auth")
        @api.response(200, "Deposit recorded successfully")
        @api.response(401, "Unauthorized", schemas["error_response"])
        @api.response(400, "Invalid coin type", schemas["error_response"])
        @jwt_required()
        def post(self, coin_type):
            """Record a deposit for a specific coin"""
            if coin_type not in WALLET_ADDRESSES:
                return {"message": "Invalid coin type"}, 400

            data = request.get_json()
            amount = data.get("amount")
            tx_hash = data.get("tx_hash")

            if not amount or not tx_hash:
                return {"message": "Amount and transaction hash are required"}, 400

            user_id = get_jwt_identity()
            user = User.objects(id=user_id).first()
            if not user:
                return {"message": "User not found"}, 404

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
                "created_at": datetime.utcnow(),
            }

            user.transactions.append(transaction)
            user.save()

            return {
                "message": f"{coin_type.capitalize()} deposit recorded successfully",
                "deposit": {
                    "user_id": str(user.id),
                    "coin_type": coin_type,
                    "amount": amount,
                    "new_balance": getattr(user, balance_field),
                },
            }, 200

    @api.route("/withdraw/<string:coin_type>")
    class Withdraw(Resource):
        @api.doc(security="Bearer Auth")
        @api.response(200, "Withdrawal processed successfully")
        @api.response(401, "Unauthorized", schemas["error_response"])
        @api.response(
            400, "Invalid coin type or insufficient balance", schemas["error_response"]
        )
        @jwt_required()
        def post(self, coin_type):
            """Process a withdrawal for a specific coin"""
            if coin_type not in WALLET_ADDRESSES:
                return {"message": "Invalid coin type"}, 400

            data = request.get_json()
            amount = data.get("amount")
            destination_address = data.get("destination_address")

            if not amount or not destination_address:
                return {"message": "Amount and destination address are required"}, 400

            user_id = get_jwt_identity()
            user = User.objects(id=user_id).first()
            if not user:
                return {"message": "User not found"}, 404

            # Check balance
            balance_field = f"{coin_type}_balance"
            current_balance = getattr(user, balance_field, 0.0)
            if current_balance < amount:
                return {"message": "Insufficient balance"}, 400

            # Update balance
            setattr(user, balance_field, current_balance - amount)

            # Record transaction
            transaction = {
                "type": "withdrawal",
                "coin_type": coin_type,
                "amount": amount,
                "destination_address": destination_address,
                "status": "completed",
                "created_at": datetime.utcnow(),
            }

            user.transactions.append(transaction)
            user.save()

            return {
                "message": f"{coin_type.capitalize()} withdrawal processed successfully",
                "withdrawal": {
                    "user_id": str(user.id),
                    "coin_type": coin_type,
                    "amount": amount,
                    "new_balance": getattr(user, balance_field),
                },
            }, 200

    @api.route("/balance/<string:coin_type>")
    class Balance(Resource):
        @api.doc(security="Bearer Auth")
        @api.response(200, "Balance retrieved successfully")
        @api.response(401, "Unauthorized", schemas["error_response"])
        @api.response(400, "Invalid coin type", schemas["error_response"])
        @jwt_required()
        def get(self, coin_type):
            """Get balance for a specific coin"""
            if coin_type not in WALLET_ADDRESSES:
                return {"message": "Invalid coin type"}, 400

            user_id = get_jwt_identity()
            user = User.objects(id=user_id).first()
            if not user:
                return {"message": "User not found"}, 404

            balance_field = f"{coin_type}_balance"
            balance = getattr(user, balance_field, 0.0)
            return {
                "coin_type": coin_type,
                "balance": balance,
                "message": f"{coin_type.capitalize()} balance retrieved successfully",
            }, 200

    @api.route("/transactions")
    class Transactions(Resource):
        @api.doc(security="Bearer Auth")
        @api.response(200, "Transactions retrieved successfully")
        @api.response(401, "Unauthorized", schemas["error_response"])
        @jwt_required()
        def get(self):
            """Get user's transaction history"""
            user_id = get_jwt_identity()
            user = User.objects(id=user_id).first()
            if not user:
                return {"message": "User not found"}, 404

            return {
                "transactions": user.transactions,
                "message": "Transactions retrieved successfully",
            }, 200
