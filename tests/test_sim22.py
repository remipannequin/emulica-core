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


import util
util.set_path()

import unittest

import logging
from emulica.core import set_up_logging
set_up_logging(logging.ERROR)

"""Test using control functions instead of Control Classes, because they usually have only one method..."""

import emulica.core.emulation as emu

EXP_RESULT = [(1, [], [(0, 'holder1')], 0, 4),
              (2, [], [(10, 'holder1')], 10, 14), 
              (3, [], [(20, 'holder1')], 20, 24), 
              (4, [], [(30, 'holder1')], 30, 34), 
              (5, [], [(40, 'holder1')], 40, 44), 
              (6, [], [(50, 'holder1')], 50, 54), 
              (7, [], [(60, 'holder1')], 60, 64), 
              (8, [], [(70, 'holder1')], 70, 74), 
              (9, [], [(80, 'holder1')], 80, 84), 
              (10, [], [(90, 'holder1')], 90, 94)]

EMULATE_UNTIL = 100;

#Control processes
def controlCreate(model):
    n = 0
    createModule = model.modules["create1"]
    report = createModule.create_report_socket()
    while n < 10:
        m = emu.Request("create1", "create")
        yield createModule.request_socket.put(m)
        #print "send request to create actuator"
        rp = yield report.get()
        #print(rp)
        #print "got report from create actuator"
        yield model.get_sim().timeout(10)

def controlDispose(model):
    disposeModule = model.modules["dispose1"]
    observerModule = model.modules["observer1"]
    report = observerModule.create_report_socket()
    act_report = disposeModule.create_report_socket()
    while True:
        rp = yield report.get()
        #print("got report from observer1", rp)
        #print("sending request to dispose")
        r = emu.Request(actor="dispose1",action="dispose",date=model.current_time()+4)
        #print(r)
        yield disposeModule.request_socket.put(r)
        r2 = yield act_report.get()
        #print("got report from dispose act", r2)
            
        

def get_model():
    model = emu.Model()
    h = emu.Holder(model, "holder1")
    obs1 = emu.PushObserver(model, "observer1", "ev1", observe_type = False, holder = h)
    c = emu.CreateAct(model, "create1", h)
    d = emu.DisposeAct(model, "dispose1", h)
    register_control(model)
    return model

def register_control(model):
    model.register_control_function(controlCreate)
    model.register_control_function(controlDispose)
    return model

class TestSim1(unittest.TestCase):
    """
    In this very simple example, we create the mot simple model possible:
    a create actuator put some product in a holder. These product trigger 
    a dispose actuator thanks to a product observer on the holder.
    """

    """
    def test_ModelCreate(self):
        get_model()
    
    
    def test_ModelControl(self):
        #register control processes
        model = emu.Model()
        model.register_control(ControlCreate)
        model.register_control(ControlDispose)
    """
    
    def setUp(self):
        print(self.id())
    
    def test_Start(self):
        model = get_model()
        model.emulate(until = EMULATE_UNTIL)


    def test_RunResults(self):
        model = get_model()
        
        model.emulate(until = EMULATE_UNTIL)
        result = [(pid, 
                   p.shape_history, 
                   p.space_history, 
                   p.create_time, 
                   p.dispose_time) for (pid, p) in model.products.items()]
        self.assertEqual(result, EXP_RESULT)

    """
    def test_MultipleRun(self):
        model = get_model()
        model.emulate(until = EMULATE_UNTIL)
        model.emulate(until = EMULATE_UNTIL)
        result = [(pid, 
                   p.shape_history, 
                   p.space_history, 
                   p.create_time, 
                   p.dispose_time) for (pid, p) in model.products.items()]
        self.assertEqual(result, EXP_RESULT)
    """

if __name__ == '__main__':    
    unittest.main()

