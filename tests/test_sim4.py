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
from emulica.core.properties import SetupMatrix

EXP_RESULT_PRODUCT = [(1, [(3, 7, 'machine', 'p1')], 
                          [(0, 'source'), 
                           (0, 'transporter'), 
                           (2, 'espaceMachine'), 
                           (7, 'transporter'), 
                           (9, 'sink')], 0, 41), 
                      (2, [(13, 19,'machine', 'p3')], 
                          [(0, 'source'),
                           (9, 'transporter'), 
                           (11, 'espaceMachine'), 
                           (19, 'transporter'), 
                           (21, 'sink')], 0, 41), 
                      (3, [(24, 29, 'machine', 'p2')],
                          [(0, 'source'),
                           (21, 'transporter'), 
                           (23, 'espaceMachine'), 
                           (29, 'transporter'), 
                           (31, 'sink')], 0, 41), 
                      (4, [(34, 38, 'machine', 'p1')],
                          [(0, 'source'),
                           (31, 'transporter'), 
                           (33, 'espaceMachine'), 
                           (38, 'transporter'), 
                           (40, 'sink')], 0, 41)] 
                      
EXP_RESULT_RESOURCE = [[(0, 0, 'setup'), 
                        (0, 2, 'load'), 
                        (7, 7, 'setup'), 
                        (7, 9, 'unload'), 
                        (9, 9, 'setup'), 
                        (9, 11, 'load'), 
                        (19, 19, 'setup'), 
                        (19, 21, 'unload'), 
                        (21, 21, 'setup'), 
                        (21, 23, 'load'), 
                        (29, 29, 'setup'), 
                        (29, 31, 'unload'), 
                        (31, 31, 'setup'), 
                        (31, 33, 'load'), 
                        (38, 38, 'setup'), 
                        (38, 40, 'unload')], 
                       [(2, 3, 'setup'), 
                        (3, 7, 'p1'), 
                        (11, 13, 'setup'), 
                        (13, 19, 'p3'), 
                        (23, 24, 'setup'), 
                        (24, 29, 'p2'), 
                        (33, 34, 'setup'), 
                        (34, 38, 'p1')]]
                        
EMULATE_UNTIL = 41;

class ControlCreate:
    def run(self, model):
        n = 0
        i = 0
        pType = ['type1', 'type2', 'type3']
        createModule = model.modules["create"]
        while n < 4:
            m = Request("create", "create",params={'productType':pType[i]})
            yield createModule.request_socket.put(m)
            i = (i+1)%3
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
            #print ev
            p = prog[ev.how['productType']]
            yield machine.request_socket.put(Request("machine","setup", params={"program":p}))
            ##début process
            yield machine.request_socket.put(Request("machine","make"))
            ##attente fin process
            fin = False
            while not fin:
                e = yield rp_machine.get()
                fin = e.what=="idle"
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
    machine.add_program('p1', 4)
    machine.add_program('p2', 5)
    machine.add_program('p3', 6)
    m = SetupMatrix(machine.properties, 1)
    m.add('p1','p3',2)
    m.add('p3','p1',3)
    machine.properties['setup'] = m
    model.register_control(ControlCreate)
    model.register_control(ControlMachine)
    return model

def register_control(model):
    model.register_control(ControlCreate)
    model.register_control(ControlMachine)
    return model

class TestSim4(unittest.TestCase):
    
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
        result_resource = [model.modules["transporter"].trace, model.modules["machine"].trace]
        self.assertEqual(result_product, EXP_RESULT_PRODUCT)
        self.assertEqual(result_resource, EXP_RESULT_RESOURCE)


if __name__ == '__main__':    
    unittest.main()

