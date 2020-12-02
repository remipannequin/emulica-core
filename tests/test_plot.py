#!/usr/bin/python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (C) 2013 Rémi Pannequin, Centre de Recherche en Automatique de Nancy remi.pannequin@univ-lorraine.fr
# This program is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License version 3, as published 
# by the Free Software Foundation.
# 
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
# PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along 
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE


"""In this model, the create actuator is controled so that the level of product in the queue stay constant"""


import unittest

import logging
from emulica.core import set_up_logging
set_up_logging(logging.ERROR)

#import util
#util.set_path()

from emulica.core import plot

class MockEnv:
    def __init__(self):
        self.now = 0 


class MockHolder:
    def __init__(self):
        self.env = MockEnv()
        self.monitor = plot.Monitor(self.env)
    
    def addEvent(self, t, v):
        self.env.now = t
        self.monitor.observe(v)
    
    
class TestHolderPlot(unittest.TestCase):
    
    def setUp(self):
        print(self.id())

    def test_ProcessTrace(self):
        chart = plot.HolderChart()
        h = MockHolder()
        for i in range(1, 5):
            h.addEvent(i, i*2)
        chart.t_end = 10
        t,v = chart.process_trace(h.monitor.tseries(), h.monitor.yseries())
        print(t,v)
        self.assertEqual(t, [0, 1, 1, 2, 2, 3, 3, 4, 4, 10])
        self.assertEqual(v, [0, 0, 2, 2, 4, 4, 6, 6, 8, 8])

    def test_ProcessTrace0(self):
        chart = plot.HolderChart()
        h = MockHolder()
        chart.t_end = 10
        t,v = chart.process_trace(h.monitor.tseries(), h.monitor.yseries())
        print(t,v)
        self.assertEqual(t, [0, 10])
        self.assertEqual(v, [0, 0])
        

if __name__ == '__main__':    
    unittest.main()
