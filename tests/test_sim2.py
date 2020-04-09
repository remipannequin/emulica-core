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
Create -> holder -> space -> holder
"""

import unittest

import logging
from emulica.core import set_up_logging
set_up_logging(logging.ERROR)

import util
util.set_path()

from emulica.core.emulation import *

EXP_RESULT_PRODUCT = [(1, [], [(0, 'h1'), (0, 'space1'), (2, 'h2')], 0, 41),
                      (2, [], [(10, 'h1'), (10, 'space1'), (12, 'h2')], 10, 41),
                      (3, [], [(20, 'h1'), (20, 'space1'), (22, 'h2')], 20, 41),
                      (4, [], [(30, 'h1'), (30, 'space1'), (32, 'h2')], 30, 41),
                      (5, [], [(40, 'h1'), (40, 'space1')], 40, 41)]                  
EXP_RESULT_RESOURCE = [(0, 0, 'setup'), 
                       (0, 2, 'p1'), 
                       (10, 12, 'p1'), 
                       (20, 22, 'p1'), 
                       (30, 32, 'p1'), 
                       (40, 41, 'p1')]
                       
EMULATE_UNTIL = 41;

class ControlCreate:
    def run(self, model):
        n = 0
        createModule = model.modules["create1"]
        report = createModule.create_report_socket()
        while n < 10:
            m = Request("create1", "create")
            yield createModule.request_socket.put(m)
            yield report.get()
            yield model.get_sim().timeout(10)


class ControlSpace:
    def run(self, model):
        sp = model.modules["space1"]
        obs1 = model.modules["observer1"]
        report = obs1.create_report_socket()
        while True:
            ev = yield report.get()
            #print ev
            rq = Request("space1","move",params={'program':'p1'})
            yield sp.request_socket.put(rq)
 
    
class MonitorSpace:
    def run(self, model):
        sp = model.modules["space1"]
        report = sp.create_report_socket()
        while True:
            yield report.get()
            

def get_model():
    model = Model()
    h1 = Holder(model, "h1")
    h2 = Holder(model, "h2")
    obs1 = PushObserver(model, "observer1", "ev1", holder = h1)
    c = CreateAct(model, "create1", h1)
    sp = SpaceAct(model, "space1")
    sp.add_program('p1', 2, {'source':h1, 'destination':h2})
    initialize_control(model)
    return model

def initialize_control(model):
    model.register_control(ControlCreate)
    model.register_control(ControlSpace)
    model.register_control(MonitorSpace)
  

class TestSim2(unittest.TestCase):
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
        result_resource = model.modules["space1"].trace
        self.assertEqual(result_product, EXP_RESULT_PRODUCT)
        self.assertEqual(result_resource, EXP_RESULT_RESOURCE)


if __name__ == '__main__':    
    unittest.main()
