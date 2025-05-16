from flask_restx import fields


def init_schemas(api):
    # Auth schemas
    auth_register = api.model(
        "AuthRegister",
        {
            "email": fields.String(required=True, description="User email"),
            "password": fields.String(required=True, description="User password"),
        },
    )

    auth_login = api.model(
        "AuthLogin",
        {
            "email": fields.String(required=True, description="User email"),
            "password": fields.String(required=True, description="User password"),
        },
    )

    auth_response = api.model(
        "AuthResponse", {"access_token": fields.String(description="JWT access token")}
    )

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

    # New schemas
    user_response = api.model(
        "UserResponse",
        {
            "message": fields.String(description="Response message"),
            "access_token": fields.String(description="JWT access token"),
            "user": fields.Nested(
                api.model(
                    "User",
                    {
                        "id": fields.String(description="User ID"),
                        "email": fields.String(description="User email"),
                        "created_at": fields.DateTime(description="User creation date"),
                        "bitcoin_balance": fields.Float(description="Bitcoin balance"),
                        "ethereum_balance": fields.Float(
                            description="Ethereum balance"
                        ),
                        "solana_balance": fields.Float(description="Solana balance"),
                    },
                )
            ),
        },
    )

    deposit_response = api.model(
        "DepositResponse",
        {
            "message": fields.String(description="Response message"),
            "deposit": fields.Nested(
                api.model(
                    "Deposit",
                    {
                        "user_id": fields.String(description="User ID"),
                        "coin_type": fields.String(
                            description="Type of cryptocurrency"
                        ),
                        "amount": fields.Float(description="Deposit amount"),
                        "new_balance": fields.Float(description="Updated balance"),
                    },
                )
            ),
        },
    )

    withdrawal_response = api.model(
        "WithdrawalResponse",
        {
            "message": fields.String(description="Response message"),
            "withdrawal": fields.Nested(
                api.model(
                    "Withdrawal",
                    {
                        "user_id": fields.String(description="User ID"),
                        "coin_type": fields.String(
                            description="Type of cryptocurrency"
                        ),
                        "amount": fields.Float(description="Withdrawal amount"),
                        "new_balance": fields.Float(description="Updated balance"),
                    },
                )
            ),
        },
    )

    balance_response = api.model(
        "BalanceResponse",
        {
            "coin_type": fields.String(description="Type of cryptocurrency"),
            "balance": fields.Float(description="Current balance"),
            "message": fields.String(description="Response message"),
        },
    )

    investment_response = api.model(
        "InvestmentResponse",
        {
            "message": fields.String(description="Response message"),
            "investment": fields.Nested(
                api.model(
                    "Investment",
                    {
                        "id": fields.String(description="Investment ID"),
                        "user_id": fields.String(description="User ID"),
                        "coin_type": fields.String(
                            description="Type of cryptocurrency (BTC/ETH/SOL)"
                        ),
                        "initial_amount": fields.Float(
                            description="Initial investment amount"
                        ),
                        "current_profit": fields.Float(
                            description="Current profit amount"
                        ),
                        "created_at": fields.DateTime(
                            description="Investment creation date"
                        ),
                        "updated_at": fields.DateTime(description="Last update date"),
                    },
                )
            ),
        },
    )

    investments_list_response = api.model(
        "InvestmentsListResponse",
        {
            "message": fields.String(description="Response message"),
            "investments": fields.List(
                fields.Nested(
                    api.model(
                        "Investment",
                        {
                            "id": fields.String(description="Investment ID"),
                            "user_id": fields.String(description="User ID"),
                            "coin_type": fields.String(
                                description="Type of cryptocurrency (BTC/ETH/SOL)"
                            ),
                            "initial_amount": fields.Float(
                                description="Initial investment amount"
                            ),
                            "current_profit": fields.Float(
                                description="Current profit amount"
                            ),
                            "created_at": fields.DateTime(
                                description="Investment creation date"
                            ),
                            "updated_at": fields.DateTime(
                                description="Last update date"
                            ),
                        },
                    )
                )
            ),
        },
    )

    transactions_response = api.model(
        "TransactionsResponse",
        {
            "transactions": fields.List(
                fields.Nested(
                    api.model(
                        "Transaction",
                        {
                            "type": fields.String(
                                description="Transaction type (deposit/withdrawal)"
                            ),
                            "coin_type": fields.String(
                                description="Type of cryptocurrency"
                            ),
                            "amount": fields.Float(description="Transaction amount"),
                            "status": fields.String(description="Transaction status"),
                            "created_at": fields.DateTime(
                                description="Transaction date"
                            ),
                            "tx_hash": fields.String(
                                description="Transaction hash (for deposits)"
                            ),
                            "destination_address": fields.String(
                                description="Destination address (for withdrawals)"
                            ),
                            "investment_id": fields.String(
                                description="Related investment ID"
                            ),
                        },
                    )
                )
            ),
            "message": fields.String(description="Response message"),
        },
    )

    return {
        "auth_register": auth_register,
        "auth_login": auth_login,
        "auth_response": auth_response,
        "wallet_response": wallet_response,
        "error_response": error_response,
        "user_response": user_response,
        "deposit_response": deposit_response,
        "withdrawal_response": withdrawal_response,
        "balance_response": balance_response,
        "transactions_response": transactions_response,
        "investment_response": investment_response,
        "investments_list_response": investments_list_response,
    }
