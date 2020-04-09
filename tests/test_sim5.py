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

import util
util.set_path()

from emulica.core.emulation import *


EXP_RESULT_PRODUCT = [(1, [], [(0, 'holder1')], 0, 1), 
              (2, [], [(0, 'holder1')], 0, 2), 
              (3, [], [(1, 'holder1')], 1, 3), 
              (4, [], [(2, 'holder1')], 2, 4), 
              (5, [], [(3, 'holder1')], 3, 5), 
              (6, [], [(4, 'holder1')], 4, 6), 
              (7, [], [(5, 'holder1')], 5, 7), 
              (8, [], [(6, 'holder1')], 6, 8), 
              (9, [], [(7, 'holder1')], 7, 9), 
              (10, [], [(8, 'holder1')], 8, 10), 
              (11, [], [(9, 'holder1')], 9, 11), 
              (12, [], [(10, 'holder1')], 10, 12), 
              (13, [], [(11, 'holder1')], 11, 13), 
              (14, [], [(12, 'holder1')], 12, 14), 
              (15, [], [(13, 'holder1')], 13, 15), 
              (16, [], [(14, 'holder1')], 14, 16), 
              (17, [], [(15, 'holder1')], 15, 17), 
              (18, [], [(16, 'holder1')], 16, 18), 
              (19, [], [(17, 'holder1')], 17, 19), 
              (20, [], [(18, 'holder1')], 18, 20), 
              (21, [], [(19, 'holder1')], 19, 21), 
              (22, [], [(20, 'holder1')], 20, 22), 
              (23, [], [(21, 'holder1')], 21, 23), 
              (24, [], [(22, 'holder1')], 22, 24), 
              (25, [], [(23, 'holder1')], 23, 25), 
              (26, [], [(24, 'holder1')], 24, 26), 
              (27, [], [(25, 'holder1')], 25, 27), 
              (28, [], [(26, 'holder1')], 26, 28), 
              (29, [], [(27, 'holder1')], 27, 29), 
              (30, [], [(28, 'holder1')], 28, 30), 
              (31, [], [(29, 'holder1')], 29, 31), 
              (32, [], [(30, 'holder1')], 30, 32), 
              (33, [], [(31, 'holder1')], 31, 33), 
              (34, [], [(32, 'holder1')], 32, 34), 
              (35, [], [(33, 'holder1')], 33, 35), 
              (36, [], [(34, 'holder1')], 34, 36), 
              (37, [], [(35, 'holder1')], 35, 37), 
              (38, [], [(36, 'holder1')], 36, 38), 
              (39, [], [(37, 'holder1')], 37, 39), 
              (40, [], [(38, 'holder1')], 38, 40), 
              (41, [], [(39, 'holder1')], 39, 41), 
              (42, [], [(40, 'holder1')], 40, 42), 
              (43, [], [(41, 'holder1')], 41, 43), 
              (44, [], [(42, 'holder1')], 42, 44), 
              (45, [], [(43, 'holder1')], 43, 45), 
              (46, [], [(44, 'holder1')], 44, 46), 
              (47, [], [(45, 'holder1')], 45, 47), 
              (48, [], [(46, 'holder1')], 46, 48), 
              (49, [], [(47, 'holder1')], 47, 49), 
              (50, [], [(48, 'holder1')], 48, 50), 
              (51, [], [(49, 'holder1')], 49, 51), 
              (52, [], [(50, 'holder1')], 50, 52), 
              (53, [], [(51, 'holder1')], 51, 53), 
              (54, [], [(52, 'holder1')], 52, 54), 
              (55, [], [(53, 'holder1')], 53, 55), 
              (56, [], [(54, 'holder1')], 54, 56), 
              (57, [], [(55, 'holder1')], 55, 57), 
              (58, [], [(56, 'holder1')], 56, 58), 
              (59, [], [(57, 'holder1')], 57, 59), 
              (60, [], [(58, 'holder1')], 58, 60), 
              (61, [], [(59, 'holder1')], 59, 61), 
              (62, [], [(60, 'holder1')], 60, 62), 
              (63, [], [(61, 'holder1')], 61, 63), 
              (64, [], [(62, 'holder1')], 62, 64), 
              (65, [], [(63, 'holder1')], 63, 65), 
              (66, [], [(64, 'holder1')], 64, 66), 
              (67, [], [(65, 'holder1')], 65, 67), 
              (68, [], [(66, 'holder1')], 66, 68), 
              (69, [], [(67, 'holder1')], 67, 69), 
              (70, [], [(68, 'holder1')], 68, 70), 
              (71, [], [(69, 'holder1')], 69, 71), 
              (72, [], [(70, 'holder1')], 70, 72), 
              (73, [], [(71, 'holder1')], 71, 73), 
              (74, [], [(72, 'holder1')], 72, 74), 
              (75, [], [(73, 'holder1')], 73, 75), 
              (76, [], [(74, 'holder1')], 74, 76), 
              (77, [], [(75, 'holder1')], 75, 77), 
              (78, [], [(76, 'holder1')], 76, 78), 
              (79, [], [(77, 'holder1')], 77, 79), 
              (80, [], [(78, 'holder1')], 78, 80), 
              (81, [], [(79, 'holder1')], 79, 81), 
              (82, [], [(80, 'holder1')], 80, 82), 
              (83, [], [(81, 'holder1')], 81, 83), 
              (84, [], [(82, 'holder1')], 82, 84), 
              (85, [], [(83, 'holder1')], 83, 85), 
              (86, [], [(84, 'holder1')], 84, 86), 
              (87, [], [(85, 'holder1')], 85, 87), 
              (88, [], [(86, 'holder1')], 86, 88), 
              (89, [], [(87, 'holder1')], 87, 89), 
              (90, [], [(88, 'holder1')], 88, 90), 
              (91, [], [(89, 'holder1')], 89, 91), 
              (92, [], [(90, 'holder1')], 90, 92), 
              (93, [], [(91, 'holder1')], 91, 93), 
              (94, [], [(92, 'holder1')], 92, 94), 
              (95, [], [(93, 'holder1')], 93, 95), 
              (96, [], [(94, 'holder1')], 94, 96), 
              (97, [], [(95, 'holder1')], 95, 97), 
              (98, [], [(96, 'holder1')], 96, 98), 
              (99, [], [(97, 'holder1')], 97, 99), 
              (100, [], [(98, 'holder1')], 98, 100), 
              (101, [], [(99, 'holder1')], 99, 101), 
              (102, [], [(100, 'holder1')], 100, 101)]

