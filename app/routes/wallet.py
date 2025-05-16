"""
입금할 지갑 주소를 관리하는 API 라우터
"""

from flask import Blueprint, jsonify, request
from flask_restx import Resource, Namespace, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.config.wallet_addresses import WALLET_ADDRESSES
from app.models.user import User
from datetime import datetime
from ..services.wallet_service import WalletService

wallet_bp = Blueprint("wallet", __name__)
ns = Namespace("wallet", description="Wallet operations")


def init_wallet_routes(api):
    api.add_namespace(ns)

    # Wallet schemas
    wallet_response = api.model(
        "WalletResponse",
        {
            "address": fields.String(description="Wallet address"),
            "message": fields.String(description="Response message"),
        },
    )

    error_response = api.model(
        "ErrorResponse", {"error": fields.String(description="Error message")}
    )

    @ns.route("/addresses")
    class WalletAddresses(Resource):
        @ns.doc(security="Bearer Auth")
        @ns.response(200, "Wallet addresses retrieved successfully")
        @ns.response(401, "Unauthorized", error_response)
        @jwt_required()
        def get(self):
            """Get fixed wallet addresses for deposits"""
            return {
                "addresses": WALLET_ADDRESSES,
                "message": "Wallet addresses retrieved successfully",
            }, 200

    @ns.route("/deposit")
    class Deposit(Resource):
        @ns.doc("make_deposit")
        @ns.response(200, "Deposit successful", wallet_response)
        @ns.response(400, "Invalid input", error_response)
        @ns.response(401, "Unauthorized", error_response)
        @jwt_required()
        def post(self):
            """Make a deposit to the wallet"""
            current_user = get_jwt_identity()
            data = request.json
            try:
                result = WalletService.make_deposit(
                    current_user, data["amount"], data["coin_type"]
                )
                return {
                    "message": "Deposit successful",
                    "address": result["address"],
                }
            except ValueError as e:
                return {"error": str(e)}, 400

    @ns.route("/withdraw")
    class Withdraw(Resource):
        @ns.doc("make_withdrawal")
        @ns.response(200, "Withdrawal successful", wallet_response)
        @ns.response(400, "Invalid input", error_response)
        @ns.response(401, "Unauthorized", error_response)
        @jwt_required()
        def post(self):
            """Make a withdrawal from the wallet"""
            current_user = get_jwt_identity()
            data = request.json
            try:
                result = WalletService.make_withdrawal(
                    current_user, data["amount"], data["coin_type"]
                )
                return {
                    "message": "Withdrawal successful",
                    "address": result["address"],
                }
            except ValueError as e:
                return {"error": str(e)}, 400

    @ns.route("/balance/<string:coin_type>")
    class Balance(Resource):
        @ns.doc(security="Bearer Auth")
        @ns.response(200, "Balance retrieved successfully")
        @ns.response(401, "Unauthorized", error_response)
        @ns.response(400, "Invalid coin type", error_response)
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

    @ns.route("/transactions")
    class Transactions(Resource):
        @ns.doc(security="Bearer Auth")
        @ns.response(200, "Transactions retrieved successfully")
        @ns.response(401, "Unauthorized", error_response)
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
