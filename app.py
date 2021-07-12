# -*- coding: utf-8 -*-
import plotly.subplots
import BitMEXWebsocket
import bitmexAPI
import binance_connections
import kuCoinsocket
import config
from time import sleep
import KuCoinApi
import json
import datetime
import pathlib
import math
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)

server = app.server
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()
bitmap = {
    "BTC_USD": "XBTUSD",
    "ETH_USD": "ETHUSD",
    "XRP_USD": "XRPUSD",
    "ADA_USD": "ADAUSD",
    "LTC_USD": "LTCUSD",
}

global_orders = []
binance_map = {
    "BTC_USD": "BTCUSDT",
    "ETH_USD": "ETHUSDT",
    "XRP_USD": "XRPUSDT",
    "ADA_USD": "ADAUSDT",
    "LTC_USD": "LTCUSDT",
}

ccxt = {
    "BTC_USD": "BTC/USD",
    "ETH_USD": "ETH/USD",
    "XRP_USD": "XRP/USD",
    "ADA_USD": "ADA/USD",
    "LTC_USD": "LTC/USD",
}
socket_dict = {}

kumap = {
    "BTC_USD": "BTC-USDT",
    "ETH_USD": "ETH-USDT",
    "ADA_USD": "ADA-USDT",
    "XRP_USD": "XRP-USDT",
    "LTC_USD": "LTC-USDT",
}


def get_bitmex_price(symbol):
    bitmex_data = socket_dict[symbol + 'bitmex'].market_depth()
    bid_amount, ask_amount, bid_weights, ask_weights = 0, 0, 0, 0
    for element in bitmex_data:
        bid_amount += float(element["bidPrice"]) * float(element['bidSize'])
        ask_amount += float(element['askPrice']) * float(element['askSize'])
        bid_weights += float(element['bidSize'])
        ask_weights += float(element['askSize'])
    return {'bid': float(bid_amount / bid_weights), 'ask': float(ask_amount / ask_weights)}


def get_kucoin_price(symbol):
    bid_amount, ask_amount, bid_weights, ask_weights = 0, 0, 0, 0
    kucoin_data = socket_dict[symbol + 'kucoin'].get_order_book()
    for element in kucoin_data:
        bid_amount += float(element["bestBid"]) * float(element['bestBidSize'])
        ask_amount += float(element['bestAsk']) * float(element['bestAskSize'])
        bid_weights += float(element['bestBidSize'])
        ask_weights += float(element['bestAskSize'])
    return {'bid': float(bid_amount / bid_weights), 'ask': float(ask_amount / ask_weights)}


def update_orders_view():
    if global_orders:
        return str(global_orders[-1])
    else:
        return "No Orders Placed Yet"


def get_binance_price(symbol):
    binance_data = client_binance.get_order_book(symbol=binance_map[symbol])
    binance_bids = binance_data['bids']
    binance_asks = binance_data['asks']
    amount, weights = 0, 0
    for element in binance_bids:
        amount = amount + float(element[0]) * float(element[1])
        weights = weights + float(element[1])
    if weights == 0:
        weights = 1
    bid_bin = float(amount / weights)
    amount, weights = 0, 0
    for element in binance_asks:
        amount = amount + float(element[0]) * float(element[1])
        weights = weights + float(element[1])

    ask_bin = float(amount / weights)
    return {'bid': bid_bin, 'ask': ask_bin}


# Loading historical tick data
currency_pair_data = {
    "BTC_USD": pd.read_csv(
        DATA_PATH.joinpath("BTC.csv"), index_col=1, parse_dates=["Date"]
    ),
    "ETH_USD": pd.read_csv(
        DATA_PATH.joinpath("ETH.csv"), index_col=1, parse_dates=["Date"]
    ),
    "XRP_USD": pd.read_csv(
        DATA_PATH.joinpath("XRP.csv"), index_col=1, parse_dates=["Date"]
    ),
    "LTC_USD": pd.read_csv(
        DATA_PATH.joinpath("LTC.csv"), index_col=1, parse_dates=["Date"]
    ),

}

# Currency pairs

currencies = ["BTC_USD", "ETH_USD", "XRP_USD", "LTC_USD"]


# Returns dataset for currency pair with nearest datetime to current time
def first_ask_bid(currency_pair, t):
    return [[currency_pair, 0.000, 0.000], 1]  # returns dataset row and index of row


