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


import unittest

import logging
from emulica.core import set_up_logging
set_up_logging(logging.ERROR)

import util
util.set_path()

"""
Real time / Hybrid time tests. Model based on sim1.
"""


import time
import threading
import emulica.core.emulation as emu
from emulica.core import controler
import logging
import test_sim1 as sim1

class TestSim9(unittest.TestCase):
    def setUp(self):
        print(self.id())

    def todotest_Start(self):
        model = sim1.get_model()
        sim1.register_control(model)
        finished = threading.Condition()
        def release_condition(model):
            finished.acquire()
            finished.notify()
            finished.release()
        
        timer = controler.TimeControler(model, real_time = True, rt_factor = 10, until = sim1.EMULATE_UNTIL)
        timer.add_callback(release_condition, controler.EVENT_FINISH)
        timer.start()
        #attente de 20s et *pause* de la simulation
        time.sleep(2)
        timer.pause()
        #attente 10s et reprise
        time.sleep(1)
        timer.resume()
        #attente de fin de simulation...
        if not timer.finished:
            finished.acquire()
            finished.wait()
            finished.release()
        
        result = [(pid, 
                   p.shape_history, 
                   p.space_history, 
                   p.create_time, 
                   p.dispose_time) for (pid, p) in model.products.items()]
        self.assertEqual(result, EXP_RESULT)


if __name__ == '__main__':    
    unittest.main()


