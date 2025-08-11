# src/utils.py
import os
import time
import logging
import json
from logging.handlers import RotatingFileHandler
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException

LOGFILE = os.path.join(os.path.dirname(__file__), "bot.log")

def setup_logger():
    logger = logging.getLogger("binance_bot")
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        # Rotating file handler
        fh = RotatingFileHandler(LOGFILE, maxBytes=5_000_000, backupCount=3, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fmt = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
        fh.setFormatter(fmt)
        logger.addHandler(fh)

        sh = logging.StreamHandler()
        sh.setLevel(logging.INFO)
        sh.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
        logger.addHandler(sh)

    return logger

logger = setup_logger()

def log_json(level, event, **kwargs):
    """
    Write structured JSON log line to logfile via logger.
    """
    entry = {"ts": int(time.time()), "event": event}
    entry.update(kwargs)
    if level == "info":
        logger.info(json.dumps(entry))
    elif level == "error":
        logger.error(json.dumps(entry))
    else:
        logger.debug(json.dumps(entry))

def get_client():
    """
    Create and return a python-binance Client configured via environment variables.
    Use BINANCE_API_KEY and BINANCE_API_SECRET, and BINANCE_FUTURES_TESTNET=true to enable testnet.
    """
    api_key = os.environ.get("BINANCE_API_KEY")
    api_secret = os.environ.get("BINANCE_API_SECRET")
    if not api_key or not api_secret:
        raise EnvironmentError("Please set BINANCE_API_KEY and BINANCE_API_SECRET environment variables.")

    testnet_flag = os.environ.get("BINANCE_FUTURES_TESTNET", "false").lower() in ("1", "true", "yes")

    client = Client(api_key, api_secret)
    if testnet_flag:
        # python-binance does not have an explicit constructor testnet flag for futures,
        # but we can switch the base URL for testing. The user should ensure they use
        # the futures testnet base URL. 
        client.FUTURES_URL = "https://testnet.binancefuture.com"  # informational; libs vary
        log_json("info", "client_init", mode="testnet")
    else:
        log_json("info", "client_init", mode="live")
    return client

def validate_symbol(client, symbol):
    """
    Validate a symbol exists on Futures exchange.
    """
    try:
        info = client.futures_exchange_info()
        symbols = {s["symbol"] for s in info.get("symbols", [])}
        return symbol in symbols
    except (BinanceAPIException, BinanceRequestException) as e:
        log_json("error", "validate_symbol_failed", error=str(e))
        raise

def validate_positive_number(name, value):
    try:
        v = float(value)
        if v <= 0:
            raise ValueError(f"{name} must be positive.")
        return v
    except ValueError as e:
        raise ValueError(f"{name} invalid: {e}")