# Creates HTML Bid and Ask (Buy/Sell buttons)
def get_row(data):
    index = data[1]
    current_row = data[0]

    return html.Div(
        children=[
            # Summary
            html.Div(
                id=current_row[0] + "summary",
                className="row summary",
                n_clicks=0,
                children=[
                    html.Div(
                        id=current_row[0] + "row",
                        className="row",
                        children=[
                            html.P(
                                current_row[0],  # currency pair name
                                id=current_row[0],
                                className="three-col",
                            ),
                            html.P(
                                round(current_row[1], 5),  # Bid value
                                id=current_row[0] + "bid",
                                className="three-col",
                            ),
                            html.P(
                                round(current_row[2], 5),  # Ask value
                                id=current_row[0] + "ask",
                                className="three-col",
                            ),
                            html.Div(
                                index,
                                id=current_row[0]
                                   + "index",  # we save index of row in hidden div
                                style={"display": "none"},
                            ),
                        ],
                    )
                ],
            ),
            # Contents
            html.Div(
                id=current_row[0] + "contents",
                className="row details",
                children=[
                    # Button for buy/sell modal
                    html.Div(
                        className="button-buy-sell-chart",
                        children=[
                            html.Button(
                                id=current_row[0] + "Buy",
                                children="Buy/Sell",
                                n_clicks=0,
                            )
                        ],
                    ),
                    # Button to display currency pair chart
                    html.Div(
                        className="button-buy-sell-chart-right",
                        children=[
                            html.Button(
                                id=current_row[0] + "Button_chart",
                                children="Chart",
                                n_clicks=1
                                if current_row[0] in ["BTC_USD", "ETH_USD"]
                                else 0,
                            )
                        ],
                    ),
                ],
            ),
        ]
    )


# color of Bid & Ask rates
def get_color(a, b):
    if a == b:
        return "white"
    elif a > b:
        return "#45df7e"
    else:
        return "#da5657"


# Replace ask_bid row for currency pair with colored values
def replace_row(currency_pair, index, bid, ask):
    index = index + 1  # index of new data row
    bit = socket_dict[currency_pair + "bitmex"].get_price()
    if currency_pair == "BTC_USD" or currency_pair == "ETH_USD":
        ku = socket_dict[currency_pair + "kucoin"].get_price()
        new_row = {"bid": bit['bid'] if bit['bid'] > ku['bid'] else ku['bid'],
                   "ask": bit['ask'] if bit['ask'] < ku['ask'] else ku['ask']}
    else:
        new_row = {"bid": bit['bid'], "ask": bit["ask"]}

    return [
        html.P(
            currency_pair, id=currency_pair, className="three-col"  # currency pair name
        ),
        html.P(
            round(new_row["bid"], 5),  # Bid value
            id=currency_pair + "bid",
            className="three-col",
            style={"color": get_color(new_row["bid"], bid)},
        ),
        html.P(
            round(new_row["ask"], 5),  # Ask value
            className="three-col",
            id=currency_pair + "ask",
            style={"color": get_color(new_row["ask"], ask)},
        ),
        html.Div(
            index, id=currency_pair + "index", style={"display": "none"}
        ),  # save index in hidden div
    ]


# Display big numbers in readable format
def human_format(num):
    try:
        num = float(num)
        # If value is 0
        if num == 0:
            return 0
        # Else value is a number
        if num < 1000000:
            return num
        magnitude = int(math.log(num, 1000))
        mantissa = str(int(num / (1000 ** magnitude)))
        return mantissa + ["", "K", "M", "G", "T", "P"][magnitude]
    except:
        return num


####### STUDIES TRACES ######

# Moving average
def moving_average_trace(df, fig):
    df2 = df.rolling(window=5).mean()
    trace = go.Scatter(
        x=df2.index, y=df2["close"], mode="lines", showlegend=False, name="MA"
    )
    fig.append_trace(trace, 1, 1)  # plot in first row
    return fig


# Exponential moving average
def e_moving_average_trace(df, fig):
    df2 = df.rolling(window=20).mean()
    trace = go.Scatter(
        x=df2.index, y=df2["close"], mode="lines", showlegend=False, name="EMA"
    )
    fig.append_trace(trace, 1, 1)  # plot in first row
    return fig


