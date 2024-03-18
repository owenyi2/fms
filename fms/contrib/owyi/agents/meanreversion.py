#!/usr/bin/env python
# -*- coding: utf8 -*-

import random
import logging
import numpy as np

from fms import agents
from fms.utils import BUY, SELL
from fms.utils.exceptions import MissingParameter

logger = logging.getLogger('fms.agents.meanreversion')

class MeanReversion(agents.Agent):
    def __init__(self, params, offset=0):
        agents.Agent.__init__(self, params, offset)
        try:
            self.max_lookback = self.args[0]
        except (AttributeError, IndexError): 
            raise MissingParameter, 'max_lookback'
        try:
            self.sigma_1 = self.args[1]
        except (AttributeError, IndexError): 
            raise MissingParameter, 'buy_threshold'
        try:
            self.sigma_2 = self.args[2]
        except (AttributeError, IndexError): 
            raise MissingParameter, 'sell_threshold'
        try:
            self.tau = self.args[3] # order lifetime
        except IndexError:
            raise MissingParameter, 'tau'
        del self.args

        self.lookback = np.random.randint(2, self.max_lookback)
        self.buy_threshold = -np.abs(np.random.normal(0, self.sigma_1))
        self.sell_threshold = np.abs(np.random.normal(0, self.sigma_2))

    def speak(self, market): # overload the `speak` method to allow agents to view market
        """
        Return order emitted by agent
        """
        orders = self.act(market=market)
        for order in orders:
            order['agent'] = order.get('agent', self)
        return orders
    
    def act(self, world=None, market=None):
        """
        Return random order as a dict with keys in (direction, price, quantity).
        """
        if len(market.ohlc) < self.lookback + 2:
            return [] 

        ma = np.mean([ohlc["close"] for ohlc in market.ohlc[-(1+self.lookback):-1]])
        std = np.std([ohlc["close"] for ohlc in market.ohlc[-(1+self.lookback):-1]])

        price = market.ohlc[-1]["close"]

        if (price - ma) / std < self.buy_threshold:
            return [{'direction':BUY, 'price': price, 'lifetime': self.tau}]
        if (price - ma) / std > self.sell_threshold:
            return [{'direction':SELL, 'price': price, 'lifetime': self.tau}]

        return []

def _test():
    """
    Run tests in docstrings
    """
    import doctest
    doctest.testmod(optionflags=+doctest.ELLIPSIS)

if __name__ == '__main__':
    _test()
