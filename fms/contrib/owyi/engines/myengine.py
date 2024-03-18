#!/usr/bin/env python
"""
Asynchronous random with replace engine
"""

import pandas as pd
import random
import logging

logger = logging.getLogger('fms.engines.myengine')

from fms.engines import Engine

class MyEngine(Engine):
    """
    Asynchronous engine, random sampling of agents,
    with replacement.

    Order expirable, orders are deleted when they exceed lifetime

    Multiple, agents can submit multiple orders per speak
    """

    def __init__(self, parameters=None, offset=0):
        """
        Constructor. Takes parameters from config.
        Seeds ramdom engine from parameter.randomseed, if any.
        """
        Engine.__init__(self, parameters, offset)
        self.params = parameters
        self.rank = offset
        self.unique_by_agent = False
        self.clearbooksateod = False
        if parameters:
            random.seed(parameters['randomseed'])

    def run(self, world, agents, market):
        """
        Sample agents (with replacement) and let them speak on market.   
        As market is asynchronous, as soon as an agent speaks, do_clearing
        is called to execute any possible transaction immediately.
        """
        market.sellbook = world.state()['sellbook']
        logger.debug("Starting with sellbook %s" % market.sellbook)
        market.buybook = world.state()['buybook']
        logger.debug("Starting with buybook %s" % market.buybook)
        for day in range(self.days): 
            for time in range(self.daylength):
                market.manage_order_lifetimes()
                agt = random.randint(0, len(agents)-1)
                orders = agents[agt].speak(market)
                orders = [market.sanitize_order(order) for order in orders] # TODO: create a new engine/market that handles agents sending multiple orders. Need to allow `speak` to return a list of orders and need to change `sanitize_order` to accept a list of orders. And also to sanitize against wash trades.
                
                print("sell", [order[0] for order in market.sellbook])
                print("buy", [order[0] for order in market.buybook])
                print(orders)
                input()

                for order in orders:
                    if market.is_valid(agents[agt], order):
                        if self.params.orderslogfile:
                            self.output_order(order)
                        market.record_order(order, world.tick,
                                self.unique_by_agent)
                        if self.showbooks:
                            market.output_books(world.tick)
                        market.do_clearing(world.tick)
                        world.lastmarketinfo.update(
                                {'sellbook':market.sellbook, 'buybook':market.buybook})

                world.tick +=1
                if self.params['timer']:
                    world.show_time(day, time, self.days*self.daylength)

                for agt in agents:
                    agt.equity = agt.stocks * market.lastprice + agt.money
                    # print(agt.equity)
                # try:
                #     print market.sellbook[0][0] - market.buybook[0][0]
                # except:
                #     pass
            if self.clearbooksateod:
                market.clear_books()
            market.summarise_ohlc()

        logger.debug("Ending with sellbook %s" % market.sellbook)
        logger.debug("Ending with buybook %s" % market.buybook)
        
        pd.DataFrame.from_records(market.ohlc).to_csv("yeet.csv")

if __name__ == '__main__':
    print AsynchronousRandWReplace()
