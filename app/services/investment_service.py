from typing import List, Optional, Dict
from datetime import datetime
from ..models.investment import Investment
from ..models.user import User


class InvestmentService:
    @staticmethod
    def create_investment(
        user: User, coin_type: str, initial_amount: float
    ) -> Investment:
        """새로운 투자를 생성합니다."""
        investment = Investment(
            user=user,
            coin_type=coin_type,
            initial_amount=initial_amount,
            current_profit=0.0,
        )
        # 초기 투자를 거래 내역에 추가
        investment.transactions.append(
            {
                "type": "deposit",
                "amount": initial_amount,
                "created_at": datetime.utcnow().isoformat(),
                "description": "Initial investment",
            }
        )
        investment.save()
        return investment

    @staticmethod
    def get_investment(investment_id: str) -> Optional[Investment]:
        """투자 ID로 투자 정보를 조회합니다."""
        try:
            return Investment.objects.get(id=investment_id)
        except Investment.DoesNotExist:
            return None

    @staticmethod
    def get_user_investments(user: User) -> List[Investment]:
        """사용자의 모든 투자 목록을 조회합니다."""
        return Investment.objects(user=user).order_by("-created_at")

    @staticmethod
    def update_investment_profit(
        investment_id: str, new_profit: float
    ) -> Optional[Investment]:
        """투자의 수익을 업데이트합니다."""
        try:
            investment = Investment.objects.get(id=investment_id)
            investment.current_profit = new_profit
            investment.save()
            return investment
        except Investment.DoesNotExist:
            return None

    @staticmethod
    def delete_investment(investment_id: str) -> bool:
        """투자를 삭제합니다."""
        try:
            investment = Investment.objects.get(id=investment_id)
            investment.delete()
            return True
        except Investment.DoesNotExist:
            return False

    @staticmethod
    def get_investments_by_coin_type(user: User, coin_type: str) -> List[Investment]:
        """특정 코인 타입의 투자 목록을 조회합니다."""
        return Investment.objects(user=user, coin_type=coin_type).order_by(
            "-created_at"
        )

    @staticmethod
    def add_deposit(
        investment_id: str, amount: float, description: str = "Additional deposit"
    ) -> Optional[Investment]:
        """투자에 추가 입금을 합니다."""
        try:
            investment = Investment.objects.get(id=investment_id)
            investment.initial_amount += amount
            investment.transactions.append(
                {
                    "type": "deposit",
                    "amount": amount,
                    "created_at": datetime.utcnow().isoformat(),
                    "description": description,
                }
            )
            investment.save()
            return investment
        except Investment.DoesNotExist:
            return None

    @staticmethod
    def make_withdrawal(
        investment_id: str, amount: float, description: str = "Withdrawal"
    ) -> Optional[Investment]:
        """투자에서 출금을 합니다."""
        try:
            investment = Investment.objects.get(id=investment_id)
            if investment.initial_amount < amount:
                raise ValueError("Insufficient funds for withdrawal")

            investment.initial_amount -= amount
            investment.transactions.append(
                {
                    "type": "withdrawal",
                    "amount": amount,
                    "created_at": datetime.utcnow().isoformat(),
                    "description": description,
                }
            )
            investment.save()
            return investment
        except Investment.DoesNotExist:
            return None
        except ValueError as e:
            raise e
