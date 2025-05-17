import requests

profit_usd = 1000  # 수익금
stake_amount = 9000338  # 실제 투자금
risk_level = "high"  # low, medium, high

r = requests.get(
    "http://localhost:5000/trade/callback/sell",
    params={
        "profit_usd": profit_usd,
        "stake_amount": stake_amount,
        "risk_level": risk_level,
    },
)

print(r.text)
