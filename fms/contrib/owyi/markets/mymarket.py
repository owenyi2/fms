#!/usr/bin/python
# -*- coding: utf8 -*-
"""
Order driven market, continuous transactions.
Any order is considered valid.
"""
from operator import itemgetter, attrgetter

import numpy as np

from fms import markets
from fms.utils import BUY, SELL
from fms.utils.exceptions import MissingParameter

class MyMarket(markets.Market):
    """
    Simulate an order driven market with continuous transactions. Orders may be Cancelled.

    This market class uses 2 order books (buybook, sellbook).
    Books are sorted lists of [price, time, quantity, agent]
    to get the best limits for the next trade.
    As best limit is the highest offered price for buybook,
    and the lowest for sellbook, buybook[-1] and sellbook[0]
    are the best limits.
    Date is an int, the instant the order entered the book.
    Date is negative in buybook to ensure that buybook[-1]
    is always the best limit, i.e. if two orders have the same
    price limit, the older wins.

    The class inherits at least one parameter from its superclass,
    the file/device where transactions should be output. If no
    filename is given in conf file, then output goes to sys.stdout:
    >>> from fms.markets.continuousorderdriven import ContinuousOrderDriven
    >>> market = ContinuousOrderDriven()
    >>> market.output_transaction(1, 10.0, 25)
    1;0;10.00;25

    Any agent can place any order : the market itself does not enforce
    any condition on the orders.
    >>> from fms import agents
    >>> agentbob = agents.Agent({'agents': [{'money':10000, 'stocks':200}]})
    >>> agentsmith = agents.Agent({'agents': [{'money':1000, 'stocks':2000}]})
    >>> order = (None,)
    >>> market.is_valid(agentbob, order)
    True
    >>> market.is_valid(agentsmith, order)
    True

    The heart of the market is the recording and/or execution of
    agents orders. We suppose agentbob is buyer and agentsmith is
    seller.
    Each call to record_order increments the self.time value, 
    and orders are recorded in the books with a timestamp.
    >>> from fms.utils import BUY, SELL
    >>> market.record_order({'agent': agentbob, 'direction':BUY, 'price':2.50, 'quantity':10}, 0, False)
    >>> market.buybook
    [[2.5, 0, 10, <fms.agents.Agent instance at ...>]]
    >>> market.sellbook
    []
    >>> market.record_order({'agent': agentsmith, 'direction':SELL, 'price':3.50, 'quantity':20}, 1, False)
    >>> market.buybook
    [[2.5, 0, 10, <fms.agents.Agent instance at ...>]]
    >>> market.sellbook
    [[3.5, 1, 20, <fms.agents.Agent instance at ...>]]

    If an order price does not "touch" a limit, the order is recorded
    in the right book, which is immediately sorted, but do_clearing does not
    do anything (no transaction is possible).
    Now we want to sell at 3.5 but the best buyer offers 2.5
    >>> market.record_order({'agent': agentsmith, 'direction':SELL, 'price':3.50, 'quantity':40}, 2, False)
    >>> market.do_clearing(2)
    >>> market.buybook
    [[2.5, 0, 10, <fms.agents.Agent instance at ...>]]
    >>> market.sellbook
    [[3.5, 1, 20, <fms.agents.Agent instance at ...>], [3.5, 2, 40, <fms.agents.Agent instance at ...>]]

    Notice that the two orders have the same price, thus the best
    limit (first item in the list) is the older one, with time==1.

    Same thing with a buy order, which does not touch the best sell
    limit : the agent wants to buy at 3 but the lowest offered price
    is 3.5
    >>> market.record_order({'agent': agentbob, 'direction':BUY, 'price':3.00, 'quantity':60}, 3, False)
    >>> market.do_clearing(3)
    >>> market.buybook
    [[2.5, 0, 10, <fms.agents.Agent instance at ...>], [3.0, -3, 60, <fms.agents.Agent instance at ...>]]
    >>> market.sellbook
    [[3.5, 1, 20, <fms.agents.Agent instance at ...>], [3.5, 2, 40, <fms.agents.Agent instance at ...>]]

    Now we place a buy order at a higher price than the best sell limit.
    Because the quantity to buy is lower than the offered quantity on
    the sell limit, the order is fully executed :
    - the quantity on the sell limited is reduced by the # of stocks sold
    - the agent gets the stocks, and pays for it at the sell limit price.
    - the seller agent gets the money, and deliver the stocks.
    Notice that the chosen sell limit is (hopefully) the "older" one.
    Because a transaction occured, the market outputs a line in the
    outputfile. The format is timestamp;transaction number;price;quantity
    >>> print agentbob.state()
    Agent ... - owns $10000.00 and    200 securities
    >>> market.record_order({'agent': agentbob, 'direction':BUY, 'price':3.60, 'quantity':15}, 4, False)
    >>> market.do_clearing(4)
    4;1;3.50;15
    >>> agentbob.stocks
    215
    >>> print agentbob.state()
    Agent ... - owns $ 9947.50 and    215 securities
    >>> print agentsmith.state()
    Agent ... - owns $ 1052.50 and   1985 securities
    >>> market.buybook
    [[2.5, 0, 10, <fms.agents.Agent instance at ...>], [3.0, -3, 60, <fms.agents.Agent instance at ...>]]
    >>> market.sellbook
    [[3.5, 1, 5, <fms.agents.Agent instance at ...>], [3.5, 2, 40, <fms.agents.Agent instance at ...>]]

    We place again a buy order at a higher price than the best sell
    limit, but the quantity is higher than the sell limit offered one.
    Because the price is the same on the second limit, the remaining
    quantity is bought on it, and the best limit disappears.
    >>> market.record_order({'agent': agentbob, 'direction':BUY, 'price':3.60, 'quantity':17}, 5, False)
    >>> market.do_clearing(5)
    5;2;3.50;5
    5;3;3.50;12
    >>> market.buybook
    [[2.5, 0, 10, <fms.agents.Agent instance at ...>], [3.0, -3, 60, <fms.agents.Agent instance at ...>]]
    >>> market.sellbook
    [[3.5, 2, 28, <fms.agents.Agent instance at ...>]]
    >>> print agentbob.state()
    Agent ... - owns $ 9888.00 and    232 securities
    >>> print agentsmith.state()
    Agent ... - owns $ 1112.00 and   1968 securities

    Now, we place a buy order which cannot be fully executed, because
    the asked quantity is greater than the bid quantity. The order
    is then partially executed, and the remaining part is recorded
    in the buybook.
    >>> market.record_order({'agent': agentbob, 'direction':BUY, 'price':3.55, 'quantity':50}, 6, False)
    >>> market.do_clearing(6)
    6;4;3.50;28
    >>> market.buybook
    [[2.5, 0, 10, <fms.agents.Agent instance at ...>], [3.0, -3, 60, <fms.agents.Agent instance at ...>], [3.5..., -6, 22, <fms.agents.Agent instance at ...>]]
    >>> market.sellbook
    []
    >>> print agentbob.state()
    Agent ... - owns $ 9790.00 and    260 securities
    >>> print agentsmith.state()
    Agent ... - owns $ 1210.00 and   1940 securities

    Same thing with sell orders :
    - order is fully executed on the best limit
    - order is fully executed on 2 limits
    - order is partially executed

    We place an order to sell at 3.4, which is lower than the best
    buy limit (3.55) :
    >>> market.record_order({'agent': agentsmith, 'direction':SELL, 'price':3.40, 'quantity':6}, 7, False)
    >>> market.do_clearing(7)
    7;5;3.55;6
    >>> market.buybook
    [[2.5, 0, 10, <fms.agents.Agent instance at ...>], [3.0, -3, 60, <fms.agents.Agent instance at ...>], [3.5..., -6, 16, <fms.agents.Agent instance at ...>]]
    >>> market.sellbook
    []
    >>> print agentbob.state()
    Agent ... - owns $ 9768.70 and    266 securities
    >>> print agentsmith.state()
    Agent ... - owns $ 1231.30 and   1934 securities

    Then a sell order at 2.8 wich is lower than the 2 best buy limits
    >>> market.record_order({'agent': agentsmith, 'direction':SELL, 'price':2.80, 'quantity':45}, 8, False)
    >>> market.do_clearing(8)
    8;6;3.55;16
    8;7;3.00;29
    >>> market.buybook
    [[2.5, 0, 10, <fms.agents.Agent instance at ...>], [3.0, -3, 31, <fms.agents.Agent instance at ...>]]
    >>> market.sellbook
    []
    >>> print agentbob.state()
    Agent ... - owns $ 9624.90 and    311 securities
    >>> print agentsmith.state()
    Agent ... - owns $ 1375.10 and   1889 securities

    Then the last order at 2.6, which is lower than the best buy limit
    but will be partially executed
    >>> market.record_order({'agent': agentsmith, 'direction':SELL, 'price':2.60, 'quantity':42}, 9, False)
    >>> market.do_clearing(9)
    9;8;3.00;31
    >>> market.buybook
    [[2.5, 0, 10, <fms.agents.Agent instance at ...>]]
    >>> market.sellbook
    [[2.6..., 9, 11, <fms.agents.Agent instance at ...>]]
    >>> print agentbob.state()
    Agent ... - owns $ 9531.90 and    342 securities
    >>> print agentsmith.state()
    Agent ... - owns $ 1468.10 and   1858 securities

    Insert new orders in the books, to check sorting is correct.
    We exchange the agents roles : agentsmith is buyer, agentbob
    is seller.
    Sell order, higher than the best buy limit
    >>> market.record_order({'agent': agentbob, 'direction':SELL, 'price':3., 'quantity':20}, 10, False)
    >>> market.do_clearing(10)
    >>> market.buybook
    [[2.5, 0, 10, <fms.agents.Agent instance at ...>]]
    >>> market.sellbook
    [[2.6..., 9, 11, <fms.agents.Agent instance at ...>], [3.0, 10, 20, <fms.agents.Agent instance at ...>]]

    Sell order, higher than the best buy limit, but lower than the previous
    one
    >>> market.record_order({'agent': agentbob, 'direction':SELL, 'price':2.8, 'quantity':30}, 11, False)
    >>> market.do_clearing(11)
    >>> market.buybook
    [[2.5, 0, 10, <fms.agents.Agent instance at ...>]]
    >>> market.sellbook
    [[2.6..., 9, 11, <fms.agents.Agent instance at ...>], [2.8..., 11, 30, <fms.agents.Agent instance at ...>], [3.0, 10, 20, <fms.agents.Agent instance at ...>]]

    Buy order, lower than the best sell limit
    >>> market.record_order({'agent': agentsmith, 'direction':BUY, 'price':2.4, 'quantity':25}, 12, False)
    >>> market.do_clearing(12)
    >>> market.buybook
    [[2.4..., -12, 25, <fms.agents.Agent instance at ...>], [2.5, 0, 10, <fms.agents.Agent instance at ...>]]
    >>> market.sellbook
    [[2.6..., 9, 11, <fms.agents.Agent instance at ...>], [2.8..., 11, 30, <fms.agents.Agent instance at ...>], [3.0, 10, 20, <fms.agents.Agent instance at ...>]]

    Buy order, lower than the best sell limit, but higher than previous one
    >>> market.record_order({'agent': agentsmith, 'direction':BUY, 'price':2.45, 'quantity':15}, 13, False)
    >>> market.do_clearing(13)
    >>> market.buybook
    [[2.4..., -12, 25, <fms.agents.Agent instance at ...>], [2.45..., -13, 15, <fms.agents.Agent instance at ...>], [2.5, 0, 10, <fms.agents.Agent instance at ...>]]
    >>> market.sellbook
    [[2.6..., 9, 11, <fms.agents.Agent instance at ...>], [2.8..., 11, 30, <fms.agents.Agent instance at ...>], [3.0, 10, 20, <fms.agents.Agent instance at ...>]]

    """

    def __init__(self, parameters=None):
        """
        Class constructor.
        Gets parameters from config, pass it to superclass.
        Adds :
        - lastprice (float) : last transaction price, see info()
        - transaction (int) : transaction counter
        """
        try:
            self.p_f = parameters['engines'][0]['market']['fundamentalprice']
        except:
            raise AttributeError, "fundamental price not found"
        
        markets.Market.__init__(self, parameters)

        self.lastprice = self.p_f 
        self.transaction = 0
        self.historical = np.array([])
        self.ohlc = [{"open": self.p_f, "high": self.p_f, "low": self.p_f, "close": self.p_f}]

    def summarise_ohlc(self):
        if len(self.historical) == 0:
            return

        open = self.historical[0]
        close = self.historical[-1]
        high = max(self.historical)
        low = min(self.historical)

        self.historical = []

        self.ohlc.append({"open": open, "high": high, "low": low, "close": close})
      
    def sanitize_order(self, raw_order):
        """
        Returns agent's order as a dict with direction, price, quantity.
        raw_order should be a dict with at least 'direction' key.
        Order keys :
        - direction: BUY or SELL
        - price: best market limit if missing
        - quantity: 1 if missing
        - lifetime: float('inf') if missing
        """
        if raw_order == None: # if agent wants to skip a tick, they can return None
            return
        order = {}
        if 'direction' in raw_order:
            order['direction'] = raw_order['direction']
            if order['direction'] == BUY:
                order['price'] = raw_order.get('price', 
                        self.info()['sellbook'][0][0])
            else:
                order['price'] = raw_order.get('price', 
                        self.info()['buybook'][-1][0])
            order['quantity'] = raw_order.get('quantity', 1)
            order['agent'] = raw_order['agent']
            
            order['lifetime'] = raw_order.get('lifetime', float('inf'))
            return order
        else:
            raise MissingParameter, 'direction'

    def manage_order_lifetimes(self):
        for order in self.sellbook:
            order[4]["age"] += 1
        self.sellbook = list(filter(lambda o: o[4]["age"] < o[4]["lifetime"], self.sellbook)) 
        for order in self.buybook:
            order[4]["age"] += 1
        self.buybook = list(filter(lambda o: o[4]["age"] < o[4]["lifetime"], self.buybook))
    
    def record_order(self, order, time, unique=True):
        """
        Record agent order in correct order book

        If an order from the same agent exists on the same
        asset and unique is True, delete it.

        >>> from fms.markets import Market
        >>> market = Market(None)
        >>> market.record_order({'direction': 1, 'quantity': 2, 'price': 3, 'agent': 'smith'}, 1)
        >>> market.sellbook
        [[3, 1, 2, 'smith']]
        >>> market.record_order({'direction': 1, 'quantity': 3, 'price': 4, 'agent': 'smith'}, 1)
        >>> market.sellbook
        [[4, 1, 3, 'smith']]
        >>> market.record_order({'direction': 1, 'quantity': 4, 'price': 5, 'agent': 'smith'}, 1, False)
        >>> market.sellbook
        [[4, 1, 3, 'smith'], [5, 1, 4, 'smith']]

        """
        if order == None:
            return
        if unique:
            for book in (self.sellbook, self.buybook):
                for line in book:
                    if order['agent'] == line[3]:
                        book.remove(line)
                        break

        if order['direction'] == SELL:
            self.sellbook.append(
                    [order['price'], time, order['quantity'], order['agent'], {"lifetime": order['lifetime'], "age": 0}])
            self.sellbook.sort(key = itemgetter(1), reverse = False) # sort by secondary key time first 
            self.sellbook.sort(key = itemgetter(0), reverse = False) # then sort by primary key price
        else:
            self.buybook.append(
                    [order['price'], time, order['quantity'], order['agent'], {"lifetime": order['lifetime'], "age": 0}])
            self.buybook.sort(key = itemgetter(1), reverse = False) # sort by secondary key time first
            self.buybook.sort(key = itemgetter(0), reverse = True) # then sort by primary key price

    def is_valid(self, agent, order):
        """
        Checks if order is valid. Always True for this market.
        """
        if order["direction"] == SELL:
            existing_orders = filter(lambda x: x[3] == agent, self.buybook)
            if len(existing_orders) == 0:
                return True
            else: 
                return order["price"] > existing_orders[0][0] 
        if order["direction"] == BUY:
            existing_orders = filter(lambda x: x[3] == agent, self.sellbook)
            if len(existing_orders) == 0:
                return True
            else:
                return order["price"] < existing_orders[0][0]
        
        return True

    def info(self):
        """
        Provides dict information about market state
        Dict keys :
        - selllimit (float): best sell limit
        - buylimit (float): best buy limit
        - lastprice (float): last transaction price
        - lasttransaction (int): # of last transaction
        """
        if self.sellbook:
            sellbook = self.sellbook
        else:
            sellbook = [['unset sellbook']]
        if self.buybook:
            buybook = self.buybook
        else:
            buybook = [['unset buybook']]
        infodict = {'sellbook': sellbook,
                    'buybook': buybook,
                    'lastprice': self.lastprice,
                    'lasttransaction': self.transaction}
        return infodict

    def do_clearing(self, time):
        """
        Clears books, executing all possible transactions
        """
                    
        if len(self.buybook) and len(self.sellbook):
            while len(self.sellbook) and len(self.buybook) \
                    and self.sellbook[0][0] <= self.buybook[0][0]:
                qty = min(self.buybook[0][2], self.sellbook[0][2])
                if self.buybook[0][1] > self.sellbook[0][1]:
                    executedprice = self.sellbook[0][0]
                else:
                    executedprice = self.buybook[0][0]
                 
                self.historical = np.append(self.historical, executedprice)
                self.lastprice = executedprice
                self.transaction += 1
                buyer = self.buybook[0][3]
                seller = self.sellbook[0][3]
                if not self.replay:
                    buyer.record(BUY, executedprice, qty)
                    seller.record(SELL, executedprice, qty)
                self.output_transaction(time, executedprice, qty)

                if qty == self.buybook[0][2]:
                    del self.buybook[0]
                else:
                    self.buybook[0][2] -= qty
                if qty == self.sellbook[0][2]:
                    del self.sellbook[0]
                else:
                    self.sellbook[0][2] -= qty


def _test():
    """
    Run tests in docstrings.
    """
    import doctest
    doctest.testmod(optionflags=+doctest.ELLIPSIS)

if __name__ == '__main__':
    _test()