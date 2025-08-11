# src/market_orders.py
"""
Usage:
    python market_orders.py SYMBOL SIDE QUANTITY
Example:
    python market_orders.py BTCUSDT BUY 0.001
"""
import sys
from binance.client import Client
from binance.exceptions import BinanceAPIException
from utils import get_client, validate_symbol, validate_positive_number, log_json

def place_market_order(symbol, side, quantity, reduce_only=False):
    client = get_client()
    side = side.upper()
    if side not in ("BUY", "SELL"):
        raise ValueError("SIDE must be BUY or SELL")
    if not validate_symbol(client, symbol):
        raise ValueError(f"Symbol {symbol} not found on Futures.")

    qty = validate_positive_number("quantity", quantity)

    try:
        resp = client.futures_create_order(
            symbol=symbol,
            side=side,
            type='MARKET',
            quantity=qty,
            reduceOnly=str(reduce_only).lower()
        )
        log_json("info", "market_order_placed", symbol=symbol, side=side, quantity=qty, response=resp)
        print("Order response:", resp)
        return resp
    except BinanceAPIException as e:
        log_json("error", "market_order_failed", error=str(e), symbol=symbol, side=side, quantity=qty)
        raise

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python market_orders.py SYMBOL SIDE QUANTITY")
        sys.exit(1)
    _, symbol, side, quantity = sys.argv
    place_market_order(symbol, side, quantity)
