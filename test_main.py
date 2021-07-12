import BitMEXWebsocket
import logging
import kuCoinsocket
import config
from time import sleep
import KuCoinApi


def run():
    logger = setup_logger()
    client_kucoin = KuCoinApi.KuCoinApi(config.kucoin["api_key"], config.kucoin["api_secret"],
                                        config.kucoin["api_passphrase"],
                                        sandbox=False)
    x = client_kucoin.get_ws_endpoint()
    token = x['token']
    endpoint = x['instanceServers'][0]['endpoint']
    ping_interval = x['instanceServers'][0]['pingInterval']
    ping_timeout = x['instanceServers'][0]['pingTimeout']
    ws_kucoin = kuCoinsocket.kuCoinsocket(endpoint=endpoint, token=token, symbol="BTC-USDT", topic="/market/ticker",
                                          ping_interval=ping_interval, ping_timeout=ping_timeout)

    while True:
        sleep(1)
        print(ws_kucoin.get_price())



def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


if __name__ == "__main__":
    run()