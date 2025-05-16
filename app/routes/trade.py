from flask import request
from flask import Blueprint
from flask_restx import Resource, Namespace, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.investment_service import InvestmentService
from ..models.user import User

investment_bp = Blueprint("investments", __name__)
ns = Namespace("investments", description="Investment operations")


def init_investment_routes(api):
    api.add_namespace(ns)

    @ns.route("/callback/sell")
    class SellCallback(Resource):
        @ns.doc("Callback for sell from freqtrade")
        def get():
            risk_level = request.args.get("risk_level")
            if risk_level not in ["low", "medium", "high"]:
                return {"message": "Invalid risk level"}, 400

            # TODO: Check Profit

            return {"message": "Sell callback received"}
