import BitMEXWebsocket
import logging
# from kucoin.client import Client
import kuCoinsocket
import config
from time import sleep
import KuCoinApi
import binance_connections
import bitmexAPI


# Basic use of websocket.
def run():
    # logger = setup_logger()
    # Instantiating the WS will make it connect. Be sure to add your api_key/api_secret.
    # client_kucoin = KuCoinApi.KuCoinApi(config.kucoin["api_key"], config.kucoin["api_secret"],
    #                                     config.kucoin["api_passphrase"],
    #                                     sandbox=False)
    # x = client_kucoin.get_ws_endpoint()
    # token = x['token']
    # endpoint = x['instanceServers'][0]['endpoint']
    # ping_interval = x['instanceServers'][0]['pingInterval']
    # ping_timeout = x['instanceServers'][0]['pingTimeout']
    # ws_kucoin = kuCoinsocket.kuCoinsocket(endpoint=endpoint, token=token, symbol="BTC-USDT", topic="/market/ticker",
    #                                       ping_interval=ping_interval, ping_timeout=ping_timeout)

    ws_bitmex = BitMEXWebsocket.BitMEXWebsocket(endpoint=config.bitmex["endpoint_actual"], symbol="XBTUSD",
                                                api_key=config.bitmex["api_key"],
                                                api_secret=config.bitmex["api_secret"])
    #
    # ws_bitmex.get_instrument()

    while ws_bitmex.ws.sock.connected:
        # sleep(2)
        print(ws_bitmex.get_price())
        # logger.info("Bitmex: %s" % ws_bitmex.market_depth())
        # logger.info("Bitmex: %s" % ws_bitmex.data['quote'])
        # logger.info("Bitmex: %s" % ws_bitmex.get_price())

        # logger.info("Bitmex: %s" % ws_bitmex.get_ticker())
        # logger.info("Bitmex: %s" % ws_bitmex.get_data_temp())
        # logger.info("Kucoin: %s" % ws_kucoin.get_price())


def setup_logger():
    # Prints logger info to terminal
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Change this to DEBUG if you want a lot more info
    ch = logging.StreamHandler()
    # create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    # add formatter to ch
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


if __name__ == "__main__":
    client_kucoin = KuCoinApi.KuCoinApi(config.kucoin["api_key"], config.kucoin["api_secret"],
                                        config.kucoin["api_passphrase"],
                                        sandbox=True)
    x = client_kucoin.get_ws_endpoint()
    token = x['token']
    endpoint = x['instanceServers'][0]['endpoint']
    ping_interval = x['instanceServers'][0]['pingInterval']
    ping_timeout = x['instanceServers'][0]['pingTimeout']
    ws_kucoin = kuCoinsocket.kuCoinsocket(endpoint=endpoint, token=token, symbol="BTC-USDT", topic="/market/ticker",
                                          ping_interval=ping_interval, ping_timeout=ping_timeout)

    client_binance = binance_connections.binance_connections(api_key=config.binance["api_key"],
                                                             api_secret=config.binance["api_secret"])
    sleep(2)

    ws_bitmex = BitMEXWebsocket.BitMEXWebsocket(endpoint=config.bitmex["endpoint_actual"], symbol="XBTUSD",
                                                api_key=config.bitmex["api_key"],
                                                api_secret=config.bitmex["api_secret"])

    print(bitmexAPI.create_order(symbol="BTC/USD", side='sell', quantity=1))
    # print(client_binance.create_order(symbol='ADAUSDT', quantity=15, side="SELL", type="market"))
    bid = {'binance': None, 'kucoin': None, 'bitmex': None}
    ask = {'binance': None, 'kucoin': None, 'bitmex': None}
    binance_data = client_binance.get_order_book(symbol='BTCUSDT')
    print(ws_kucoin.get_price())

    kucoin_data = ws_kucoin.get_order_book()
    bitmex_data = ws_bitmex.market_depth()
    binance_bids = binance_data['bids']
    binance_asks = binance_data['asks']
    amount, weights = 0, 0
    for element in binance_bids:
        amount = amount + float(element[0]) * float(element[1])
        weights = weights + float(element[1])
    if weights == 0:
        weights = 1
    bid['binance'] = float(amount / weights)
    amount, weights = 0, 0
    for element in binance_asks:
        amount = amount + float(element[0]) * float(element[1])
        weights = weights + float(element[1])
    ask['binance'] = float(amount / weights)

    bid_amount, ask_amount, bid_weights, ask_weights = 0, 0, 0, 0
    for element in kucoin_data:
        bid_amount += float(element["bestBid"]) * float(element['bestBidSize'])
        ask_amount += float(element['bestAsk']) * float(element['bestAskSize'])
        bid_weights += float(element['bestBidSize'])
        ask_weights += float(element['bestAskSize'])
    bid['kucoin'] = float(bid_amount / bid_weights)
    ask['kucoin'] = float(ask_amount / ask_weights)

    bid_amount, ask_amount, bid_weights, ask_weights = 0, 0, 0, 0
    for element in bitmex_data:
        bid_amount += float(element["bidPrice"]) * float(element['bidSize'])
        ask_amount += float(element['askPrice']) * float(element['askSize'])
        bid_weights += float(element['bidSize'])
        ask_weights += float(element['askSize'])
    bid['bitmex'] = float(bid_amount / bid_weights)
    ask['bitmex'] = float(ask_amount / ask_weights)
    print(bid, ask)
    # binanace_bids,binance_asks = client_binance.get_order_book(symbol='XRPUSDT')['bids']

    # print(client_binance.get_exchange_info())

    # print(client_kucoin.create_market_order(side="buy", symbol="BTC-USDT", size=0.0001))
    # x = client.get_ws_endpoint()
    # run()
