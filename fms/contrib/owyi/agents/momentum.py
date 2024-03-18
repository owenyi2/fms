#!/usr/bin/env python
# -*- coding: utf8 -*-

import random
import logging
import numpy as np

from fms import agents
from fms.utils import BUY, SELL
from fms.utils.exceptions import MissingParameter

logger = logging.getLogger('fms.agents.momentum')

class Momentum(agents.Agent):
    def __init__(self, params, offset=0):
        agents.Agent.__init__(self, params, offset)
        try:
            self.lookback = random.randint(1, self.args[0])
        except (AttributeError, IndexError): # max_lookback
            raise MissingParameter, 'lookback'
        try:
            self.buy_threshold = np.random.normal(1, self.args[1])
        except (AttributeError, IndexError): # buy_threshold
            raise MissingParameter, 'buy_threshold'
        try:
            self.sell_threshold = np.random.normal(1, self.args[2])
        except (AttributeError, IndexError): # sell_threshold
            raise MissingParameter, 'sell_threshold'
        try:
            self.tau = self.args[3] # order lifetime
        except IndexError:
            raise MissingParameter, 'tau'
        del self.args
        
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

        current_momentum = market.ohlc[-1]["close"] / market.ohlc[-(1+self.lookback)]["close"]
        previous_momentum = market.ohlc[-2]["close"] / market.ohlc[-(2+self.lookback)]["close"]

        price = market.ohlc[-1]["close"]

        if current_momentum > self.buy_threshold and previous_momentum < self.buy_threshold:
            return [{'direction':BUY, 'price': price, 'lifetime': self.tau}]
        if current_momentum < self.sell_threshold and previous_momentum > self.sell_threshold:
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
