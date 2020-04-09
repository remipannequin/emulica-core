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

import logging

import logging
from emulica.core import set_up_logging
set_up_logging(logging.ERROR)

import unittest

import util
util.set_path()

from emulica.core import emulation as emu

class TestHolderState(unittest.TestCase):
    
    def setUp(self):
        print(self.id())
        import test_sim14 as sim
        self.model = sim.get_model()
        self.h = emu.Holder(emu.Model(), "h", speed = 0)
        
    def test_Creation(self):
        instance = emu.HolderState(self.h)
        r =  0, len(instance)
        self.assertFalse(instance.is_first_ready())
        self.assertEqual(len(instance.product_list()), 0)
        

    def test_Append(self):
        instance = emu.HolderState(self.h)
        instance.append(1)
        r = len(instance), 1
        self.assertTrue(instance.is_first_ready())
        self.assertEqual(instance.product_list(), [1])
        instance = emu.HolderState(self.h)
        for i in range(10):
            instance.append(i)
        self.assertEqual(len(instance), 10)
        self.assertTrue(instance.is_first_ready())
        self.assertEqual(instance.product_list(), [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        
    def test_Pop(self):
        instance = emu.HolderState(self.h)
        for i in range(10):
            instance.append(i)
        self.assertEqual(instance.product_list(), [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        instance.pop()
        self.assertEqual(instance.product_list(), [1, 2, 3, 4, 5, 6, 7, 8, 9])
        instance.append(10)
        for i in range(5):
            instance.pop()
        self.assertEqual(instance.product_list(), [6, 7, 8 , 9, 10])


    def test_UpdatePos(self):
        #test update_pos
        instance = emu.HolderState(self.h)
        for i in range(10):
            instance.append(i)
        instance.update_positions()
        self.assertEqual(len(instance), 10)
        self.assertTrue(instance.is_first_ready())
        self.assertEqual(instance.product_list(), [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])


if __name__ == '__main__':    
    unittest.main()


