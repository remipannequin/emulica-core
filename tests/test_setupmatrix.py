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
from emulica.core import set_up_logging
set_up_logging(logging.ERROR)


import unittest

import util
util.set_path()

_ = lambda x:x

from emulica.core.properties import SetupMatrix, Registry
from emulica.core import emulation



class TestSetupMatrix(unittest.TestCase):
    
    
    
    def setUp(self):
        print(self.id())
        self.model = emulation.Model()
        self.p = emulation.Product(self.model)

    def compare(self, instance, init, final, expRes):
        t = instance.get(init, final)
        self.assertEqual(t, expRes)



    def test_AddValues(self):
        instance = SetupMatrix(Registry(self.p, self.model.rng), 3)
        instance.add('p1', 'p2', 1)
        self.compare(instance, 'p1', 'p2', 1)
        instance.add('p1', 'p3', 2)
        self.compare(instance, 'p1', 'p3', 2)
        self.compare(instance, 'p0', 'p0', 0)
        self.compare(instance, 'p0', 'p1', 3)
        instance.add('p2', 'p3', 4)
        self.compare(instance, 'p2', 'p3', 4)
        self.compare(instance, 'p1', 'p2', 1)
        self.compare(instance, 'p1', 'p3', 2)
        instance.add('p3', 'p1', 5)
        self.compare(instance, 'p3', 'p1', 5)


    def test_ModValue(self):
        instance = SetupMatrix(Registry(self.p, self.model.rng), 3)
        instance.add('p3', 'p1', 5)
        instance.modify('p3', 'p1', new_final = 'p12')
        self.compare(instance, 'p3', 'p12', 5)
        instance.add('p2', 'p3', 4)
        instance.modify('p2', 'p3', new_initial = 'p12')
        self.compare(instance, 'p12', 'p3', 4)
        instance.add('p1', 'p2', 1)
        instance.modify('p1', 'p2', new_time = 2)
        self.compare(instance, 'p1', 'p2', 2)
        
        
if __name__ == '__main__':    
    unittest.main()
        
        
