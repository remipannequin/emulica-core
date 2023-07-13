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


"""
Test resource in programs
"""



import unittest

import util
util.set_path()

import logging
from emulica.core import set_up_logging
set_up_logging(logging.WARNING)

from emulica.core import emulation
import logging
logger = logging.getLogger('test_sim21')


EXP_RESULT_PRODUCT = [(1, 
                       [(2.0, 5.0, 'machine', 'p1')],
                       [(0, 'input'),
                        (0, 'trans'),
                        (2.0, 'buffer'),
                        (5.0, 'trans'), 
                        (7.0, 'sink')], 0, 200), 
                      (2, 
                       [(9.0, 12.0, 'machine', 'p1')], 
                       [(1, 'input'),
                        (7.0, 'trans'),
                        (9.0, 'buffer'),
                        (12.0, 'trans'),
                        (14.0, 'sink')], 1, 200), 
                      (3, 
                       [(16.0, 19.0, 'machine', 'p1')], 
                       [(2, 'input'), 
                        (14.0, 'trans'), 
                        (16.0, 'buffer'), 
                        (19.0, 'trans'), 
                        (21.0, 'sink')], 2, 200), 
                      (4, 
                       [(23.0, 26.0, 'machine', 'p1')], 
                       [(3, 'input'), 
                        (21.0, 'trans'), 
                        (23.0, 'buffer'), 
                        (26.0, 'trans'), 
                        (28.0, 'sink')], 3, 200), 
                      (5, 
                       [(30.0, 33.0, 'machine', 'p1')], 
                       [(4, 'input'), 
                        (28.0, 'trans'), 
                        (30.0, 'buffer'), 
                        (33.0, 'trans'), 
                        (35.0, 'sink')], 4, 200)]

EXP_RESULT_RESOURCE = [[(0, 0, 'setup'),
                        (0, 2.0, 'load'),
                        (5.0, 5.0, 'setup'), 
                        (5.0, 7.0, 'unload'), 
                        (7.0, 7.0, 'setup'), 
                        (7.0, 9.0, 'load'), 
                        (12.0, 12.0, 'setup'), 
                        (12.0, 14.0, 'unload'),
                        (14.0, 14.0, 'setup'), 
                        (14.0, 16.0, 'load'), 
                        (19.0, 19.0, 'setup'), 
                        (19.0, 21.0, 'unload'), 
                        (21.0, 21.0, 'setup'), 
                        (21.0, 23.0, 'load'),
                        (26.0, 26.0, 'setup'), 
                        (26.0, 28.0, 'unload'), 
                        (28.0, 28.0, 'setup'), 
                        (28.0, 30.0, 'load'),
                        (33.0, 33.0, 'setup'), 
                        (33.0, 35.0, 'unload')], 
                       [(2.0, 2.0, 'setup'), 
                        (2.0, 5.0, 'p1'), 
                        (9.0, 12.0, 'p1'), 
                        (16.0, 19.0, 'p1'), 
                        (23.0, 26.0, 'p1'), 
                        (30.0, 33.0, 'p1')]]



EMULATE_UNTIL = 200;


class ControlCreate:
    def run(self, model):
        create = model.modules["create"]
        dates1 = [0, 1, 2, 3, 4]
        requests = [
            emulation.Request("create_carrier", "create",params={'productType':'carrier'}, date=d)
            for d in dates1]
        for rq in requests:
            yield create.request_socket.put(rq)
        

class ControlInput:
    def run(self, model):
        obs = model.modules['obs_input'].create_report_socket()
        obs2 = model.modules['obs_buffer'].create_report_socket(multiple_observation=True)
        while True:
            # wait for a part to arrive
            yield obs.get()
            yield from emulation.execute(model, 'trans', 'move', 'load')
            # wait for the part to leave the buffer
            ev = yield obs2.get()
            while ev.how['present'] == True:
                ev = yield obs2.get()

class ControlMachine:
    def run(self, model):
        obs = model.modules['obs_buffer'].create_report_socket(multiple_observation=True)
        while True:
            ev = yield obs.get()
            if ev.how['present']:
                yield from emulation.execute(model, 'machine', 'make', 'p1')
                yield from emulation.execute(model, 'trans', 'move', 'unload')


def get_model():
    model = emulation.Model()
    source = emulation.Holder(model, "input")
    obs_source = emulation.PushObserver(model, "obs_input", holder = source)
   

    create = emulation.CreateAct(model, "create", destination = source)
   
    buff = emulation.Holder(model, "buffer")
    obs_buff = emulation.PushObserver(model, "obs_buffer", holder = buff, observe_absence=True)
    sink = emulation.Holder(model, "sink")

    trans = emulation.SpaceAct(model, "trans")
    machine = emulation.ShapeAct(model, "machine", buff)

    operator = emulation.Resource(model, 'operator')
    trans.add_program('load', 2, {'source':source, 'destination':buff}, [operator])
    trans.add_program('unload', 2, {'source':buff, 'destination':sink}, [operator])
  
    machine.add_program('p1', 3, {}, [operator])

    model.register_control(ControlCreate)
    model.register_control(ControlInput)
    model.register_control(ControlMachine)
    return model


class TestSim21(unittest.TestCase):
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
                       p.create_time, 
                       p.dispose_time) for (pid, p) in model.products.items()]
        result_resource = [model.get_module("trans").trace, model.get_module("machine").trace]
        self.assertEqual(result_product, EXP_RESULT_PRODUCT)
        self.assertEqual(result_resource, EXP_RESULT_RESOURCE)

        


if __name__ == '__main__':    
    unittest.main()
