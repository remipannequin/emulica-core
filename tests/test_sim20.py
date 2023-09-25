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
In this test model, we use assemble actuators...
*With assemble keys*
two type of products are created, and then assembled, and finally put in inventory
"""



import unittest

import util
util.set_path()

import logging
from emulica.core import set_up_logging
set_up_logging(logging.WARNING)

from emulica.core import emulation
import logging
logger = logging.getLogger('test_sim20')

EXP_RESULT_RESOURCE = [[(5, 5, 'setup'), (5, 10.0, 'p'), (13.0, 18.0, 'p'), (21.0, 26.0, 'p'), (29.0, 34.0, 'p'), (37.0, 42.0, 'p'), (45.0, 50.0, 'p'), (53.0, 58.0, 'p')], 
                       [(15.0, 15.0, 'setup'), (15.0, 20.0, 'p'), (24.0, 29.0, 'p'), (32.0, 37.0, 'p'), (40.0, 45.0, 'p'), (48.0, 53.0, 'p'), (56.0, 61.0, 'p'), (64.0, 69.0, 'p')]]


EXP_RESULT_PRODUCT = [
(1,  [( 5.0, 10.0, 'assy', 'p')], [(0, 'source1'), (0, 'trans'), (2.0, 'assy_space'), (10.0, 'trans'), (11.0, 'buffer'), (13.0, 'trans'), (15.0, 'unassy_space'), (21.0, 'trans'), (22.0, 'out1')], 0, 100.0), 
(2,  [(13.0, 18.0, 'assy', 'p')], [(1, 'source1'), (11.0, 'trans'), (13.0, 'assy_space'), (18.0, 'trans'), (19.0, 'buffer'), (22.0, 'trans'), (24.0, 'unassy_space'), (29.0, 'trans'), (30.0, 'out1')], 1, 100.0), 
(3,  [(21.0, 26.0, 'assy', 'p')], [(3, 'source1'), (19.0, 'trans'), (21.0, 'assy_space'), (26.0, 'trans'), (27.0, 'buffer'), (30.0, 'trans'), (32.0, 'unassy_space'), (37.0, 'trans'), (38.0, 'out1')], 3, 100.0), 
(4,  [( 5.0, 10.0, 'assy', 'p')], [(5, 'source2'), (5, 'assy_space'), (10.0, 'trans'), (11.0, 'buffer'), (13.0, 'trans'), (15.0, 'unassy_space'), (20.0, 'out2')], 5, 100.0), 
(5,  [(13.0, 18.0, 'assy', 'p')], [(6, 'source2'), (13.0, 'assy_space'), (18.0, 'trans'), (19.0, 'buffer'), (22.0, 'trans'), (24.0, 'unassy_space'), (29.0, 'out2')], 6, 100.0), 
(6,  [(29.0, 34.0, 'assy', 'p')], [(7, 'source1'), (27.0, 'trans'), (29.0, 'assy_space'), (34.0, 'trans'), (35.0, 'buffer'), (38.0, 'trans'), (40.0, 'unassy_space'), (45.0, 'trans'), (46.0, 'out1')], 7, 100.0), 
(7,  [(21.0, 26.0, 'assy', 'p')], [(7, 'source2'), (21.0, 'assy_space'), (26.0, 'trans'), (27.0, 'buffer'), (30.0, 'trans'), (32.0, 'unassy_space'), (37.0, 'out2')], 7, 100.0), 
(8,  [(29.0, 34.0, 'assy', 'p')], [(9, 'source2'), (29.0, 'assy_space'), (34.0, 'trans'), (35.0, 'buffer'), (38.0, 'trans'), (40.0, 'unassy_space'), (45.0, 'out2')], 9, 100.0), 
(9,  [(37.0, 42.0, 'assy', 'p')], [(11, 'source2'), (37.0, 'assy_space'), (42.0, 'trans'), (43.0, 'buffer'), (46.0, 'trans'), (48.0, 'unassy_space'), (53.0, 'out2')], 11, 100.0), 
(10, [(37.0, 42.0, 'assy', 'p')], [(12, 'source1'), (35.0, 'trans'), (37.0, 'assy_space'), (42.0, 'trans'), (43.0, 'buffer'), (46.0, 'trans'), (48.0, 'unassy_space'), (53.0, 'trans'), (54.0, 'out1')], 12, 100.0), 
(11, [(45.0, 50.0, 'assy', 'p')], [(20, 'source1'), (43.0, 'trans'), (45.0, 'assy_space'), (50.0, 'trans'), (51.0, 'buffer'), (54.0, 'trans'), (56.0, 'unassy_space'), (61.0, 'trans'), (62.0, 'out1')], 20, 100.0), 
(12, [(45.0, 50.0, 'assy', 'p')], [(23, 'source2'), (45.0, 'assy_space'), (50.0, 'trans'), (51.0, 'buffer'), (54.0, 'trans'), (56.0, 'unassy_space'), (61.0, 'out2')], 23, 100.0), 
(13, [(53.0, 58.0, 'assy', 'p')], [(30, 'source1'), (51.0, 'trans'), (53.0, 'assy_space'), (58.0, 'trans'), (59.0, 'buffer'), (62.0, 'trans'), (64.0, 'unassy_space'), (69.0, 'trans'), (70.0, 'out1')], 30, 100.0), 
(14, [(53.0, 58.0, 'assy', 'p')], [(35, 'source2'), (53.0, 'assy_space'), (58.0, 'trans'), (59.0, 'buffer'), (62.0, 'trans'), (64.0, 'unassy_space'), (69.0, 'out2')], 35, 100.0)]

EMULATE_UNTIL = 200;


class ControlCreate:
    def run(self, model):
        create1 = model.modules["create_carrier"]
        create2 = model.modules["create_part1"]
        create3 = model.modules["create_part2"]
       
        dates1 = [0, 1]
        requests1 = [
            emulation.Request("create_carrier", "create",params={'productType':'carrier'}, date=d)
            for d in dates1]
        dates2 = [0]*9
        requests2 = [
            emulation.Request("create_part1", "create",params={'productType':'P1'}, date=d)
            for d in dates2]
        requests3 = [
            emulation.Request("create_part2", "create",params={'productType':'P2'}, date=d)
            for d in dates2]
        
        for rq in requests1:
            yield create1.request_socket.put(rq)
        for rq in requests2:
            yield create2.request_socket.put(rq)
        for rq in requests3:
            yield create3.request_socket.put(rq)


class ControlAssy:
    def run(self, model):
        trans = model.modules["trans"]
        assy = model.modules["assy"]
        rp_assy = assy.create_report_socket()
        obs_in = model.modules["obs_input"]
        obs1 = model.modules["obs_source_part1"]
        obs2 = model.modules["obs_source_part2"]
        rp_obsin = obs_in.create_report_socket()
        rp_obs1 = obs1.create_report_socket()
        rp_obs2 = obs2.create_report_socket()
        obs_assy = model.modules["obs_assy"]
        rp_obs_assy = obs_assy.create_report_socket()
        n = 0
        while n < 3:
            ##attente de l'arrivée d'un pièce
            print("waiting for carrier")
            ev = yield rp_obsin.get()
            print(ev)
            print("carrier ready")
            
            print("requesting carrier admission in assy station")
            rq = emulation.Request("trans","move",params={'program':'load_assy'})
            yield trans.request_socket.put(rq)
            
            yield rp_obs_assy.get()
            print("carrier loaded in assembly station")
            ##début process
            print("assembly...")
            yield assy.request_socket.put(emulation.Request("assy","assy", params={"program":'p1_z1'}))
            yield assy.request_socket.put(emulation.Request("assy","assy", params={"program":'p2_z1'}))
            yield assy.request_socket.put(emulation.Request("assy","assy", params={"program":'p1_z1'}))
            yield assy.request_socket.put(emulation.Request("assy","assy", params={"program":'p2_z2'}))
            yield assy.request_socket.put(emulation.Request("assy","assy", params={"program":'p1_z2'}))
            yield assy.request_socket.put(emulation.Request("assy","assy", params={"program":'p2_z2'}))

            ##attente fin process
            fin = 6
            while fin > 0:
                ev = yield rp_assy.get()
                print(ev)
                if ev.what=="idle":
                    fin -= 1
            ##déchargement
            print("unloading assembly station")
            yield trans.request_socket.put(emulation.Request("trans", "move", params={"program": 'unload_assy'}))
            n += 1
    

class ControlUnassy:
    def run(self, model):
        obs = model.modules["obs_buffer"]
        rp_obs = obs.create_report_socket()
        obs_unassy = model.modules["obs_unassy"]
        rp_obs_unassy = obs_unassy.create_report_socket()
        trans = model.modules["trans"]
        unassy = model.modules["unassy"]
        rp_unassy = unassy.create_report_socket()
        n = 0
        while n < 3:
            ev = yield rp_obs.get()
            rq = emulation.Request("trans","move",params={'program':'load_unassy'})
            yield trans.request_socket.put(rq)
            # wait for product to be loaded
            yield rp_obs_unassy.get()
            ##début process
            print("unassy process")
            yield unassy.request_socket.put(emulation.Request("unassy","unassy", params={"program":'z1'}))
            yield unassy.request_socket.put(emulation.Request("unassy","unassy", params={"program":'z2'}))
            ##attente fin process
            fin = 2
            while fin > 0:
                ev = yield rp_unassy.get()
                if ev.what=="idle":
                    fin -= 1
            rq = emulation.Request("trans","move",params={'program':'unload_unassy'})
            yield trans.request_socket.put(rq)
            n += 1


def get_model():
    model = emulation.Model()
    source1 = emulation.Holder(model, "input")
    obs_source1 = emulation.PushObserver(model, "obs_input", holder = source1)
    source2 = emulation.Holder(model, "source_part1")
    obs_source2 = emulation.PushObserver(model, "obs_source_part1", holder = source2)
    source3 = emulation.Holder(model, "source_part2")
    obs_source3 = emulation.PushObserver(model, "obs_source_part2", holder = source3)

    create1 = emulation.CreateAct(model, "create_carrier", destination = source1)
    create2 = emulation.CreateAct(model, "create_part1", destination = source2)
    create3 = emulation.CreateAct(model, "create_part2", destination = source3)

    assy_space = emulation.Holder(model, "assy_space")
    unassy_space = emulation.Holder(model, "unassy_space")
    obs_assy = emulation.PushObserver(model, "obs_assy", holder = assy_space)
    assy = emulation.AssembleAct(model, "assy", assy_holder = assy_space)
    unassy = emulation.DisassembleAct(model, "unassy", unassy_holder = unassy_space)
    obs_unassy = emulation.PushObserver(model, "obs_unassy", holder = unassy_space)
    trans = emulation.SpaceAct(model, "trans")
    buff = emulation.Holder(model, "buffer")
    out1 = emulation.Holder(model, "out1")
    out2 = emulation.Holder(model, "out2")
    obs_buff = emulation.PushObserver(model, "obs_buffer", holder = buff)
    trans.add_program('load_assy', 2, {'source':source1, 'destination':assy_space})
    trans.add_program('unload_assy', 1, {'source':assy_space, 'destination':buff})
    trans.add_program('load_unassy', 2, {'source':buff, 'destination':unassy_space})
    trans.add_program('unload_unassy', 1, {'source':unassy_space, 'destination':source1})
    assy.add_program('p1_z1', 5, {'source':source2, 'key': 'z1'})
    assy.add_program('p1_z2', 5, {'source':source2, 'key': 'z2'})
    assy.add_program('p2_z1', 5, {'source':source3, 'key': 'z1'})
    assy.add_program('p2_z2', 5, {'source':source3, 'key': 'z2'})
    unassy.add_program('z1', 5, {'destination':out1, 'key': 'z1'})
    unassy.add_program('z2', 5, {'destination':out2, 'key': 'z2'})
    model.register_control(ControlCreate)
    model.register_control(ControlAssy)
    model.register_control(ControlUnassy)
    return model


class TestSim20(unittest.TestCase):
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
        prod_out1 = [(pid, p.product_type, p.space_history[-1][1]) for (pid, p) in model.products.items()]
        
        def display_components(p):
            
            s = f"{p.product_type}(#{p.pid})"
            for k, v in p.components.items():
                if k == '':
                    s += f"->{display_components(v)}"
                else:
                    s += f" {k}: {display_components(v)}"
            return s
        out1 = []
        out2 = []
        c = []
        for p in model.modules['out1'].get_products():
            out1.append(display_components(p))
        print("in out2")
        for p in model.modules['out2'].get_products():
            out2.append(display_components(p))
        for p in [p for p in model.products.values() if p.product_type == 'carrier']:
            c.append(display_components(p))
        self.assertListEqual(out1, [
            "P1(#2)->P2(#6)->P1(#3)",
            "P1(#5)->P2(#12)->P1(#7)",
            "P1(#11)->P2(#17)->P1(#13)"])
        self.assertListEqual(out2, [
            "P2(#8)->P1(#4)->P2(#10)",
            "P2(#14)->P1(#9)->P2(#16)",
            "P2(#18)->P1(#15)->P2(#19)"])
        self.assertListEqual(c, ["carrier(#1)","carrier(#20)"])


if __name__ == '__main__':    
    unittest.main()
