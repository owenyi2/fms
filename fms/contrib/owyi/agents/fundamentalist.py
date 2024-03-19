#!/usr/bin/env python
# -*- coding: utf8 -*-

import random
import logging
import numpy as np

from fms import agents
from fms.utils import BUY, SELL
from fms.utils.exceptions import MissingParameter

logger = logging.getLogger('fms.agents.fundamentalist')

class Fundamentalist(agents.Agent):
    def __init__(self, params, offset=0):
        agents.Agent.__init__(self, params, offset)
        try:
            self.sigma = self.args[0]
        except (AttributeError, IndexError): 
            raise MissingParameter, 'max_lookback'
        try:
            self.tau = self.args[1] # order lifetime
        except IndexError:
            raise MissingParameter, 'tau'
        del self.args

        self.fundamental = params["engines"][0]["market"]["fundamentalprice"] * np.random.lognormal(0, self.sigma)
        self.noise = params["engines"][0]["market"]["executionnoise"]

    def speak(self, market): # overload the `speak` method to allow agents to view market
        """
        Return order emitted by agent
        """
        order = self.act(market=market)
        order['agent'] = order.get('agent', self)
        return [order]
    
    def act(self, world=None, market=None):
        """
        Return random order as a dict with keys in (direction, price, quantity).
        """

        price = market.lastprice
        limit = price * np.random.normal(1, self.noise)

        if price < self.fundamental:
            return {'direction':BUY, 'price':limit, 'lifetime': self.tau}
        if price > self.fundamental:
            return {'direction':SELL, 'price':limit, 'lifetime': self.tau}


def _test():
    """
    Run tests in docstrings
    """
    import doctest
    doctest.testmod(optionflags=+doctest.ELLIPSIS)

if __name__ == '__main__':
    _test()