# Bollinger Bands
def bollinger_trace(df, fig, window_size=10, num_of_std=5):
    price = df["close"]
    rolling_mean = price.rolling(window=window_size).mean()
    rolling_std = price.rolling(window=window_size).std()
    upper_band = rolling_mean + (rolling_std * num_of_std)
    lower_band = rolling_mean - (rolling_std * num_of_std)

    trace = go.Scatter(
        x=df.index, y=upper_band, mode="lines", showlegend=False, name="BB_upper"
    )

    trace2 = go.Scatter(
        x=df.index, y=rolling_mean, mode="lines", showlegend=False, name="BB_mean"
    )

    trace3 = go.Scatter(
        x=df.index, y=lower_band, mode="lines", showlegend=False, name="BB_lower"
    )

    fig.append_trace(trace, 1, 1)  # plot in first row
    fig.append_trace(trace2, 1, 1)  # plot in first row
    fig.append_trace(trace3, 1, 1)  # plot in first row
    return fig


# Accumulation Distribution
def accumulation_trace(df):
    df["volume"] = ((df["close"] - df["low"]) - (df["high"] - df["close"])) / (
            df["high"] - df["low"]
    )
    trace = go.Scatter(
        x=df.index, y=df["volume"], mode="lines", showlegend=False, name="Accumulation"
    )
    return trace


# Commodity Channel Index
def cci_trace(df, ndays=5):
    TP = (df["high"] + df["low"] + df["close"]) / 3
    CCI = pd.Series(
        (TP - TP.rolling(window=10, center=False).mean())
        / (0.015 * TP.rolling(window=10, center=False).std()),
        name="cci",
    )
    trace = go.Scatter(x=df.index, y=CCI, mode="lines", showlegend=False, name="CCI")
    return trace


# Price Rate of Change
def roc_trace(df, ndays=5):
    N = df["close"].diff(ndays)
    D = df["close"].shift(ndays)
    ROC = pd.Series(N / D, name="roc")
    trace = go.Scatter(x=df.index, y=ROC, mode="lines", showlegend=False, name="ROC")
    return trace


# Stochastic oscillator %K
def stoc_trace(df):
    SOk = pd.Series((df["close"] - df["low"]) / (df["high"] - df["low"]), name="SO%k")
    trace = go.Scatter(x=df.index, y=SOk, mode="lines", showlegend=False, name="SO%k")
    return trace


# Momentum
def mom_trace(df, n=5):
    M = pd.Series(df["close"].diff(n), name="Momentum_" + str(n))
    trace = go.Scatter(x=df.index, y=M, mode="lines", showlegend=False, name="MOM")
    return trace


# Pivot points
def pp_trace(df, fig):
    PP = pd.Series((df["high"] + df["low"] + df["close"]) / 3)
    R1 = pd.Series(2 * PP - df["low"])
    S1 = pd.Series(2 * PP - df["high"])
    R2 = pd.Series(PP + df["high"] - df["low"])
    S2 = pd.Series(PP - df["high"] + df["low"])
    R3 = pd.Series(df["high"] + 2 * (PP - df["low"]))
    S3 = pd.Series(df["low"] - 2 * (df["high"] - PP))
    trace = go.Scatter(x=df.index, y=PP, mode="lines", showlegend=False, name="PP")
    trace1 = go.Scatter(x=df.index, y=R1, mode="lines", showlegend=False, name="R1")
    trace2 = go.Scatter(x=df.index, y=S1, mode="lines", showlegend=False, name="S1")
    trace3 = go.Scatter(x=df.index, y=R2, mode="lines", showlegend=False, name="R2")
    trace4 = go.Scatter(x=df.index, y=S2, mode="lines", showlegend=False, name="S2")
    trace5 = go.Scatter(x=df.index, y=R3, mode="lines", showlegend=False, name="R3")
    trace6 = go.Scatter(x=df.index, y=S3, mode="lines", showlegend=False, name="S3")
    fig.append_trace(trace, 1, 1)
    fig.append_trace(trace1, 1, 1)
    fig.append_trace(trace2, 1, 1)
    fig.append_trace(trace3, 1, 1)
    fig.append_trace(trace4, 1, 1)
    fig.append_trace(trace5, 1, 1)
    fig.append_trace(trace6, 1, 1)
    return fig


# MAIN CHART TRACES (STYLE tab)
def line_trace(df):
    trace = go.Scatter(
        x=df.index, y=df["close"], mode="lines", showlegend=False, name="line"
    )
    return trace


def area_trace(df):
    trace = go.Scatter(
        x=df.index, y=df["close"], showlegend=False, fill="toself", name="area"
    )
    return trace


def bar_trace(df):
    return go.Ohlc(
        x=df.index,
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        increasing=dict(line=dict(color="#888888")),
        decreasing=dict(line=dict(color="#888888")),
        showlegend=False,
        name="bar",
    )


