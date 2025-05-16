"""
입금할 지갑 주소를 관리하는 API 라우터
"""

from flask import Blueprint, jsonify, request
from flask_restx import Resource, Namespace, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.usdt_transaction import USDTTransaction
from math import ceil

wallet_bp = Blueprint("wallet", __name__)
ns = Namespace("wallet", description="Wallet operations")


def init_wallet_routes(api):
    api.add_namespace(ns)

    error_response = api.model(
        "ErrorResponse", {"error": fields.String(description="Error message")}
    )

    @ns.route("/transactions")
    class Transactions(Resource):
        @ns.doc(security="Bearer Auth")
        @ns.response(200, "Transactions retrieved successfully")
        @ns.response(401, "Unauthorized", error_response)
        @jwt_required()
        def get(self):
            """Get user's transaction history"""
            try:
                user_id = get_jwt_identity()
                user = User.objects.get(user_id=user_id)

                # 페이지네이션 파라미터
                page = int(request.args.get("page", 1))
                per_page = int(request.args.get("per_page", 10))
                sort = request.args.get("sort", "desc")  # 기본값은 최신순

                # 전체 거래 수 조회
                total_transactions = USDTTransaction.objects(user=user).count()
                total_pages = ceil(total_transactions / per_page)

                # 정렬 방향 설정
                sort_direction = "-" if sort == "desc" else ""

                # 거래 내역 조회
                transactions = (
                    USDTTransaction.objects(user=user)
                    .order_by(f"{sort_direction}created_at")
                    .skip((page - 1) * per_page)
                    .limit(per_page)
                )

                return {
                    "transactions": [t.to_dict() for t in transactions],
                    "page": page,
                    "per_page": per_page,
                    "total_pages": total_pages,
                    "total_transactions": total_transactions,
                    "sort": sort,
                }, 200

            except Exception as e:
                return {"error": str(e)}, 500

    @ns.route("/deposit")
    class Deposit(Resource):
        @ns.doc(security="Bearer Auth")
        @ns.response(200, "Deposit successful")
        @ns.response(400, "Invalid amount", error_response)
        @ns.response(401, "Unauthorized", error_response)
        @jwt_required()
        def post(self):
            """Deposit USDT"""
            try:
                data = request.get_json()
                amount = float(data.get("amount", 0))

                if amount <= 0:
                    return {"error": "입금 금액은 0보다 커야 합니다."}, 400

                user_id = get_jwt_identity()
                user = User.objects.get(user_id=user_id)

                # USDT 잔액 업데이트
                user.usdt_balance += amount
                user.save()

                # 거래 내역 생성
                transaction = USDTTransaction(
                    user=user,
                    amount=amount,
                    transaction_type="deposit",
                    status="completed",
                ).save()

                return {
                    "message": "입금이 완료되었습니다.",
                    "transaction": transaction.to_dict(),
                    "new_balance": user.usdt_balance,
                }, 200

            except Exception as e:
                return {"error": str(e)}, 500

    @ns.route("/withdraw")
    class Withdraw(Resource):
        @ns.doc(security="Bearer Auth")
        @ns.response(200, "Withdrawal successful")
        @ns.response(400, "Invalid amount or insufficient balance", error_response)
        @ns.response(401, "Unauthorized", error_response)
        @jwt_required()
        def post(self):
            """Withdraw USDT"""
            try:
                data = request.get_json()
                amount = float(data.get("amount", 0))

                if amount <= 0:
                    return {"error": "출금 금액은 0보다 커야 합니다."}, 400

                user_id = get_jwt_identity()
                user = User.objects.get(user_id=user_id)

                # 잔액 확인
                if user.usdt_balance < amount:
                    return {"error": "잔액이 부족합니다."}, 400

                # USDT 잔액 업데이트
                user.usdt_balance -= amount
                user.save()

                # 거래 내역 생성
                transaction = USDTTransaction(
                    user=user,
                    amount=-amount,  # 출금은 음수로 저장
                    transaction_type="withdraw",
                    status="completed",
                ).save()

                return {
                    "message": "출금이 완료되었습니다.",
                    "transaction": transaction.to_dict(),
                    "new_balance": user.usdt_balance,
                }, 200

            except Exception as e:
                return {"error": str(e)}, 500

    @ns.route("/balance")
    class Balance(Resource):
        @ns.doc(security="Bearer Auth")
        @ns.response(200, "Balance retrieved successfully")
        @ns.response(401, "Unauthorized", error_response)
        @jwt_required()
        def get(self):
            """Get USDT balance"""
            try:
                user_id = get_jwt_identity()
                user = User.objects.get(user_id=user_id)

                return {"usdt_balance": user.usdt_balance}, 200

            except Exception as e:
                return {"error": str(e)}, 500
