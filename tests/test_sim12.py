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
"""
This simple model based on sim1 tests the insert_request(): test of out-of-simulation request insertion
"""

import util
util.set_path()

import logging
from emulica.core import set_up_logging
set_up_logging(logging.ERROR)

import unittest



import time
import threading
from emulica.core.emulation import *
from emulica.core import controler

EXP_RESULT = [(1, [], [(5, 'holder1')], 5, 30.1),
              (2, [], [(15, 'holder1')], 15, 30.1),
              (3, [], [(30, 'holder1')], 30, 30.1)]


EMULATE_UNTIL = 30.1;


def get_model():
    model = Model()
    h = Holder(model, "holder1")
    c = CreateAct(model, "create1", h)
    o = PushObserver(model, "obs", "ev1", observe_type = False, holder = h)
    return model

class TestSim12(unittest.TestCase):
    def setUp(self):
        print(self.id())

    def test_ModelCreate(self):
        get_model()

    def test_Start(self):
        model = get_model()
        model.emulate(until = EMULATE_UNTIL)

    def begin_cb(self, model):
        #print("begin = %s"%self.begin)
        self.begin = True
    
    def finish_cb(self, model):
        self.finish = True
    
    def step(self, model):
        #print(model.sim.now)
        self.t.append(model.sim.now)
    
    def test_RunResults(self):
        model = get_model()
        finished = threading.Condition()
        self.begin = False
        self.finish = False
        self.t = []
        timer = controler.TimeControler(model, 
                                        real_time = True, 
                                        rt_factor = 1/5, 
                                        until = EMULATE_UNTIL, 
                                        step=2)
        timer.add_callback(self.begin_cb, controler.EVENT_START)
        timer.add_callback(self.finish_cb, controler.EVENT_FINISH)
        timer.add_callback(self.step, controler.EVENT_TIME)
        timer.start()
        self.assertTrue(timer.is_alive())
        time.sleep(1)
        #attente de 5s et ajout d'une requête de la simulation
        timer.dispatch(Request("create1", "create", date = 5))
        #attente 10s et ajout
        time.sleep(0.1)
        timer.dispatch(Request("create1", "create", date = 15))
        #attente 15s et ajout
        time.sleep(2)
        timer.dispatch(Request("create1", "create", date = 30))
        #attente de fin de simulation (au plus 10s)...
        timer.join(60)
        self.assertTrue(self.begin)
        self.assertTrue(self.finish)
        self.assertEqual([2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30], self.t)
        result = [(pid, p.shape_history, p.space_history, p.create_time, p.dispose_time) for (pid, p) in model.products.items()]
        self.assertEqual(result, EXP_RESULT)

if __name__ == '__main__':
    unittest.main()

