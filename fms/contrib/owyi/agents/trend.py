#!/usr/bin/env python
# -*- coding: utf8 -*-

import random
import logging
import numpy as np

from fms import agents
from fms.utils import BUY, SELL
from fms.utils.exceptions import MissingParameter

logger = logging.getLogger('fms.agents.trend')

class Trend(agents.Agent):
    def __init__(self, params, offset=0):
        agents.Agent.__init__(self, params, offset)
        try:
            self.max_lookback = self.args[0]
        except (AttributeError, IndexError): 
            raise MissingParameter, 'max_lookback'
        try:
            self.tau = self.args[1] # order lifetime
        except IndexError:
            raise MissingParameter, 'tau'
        del self.args

        lookbacks = np.random.randint(1, self.max_lookback, 2)
        self.short_lookback = min(lookbacks)
        self.long_lookback = max(lookbacks)

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
        if len(market.ohlc) < self.long_lookback + 2:
            return [] 
        
        short_ma = np.mean([ohlc["close"] for ohlc in market.ohlc[-(1+self.short_lookback):-1]])
        long_ma = np.mean([ohlc["close"] for ohlc in market.ohlc[-(1+self.long_lookback):-1]])

        previous_short_ma = np.mean([ohlc["close"] for ohlc in market.ohlc[-(2+self.short_lookback):-2]])
        previous_long_ma = np.mean([ohlc["close"] for ohlc in market.ohlc[-(2+self.long_lookback):-2]])

        price = market.ohlc[-1]["close"]

        if short_ma > long_ma and previous_short_ma < previous_long_ma:
            return [{'direction':BUY, 'price': price, 'lifetime': self.tau}]
        if short_ma < long_ma and previous_short_ma > previous_long_ma:
            return [{'direction':SELL, 'price': price, 'lifetime': self.tau}]

        # if short_ma > long_ma:
        #     return [{'direction':BUY, 'price': price, 'lifetime': self.tau}]
        # if short_ma < long_ma:
        #     return [{'direction':SELL, 'price': price, 'lifetime': self.tau}]

        return []

def _test():
    """
    Run tests in docstrings
    """
    import doctest
    doctest.testmod(optionflags=+doctest.ELLIPSIS)

if __name__ == '__main__':
    _test()