EMULATE_UNTIL = 101;

class ControlCreate:
    def run(self, model):
        createModule = model.modules["create1"]
        observerModule = model.modules["observer1"]
        rp_obs = observerModule.create_report_socket(multiple_observation = True)
        while True:
            yield createModule.request_socket.put(Request("create1", "create"))
            yield rp_obs.get()

class ControlDispose:
    def run(self, model):
        disposeModule = model.modules["dispose1"]
        observerModule = model.modules["observer1"]
        rp_obs = observerModule.create_report_socket(multiple_observation = True)
        while True:
            yield rp_obs.get()
            yield disposeModule.request_socket.put(Request("dispose1","dispose",date=model.get_sim().now+1))

def get_model():
    model = Model()
    h = Holder(model, "holder1")
    obs1 = PushObserver(model, "observer1", "ev1", observe_type = False, holder = h)
    c = CreateAct(model,"create1", h)
    d = DisposeAct(model,"dispose1", h)
    model.register_control(ControlDispose)
    model.register_control(ControlCreate)
    return model
    
    
class TestSim5(unittest.TestCase):
    
    def setUp(self):
        print(self.id())
    
    def test_ModelCreate(self):
        get_model()

    def test_Start(self):
        model = get_model()
        model.emulate(until = EMULATE_UNTIL)

    def test_RunResults(self):
        model = get_model()
        model.emulate(until = EMULATE_UNTIL)
        result_product = [(pid, p.shape_history, 
                       p.space_history, 
                       p.create_time, 
                       p.dispose_time) for (pid, p) in model.products.items()]
        self.assertEqual(result_product, EXP_RESULT_PRODUCT)



if __name__ == '__main__':    
    unittest.main()
