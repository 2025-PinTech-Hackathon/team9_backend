from flask import request, jsonify
from flask import Blueprint
from flask_restx import Resource, Namespace, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.investment_service import InvestmentService
from ..models.user import User
from ..models.investment import Investment

investment_bp = Blueprint("investments", __name__)
ns = Namespace("investments", description="Investment operations")


def init_investment_routes(api):
    api.add_namespace(ns)

    # Investment 관련 스키마 정의
    investment_model = api.model(
        "Investment",
        {
            "name": fields.String(required=True, description="Investment name/alias"),
            "coin_type": fields.String(
                required=True, description="Type of cryptocurrency (BTC/ETH/SOL)"
            ),
            "initial_amount": fields.Float(
                required=True, description="Initial investment amount"
            ),
            "risk_level": fields.String(
                required=True, description="Risk level (low/medium/high)"
            ),
            "internal_position": fields.Integer(
                required=False, description="Internal position"
            ),
        },
    )

    investment_response = api.model(
        "InvestmentResponse",
        {
            "message": fields.String(description="Response message"),
            "investment": fields.Nested(investment_model),
        },
    )

    investments_list_response = api.model(
        "InvestmentsListResponse",
        {
            "message": fields.String(description="Response message"),
            "investments": fields.List(fields.Nested(investment_model)),
        },
    )

    @ns.route("")
    class InvestmentList(Resource):
        @ns.doc("create_investment")
        @ns.expect(investment_model)
        @ns.response(201, "Investment created successfully", investment_response)
        @ns.response(
            400, "Invalid input", api.model("ErrorResponse", {"error": fields.String()})
        )
        @jwt_required()
        def post(self):
            """새로운 투자를 생성합니다."""
            current_user = get_jwt_identity()
            user = User.objects(user_id=current_user).first()
            data = request.json
            risk_level = data.get("risk_level", "medium")
            internal_position = data.get("internal_position", 0)
            try:
                investment = InvestmentService.create_investment(
                    name=data["name"],
                    coin_type=data["coin_type"],
                    initial_amount=data["initial_amount"],
                    internal_position=internal_position,
                    risk_level=risk_level,
                    user=user,
                )
                user.investments.append(investment)
                user.save()

                return {
                    "message": "Investment created successfully",
                    "investment": investment.to_dict(),
                }, 201
            except ValueError as e:
                return {"error": str(e)}, 400

        @ns.doc("get_user_investments")
        @ns.response(
            200, "Investments retrieved successfully", investments_list_response
        )
        @ns.response(
            401, "Unauthorized", api.model("ErrorResponse", {"error": fields.String()})
        )
        @jwt_required()
        def get(self):
            """사용자의 모든 투자 목록을 조회합니다."""
            current_user = get_jwt_identity()
            user = User.objects(user_id=current_user).first()
            investments = user.investments
            return {
                "message": "Investments retrieved successfully",
                "investments": [inv.to_dict() for inv in investments],
            }

    @ns.route("/<investment_id>")
    class InvestmentResource(Resource):
        @ns.doc("get_investment")
        @ns.response(200, "Investment retrieved successfully", investment_response)
        @ns.response(
            404,
            "Investment not found",
            api.model("ErrorResponse", {"error": fields.String()}),
        )
        @jwt_required()
        def get(self, investment_id: str):
            """특정 투자 정보를 조회합니다."""
            current_user = get_jwt_identity()
            investment = InvestmentService.get_investment(investment_id)
            if not investment or investment.user.id != current_user.id:
                return {"error": "Investment not found"}, 404
            return {
                "message": "Investment retrieved successfully",
                "investment": investment.to_dict(),
            }

        @ns.doc("delete_investment")
        @ns.response(200, "Investment deleted successfully")
        @ns.response(
            404,
            "Investment not found",
            api.model("ErrorResponse", {"error": fields.String()}),
        )
        @jwt_required()
        def delete(self, investment_id: str):
            """투자를 삭제합니다."""
            current_user = get_jwt_identity()
            user = User.objects(user_id=current_user).first()
            investment = InvestmentService.get_investment(investment_id)
            if not investment or investment.user.id != current_user.id:
                return {"error": "Investment not found"}, 404
            InvestmentService.delete_investment(investment_id, user)
            return {"message": "Investment deleted successfully"}, 200

    @ns.route("/coin/<coin_type>")
    class InvestmentByCoin(Resource):
        @ns.doc("get_investments_by_coin")
        @ns.response(
            200, "Investments retrieved successfully", investments_list_response
        )
        @ns.response(
            401, "Unauthorized", api.model("ErrorResponse", {"error": fields.String()})
        )
        @jwt_required()
        def get(self, coin_type: str):
            """특정 코인 타입의 투자 목록을 조회합니다."""
            current_user = get_jwt_identity()
            investments = InvestmentService.get_investments_by_coin_type(
                current_user, coin_type
            )
            return {
                "message": "Investments retrieved successfully",
                "investments": [inv.to_dict() for inv in investments],
            }

    @ns.route("/<investment_id>/deposit")
    class InvestmentDeposit(Resource):
        @ns.doc("add_deposit")
        @ns.response(200, "Deposit successful", investment_response)
        @ns.response(
            400, "Invalid input", api.model("ErrorResponse", {"error": fields.String()})
        )
        @ns.response(
            404,
            "Investment not found",
            api.model("ErrorResponse", {"error": fields.String()}),
        )
        @jwt_required()
        def post(self, investment_id: str):
            """투자에 추가 입금을 합니다."""
            current_user = get_jwt_identity()
            data = request.json
            investment = InvestmentService.get_investment(investment_id)
            user = User.objects(user_id=current_user).first()
            for inv in user.investments:
                if inv.id == investment_id:
                    investment = inv
                    break
            if not investment:
                return {"error": "Investment not found"}, 404

            try:
                investment = InvestmentService.add_deposit(
                    investment_id=investment_id,
                    amount=data["amount"],
                    description=data.get("description", "Additional deposit"),
                )
                return {
                    "message": "Deposit successful",
                    "investment": investment.to_dict(),
                }
            except Exception as e:
                return {"error": str(e)}, 400

    @ns.route("/<investment_id>/withdraw")
    class InvestmentWithdrawal(Resource):
        @ns.doc("make_withdrawal")
        @ns.response(200, "Withdrawal successful", investment_response)
        @ns.response(
            400, "Invalid input", api.model("ErrorResponse", {"error": fields.String()})
        )
        @ns.response(
            404,
            "Investment not found",
            api.model("ErrorResponse", {"error": fields.String()}),
        )
        @jwt_required()
        def post(self, investment_id: str):
            """투자에서 출금을 합니다."""
            current_user = get_jwt_identity()
            data = request.json
            investment = InvestmentService.get_investment(investment_id)
            user = User.objects(user_id=current_user).first()
            for inv in user.investments:
                if inv.id == investment_id:
                    investment = inv
                    break
            if not investment:
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

    @ns.route("/get_investment_by_email_position", methods=["GET"])
    class GetInvestmentByEmailPosition(Resource):
        @ns.doc("get_investment_by_email_position")
        @ns.response(200, "Investment retrieved successfully", investment_response)
        @ns.response(
            400, "Invalid input", api.model("ErrorResponse", {"error": fields.String()})
        )
        @ns.response(
            404,
            "Investment not found",
            api.model("ErrorResponse", {"error": fields.String()}),
        )
        @ns.response(
            500, "Server error", api.model("ErrorResponse", {"error": fields.String()})
        )
        def get(self):
            """이메일과 internal_position으로 투자 정보를 조회하는 API"""
            try:
                email = request.args.get("email")
                internal_position = request.args.get("internal_position")

                if not email or not internal_position:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "message": "이메일과 internal_position이 필요합니다.",
                            }
                        ),
                        400,
                    )

                try:
                    internal_position = int(internal_position)
                except ValueError:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "message": "internal_position은 숫자여야 합니다.",
                            }
                        ),
                        400,
                    )

                user = User.objects(email=email).first()
                investment: Investment = None
                for inv in user.investments:
                    if inv.internal_position == internal_position:
                        investment = inv
                        break

                if not investment:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "message": "투자 정보를 찾을 수 없습니다.",
                            }
                        ),
                        404,
                    )

                return (
                    jsonify(
                        {
                            "success": True,
                            "data": investment.to_dict(),
                        }
                    ),
                    200,
                )

            except Exception as e:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": f"서버 오류가 발생했습니다: {str(e)}",
                        }
                    ),
                    500,
                )

    @ns.route("/get_investment_by_position", methods=["GET"])
    class GetInvestmentByPosition(Resource):
        @ns.doc("get_investment_by_position")
        @ns.response(200, "Investment retrieved successfully", investment_response)
        @ns.response(
            400, "Invalid input", api.model("ErrorResponse", {"error": fields.String()})
        )
        @ns.response(
            404,
            "Investment not found",
            api.model("ErrorResponse", {"error": fields.String()}),
        )
        @ns.response(
            500, "Server error", api.model("ErrorResponse", {"error": fields.String()})
        )
        @jwt_required()
        def get(self):
            """internal_position으로 투자 정보를 조회하는 API"""
            try:
                internal_position = request.args.get("internal_position")
                current_user = get_jwt_identity()
                user = User.objects(user_id=current_user).first()

                if not internal_position:
                    return {
                        "success": False,
                        "message": "internal_position이 필요합니다.",
                    }, 400

                try:
                    internal_position = int(internal_position)
                except ValueError:
                    return {
                        "success": False,
                        "message": "internal_position은 숫자여야 합니다.",
                    }, 400

                investment: Investment = None
                for inv in user.investments:
                    if inv.internal_position == internal_position:
                        investment = inv
                        break

                if not investment:
                    return {
                        "success": False,
                        "message": "투자 정보를 찾을 수 없습니다.",
                    }, 404

                return {
                    "success": True,
                    "data": investment.to_dict(),
                }, 200

            except Exception as e:
                return {
                    "success": False,
                    "message": f"서버 오류가 발생했습니다: {str(e)}",
                }, 500
