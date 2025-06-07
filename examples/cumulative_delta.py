import bookmap as bm

alias_to_cvd = {}
alias_to_indicator_id = {}
request_ids = {}
next_req_id = 1


def handle_subscribe_instrument(addon, alias, full_name, is_crypto, pips,
                                size_multiplier, instrument_multiplier,
                                supported_features):
    global next_req_id
    alias_to_cvd[alias] = 0
    request_ids[alias] = next_req_id
    bm.register_indicator(addon, alias, next_req_id,
                          "Cumulative Delta", "BOTTOM")
    next_req_id += 1


def handle_indicator_response(addon, request_id, indicator_id):
    for alias, req in request_ids.items():
        if req == request_id:
            alias_to_indicator_id[alias] = indicator_id
            break


def handle_trades(addon, alias, price, size, is_otc, is_bid,
                  is_execution_start, is_execution_end,
                  aggressor_order_id, passive_order_id):
    if alias not in alias_to_indicator_id:
        return
    if is_bid:
        alias_to_cvd[alias] += size
    else:
        alias_to_cvd[alias] -= size
    bm.add_point(addon, alias, alias_to_indicator_id[alias],
                 alias_to_cvd[alias])


def handle_unsubscribe_instrument(addon, alias):
    alias_to_cvd.pop(alias, None)
    alias_to_indicator_id.pop(alias, None)
    request_ids.pop(alias, None)


if __name__ == "__main__":
    addon = bm.create_addon()
    bm.add_indicator_response_handler(addon, handle_indicator_response)
    bm.add_trades_handler(addon, handle_trades)
    bm.start_addon(addon, handle_subscribe_instrument,
                   handle_unsubscribe_instrument)
    bm.wait_until_addon_is_turned_off(addon)
