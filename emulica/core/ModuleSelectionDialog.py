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

class ModuleSelectionDialog(Gtk.Dialog):
    __gtype_name__ = "ModuleSelectionDialog"

    def __new__(cls):
        """Special static method that's automatically called by Python when 
        constructing a new instance of this class.
        
        Returns a fully instantiated ModuleSelectionDialog object.
        """
        builder = get_builder('ModuleSelectionDialog')
        new_object = builder.get_object('moduleselection_dialog')
        new_object.finish_initializing(builder)
        return new_object

    def finish_initializing(self, builder):
        """Called when we're finished initializing.

        finish_initalizing should be called after parsing the ui definition
        and creating a ModuleselectionDialog object with it in order to
        finish initializing the start of the new ModuleselectionDialog
        instance.
        """
        # Get a reference to the builder and set up the signals.
        self.builder = builder
        self.ui = builder.get_ui(self)
        self.model = builder.get_object("liststore");
        

    def set_modules_list(self, modules, mod_filter = None):
        """Set the list of module to display
        Arguments: 
            modules -- a dictionary of modules to display
            mod_filter -- a function that determine if a module should be displayed (default=lambda m: True)
        """
        mod_filter = mod_filter or (lambda s: True)
        
        sorted_mod_list = modules.keys()
        sorted_mod_list.sort()
        for name in sorted_mod_list:
            if mod_filter(modules[name]):
                self.model.append((name,modules[name]))
        

    def selected(self):
        """Return the list of selected modules name"""
        return self.sel

    def select_all(self, button):
        """Select all the rows"""
        for row in self.model:
            row[0] = True

    def select_none(self, button):
        """Unselect all the rows"""
        for row in self.model:
            row[0] = False

    def select_invert(self, button):
        """Invert selection of the rows"""
        for row in self.model:
            row[0] = not row[0]

    def on_btn_ok_clicked(self, widget, data=None):
        """The user has elected to save the changes.

        Called before the dialog returns Gtk.ResponseType.ACCEPT from run().
        """
        selection = self.builder.get_object('treeview-selection')
        (model, paths) = selection.get_selected_rows()
        self.sel = [model[path][0] for path in paths]

    def on_btn_cancel_clicked(self, widget, data=None):
        """The user has elected cancel changes.

        Called before the dialog returns Gtk.ResponseType.CANCEL for run()
        """
        self.sel = []
        pass


if __name__ == "__main__":
    dialog = ModuleselectionDialog()
    dialog.show()
    Gtk.main()
