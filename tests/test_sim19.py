#!/usr/bin/python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (C) 2023 Rémi Pannequin, Centre de Recherche en Automatique de Nancy remi.pannequin@univ-lorraine.fr
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

"""Test measurment of product physical charateristics.
"""

import logging
from emulica.core import set_up_logging
set_up_logging(logging.ERROR)

import unittest

import util
util.set_path()

from emulica.core.emulation import *
from emulica.core.properties import SetupMatrix

EXP_RESULT_PRODUCT = [(1, [(6.0, 10.0, 'machine', 'p1')], 
                          [(0, 'source'), 
                           (3, 'transporter'), 
                           (5.0, 'espaceMachine'), 
                           (11.9, 'transporter'), 
                           (13.9, 'sink')],
                          {'mass': 5, 'length': 19}, 0, 70), 
                      (2, [(16.9, 20.9, 'machine', 'p1')], 
                          [(0, 'source'),
                           (14.9, 'transporter'), 
                           (16.9, 'espaceMachine'), 
                           (23.8, 'transporter'), 
                           (25.8, 'sink')],
                          {'mass': 5, 'length': 29}, 0, 70), 
                      (3, [(28.8, 32.8, 'machine', 'p1')],
                          [(0, 'source'),
                           (26.8, 'transporter'), 
                           (28.8, 'espaceMachine'), 
                           (36.7, 'transporter'), 
                           (38.7, 'sink')],
                          {'mass': 5, 'length': 39}, 0, 70), 
                      (4, [(41.7, 45.7, 'machine', 'p1')],
                          [(0, 'source'),
                           (39.7, 'transporter'), 
                           (41.7, 'espaceMachine'), 
                           (50.6, 'transporter'), 
                           (52.6, 'sink')],
                          {'mass': 5, 'length': 49}, 0, 70)] 
                                            
                      
EXP_RESULT_MEAS = [(3, 20), (11.9, 19), (14.9, 30), (23.8, 29), (26.8, 40), (36.7, 39), (39.7, 50), (50.6, 49)]
meas_result = []
EMULATE_UNTIL = 70;

class ControlCreate:
    def run(self, model):
        n = 0
        i = 0
        createModule = model.modules["create"]
        while n < 4:
            m = Request("create", "create",params={'physical-properties': {'mass':5, 'length': n*10+20}})
            yield createModule.request_socket.put(m)
            i = (i+1)%4
            n += 1


class ControlMachine:
    def run(self, model):

        sp = model.modules["transporter"]
        machine = model.modules["machine"]
        rp_machine = machine.create_report_socket()
        obs1 = model.modules["obsSource"]
        rp_obs1 = obs1.create_report_socket()
        obs2 = model.modules["obsMachine"]
        rp_obs2 = obs2.create_report_socket()
        meas1 = model.modules["measure1"]
        rp_meas1 = meas1.create_report_socket()
        meas2 = model.modules["measure2"]
        rp_meas2 = meas2.create_report_socket()
        
        while True:
            ##attente de l'arrivée d'un pièce
            ev = yield rp_obs1.get()

            # Observe some physical properties on products
            yield meas1.request_socket.put(Request("measure1", "measure", params={'program':"L"}))
            m = yield rp_meas1.get()
            meas_result.append((m.when, m.how['length']))
            # move
            rq = Request("transporter","move",params={'program':'load'})
            yield sp.request_socket.put(rq)
            ##pièce prête
            ev = yield rp_obs2.get()
            yield machine.request_socket.put(Request("machine","setup", params={"program":"p1"}))
            ##début process
            yield machine.request_socket.put(Request("machine","make"))
            ##attente fin process
            fin = False
            while not fin:
                ev = yield rp_machine.get()
                fin = ev.what=="idle"
            
            yield meas2.request_socket.put(Request("measure2", "measure", params={'program':"Lfast"}))
            m = yield rp_meas2.get()
            meas_result.append((m.when, m.how['length']))
            
            ##déchargement
            yield sp.request_socket.put(Request("transporter", "move", params={"program":'unload'}))


def get_model():
    model = Model()
    source = Holder(model, "source")
    sink = Holder(model, "sink")
    espaceMachine = Holder(model, "espaceMachine")

    obsSource = PushObserver(model, "obsSource", "source-ready", observe_type = False, holder = source)
    measure1 = MeasurementObserver(model, "measure1", holder=source)
    # measure the length of the part, in 3 seconds
    measure1.add_program('L', 3, {'property': 'length'})
    measure2 = MeasurementObserver(model, "measure2", holder=espaceMachine)
    measure2.add_program('Lfast', "product['length']/10", {'property': 'length'})
    obsMachine = PushObserver(model, "obsMachine", "machine-ready", holder = espaceMachine)
    obsSink = PushObserver(model, "obsSink", "sink-ready", holder = sink)
    
    c = CreateAct(model, "create", source)
    sp = SpaceAct(model, "transporter")
    sp.add_program('load', 2, {'source':source, 'destination':espaceMachine})
    sp.add_program('unload', 2, {'source':espaceMachine, 'destination':sink})
    machine = ShapeAct(model, "machine", espaceMachine)
    machine.add_program('p1', 4, {'change': {'length': 'length-1'}})
    m = SetupMatrix(machine.properties, 1)
    m.add('p1','p3',2)
    m.add('p3','p1',3)
    machine['setup'] = m
    model.register_control(ControlCreate)
    model.register_control(ControlMachine)
    return model

def register_control(model):
    model.register_control(ControlCreate)
    model.register_control(ControlMachine)
    return model

class TestSim19(unittest.TestCase):
    
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
        for act, exp in zip(meas_result, EXP_RESULT_MEAS):
            self.assertAlmostEqual(act[0], exp[0])
            self.assertAlmostEqual(act[1], exp[1])


if __name__ == '__main__':    
    unittest.main()
    
