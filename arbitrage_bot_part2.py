from catalyst.api import symbol, order, get_open_orders
from catalyst.utils.run_algo import run_algorithm
from catalyst.api import (record, symbol, order_target_percent, )
from catalyst.exchange.utils.stats_utils import extract_transactions

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from logbook import Logger


def is_profitable_after_fees(sell_price, buy_price, sell_market, buy_market):
    sell_fee = get_fee(sell_market, sell_price)
    buy_fee = get_fee(buy_market, buy_price)
    expected_profit = sell_price - buy_price - sell_fee - buy_fee

    if expected_profit > 0:
        print("Sell {} at {}, Buy {} at {}".format(sell_market.name, sell_price, buy_market.name, buy_price))
        print("Total fees: {}".format(buy_fee + sell_fee))
        print("Expected profit: {}".format(expected_profit))
        return True
    return False


def get_fee(market, price):
    return round(market.api.fees['trading']['taker'] * price, 5)

def get_adjusted_prices(price, slippage):
    adj_sell_price = price * (1 - slippage)
    adj_buy_price = price * (1 + slippage)
    return adj_sell_price, adj_buy_price


def initialze(context):
    context.bitfinex = context.exchanges['bitfinex']
    context.poloniex = context.exchanges['poloniex']



    context.bitfinex_trading_pair = symbol('btc_usd', context.bitfinex.name)
    context.poloniex_trading_pair = symbol('btc_usdt', context.poloniex.name)


def handle_data(context, data):
    poloniex_price = data.current(context.poloniex_trading_pair, 'price')
    bitfinex_price = data.current(context.bitfinex_trading_pair, 'price')
    slippage = 0.03
    sell_p, buy_p = get_adjusted_prices(poloniex_price, slippage)
    sell_b, buy_b = get_adjusted_prices(bitfinex_price, slippage)

    if is_profitable_after_fees(sell_p, buy_b, context.poloniex, context.bitfinex):
        print('Date: {}'.format(data.current_dt))
        print('Bitfinex Price: {}, Poloniex Price: {}'.format(bitfinex_price, poloniex_price))

        order(asset=context.bitfinex_trading_pair,
              amount=1,
              limit_price=buy_b)
        order(asset=context.poloniex_trading_pair,
              amount=-1,
              limit_price=sell_p)

    elif is_profitable_after_fees(sell_b, buy_p, context.bitfinex, context.poloniex):
        print('Date: {}'.format(data.current_dt))
        print('Bitfinex Price: {}, Poloniex Price: {}'.format(bitfinex_price, poloniex_price))
        order(asset=context.poloniex_trading_pair,
              amount=1,
              limit_price=buy_p)
        order(asset=context.bitfinex_trading_pair,
              amount=-1,
              limit_price=sell_b)




if __name__ == '__main__':
    run_algorithm(capital_base=10000,
                         initialize=initialze,
                         handle_data=handle_data,
                         live=False,
                         quote_currency='usd',
                         exchange_name='bitfinex, poloniex',
                         algo_namespace='arbitrage002',
                         data_frequency='minute',
                         start=pd.to_datetime('2017-12-06', utc=True),
                         end=pd.to_datetime('2018-05-03', utc=True)
                  )
