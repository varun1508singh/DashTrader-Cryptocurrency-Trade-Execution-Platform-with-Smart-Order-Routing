import websocket
import threading
from time import sleep
import json
import logging
from random import seed
from random import randint



class kuCoinsocket:
    # Don't grow a table larger than this amount. Helps cap memory usage.
    MAX_LEN = 100

    def __init__(self, endpoint, token, topic, symbol, ping_interval, ping_timeout, api_key=None, api_secret=None):
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Initializing WebSocket.")
        self.token = token
        self.endpoint = endpoint
        self.symbol = symbol
        self.topic = topic
        self.ping_interval = ping_interval / 1000
        self.ping_timeout = ping_timeout / 1000
        self.data = []
        self.exited = False


        wsURL = self.endpoint + "?token=" + self.token + "&[connectId=1234]"
        self.logger.info("Connecting to %s" % wsURL)
        self.__connect(wsURL)
        self.logger.info('Connected to WS.')



    def exit(self):
        self.exited = True
        self.ws.close()

    def get_price(self):
        temp = self.data[-1]
        return {
            "bid": float(temp["bestBid"]),
            "ask": float(temp["bestAsk"])}

    def get_order_book(self):
        return self.data[:50]

    def __connect(self, wsURL):
        self.logger.debug("Starting thread")
        self.ws = websocket.WebSocketApp(wsURL,
                                         on_message=self.__on_message,
                                         on_close=self.__on_close,
                                         on_open=self.__on_open,
                                         on_error=self.__on_error,
                                         )

        self.wst = threading.Thread(
            target=lambda: self.ws.run_forever(None, None, self.ping_interval, self.ping_timeout))
        self.wst.daemon = True
        self.wst.start()
        self.logger.debug("Started thread")
        # Wait for connect before continuing
        conn_timeout = 5
        while (not self.ws.sock or not self.ws.sock.connected) and conn_timeout:
            sleep(1)
            conn_timeout -= 1
        if not conn_timeout:
            self.logger.error("Couldn't connect to WS! Exiting.")
            self.exit()
            raise websocket.WebSocketTimeoutException('Couldn\'t connect to WS! Exiting.')

    def __send_command(self):
        seed(1)
        value = randint(1000, 100000000)
        topic = self.topic + ":" + self.symbol
        data_send = {"id": value, "type": "subscribe", "topic": topic}
        self.ws.send(json.dumps(data_send))

    def __on_message(self, obj=None, message=None):

        # '''Handler for parsing WS messages.'''
        if message is None:
            message = obj

        message = json.loads(message)

        if message["type"] == "welcome":
            self.__send_command()
        else:
            message = message['data']
            self.data.append(message)
            if len(self.data) > self.MAX_LEN:
                self.data = self.data[:50]

    def __on_error(self, obj=None, error=None):
        if not self.exited:
            self.logger.error("Error : %s" % error)
            raise websocket.WebSocketException(error)

    def __on_open(self, message=None):
        print("socket open")
        self.logger.debug("Websocket Opened.")

    def __on_close(self, obj=None):
        self.logger.info('Websocket Closed')
