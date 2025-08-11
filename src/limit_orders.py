# src/limit_orders.py
"""
Usage:
    python limit_orders.py SYMBOL SIDE QUANTITY PRICE
Example:
    python limit_orders.py BTCUSDT SELL 0.001 60000
"""
import sys
from binance.exceptions import BinanceAPIException
from utils import get_client, validate_symbol, validate_positive_number, log_json

def place_limit_order(symbol, side, quantity, price, timeInForce="GTC"):
    client = get_client()
    side = side.upper()
    if side not in ("BUY", "SELL"):
        raise ValueError("SIDE must be BUY or SELL")
    if not validate_symbol(client, symbol):
        raise ValueError(f"Symbol {symbol} not found on Futures.")

    qty = validate_positive_number("quantity", quantity)
    pr = validate_positive_number("price", price)

    try:
        resp = client.futures_create_order(
            symbol=symbol,
            side=side,
            type='LIMIT',
            timeInForce=timeInForce,
            quantity=qty,
            price=str(pr)
        )
        log_json("info", "limit_order_placed", symbol=symbol, side=side, quantity=qty, price=pr, response=resp)
        print("Order response:", resp)
        return resp
    except BinanceAPIException as e:
        log_json("error", "limit_order_failed", error=str(e), symbol=symbol, side=side, quantity=qty, price=pr)
        raise

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python limit_orders.py SYMBOL SIDE QUANTITY PRICE")
        sys.exit(1)
    _, symbol, side, quantity, price = sys.argv
    place_limit_order(symbol, side, quantity, price)
