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

"""Test for the product physical charateristics. 
"""

import logging
from emulica.core import set_up_logging
set_up_logging(logging.ERROR)

import unittest

import util
util.set_path()

from emulica.core.emulation import *
from emulica.core.properties import SetupMatrix

EXP_RESULT_PRODUCT = [(1, [(3, 7, 'machine', 'p1')], 
                          [(0, 'source'), 
                           (0, 'transporter'), 
                           (2, 'espaceMachine'), 
                           (7, 'transporter'), 
                           (9, 'sink')],
                          {'mass': 0, 'length': 1}, 0, 50), 
                      (2, [(13, 14, 'machine', 'p3')], 
                          [(0, 'source'),
                           (9, 'transporter'), 
                           (11, 'espaceMachine'), 
                           (14, 'transporter'), 
                           (16, 'sink')],
                          {'mass': 1, 'length': 4}, 0, 50), 
                      (3, [(19, 24, 'machine', 'p2')],
                          [(0, 'source'),
                           (16, 'transporter'), 
                           (18, 'espaceMachine'), 
                           (24, 'transporter'), 
                           (26, 'sink')],
                          {'mass': 2, 'length': 3}, 0, 50), 
                      (4, [(29, 32, 'machine', 'p3')],
                          [(0, 'source'),
                           (26, 'transporter'), 
                           (28, 'espaceMachine'), 
                           (32, 'transporter'), 
                           (34, 'sink')],
                          {'mass': 3, 'length': 4}, 0, 50)] 
                                            
                      
EXP_RESULT_RESOURCE = [[(0, 0, 'setup'), 
                        (0, 2, 'load'), 
                        (7, 7, 'setup'), 
                        (7, 9, 'unload'), 
                        (9, 9, 'setup'), 
                        (9, 11, 'load'), 
                        (14, 14, 'setup'), 
                        (14, 16, 'unload'), 
                        (16, 16, 'setup'), 
                        (16, 18, 'load'), 
                        (24, 24, 'setup'), 
                        (24, 26, 'unload'), 
                        (26, 26, 'setup'), 
                        (26, 28, 'load'), 
                        (32, 32, 'setup'), 
                        (32, 34, 'unload')], 
                       [(2, 3, 'setup'), 
                        (3, 7, 'p1'), 
                        (11, 13, 'setup'), 
                        (13, 14, 'p3'), 
                        (18, 19, 'setup'), 
                        (19, 24, 'p2'), 
                        (28, 29, 'setup'), 
                        (29, 32, 'p3')]]

EMULATE_UNTIL = 50;

class ControlCreate:
    def run(self, model):
        n = 0
        i = 0
        pType = ['type1', 'type2', 'type3', 'type2']
        createModule = model.modules["create"]
        while n < 4:
            m = Request("create", "create",params={'productType':pType[i], 'physical-properties': {'mass':n, 'length': 5}})
            yield createModule.request_socket.put(m)
            i = (i+1)%4
            n += 1


class ControlMachine:
    def run(self, model):
        prog = {'type1':'p1','type2':'p3','type3':'p2'}
        sp = model.modules["transporter"]
        machine = model.modules["machine"]
        rp_machine = machine.create_report_socket()
        obs1 = model.modules["obsSource"]
        rp_obs1 = obs1.create_report_socket()
        obs2 = model.modules["obsMachine"]
        rp_obs2 = obs2.create_report_socket()
        while True:
            ##attente de l'arrivée d'un pièce
            ev = yield rp_obs1.get()
            rq = Request("transporter","move",params={'program':'load'})
            yield sp.request_socket.put(rq)
            ##pièce prête
            ev = yield rp_obs2.get()
            p = prog[ev.how['productType']]
            yield machine.request_socket.put(Request("machine","setup", params={"program":p}))
            ##début process
            yield machine.request_socket.put(Request("machine","make"))
            ##attente fin process
            fin = False
            while not fin:
                ev = yield rp_machine.get()
                fin = ev.what=="idle"
            ##déchargement
            yield sp.request_socket.put(Request("transporter", "move", params={"program":'unload'}))


def get_model():
    model = Model()
    source = Holder(model, "source")
    sink = Holder(model, "sink")
    espaceMachine = Holder(model, "espaceMachine")

    obsSource = PushObserver(model, "obsSource", "source-ready", observe_type = False, holder = source)
    obsMachine = PushObserver(model, "obsMachine", "machine-ready", holder = espaceMachine)
    obsSink = PushObserver(model, "obsSink", "sink-ready", holder = sink)
    
    c = CreateAct(model, "create", source)
    sp = SpaceAct(model, "transporter")
    sp.add_program('load', 2, {'source':source, 'destination':espaceMachine})
    sp.add_program('unload', 2, {'source':espaceMachine, 'destination':sink})
    machine = ShapeAct(model, "machine", espaceMachine)
    machine.add_program('p1', 4, {'change': {'length': 1}})
    machine.add_program('p2', 5, {'change': {'length': "mass + 1"}})
    machine.add_program('p3', "product['mass']", {'change': {'length': "length - 1"}})
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

class TestSim14(unittest.TestCase):
    
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
        result_product = [(pid, 
                       p.shape_history, 
                       p.space_history,
                       dict([(key, p[key]) for key in p.properties.keys()]),
                       p.create_time, 
                       p.dispose_time) for (pid, p) in model.products.items()]
        result_resource = [model.modules["transporter"].trace, model.modules["machine"].trace]
        self.assertEqual(result_product, EXP_RESULT_PRODUCT)
        self.assertEqual(result_resource, EXP_RESULT_RESOURCE)


if __name__ == '__main__':    
    unittest.main()
    
