import BitMEXWebsocket
import logging
import kuCoinsocket
import config
from time import sleep
import KuCoinApi


def bestBidAsk(symbol):
    logger = setup_logger()
    bitmap = {
        "BTC_USD": "XBTUSD",
        "ETH_USD": "ETHUSD",
        "XRP_USD": "XRPUSD",
        "ADA_USD": "ADAUSDT",
        "LTC_USD": "LTCUSD",
    }
    kumap = {
        "BTC_USD": "BTC-USDT",
        "ETH_USD": "ETH-USDT",
    }
    client_kucoin = KuCoinApi.KuCoinApi(config.kucoin["api_key"], config.kucoin["api_secret"],
                                        config.kucoin["api_passphrase"],
                                        sandbox=True)
    x = client_kucoin.get_ws_endpoint()

    if symbol == "BTC_USD" or symbol == "ETH_USD":
        ws_kucoin = kuCoinsocket.kuCoinsocket(endpoint=x['instanceServers'][0]['endpoint'], token=x['token'],
                                              symbol=kymap[symbol], topic="/market/ticker")
        ws_bitmex = BitMEXWebsocket.BitMEXWebsocket(endpoint=config.bitmex["endpoint"], symbol=bitmap[symbol],
                                                    api_key=config.bitmex["api_key"],
                                                    api_secret=config.bitmex["api_secret"])
        sleep(3)

        bit = ws_bitmex.get_price()
        ku = ws_kucoin.get_price()
        return {
            "bid": bit['bid'] if bit['bid'] > ku['bid'] else ku['bid'],
            "ask": bit['ask'] if bit['ask'] < ku['ask'] else ku['ask']
        }
    else:
        ws_bitmex = BitMEXWebsocket.BitMEXWebsocket(endpoint=config.bitmex["endpoint"], symbol=bitmap[symbol],
                                                    api_key=config.bitmex["api_key"],
                                                    api_secret=config.bitmex["api_secret"])
        bit = ws_bitmex.get_price()
        return {
            "bid": bit['bid'],
            "ask": bit['ask']
        }
#
# def create_order():


def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


if __name__ == "__main__":
    print(bestBidAsk("ADA_USD"))
