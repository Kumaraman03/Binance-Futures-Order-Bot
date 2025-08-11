# src/advanced/twap.py
"""
Simple TWAP implementation:
Usage:
    python twap.py BTCUSDT BUY 0.01 --slices 5 --duration 60
This will split 0.01 into 5 equal trades executed over 60 seconds.
"""
import time
import sys
import argparse
from utils import get_client, validate_symbol, validate_positive_number, log_json
from binance.exceptions import BinanceAPIException

def place_twap(symbol, side, quantity, slices=5, duration=60, sleep_override=None):
    client = get_client()
    if not validate_symbol(client, symbol):
        raise ValueError(f"Symbol {symbol} not on Futures.")
    qty = validate_positive_number("quantity", quantity)
    slices = int(slices)
    if slices < 1:
        raise ValueError("slices must be >= 1")
    interval = duration / slices
    slice_qty = round(qty / slices, 8)  # rounding to reasonable precision

    log_json("info", "twap_start", symbol=symbol, side=side, total_qty=qty, slices=slices, interval=interval, slice_qty=slice_qty)
    results = []
    for i in range(slices):
        try:
            resp = client.futures_create_order(
                symbol=symbol,
                side=side.upper(),
                type='MARKET',
                quantity=slice_qty
            )
            log_json("info", "twap_slice_fired", index=i+1, resp=resp)
            results.append(resp)
        except BinanceAPIException as e:
            log_json("error", "twap_slice_failed", slice=i+1, error=str(e))
            raise
        # allow a short-circuit for tests
        if sleep_override is not None:
            time.sleep(sleep_override)
        else:
            time.sleep(interval)
    log_json("info", "twap_complete", count=len(results))
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol")
    parser.add_argument("side")
    parser.add_argument("quantity")
    parser.add_argument("--slices", type=int, default=5)
    parser.add_argument("--duration", type=int, default=300, help="total duration in seconds")
    args = parser.parse_args()
    place_twap(args.symbol, args.side, args.quantity, args.slices, args.duration)
