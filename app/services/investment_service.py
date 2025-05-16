from typing import List, Optional, Dict
from datetime import datetime
from ..models.investment import Investment
from ..models.user import User
from .binance_service import BinanceService


class InvestmentService:
    @staticmethod
    def create_investment(
        name: str,
        coin_type: str,
        risk_level: str,
        initial_amount: float,
        internal_position: int,
        user: User,
    ) -> Investment:
        """새로운 투자를 생성합니다."""
        # 동일한 name과 internal_position을 가진 투자가 있는지 확인
        existing_investment = None

        for inv in user.investments:
            if inv.internal_position == internal_position:
                existing_investment = inv
                break

        if existing_investment:
            raise ValueError("이미 동일한 이름과 포지션을 가진 투자가 존재합니다.")

        # 사용자의 USDT 잔액 확인
        if user.usdt_balance < initial_amount:
            raise ValueError("잔액이 부족합니다.")

        # USDT 잔액 차감
        user.usdt_balance -= initial_amount
        user.save()

        # 현재 BTC 가격 가져오기
        current_price = BinanceService.get_btc_price()
        if current_price is None:
            raise ValueError("현재 BTC 가격을 가져올 수 없습니다.")

        investment = Investment(
            name=name,
            coin_type=coin_type,
            risk_level=risk_level,
            initial_amount=initial_amount,
            entry_price_usdt=current_price,
            current_profit=0.0,
            internal_position=internal_position,
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
    def delete_investment(investment_id: str, user: User) -> bool:
        """투자를 삭제합니다."""
        try:
            investment = Investment.objects.get(id=investment_id)

            # 투자 금액을 사용자의 USDT 잔액에 환불
            user.usdt_balance += investment.initial_amount
            user.save()

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

    @staticmethod
    def get_all_investments() -> List[Investment]:
        """모든 투자 목록을 조회합니다."""
        return list(Investment.objects.all())

    @staticmethod
    def get_investments_by_risk_level(risk_level: str) -> List[Investment]:
        """특정 위험 수준의 투자 목록을 조회합니다."""
        return list(Investment.objects(risk_level=risk_level))

    @staticmethod
    def update_investment(
        investment_id: str,
        name: Optional[str] = None,
        coin_type: Optional[str] = None,
        risk_level: Optional[str] = None,
        initial_amount: Optional[float] = None,
        current_profit: Optional[float] = None,
    ) -> Optional[Investment]:
        investment = Investment.objects(id=investment_id).first()
        if not investment:
            return None

        if name is not None:
            investment.name = name
        if coin_type is not None:
            investment.coin_type = coin_type
        if risk_level is not None:
            investment.risk_level = risk_level
        if initial_amount is not None:
            investment.initial_amount = initial_amount
        if current_profit is not None:
            investment.current_profit = current_profit

        investment.save()
        return investment

    @staticmethod
    def add_transaction(
        investment_id: str,
        transaction_type: str,
        amount: float,
        price: float,
        created_at: Optional[datetime] = None,
    ) -> Optional[Investment]:
        investment = Investment.objects(id=investment_id).first()
        if not investment:
            return None

        transaction = {
            "type": transaction_type,
            "amount": amount,
            "price": price,
            "created_at": created_at or datetime.utcnow(),
        }

        investment.transactions.append(transaction)
        investment.save()
        return investment

    @staticmethod
    def get_investment_by_email_and_position(
        email: str, internal_position: int
    ) -> Optional[Investment]:
        """사용자 이메일과 internal_position으로 투자 정보를 조회합니다."""
        try:
            user = User.objects.get(email=email)
            return Investment.objects.get(
                user=user, internal_position=internal_position
            )
        except (User.DoesNotExist, Investment.DoesNotExist):
            return None
