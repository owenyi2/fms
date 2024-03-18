#!/usr/bin/env python
# -*- coding: utf8 -*-

import random
import logging
import numpy as np

from fms import agents
from fms.utils import BUY, SELL
from fms.utils.exceptions import MissingParameter

logger = logging.getLogger('fms.agents.MarketMaking')

class MarketMaking(agents.Agent):
    
    def __init__(self, params, offset=0):
        agents.Agent.__init__(self, params, offset)
        try:
            self.sigma_1 = self.args[0]
        except (AttributeError, IndexError): # weight_1. controls reservation price
            raise MissingParameter, 'sigma_1'
 
        try:
            self.sigma_2 = self.args[1]
        except (AttributeError, IndexError): # weight_2. controls spread
            raise MissingParameter, 'sigma_2'
        try:
            self.tau = self.args[2] # order lifetime
        except IndexError:
            raise MissingParameter, 'tau'
        del self.args

        self.w_1 = np.abs(random.normalvariate(0, self.sigma_1))
        self.w_2 = np.abs(random.normalvariate(0, self.sigma_2))

    def speak(self, market): 
        # overload the `speak` method to allow agents to view market

        # TODO: overload `speak` to allow sending a bid and ask simultaneously

        # Also Realised that we need to implement an account balance and tracking of position to properly do this
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
        sellbook = market.info()["sellbook"]
        buybook = market.info()["buybook"]

        # print sellbook[0]
        # print buybook[0]

        if sellbook[0][0] == "unset sellbook" or buybook[0][0] == "unset buybook":
            return [{"direction": BUY, "price": market.p_f * .99, 'lifetime':self.tau}, 
                {"direction": SELL, "price": market.p_f * 1.01, 'lifetime':self.tau}]

        # self.w_1 > 0. E.g. if we have too much inventory, then we want to make it more likely our ask is filled than our bid so we drop the price
        self.reservation_price = (sellbook[0][0] + buybook[0][0]) / 2 - self.stocks * self.w_1
    
        # self.w_2 > 0. Because spread is positive
        self.spread = (sellbook[0][0] - buybook[0][0]) / 2 * self.w_2
        
        # print("order")
        # print(self.reservation_price + self.spread, self.reservation_price - self.spread)
        # print("market")
        # print(sellbook[0][0], buybook[0][0])

        return [{"direction": BUY, "price": self.reservation_price - self.spread, 'lifetime':self.tau}, 
                {"direction": SELL, "price": self.reservation_price + self.spread, 'lifetime':self.tau}]
    

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
