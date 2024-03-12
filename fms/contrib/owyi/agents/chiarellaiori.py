#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
Module defining RandomTrader agent class.
"""

import random
import logging
import numpy as np

from fms import agents
from fms.utils import BUY, SELL
from fms.utils.exceptions import MissingParameter

logger = logging.getLogger('fms.agents.randomtrader')

class ChiarellaIori(agents.Agent):
    """
    Simulate an agent taking random but not stupid decisions

    This agent subclass should have three keys in the
    args dict :
    - avgprice : average order price (float)
    - maxfluct : maximum % fluctuation around price (int)
    - maxbuy : maximum quantity to buy (int)
    If any of those parameters is missing, a MissingParameter
    exception is raised.
    >>> from fms.agents import randomtrader
    >>> params = {'agents': [{'money':10000, 'stocks':200}]}
    >>> agent = randomtrader.RandomTrader(params)
    Traceback (most recent call last):
        ...
    MissingParameter: avgprice
    >>> params = {'agents': [{'money':10000, 'stocks':200, 'args':[100]}]}
    >>> agent = randomtrader.RandomTrader(params)
    Traceback (most recent call last):
        ...
    MissingParameter: maxfluct
    >>> params = {'agents': [{'money':10000, 'stocks':200, 'args':[100, 20]}]}
    >>> agent = randomtrader.RandomTrader(params)
    Traceback (most recent call last):
        ...
    MissingParameter: maxbuy
    >>> params = {'agents': [{'money':10000, 'stocks':200, 'args':[100, 20, 200]}]}
    >>> agent = randomtrader.RandomTrader(params)
    >>> print agent.state()
    Agent ... - owns $10000.00 and    200 securities
    >>> print agent.avgprice
    100
    >>> print agent.maxfluct
    20
    >>> print agent.maxbuy
    200

    The RandomTrader acts by returning a
    dict with (direction, price, quantity) keys.
    >>> len(agent.act())
    3
    
    If avgprice is 0 then the last transaction price is used.
    - direction is buy or sell
    - price is a %.2f float in 
      [avgprice*(1-maxfluct/100), avgprice*(1+maxfluct/100)]
    - quantity is an int in :
      - if direction==BUY, [1,self.maxbuy]
      - if direction==SELL, [1,self.stocks]
    But quantity is strictly controlled :
    neither shortselling nor buy position without required cash
    are allowed.
    >>> order = agent.act()
    >>> order['price'] >= 80
    True
    >>> order['price'] <= 120
    True

    """
    
    def __init__(self, params, offset=0):
        agents.Agent.__init__(self, params, offset)
        try:
            self.sigma_1 = self.args[0]
        except (AttributeError, IndexError): # standard deviation of the fundamentalist weight
            raise MissingParameter, 'sigma_1'
        try:
            self.sigma_2 = self.args[1] # standard deviation of the chartist weight
        except IndexError:
            raise MissingParameter, 'sigma_2'
        try:
            self.n_0 = self.args[2] # noise weight
        except IndexError:
            raise MissingParameter, 'n'
        try:
            self.k_max = self.args[3] # order price tolerance 
        except IndexError:
            raise MissingParameter, 'k_max'
        try:
            self.tau = self.args[4] # order lifetime
        except IndexError:
            raise MissingParameter, 'tau'

        del self.args
        
        self.L_max = params["agents"][0]["l_max"]

        self.g_1 = abs(random.normalvariate(0, self.sigma_1))
        self.g_2 = random.normalvariate(0, self.sigma_2)
        self.n = random.normalvariate(0, self.n_0)
        self.L = random.randint(1, self.L_max)
        self.k = random.random() * self.k_max

    def speak(self, market): # overload the `speak` method to allow agents to view market
        """
        Return order emitted by agent
        """
        order = self.act(market=market)
        order['agent'] = order.get('agent', self)
        return order

    def act(self, world=None, market=None):
        """
        Return random order as a dict with keys in (direction, price, quantity).
        """
        forecast = self.g_1 * market.forecasts["fundamentalist"] + self.g_2 * market.forecasts["chartist"][self.L - 1] + self.n * random.normalvariate(0, 1)
        forecast = forecast / (self.g_1 + self.g_2 + self.n)

        # bound the forecast
        forecast = min(forecast, .2)
        forecast = max(forecast, -.2)

        self.price_forecast = market.lastprice * np.exp(forecast)

        if self.price_forecast > market.lastprice:
            bid = (1. - self.k) * self.price_forecast

            return {'direction':BUY, 'price':bid, 'quantity':1, 'lifetime':self.tau}
        else:
            ask = (1. + self.k) * self.price_forecast 
            return {'direction':SELL, 'price':ask, 'quantity':1, 'lifetime':self.tau}

        # if self.stocks > 0:
        #     direction = random.choice((BUY, SELL))
        # else:
        #     direction = BUY
        # 
        # self.avgprice = market.p_f
        # self.maxfluct = 20
        # self.maxbuy = 200
        # if self.avgprice == 0:
        #     try:
        #         self.avgprice = market.lastprice
        #     except AttributeError:
        #         self.avgprice = 100
        #         logger.warning("No market, no avgprice, avgprice set to 100")
        # price = random.randint(self.avgprice*(100-self.maxfluct), 
        #         self.avgprice*(100+self.maxfluct))/100.
        # if direction:
        #     maxq = self.stocks
        # else:
        #     maxq = min(self.maxbuy, int(self.money/price))
        # try:
        #     quantity = random.randint(1, maxq)
        # except ValueError:
        #     quantity = 1
        # return {'direction':direction, 'price':price, 'quantity':quantity}

def _test():
    """
    Run tests in docstrings
    """
    import doctest
    doctest.testmod(optionflags=+doctest.ELLIPSIS)

if __name__ == '__main__':
    _test()