def colored_bar_trace(df):
    return go.Ohlc(
        x=df.index,
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        showlegend=False,
        name="colored bar",
    )


def candlestick_trace(df):
    return go.Candlestick(
        x=df.index,
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        increasing=dict(line=dict(color="#00ff00")),
        decreasing=dict(line=dict(color="white")),
        showlegend=False,
        name="candlestick",
    )


# Returns graph figure
def get_fig(currency_pair, ask, bid, type_trace, studies, period):
    # Get OHLC data
    data_frame = currency_pair_data[currency_pair]
    t = datetime.datetime.now()
    data = data_frame.loc[
           : t.strftime(
               "2016-01-05 %H:%M:%S"
           )  # all the data from the beginning until current time
           ]
    data_bid = data["Bid"]
    df = data_bid.resample(period).ohlc()

    subplot_traces = [  # first row traces
        "accumulation_trace",
        "cci_trace",
        "roc_trace",
        "stoc_trace",
        "mom_trace",
    ]
    selected_subplots_studies = []
    selected_first_row_studies = []
    row = 1  # number of subplots

    if studies:
        for study in studies:
            if study in subplot_traces:
                row += 1  # increment number of rows only if the study needs a subplot
                selected_subplots_studies.append(study)
            else:
                selected_first_row_studies.append(study)

    fig = plotly.subplots.make_subplots(
        rows=row,
        shared_xaxes=True,
        shared_yaxes=True,
        cols=1,
        print_grid=False,
        vertical_spacing=0.12,
    )

    # Add main trace (style) to figure
    fig.append_trace(eval(type_trace)(df), 1, 1)

    # Add trace(s) on fig's first row
    for study in selected_first_row_studies:
        fig = eval(study)(df, fig)

    row = 1
    # Plot trace on new row
    for study in selected_subplots_studies:
        row += 1
        fig.append_trace(eval(study)(df), row, 1)

    fig["layout"][
        "uirevision"
    ] = "The User is always right"  # Ensures zoom on graph is the same on update
    fig["layout"]["margin"] = {"t": 50, "l": 50, "b": 50, "r": 25}
    fig["layout"]["autosize"] = True
    fig["layout"]["height"] = 400
    fig["layout"]["xaxis"]["rangeslider"]["visible"] = False
    fig["layout"]["xaxis"]["tickformat"] = "%H:%M"
    fig["layout"]["yaxis"]["showgrid"] = True
    fig["layout"]["yaxis"]["gridcolor"] = "#3E3F40"
    fig["layout"]["yaxis"]["gridwidth"] = 1
    fig["layout"].update(paper_bgcolor="#21252C", plot_bgcolor="#21252C")

    return fig


