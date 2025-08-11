# src/grid_strategy.py
"""
Basic grid strategy template.

Usage (example):
    python grid_strategy.py BTCUSDT 48000 52000 5 0.001

This will create 5 grid levels between 48000 and 52000 for quantity 0.001.
"""
import sys
from utils import get_client, validate_symbol, validate_positive_number, log_json
from binance.exceptions import BinanceAPIException
import numpy as np

def place_grid(symbol, low_price, high_price, steps, qty_per_order):
    client = get_client()
    if not validate_symbol(client, symbol):
        raise ValueError("Invalid symbol")

    low = validate_positive_number("low_price", low_price)
    high = validate_positive_number("high_price", high_price)
    steps = int(steps)
    qty = validate_positive_number("qty_per_order", qty_per_order)
    if high <= low:
        raise ValueError("high_price must be > low_price")
    if steps < 1:
        raise ValueError("steps must be >= 1")

    levels = np.linspace(low, high, steps+1)  # endpoints inclusive
    orders = []
    for p in levels:
        price = round(float(p), 2)
        try:
            # Place a limit order both buy and sell across grid — simple template
            buy_resp = client.futures_create_order(symbol=symbol, side='BUY', type='LIMIT', timeInForce='GTC', price=str(price), quantity=qty)
            sell_resp = client.futures_create_order(symbol=symbol, side='SELL', type='LIMIT', timeInForce='GTC', price=str(price), quantity=qty)
            orders.append({"price": price, "buy": buy_resp, "sell": sell_resp})
            log_json("info", "grid_order_placed", price=price)
        except BinanceAPIException as e:
            log_json("error", "grid_place_failed", error=str(e), price=price)
            raise
    return orders

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python grid_strategy.py SYMBOL LOW_PRICE HIGH_PRICE STEPS QTY")
        sys.exit(1)
    _, symbol, low, high, steps, qty = sys.argv
    place_grid(symbol, low, high, steps, qty)
