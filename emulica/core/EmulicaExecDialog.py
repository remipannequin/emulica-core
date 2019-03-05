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

from gi.repository import Gtk # pylint: disable=E0611

from emulica_lib.helpers import get_builder

import gettext
from gettext import gettext as _
gettext.textdomain('emulica')

class EmulicaExecDialog(Gtk.Dialog):
    __gtype_name__ = "EmulicaExecDialog"

    def __new__(cls):
        """Special static method that's automatically called by Python when 
        constructing a new instance of this class.
        
        Returns a fully instantiated EmulicaexecpropDialog object.
        """
        builder = get_builder('EmulicaExecDialog')
        new_object = builder.get_object('emulicaexec_dialog')
        new_object.finish_initializing(builder)
        return new_object

    def finish_initializing(self, builder):
        """Called when we're finished initializing.

        finish_initalizing should be called after parsing the ui definition
        and creating a EmulicaexecpropDialog object with it in order to
        finish initializing the start of the new EmulicaExecDialog
        instance.
        """
        # Get a reference to the builder and set up the signals.
        self.builder = builder
        self.ui = builder.get_ui(self)
        self.combo = builder.get_object('combo_mode')
        self.time_limit_adj = builder.get_object('time_limit_adj')
        self.rt_factor_adj = builder.get_object('rt_factor_adj')
        self.animate_switch = builder.get_object('animate_switch')
        
    def set_props(self, props):
        self.combo.set_active(props['exec']['real-time'])
        self.time_limit_adj.set_value(props['exec']['limit'])
        self.rt_factor_adj.set_value(props['exec']['rt-factor']) 
        self.animate_switch.set_active(props['exec']['animate'])
        
    def on_combo_mode_changed(self, combo):
        label = self.builder.get_object('label_rt_factor')
        widget = self.builder.get_object('rt_fact_spin')
        if combo.get_active() == 0:
            widget.set_sensitive(False)
            label.set_sensitive(False)
        else:
            widget.set_sensitive(True)
            label.set_sensitive(True)

    def get_rt(self):
        return (self.combo_mode.get_active() == 1)

    def get_limit(self):
        return self.time_limit_adj.get_value()

    def get_rt_factor(self):
        return self.rt_factor_adj.get_value()

    def get_animate(self):
        return self.animate_switch.get_active()

    def on_btn_ok_clicked(self, widget, data=None):
        """The user has elected to save the changes.

        Called before the dialog returns Gtk.ResponseType.OK from run().
        """
        pass

    def on_btn_cancel_clicked(self, widget, data=None):
        """The user has elected cancel changes.

        Called before the dialog returns Gtk.ResponseType.CANCEL for run()
        """
        pass


if __name__ == "__main__":
    dialog = EmulicaExecDialog()
    dialog.show()
    Gtk.main()