# returns chart div
def chart_div(pair):
    return html.Div(
        id=pair + "graph_div",
        className="display-none",
        children=[
            # Menu for Currency Graph
            html.Div(
                id=pair + "menu",
                className="not_visible",
                children=[
                    # stores current menu tab
                    html.Div(
                        id=pair + "menu_tab",
                        children=["Studies"],
                        style={"display": "none"},
                    ),
                    html.Span(
                        "Style",
                        id=pair + "style_header",
                        className="span-menu",
                        n_clicks_timestamp=2,
                    ),
                    html.Span(
                        "Studies",
                        id=pair + "studies_header",
                        className="span-menu",
                        n_clicks_timestamp=1,
                    ),
                    # Studies Checklist
                    html.Div(
                        id=pair + "studies_tab",
                        children=[
                            dcc.Checklist(
                                id=pair + "studies",
                                options=[
                                    {
                                        "label": "Accumulation/D",
                                        "value": "accumulation_trace",
                                    },
                                    {
                                        "label": "Bollinger bands",
                                        "value": "bollinger_trace",
                                    },
                                    {"label": "MA", "value": "moving_average_trace"},
                                    {"label": "EMA", "value": "e_moving_average_trace"},
                                    {"label": "CCI", "value": "cci_trace"},
                                    {"label": "ROC", "value": "roc_trace"},
                                    {"label": "Pivot points", "value": "pp_trace"},
                                    {
                                        "label": "Stochastic oscillator",
                                        "value": "stoc_trace",
                                    },
                                    {
                                        "label": "Momentum indicator",
                                        "value": "mom_trace",
                                    },
                                ],
                                value=[],
                            )
                        ],
                        style={"display": "none"},
                    ),
                    # Styles checklist
                    html.Div(
                        id=pair + "style_tab",
                        children=[
                            dcc.RadioItems(
                                id=pair + "chart_type",
                                options=[
                                    {
                                        "label": "candlestick",
                                        "value": "candlestick_trace",
                                    },
                                    {"label": "line", "value": "line_trace"},
                                    {"label": "mountain", "value": "area_trace"},
                                    {"label": "bar", "value": "bar_trace"},
                                    {
                                        "label": "colored bar",
                                        "value": "colored_bar_trace",
                                    },
                                ],
                                value="colored_bar_trace",
                            )
                        ],
                    ),
                ],
            ),
            # Chart Top Bar
            html.Div(
                className="row chart-top-bar",
                children=[
                    html.Span(
                        id=pair + "menu_button",
                        className="inline-block chart-title",
                        children=f"{pair} ☰",
                        n_clicks=0,
                    ),
                    # Dropdown and close button float right
                    html.Div(
                        className="graph-top-right inline-block",
                        children=[
                            html.Div(
                                className="inline-block",
                                children=[
                                    dcc.Dropdown(
                                        className="dropdown-period",
                                        id=pair + "dropdown_period",
                                        options=[
                                            {"label": "5 min", "value": "5Min"},
                                            {"label": "15 min", "value": "15Min"},
                                            {"label": "30 min", "value": "30Min"},
                                        ],
                                        value="15Min",
                                        clearable=False,
                                    )
                                ],
                            ),
                            html.Span(
                                id=pair + "close",
                                className="chart-close inline-block float-right",
                                children="×",
                                n_clicks=0,
                            ),
                        ],
                    ),
                ],
            ),
            # Graph div
            html.Div(
                dcc.Graph(
                    id=pair + "chart",
                    className="chart-graph",
                    config={"displayModeBar": False, "scrollZoom": True},
                )
            ),
        ],
    )


