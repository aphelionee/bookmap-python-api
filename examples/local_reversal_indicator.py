"""Example indicator for detecting potential local market reversals.

The script listens to trades and depth updates to locate a large absorbed trade
at an extreme price level. If subsequent ticks show price and CVD stalling while
nearby liquidity remains strong, a point is placed on the chart signalling a
possible reversal.
"""

import time
from collections import deque
import bookmap as bm

# Window for analysis in seconds (5 minutes)
WINDOW_SECONDS = 300
# Number of recent trades to examine for stall phase
TICK_WINDOW = 20
# Threshold for a large trade volume
VOLUME_THRESHOLD = 100
# Number of depth levels to inspect when verifying nearby liquidity
DEPTH_LEVELS = 20

# alias -> instrument data
data_by_alias = {}


def handle_instrument(addon, alias, full_name, is_crypto, pips, size_mult,
                      inst_mult, features):
    data_by_alias[alias] = {
        "order_book": bm.create_order_book(),
        "trades": deque(),  # (timestamp, price, size, is_bid)
        "cvd": 0.0,
        "indicator_id": None,
        "pips": pips,
        "size_mult": size_mult,
    }
    req_id = 1
    bm.subscribe_to_depth(addon, alias, req_id); req_id += 1
    bm.subscribe_to_trades(addon, alias, req_id); req_id += 1
    bm.register_indicator(addon, alias, req_id, "LocalReversal", "BOTTOM")


def handle_indicator_response(addon, req_id, indicator_id):
    for data in data_by_alias.values():
        if data["indicator_id"] is None:
            data["indicator_id"] = indicator_id
            break


def handle_depth(addon, alias, is_bid, price, size):
    data = data_by_alias[alias]
    bm.on_depth(data["order_book"], is_bid, price, size)


def handle_trades(addon, alias, price_lvl, size_lvl, is_otc, is_bid, *_):
    data = data_by_alias[alias]
    ts = time.time()
    size = size_lvl / data["size_mult"]
    price = price_lvl * data["pips"]
    data["cvd"] += size if is_bid else -size
    data["trades"].append((ts, price, size, is_bid, data["cvd"]))

    # remove old trades
    while data["trades"] and data["trades"][0][0] < ts - WINDOW_SECONDS:
        data["trades"].popleft()

    if detect_reversal(data):
        ind = data["indicator_id"]
        if ind is not None:
            bm.add_point(addon, alias, ind, price)


def detect_reversal(data):
    trades = data["trades"]
    if len(trades) < TICK_WINDOW:
        return False

    # consider last N trades
    recent = list(trades)[-TICK_WINDOW:]
    first_cvd = recent[0][4]
    last_cvd = recent[-1][4]
    cvd_diff = last_cvd - first_cvd
    price_diff = recent[-1][1] - recent[0][1]

    if cvd_diff < 0 or price_diff < 0:
        return False

    # last trade details
    _, last_price, last_size, last_is_bid, _ = recent[-1]
    prices = [p for _, p, *_ in trades]
    high, low = max(prices), min(prices)

    if last_size < VOLUME_THRESHOLD:
        return False

    # no large trades of opposite side in recent window
    if last_is_bid:
        if last_price > low:
            return False
        for _, _, s, bid, _ in recent:
            if not bid and s >= VOLUME_THRESHOLD:
                return False
    else:
        if last_price < high:
            return False
        for _, _, s, bid, _ in recent:
            if bid and s >= VOLUME_THRESHOLD:
                return False

    bid_sum, ask_sum = bm.get_sum(data["order_book"], DEPTH_LEVELS)
    if last_is_bid:
        return ask_sum > bid_sum * 1.5
    else:
        return bid_sum > ask_sum * 1.5


def on_unsubscribe(addon, alias):
    data_by_alias.pop(alias, None)


if __name__ == "__main__":
    addon = bm.create_addon()
    bm.add_depth_handler(addon, handle_depth)
    bm.add_trades_handler(addon, handle_trades)
    bm.add_indicator_response_handler(addon, handle_indicator_response)
    bm.start_addon(addon, handle_instrument, on_unsubscribe)
    bm.wait_until_addon_is_turned_off(addon)
