# src/advanced/oco.py
"""
Simple OCO emulation for Binance Futures:
1) Place initial opening order (market or limit)
2) Place two child orders: take-profit and stop-loss (reduceOnly)
3) Poll the order statuses and cancel the losing order when the other executes.

Usage (example):
    python oco.py BTCUSDT BUY 0.001 --tp 65000 --sl 58000
"""
import time
import sys
import argparse
from binance.exceptions import BinanceAPIException
from utils import get_client, validate_symbol, validate_positive_number, log_json

POLL_INTERVAL = 2.0  # seconds

def place_oco(symbol, side, quantity, tp_price, sl_price, open_type="MARKET"):
    client = get_client()
    if not validate_symbol(client, symbol):
        raise ValueError(f"Symbol {symbol} not found on Futures.")

    side = side.upper()
    qty = validate_positive_number("quantity", quantity)
    tp = validate_positive_number("tp_price", tp_price)
    sl = validate_positive_number("sl_price", sl_price)

    # 1) Place opening order
    try:
        if open_type == "MARKET":
            open_resp = client.futures_create_order(symbol=symbol, side=side, type='MARKET', quantity=qty)
        else:
            # For simplicity: limit open must be created separately via client.futures_create_order TYPE=LIMIT
            open_resp = client.futures_create_order(symbol=symbol, side=side, type='LIMIT', quantity=qty, price=str(tp))
        log_json("info", "oco_open_order", resp=open_resp)
    except BinanceAPIException as e:
        log_json("error", "oco_open_failed", error=str(e))
        raise

    # 2) Place TP and SL as reduceOnly orders (opposite side)
    opp_side = "SELL" if side == "BUY" else "BUY"
    try:
        tp_order = client.futures_create_order(
            symbol=symbol, side=opp_side, type='TAKE_PROFIT_LIMIT',
            timeInForce='GTC', price=str(tp), stopPrice=str(tp), quantity=qty, reduceOnly='true'
        )
        sl_order = client.futures_create_order(
            symbol=symbol, side=opp_side, type='STOP_MARKET',
            stopPrice=str(sl), closePosition='true', reduceOnly='true'
        )
        log_json("info", "oco_child_orders_placed", tp=tp_order, sl=sl_order)
    except BinanceAPIException as e:
        log_json("error", "oco_place_child_failed", error=str(e))
        raise

    tp_id = tp_order.get("orderId")
    sl_id = sl_order.get("orderId")

    # 3) Poll and cancel counterpart when one is FILLED
    try:
        while True:
            tp_status = client.futures_get_order(symbol=symbol, orderId=tp_id)
            sl_status = client.futures_get_order(symbol=symbol, orderId=sl_id)
            log_json("debug", "oco_poll", tp_status=tp_status.get("status"), sl_status=sl_status.get("status"))
            if tp_status.get("status") == "FILLED":
                # Cancel SL
                client.futures_cancel_order(symbol=symbol, orderId=sl_id)
                log_json("info", "oco_tp_filled", tp=tp_status)
                break
            if sl_status.get("status") in ("FILLED", "PARTIALLY_FILLED"):
                # Cancel TP
                client.futures_cancel_order(symbol=symbol, orderId=tp_id)
                log_json("info", "oco_sl_filled", sl=sl_status)
                break
            time.sleep(POLL_INTERVAL)
    except Exception as e:
        log_json("error", "oco_monitor_error", error=str(e))
        raise

    return {"tp": tp_status, "sl": sl_status}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol")
    parser.add_argument("side")
    parser.add_argument("quantity")
    parser.add_argument("--tp", required=True, help="take profit price")
    parser.add_argument("--sl", required=True, help="stop loss price")
    parser.add_argument("--open-type", default="MARKET", choices=["MARKET","LIMIT"])
    args = parser.parse_args()
    place_oco(args.symbol, args.side, args.quantity, args.tp, args.sl, args.open_type)
