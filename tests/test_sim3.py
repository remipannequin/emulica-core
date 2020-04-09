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
source -> machine -> sink
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
                           (10, 'sink')], 0, 45),
                      (2, [(14, 20, 'machine', 'p3')], 
                          [(10, 'source'), 
                           (10, 'transporter'), 
                           (12, 'espaceMachine'), 
                           (20, 'transporter'), 
                           (23, 'sink')], 10, 45),
                      (3, [(26, 31, 'machine', 'p2')], 
                          [(20, 'source'), 
                           (23, 'transporter'), 
                           (25, 'espaceMachine'), 
                           (31, 'transporter'), 
                           (34, 'sink')], 20, 45), 
                      (4, [(37, 41, 'machine', 'p1')], 
                          [(30, 'source'), 
                           (34, 'transporter'), 
                           (36, 'espaceMachine'), 
                           (41, 'transporter'),
                           (44, 'sink')], 30, 45), 
                      (5, [], 
                          [(40, 'source'),
                           (44, 'transporter')], 40, 45)]

EXP_RESULT_RESOURCE = [[(0, 0, 'setup'), 
                        (0, 2, 'load'), 
                        (7, 7, 'setup'), 
                        (7, 10, 'unload'), 
                        (10, 10, 'setup'), 
                        (10, 12, 'load'), 
                        (20, 20, 'setup'), 
                        (20, 23, 'unload'), 
                        (23, 23, 'setup'), 
                        (23, 25, 'load'), 
                        (31, 31, 'setup'), 
                        (31, 34, 'unload'), 
                        (34, 34, 'setup'), 
                        (34, 36, 'load'),
                        (41, 41, 'setup'), 
                        (41, 44, 'unload'), 
                        (44, 44, 'setup'), 
                        (44, 45, 'load')], 
                       [(2, 3, 'setup'), 
                        (3, 7, 'p1'), 
                        (12, 14, 'setup'), 
                        (14, 20, 'p3'), 
                        (25, 26, 'setup'), 
                        (26, 31, 'p2'), 
                        (36, 37, 'setup'), 
                        (37, 41, 'p1')]]
                        
EMULATE_UNTIL = 45;

class ControlCreate:
    def run(self, model):
        n = 0
        createModule = model.modules["create"]
        report = createModule.create_report_socket()
        while n < 10:
            m = Request("create", "create")
            yield createModule.request_socket.put(m)
            yield report.get()
            #print self.got[0]
            yield model.get_sim().timeout(10)


class ControlMachine:
    def run(self, model):
        prog = ['p1','p3','p2']
        i = 0
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
            yield machine.request_socket.put(Request("machine","setup", params={"program":prog[i]}))
            i = (i+ 1) % 3
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
    obsSource = PushObserver(model, "obsSource", "source-ready", holder = source)
    obsMachine = PushObserver(model, "obsMachine", "machine-ready", holder = espaceMachine)
    c = CreateAct(model, "create", source)
    sp = SpaceAct(model, "transporter")
    sp.add_program('load', 2, {'source':source, 'destination':espaceMachine})
    sp.add_program('unload', 3, {'source':espaceMachine, 'destination':sink})
    machine = ShapeAct(model, "machine", espaceMachine)
    machine.add_program('p1', 4)
    machine.add_program('p2', 5)
    machine.add_program('p3', 6)
    m = SetupMatrix(machine.properties, 1)
    m.add('p1','p3',2)
    m.add('p3','p1',2)
    machine['setup'] = m
    initialize_control(model)
    return model

def initialize_control(model):
    model.register_control(ControlCreate)
    model.register_control(ControlMachine)

class TestSim3(unittest.TestCase):
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
