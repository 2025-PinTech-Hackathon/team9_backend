from flask import request
from flask import Blueprint
from flask_restx import Resource, Namespace, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.investment_service import InvestmentService
from ..models.user import User
from ..models.investment import Investment
from ..services.freqtrade_provider import get_freqtrade_profit
from ..models.freqtrade_history import FreqtradeHistory
import os
import json
from typing import List

trade_bp = Blueprint("trade", __name__)
ns = Namespace("trade", description="Trade operations")


def init_trade_routes(api):
    api.add_namespace(ns)

    @ns.route("/callback/sell")
    class SellCallback(Resource):
        @ns.doc("Callback for sell from freqtrade")
        def get(self):
            risk_level = request.args.get("risk_level")
            profit_usd = request.args.get("profit_usd")
            if risk_level not in ["low", "medium", "high"]:
                return {"message": "Invalid risk level"}, 400

            # Config 가져오기
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(
                current_dir,
                "..",
                "services",
                "freqtrade_configs",
                f"config_{risk_level}_risk.json",
            )
            with open(config_path, "r") as f:
                config = json.load(f)
            stake_amount = config.get("stake_amount", 0)
            if stake_amount == "unlimited":
                print("stake_amount is unlimited!!! Please change the config file")
                return {"message": "Stake amount is unlimited"}, 400

            # 이번 거래로 인해 얻은 수익
            real_profit_in_this_sell = profit_usd

            # Get profit data from freqtrade

            # profit_json = get_freqtrade_profit(risk_level)

            # # Risk level 에서 가장 최근 FreqtradeHistory 조회
            # latest_history = (
            #     FreqtradeHistory.objects.filter(risk_level=risk_level)
            #     .order_by("-created_at")
            #     .first()
            # )

            # if latest_history:
            #     real_profit_in_this_sell = (
            #         profit_json.get("profit_closed_fiat", 0)
            #         - latest_history.profit_closed_fiat
            #     )
            # else:
            #     real_profit_in_this_sell = profit_json.get("profit_closed_fiat", 0)

            # 선택한 risk_level 에 해당하는 모든 investment 가져옴
            investments: List[Investment] = Investment.objects.filter(
                risk_level=risk_level,
                coin_type="BTC",
            )

            # 각 investment 에 대해 이번 거래로 인해 얻은 수익 추가
            for investment in investments:
                # stake_amount 대비 실제로 얼마 투자했는지 계산
                investment_stake_ratio = (
                    investment.initial_amount + investment.current_profit
                ) / stake_amount
                investment.current_profit += (
                    real_profit_in_this_sell * investment_stake_ratio
                )
                print(
                    f"Investment of {investment.name}:\tProfit: {investment.current_profit}, Real Profit: {real_profit_in_this_sell}, Investment Stake Ratio: {investment_stake_ratio}"
                )
                investment.save()

            # Create and save freqtrade history
            history = FreqtradeHistory(
                risk_level=risk_level,
                real_profit_in_this_sell=real_profit_in_this_sell,
                # **profit_json,
            )
            history.save()

            return {"message": "Sell callback received"}
