# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (C) 2022 Centre de Recherche en Automatique de Nancy 
#
# Authors:
# Rémi Pannequin (remi.pannequin@univ-lorraine.fr)
#
### END LICENSE


"""Try to reproduce a bug that arise when two products are added in a holder 
with presence observation.

"""

from emulica.core.emulation import Model, Holder, PushObserver, CreateAct, Request

model = Model()

c1 = Holder(model, 'C1')
c1['capacity'] = 6
c1['speed'] = 0.5
obs = PushObserver(model, "C1_obs", "ev_C1", holder=c1)
obs['identify'] = True
obs['observe_absence'] = True

create = CreateAct(model, 'create', c1)


class ObserveProduct:
    def run(self, model):
        mod = model.modules['C1_obs']
        report = mod.create_report_socket(multiple_observation=True)
        while True:
            ev = yield report.get()
            print(ev)


class ControlCreate:
    def run(self, model, prod_ids):
        createModule = model.modules["create"]
        report = createModule.create_report_socket(multiple_observation=True)

        for pid in prod_ids:
            m = Request("create_support",
                        "create",
                        params={'productID': pid, 'productType': 'S'})
            yield model.get_sim().timeout(5)
            yield createModule.request_socket.put(m)
            yield report.get()
            yield model.get_sim().timeout(15)


model.register_control(ControlCreate, pem_args=(model, [1, 2]))
model.register_control(ObserveProduct)

model.emulate(6000)
