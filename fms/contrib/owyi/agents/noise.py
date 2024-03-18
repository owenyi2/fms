#!/usr/bin/env python
# -*- coding: utf8 -*-

import random
import logging
import numpy as np

from fms import agents
from fms.utils import BUY, SELL
from fms.utils.exceptions import MissingParameter

logger = logging.getLogger('fms.agents.noise')

class Noise(agents.Agent):
    def __init__(self, params, offset=0):
        agents.Agent.__init__(self, params, offset)
        try:
            self.sigma = np.random.uniform(0, self.args[0])

        except (AttributeError, IndexError): # sigma
            raise MissingParameter, 'sigma'
        try:
            self.tau = self.args[1] # order lifetime
        except IndexError:
            raise MissingParameter, 'tau'


        del self.args
        
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
        direction = random.choice((BUY, SELL))
        
        
        price = market.ohlc[-1]["close"] * np.clip(np.random.normal(1, self.sigma), 0.8, 1.2)


        return {'direction':direction, 'price':price, 'lifetime': self.tau}


def _test():
    """
    Run tests in docstrings
    """
    import doctest
    doctest.testmod(optionflags=+doctest.ELLIPSIS)

if __name__ == '__main__':
    _test()
