from .ft_rest_client import FtRestClient
import sys
import os
import json

HOSTNAME = "localhost"


def turn_on_freqtrade_bot(risk_level: str):
    """
    Warning: DO NOT use this function when deploy service in a multiprocess environment.
    Such as: Gunicorn, etc...
    """
    if risk_level not in ["low", "medium", "high"]:
        raise ValueError("Invalid risk level")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(
        current_dir, "freqtrade_configs", f"config_{risk_level}_risk.json"
    )

    import subprocess

    subprocess.Popen(
        ["freqtrade", "trade", "--config", config_path, "--dry-run"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )


def get_freqtrade_bot(risk_level: str) -> FtRestClient:
    if risk_level not in ["low", "medium", "high"]:
        raise ValueError("Invalid risk level")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(
        current_dir, "freqtrade_configs", f"config_{risk_level}_risk.json"
    )

    with open(config_path, "r") as f:
        config = json.load(f)

    server_hostname = config["api_server"]["listen_ip_address"]
    server_port = config["api_server"]["listen_port"]
    username = config["api_server"]["username"]
    password = config["api_server"]["password"]

    server_url = f"http://{server_hostname}:{server_port}"

    rest_client = FtRestClient(server_url, username, password)
    return rest_client


def get_freqtrade_daily_profit(risk_level: str) -> dict:
    rest_client = get_freqtrade_bot(risk_level)
    return rest_client.daily()


def get_freqtrade_weekly_profit(risk_level: str) -> dict:
    rest_client = get_freqtrade_bot(risk_level)
    return rest_client.weekly()


def get_freqtrade_monthly_profit(risk_level: str) -> dict:
    rest_client = get_freqtrade_bot(risk_level)
    return rest_client.monthly()


def get_freqtrade_profit(risk_level: str) -> dict:
    rest_client = get_freqtrade_bot(risk_level)
    return rest_client.profit()