# returns modal Buy/Sell
def modal(pair):
    return html.Div(
        id=pair + "modal",
        className="modal",
        style={"display": "none"},
        children=[
            html.Div(
                className="modal-content",
                children=[
                    html.Span(
                        id=pair + "closeModal", className="modal-close", children="×"
                    ),
                    html.P(id="modal" + pair, children=pair),
                    # row div with two div
                    html.Div(
                        className="row",
                        children=[
                            # order values div
                            html.Div(
                                className="six columns modal-user-control",
                                children=[
                                    html.Div(
                                        children=[
                                            html.P("Volume"),
                                            dcc.Input(
                                                id=pair + "volume",
                                                className="modal-input",
                                                type="number",
                                                value=0.1,
                                                min=0,
                                                step=0.1,
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        children=[
                                            html.P("Type"),
                                            dcc.RadioItems(
                                                id=pair + "trade_type",
                                                options=[
                                                    {"label": "Buy", "value": "buy"},
                                                    {"label": "Sell", "value": "sell"},
                                                ],
                                                value="buy",
                                                labelStyle={"display": "inline-block"},
                                            ),
                                        ]
                                    ),
                                ],
                            ),
                        ],
                    ),
                    html.Div(
                        className="modal-order-btn",
                        children=html.Button(
                            "Order", id=pair + "button_order", n_clicks=0
                        ),
                    ),
                ],
            )
        ],
    )


# Dash App Layout
app.layout = html.Div(
    className="row",
    children=[
        # Interval component for live clock
        dcc.Interval(id="interval", interval=1 * 1000, n_intervals=0),
        # Interval component for ask bid updates
        dcc.Interval(id="i_bis", interval=1 * 2000, n_intervals=0),
        # Interval component for graph updates
        dcc.Interval(id="i_tris", interval=1 * 5000, n_intervals=0),

        html.Div(
            className="three columns div-left-panel",
            children=[
                # Div for Left Panel App Info
                html.Div(
                    className="div-info",
                    children=[
                        html.Img(
                            className="logo", src=app.get_asset_url("logo3.png")
                        ),
                        html.H6(className="title-header", children="Crypto TRADER"),
                        html.P(
                            """
                            DashTrader is a comprehensive solution for institutional and retail investors which
                            facilitates live prices, interactive graphs for technical analysis and a smart order
                            routing system to execute orders at the best price
                            """
                        ),
                    ],
                ),
                # Ask Bid Currency Div
                html.Div(
                    className="div-currency-toggles",
                    children=[
                        html.P(
                            id="live_clock",
                            className="three-col",
                            children=datetime.datetime.now().strftime("%H:%M:%S"),
                        ),
                        html.P(className="three-col", children="Bid"),
                        html.P(className="three-col", children="Ask"),
                        html.Div(
                            id="pairs",
                            className="div-bid-ask",
                            children=[
                                get_row(first_ask_bid(pair, datetime.datetime.now())) for pair in currencies
                            ],
                        ),
                    ],
                ),

            ],
        ),
        # Right Panel Div
        html.Div(
            className="nine columns div-right-panel",
            children=[
                dcc.Interval(id="order_book_update", interval=1 * 1000, n_intervals=0),
                # Charts Div
                html.Div(
                    id="charts",
                    className="row",
                    children=[chart_div(pair) for pair in currencies],
                ),
                # Panel for orders
                html.Div(

                    id="bottom_panel",
                    className="row div-bottom-panel",
                    children=[
                        html.Div(
                            id="display_order_message",
                            className="display-inlineblock",
                            children=update_orders_view()
                        )]

                ),
            ],
        ),
        # Hidden div that stores all clicked charts (EURUSD, USDCHF, etc.)
        html.Div(id="charts_clicked", style={"display": "none"}),
        # Hidden div for each pair that stores orders
        html.Div(
            children=[
                html.Div(id=pair + "orders", style={"display": "none"})
                for pair in currencies
            ]
        ),
        html.Div([modal(pair) for pair in currencies]),
        # Hidden Div that stores all orders
        html.Div(id="orders", style={"display": "none"}),
    ],
)


# Dynamic Callbacks

# Replace currency pair row
def generate_ask_bid_row_callback(pair):
    def output_callback(n, i, bid, ask):
        return replace_row(pair, int(i), float(bid), float(ask))

    return output_callback


# returns string containing clicked charts
def generate_chart_button_callback():
    def chart_button_callback(*args):
        pairs = ""
        for i in range(len(currencies)):
            if args[i] > 0:
                pair = currencies[i]
                if pairs:
                    pairs = pairs + "," + pair
                else:
                    pairs = pair
        return pairs

    return chart_button_callback


# Function to update Graph Figure
def generate_figure_callback(pair):
    def chart_fig_callback(n_i, p, t, s, pairs, a, b, old_fig):

        if pairs is None:
            return {"layout": {}, "data": {}}

        pairs = pairs.split(",")
        if pair not in pairs:
            return {"layout": {}, "data": []}

        if old_fig is None or old_fig == {"layout": {}, "data": {}}:
            return get_fig(pair, a, b, t, s, p)

        fig = get_fig(pair, a, b, t, s, p)
        return fig

    return chart_fig_callback


# Function to close currency pair graph
def generate_close_graph_callback():
    def close_callback(n, n2):
        if n == 0:
            if n2 == 1:
                return 1
            return 0
        return 0

    return close_callback


# Function to open or close STYLE or STUDIES menu
def generate_open_close_menu_callback():
    def open_close_menu(n, className):
        if n == 0:
            return "not_visible"
        if className == "visible":
            return "not_visible"
        else:
            return "visible"

    return open_close_menu


# Function for hidden div that stores the last clicked menu tab
# Also updates style and studies menu headers
def generate_active_menu_tab_callback():
    def update_current_tab_name(n_style, n_studies):
        if n_style >= n_studies:
            return "Style", "span-menu selected", "span-menu"
        return "Studies", "span-menu", "span-menu selected"

    return update_current_tab_name


# Function show or hide studies menu for chart
def generate_studies_content_tab_callback():
    def studies_tab(current_tab):
        if current_tab == "Studies":
            return {"display": "block", "textAlign": "left", "marginTop": "30"}
        return {"display": "none"}

    return studies_tab


# Function show or hide style menu for chart
def generate_style_content_tab_callback():
    def style_tab(current_tab):
        if current_tab == "Style":
            return {"display": "block", "textAlign": "left", "marginTop": "30"}
        return {"display": "none"}

    return style_tab


# Open Modal
def generate_modal_open_callback():
    def open_modal(n):
        if n > 0:
            return {"display": "block"}
        else:
            return {"display": "none"}

    return open_modal


# Function to close modal
def generate_modal_close_callback():
    def close_modal(n, n2):
        return 0

    return close_modal


# Function updates the pair orders div
def generate_order_button_callback(pair):
    def order_callback(n, vol, type_order, pair_orders, ask, bid):
        if n > 0:
            t = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            l = [] if pair_orders is None else json.loads(pair_orders)
            asks = {'bitmex': float('inf'), 'binance': float('inf'), 'kucoin': float('inf')}
            bids = {'bitmex': float('-inf'), 'binance': float('-inf'), 'kucoin': float('-inf')}
            try:
                bitmex_values = get_bitmex_price(pair)
                bids["bitmex"], asks["bitmex"] = bitmex_values['bid'], bitmex_values['ask']
            except:
                pass

            try:
                kucoin_values = get_kucoin_price(pair)
                bids["kucoin"], asks["kucoin"] = kucoin_values['bid'], kucoin_values['ask']
            except:
                pass

            try:
                binance_values = get_binance_price(pair)
                bids["binance"], asks["binance"] = binance_values['bid'], binance_values['ask']
            except:
                pass
            print("bids", bids)
            print("asks", asks)

            if type_order == "buy":
                exchange = min(asks, key=asks.get)
                price = asks[exchange]
                binance_price = asks["binance"]
                kucoin_price = asks["kucoin"]
                bitmex_price = asks['bitmex']
            else:
                exchange = max(bids, key=bids.get)
                price = bids[exchange]
                binance_price = bids["binance"]
                kucoin_price = bids["kucoin"]
                bitmex_price = bids['bitmex']

            print(exchange)
            count = 0
            order_resp = ""

            try:
                if exchange == "binance":
                    order_resp = client_binance.create_order(symbol=binance_map[pair], quantity=vol, side=type_order,
                                                             type="market")
                    print(order_resp)
            except Exception as e:
                count += 1
                print(e)

            try:
                if exchange == "kucoin":
                    order_resp = client_kucoin.create_market_order(side=type_order, symbol=kumap[pair], size=vol)
                    print(order_resp)
            except Exception as e:
                count += 1
                print(e)

            try:
                if exchange == "bitmex":
                    order_resp = bitmexAPI.create_order(symbol=bitmap[pair], side=type_order, quantity=vol)
                print(order_resp)
            except Exception as e:
                count += 1
                print(e)

            order = {
                "time": t,
                "symbol": pair,
                "price": price,
                "side": type_order,
                "exchange": exchange,
                "binance": binance_price,
                "bitmex": bitmex_price,
                "kucoin": kucoin_price,
            }
            l.append(order)
            global_orders.append(order)

            return json.dumps(l)

        return json.dumps([])

    return order_callback


# Resize pair div according to the number of charts displayed
def generate_show_hide_graph_div_callback(pair):
    def show_graph_div_callback(charts_clicked):
        if pair not in charts_clicked:
            return "display-none"

        charts_clicked = charts_clicked.split(",")  # [:4] max of 4 graph
        len_list = len(charts_clicked)

        classes = "chart-style"
        if len_list % 2 == 0:
            classes = classes + " six columns"
        elif len_list == 3:
            classes = classes + " four columns"
        else:
            classes = classes + " twelve columns"
        return classes

    return show_graph_div_callback


# Generate Buy/Sell and Chart Buttons for Left Panel
def generate_contents_for_left_panel():
    def show_contents(n_clicks):
        if n_clicks is None:
            return "display-none", "row summary"
        elif n_clicks % 2 == 0:
            return "display-none", "row summary"
        return "row details", "row summary-open"

    return show_contents


# Loop through all currencies
for pair in currencies:
    # Callback for Buy/Sell and Chart Buttons for Left Panel
    app.callback(
        [Output(pair + "contents", "className"), Output(pair + "summary", "className")],
        [Input(pair + "summary", "n_clicks")],
    )(generate_contents_for_left_panel())

    # Callback for className of div for graphs
    app.callback(
        Output(pair + "graph_div", "className"), [Input("charts_clicked", "children")]
    )(generate_show_hide_graph_div_callback(pair))

    # Callback to update the actual graph
    app.callback(
        Output(pair + "chart", "figure"),
        [
            Input("i_tris", "n_intervals"),
            Input(pair + "dropdown_period", "value"),
            Input(pair + "chart_type", "value"),
            Input(pair + "studies", "value"),
            Input("charts_clicked", "children"),
        ],
        [
            State(pair + "ask", "children"),
            State(pair + "bid", "children"),
            State(pair + "chart", "figure"),
        ],
    )(generate_figure_callback(pair))

    # updates the ask and bid prices
    app.callback(
        Output(pair + "row", "children"),
        [Input("i_bis", "n_intervals")],
        [
            State(pair + "index", "children"),
            State(pair + "bid", "children"),
            State(pair + "ask", "children"),
        ],
    )(generate_ask_bid_row_callback(pair))

    # close graph by setting to 0 n_clicks property
    app.callback(
        Output(pair + "Button_chart", "n_clicks"),
        [Input(pair + "close", "n_clicks")],
        [State(pair + "Button_chart", "n_clicks")],
    )(generate_close_graph_callback())

    # show or hide graph menu
    app.callback(
        Output(pair + "menu", "className"),
        [Input(pair + "menu_button", "n_clicks")],
        [State(pair + "menu", "className")],
    )(generate_open_close_menu_callback())

    # stores in hidden div name of clicked tab name
    app.callback(
        [
            Output(pair + "menu_tab", "children"),
            Output(pair + "style_header", "className"),
            Output(pair + "studies_header", "className"),
        ],
        [
            Input(pair + "style_header", "n_clicks_timestamp"),
            Input(pair + "studies_header", "n_clicks_timestamp"),
        ],
    )(generate_active_menu_tab_callback())

    # hide/show STYLE tab content if clicked or not
    app.callback(
        Output(pair + "style_tab", "style"), [Input(pair + "menu_tab", "children")]
    )(generate_style_content_tab_callback())

    # hide/show MENU tab content if clicked or not
    app.callback(
        Output(pair + "studies_tab", "style"), [Input(pair + "menu_tab", "children")]
    )(generate_studies_content_tab_callback())

    # show modal
    app.callback(Output(pair + "modal", "style"), [Input(pair + "Buy", "n_clicks")])(
        generate_modal_open_callback()
    )

    # hide modal
    app.callback(
        Output(pair + "Buy", "n_clicks"),
        [
            Input(pair + "closeModal", "n_clicks"),
            Input(pair + "button_order", "n_clicks"),
        ],
    )(generate_modal_close_callback())

    # each pair saves its orders in hidden div
    app.callback(
        Output(pair + "orders", "children"),
        [Input(pair + "button_order", "n_clicks")],
        [
            State(pair + "volume", "value"),
            State(pair + "trade_type", "value"),
            State(pair + "orders", "children"),
            State(pair + "ask", "children"),
            State(pair + "bid", "children"),
        ],
    )(generate_order_button_callback(pair))

# updates hidden div with all the clicked charts
app.callback(
    Output("charts_clicked", "children"),
    [Input(pair + "Button_chart", "n_clicks") for pair in currencies],
    [State("charts_clicked", "children")],
)(generate_chart_button_callback())


# Callback to update live clock
@app.callback(Output("live_clock", "children"), [Input("interval", "n_intervals")])
def update_time(n):
    return datetime.datetime.now().strftime("%H:%M:%S")


# callback to show executed trades
@app.callback(Output("display_order_message", "children"), [Input("order_book_update", "n_intervals")])
def update_orders_screen(n):
    return update_orders_view()


if __name__ == "__main__":
    client_binance = binance_connections.binance_connections(api_key=config.binance["api_key"],
                                                             api_secret=config.binance["api_secret"])
    client_kucoin = KuCoinApi.KuCoinApi(config.kucoin["api_key"], config.kucoin["api_secret"],
                                        config.kucoin["api_passphrase"],
                                        sandbox=True)
    x = client_kucoin.get_ws_endpoint()
    for symbol in currencies:
        if symbol == "BTC_USD" or symbol == "ETH_USD":
            ws_kucoin = kuCoinsocket.kuCoinsocket(endpoint=x['instanceServers'][0]['endpoint'], token=x['token'],
                                                  ping_interval=x['instanceServers'][0]['pingInterval'],
                                                  ping_timeout=x['instanceServers'][0]['pingTimeout'],
                                                  symbol=kumap[symbol], topic="/market/ticker")
            ws_bitmex = BitMEXWebsocket.BitMEXWebsocket(endpoint=config.bitmex["endpoint"], symbol=bitmap[symbol],
                                                        api_key=config.bitmex["api_key"],
                                                        api_secret=config.bitmex["api_secret"])
            socket_dict[symbol + "kucoin"] = ws_kucoin
            socket_dict[symbol + "bitmex"] = ws_bitmex

        else:
            ws_bitmex = BitMEXWebsocket.BitMEXWebsocket(endpoint=config.bitmex["endpoint"], symbol=bitmap[symbol],
                                                        api_key=config.bitmex["api_key"],
                                                        api_secret=config.bitmex["api_secret"])
            socket_dict[symbol + "bitmex"] = ws_bitmex

    sleep(5)

    app.run_server(debug=True, use_reloader=False)
