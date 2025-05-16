from flask import request
from flask_restx import Resource, Namespace
from ..services.investment_service import InvestmentService
from ..utils.auth import token_required
from ..models.user import User

api = Namespace("investments", description="Investment operations")


@api.route("")
class InvestmentList(Resource):
    @api.doc("create_investment")
    @token_required
    def post(self, current_user: User):
        """새로운 투자를 생성합니다."""
        data = request.json
        investment = InvestmentService.create_investment(
            user=current_user,
            coin_type=data["coin_type"],
            initial_amount=data["initial_amount"],
        )
        return {
            "message": "Investment created successfully",
            "investment": investment.to_dict(),
        }, 201

    @api.doc("get_user_investments")
    @token_required
    def get(self, current_user: User):
        """사용자의 모든 투자 목록을 조회합니다."""
        investments = InvestmentService.get_user_investments(current_user)
        return {
            "message": "Investments retrieved successfully",
            "investments": [inv.to_dict() for inv in investments],
        }


@api.route("/<investment_id>")
class InvestmentResource(Resource):
    @api.doc("get_investment")
    @token_required
    def get(self, current_user: User, investment_id: str):
        """특정 투자 정보를 조회합니다."""
        investment = InvestmentService.get_investment(investment_id)
        if not investment or investment.user.id != current_user.id:
            return {"error": "Investment not found"}, 404
        return {
            "message": "Investment retrieved successfully",
            "investment": investment.to_dict(),
        }

    @api.doc("update_investment")
    @token_required
    def put(self, current_user: User, investment_id: str):
        """투자의 수익을 업데이트합니다."""
        data = request.json
        investment = InvestmentService.update_investment_profit(
            investment_id=investment_id, new_profit=data["current_profit"]
        )
        if not investment or investment.user.id != current_user.id:
            return {"error": "Investment not found"}, 404
        return {
            "message": "Investment updated successfully",
            "investment": investment.to_dict(),
        }

    @api.doc("delete_investment")
    @token_required
    def delete(self, current_user: User, investment_id: str):
        """투자를 삭제합니다."""
        investment = InvestmentService.get_investment(investment_id)
        if not investment or investment.user.id != current_user.id:
            return {"error": "Investment not found"}, 404
        InvestmentService.delete_investment(investment_id)
        return {"message": "Investment deleted successfully"}, 200


@api.route("/coin/<coin_type>")
class InvestmentByCoin(Resource):
    @api.doc("get_investments_by_coin")
    @token_required
    def get(self, current_user: User, coin_type: str):
        """특정 코인 타입의 투자 목록을 조회합니다."""
        investments = InvestmentService.get_investments_by_coin_type(
            current_user, coin_type
        )
        return {
            "message": "Investments retrieved successfully",
            "investments": [inv.to_dict() for inv in investments],
        }


@api.route("/<investment_id>/deposit")
class InvestmentDeposit(Resource):
    @api.doc("add_deposit")
    @token_required
    def post(self, current_user: User, investment_id: str):
        """투자에 추가 입금을 합니다."""
        data = request.json
        investment = InvestmentService.get_investment(investment_id)
        if not investment or investment.user.id != current_user.id:
            return {"error": "Investment not found"}, 404

        try:
            investment = InvestmentService.add_deposit(
                investment_id=investment_id,
                amount=data["amount"],
                description=data.get("description", "Additional deposit"),
            )
            return {"message": "Deposit successful", "investment": investment.to_dict()}
        except Exception as e:
            return {"error": str(e)}, 400


@api.route("/<investment_id>/withdraw")
class InvestmentWithdrawal(Resource):
    @api.doc("make_withdrawal")
    @token_required
    def post(self, current_user: User, investment_id: str):
        """투자에서 출금을 합니다."""
        data = request.json
        investment = InvestmentService.get_investment(investment_id)
        if not investment or investment.user.id != current_user.id:
            return {"error": "Investment not found"}, 404

        try:
            investment = InvestmentService.make_withdrawal(
                investment_id=investment_id,
                amount=data["amount"],
                description=data.get("description", "Withdrawal"),
            )
            return {
                "message": "Withdrawal successful",
                "investment": investment.to_dict(),
            }
        except ValueError as e:
            return {"error": str(e)}, 400
        except Exception as e:
            return {"error": str(e)}, 500
