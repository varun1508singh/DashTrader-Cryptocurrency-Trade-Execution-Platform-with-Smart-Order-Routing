import ccxt
import config


def create_order(symbol, side, quantity, type="market"):
    exchange = ccxt.bitmex({
        'apiKey': config.bitmex['api_key'],
        'secret': config.bitmex['api_secret'],
        'enableRateLimit': True
    })
    # if 'test' in exchange.urls:
    exchange.urls['api'] = exchange.urls['test']  # ←----- switch the base URL to testnet
    return exchange.create_order(symbol, type, side, quantity)
