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


"""This model tests the random number generation features.
"""


import unittest

import logging
from emulica.core import set_up_logging
set_up_logging(logging.ERROR)

import util
util.set_path()

from emulica.core import emulation as emu
from emulica.core.emulation import Report, Request

EMULATE_UNTIL = 250;

class ControlCreate:

    def run(self, model, a):
        n = 0
        createModule = model.modules["create1"]
        while True:
            m = Request("create1", "create")
            yield createModule.request_socket.put(m)
            yield model.get_sim().timeout(model.rng.expovariate(a))
            n += 1


class ControlSpace:
    def run(self, model):
        sp = model.modules["space1"]
        obs1 = model.modules["observer1"]
        rp_obs1 = obs1.create_report_socket()
        while True:
            yield rp_obs1.get()
            rq = Request("space1","move",params={'program':'p1'})
            yield sp.request_socket.put(rq)


def get_model(a, b):
    model = emu.Model()
    h1 = emu.Holder(model, "h1")
    h2 = emu.Holder(model, "h2")
    obs1 = emu.PushObserver(model, "observer1", "ev1", holder = h1)
    obs2 = emu.PushObserver(model, "observer2", "ev2", holder = h2)
    c = emu.CreateAct(model, "create1", h1)
    sp = emu.SpaceAct(model, "space1")
    sp['setup'].default_time = 1 
    sp.add_program('p1', "rng.expovariate("+str(b)+")", {'source':h1, 'destination':h2})
    model.register_control(ControlCreate, 'run', (model, a))
    model.register_control(ControlSpace)
    return model


def run(a, b, seed, until = 250):
    model = get_model(a, b)   
    model.emulate(until, seed = seed)
    l = [(pid, p.create_time, p.dispose_time, 
          p.shape_history, p.space_history) for (pid, p) in model.products.items()]
    t = model.modules["space1"].trace
    m = model.modules["h1"].monitor.time_average()
    return (l, t, m)

class TestSim6(unittest.TestCase):
            
    def setUp(self):
        print(self.id())
        
    def test_ModelCreate(self):
        get_model(0.7, 1)

    def test_Start(self):
        run(0.7, 1, 1)

    def test_Seed1(self):
        (l1, t1, m) = run(1, 1, 123456)
        (l2, t2, m) = run(1, 1, 123456)
        self.assertEqual(t1, t2)
        self.assertEqual(l1, l2)
    
    def test_Seed2(self):
        (l1, t1, m) = run(1.2, 1, 8750)
        (l2, t2, m) = run(1.2, 1, 8750)
        self.assertEqual(t1, t2)
        self.assertEqual(l1, l2)
        (l3, t3, m) = run(1.2, 1, 480972)
        self.assertNotEqual(t1, t3)
        self.assertNotEqual(l1, l3)
    
    #remove toolong to run this test, but this may take several minutes, beware !
    def toolongtest_RunResults(self):
        e = [(0.7, 976), (0.1, 6532109)]
        s = list()
        replication = 10
        for i in range(replication):
            s.append([run(a, 1, seed+i*375, until = 20000)[2] for (a, seed) in e])

        
        result = [sum([s[i][j] for i in range(replication)])/replication for j in range(len(e))]
        exp_result = [a*a/(1-a) for (a, seed) in e]
        #print result
        #print exp_result
        for i in range(len(result)):
            self.assertAlmostEquals(result[i], exp_result[i], delta = exp_result[i]*0.05)


if __name__ == '__main__':    
    unittest.main()

