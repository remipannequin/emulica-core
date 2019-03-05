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
from gi.repository import Gdk # pylint: disable=E0611

from emulica_lib.helpers import get_builder

import gettext
from gettext import gettext as _
gettext.textdomain('emulica')

class ModelPropertiesDialog(Gtk.Dialog):
    __gtype_name__ = "ModelPropertiesDialog"

    def __new__(cls):
        """Special static method that's automatically called by Python when 
        constructing a new instance of this class.
        
        Returns a fully instantiated ModelpropertiesDialog object.
        """
        builder = get_builder('ModelPropertiesDialog')
        new_object = builder.get_object('modelproperties_dialog')
        new_object.finish_initializing(builder)
        return new_object

    def finish_initializing(self, builder):
        """Called when we're finished initializing.

        finish_initalizing should be called after parsing the ui definition
        and creating a ModelpropertiesDialog object with it in order to
        finish initializing the start of the new ModelpropertiesDialog
        instance.
        """
        # Get a reference to the builder and set up the signals.
        self.builder = builder
        self.ui = builder.get_ui(self)
        self.tree_model = self.builder.get_object('tree_model')
        self.mod_list = self.builder.get_object('mod_list')
        self.prop_list = self.builder.get_object('prop_list')
        act = self.builder.get_object('del')
        act.set_sensitive(False);
        
    def set_model(self, model):
        self.model = model
        self.inputs = model.inputs
        self.properties = self.model.properties
        
        for (name, (module, prop)) in self.inputs.items():
            self.tree_model.append([name, module, prop])
        no_mod = True;
        for mod in self.model.module_list():
            self.mod_list.append([mod.name, mod])
            no_mod = False;
        act = self.builder.get_object('add')
        act.set_sensitive(not no_mod);
    
        
    def __add_row(self):
        row = self.tree_model.append()
        prop_name = _("property{0}").format(self.tree_model.get_string_from_iter(row))
        
        self.tree_model.set_value(row, 0, prop_name)
        self.tree_model.set_value(row, 1, self.mod_list[0][0])
        self.update_prop_list(row)
        self.tree_model.set_value(row, 2, self.prop_list[0][0])
        self.update_inputs(row)

    def __del_row(self):
        #code adapted from pygtk faq
        selection = self.builder.get_object('treeview-selection')
        model, treeiter, = selection.get_selected()
        if treeiter:
            path = model.get_path(treeiter)
            (prop, ) = self.tree_model.get(treeiter, 0)
            del self.inputs[prop]
            model.remove(treeiter)
            selection.select_path(path)    
            if not selection.path_is_selected(path):
                row = path[0]-1
                if row >= 0:
                    selection.select_path((row,))


    def update_inputs(self, treeiter):
        name, = self.tree_model.get(treeiter, 0)
        mod_name, = self.tree_model.get(treeiter, 1)
        prop_name, = self.tree_model.get(treeiter, 2)
        self.inputs[name] = (mod_name, prop_name)

        
    def update_prop_list(self, treeiter):
        (name, ) = self.tree_model.get(treeiter, 0)
        (mod_name, ) = self.tree_model.get(treeiter, 1)
        module = self.model.get_module(mod_name)
        #update prop_list
        self.prop_list.clear()
        for p_name in module.properties.keys():
            self.prop_list.append([p_name])

    def on_combo_mod_changed(self, combo, path, selected_iter):
        """Clear and populate self.prop_list. Add/change values in inputs"""
        #get iter on selected row in tree
        treeiter = self.tree_model.get_iter_from_string(path)
        #get the new module and name
        (name, mod) = self.mod_list[selected_iter]
        self.update_prop_list(treeiter)
        self.tree_model.set(treeiter, 1, name)
        self.tree_model.set(treeiter, 2, self.prop_list[0][0])
        self.update_inputs(treeiter)
        
        
    def on_combo_prop_changed(self, combo, path, selected_iter):
        """Add/change values in inputs"""
        name =  self.prop_list[selected_iter][0]
        treeiter = self.tree_model.get_iter_from_string(path)
        self.tree_model.set(treeiter, 2, name)
        self.update_inputs(treeiter)
        
    def on_add_activate(self, action):
        """Callback connected to 'New' button. Add a new row on double click."""
        self.__add_row()
    
    def on_del_activate(self, action):
        """Callback connected to 'Delete' button. Delete selected row on Del key."""
        self.__del_row()

    def on_key_press_event(self, widget, event):
        """Callback connected to button-clicks. Delete selected row on Del key."""
        if event.type == Gdk.EventType.KEY_PRESS and 'Delete' == Gdk.keyval_name(event.keyval):
            self.__del_row()
    
    def on_treeview_cursor_changed(self, treeview):
        """Called when the cursor position change in the treeview; Get selected 
        row, and display corresponding program's properties."""
        selection = self.builder.get_object('treeview-selection')
        model, treeiter, = selection.get_selected()
        if treeiter:
            self.update_prop_list(treeiter)
            
    
    def apply_change_name(self, cellrenderertext, path, new_name):
        """Change property name"""
        treeiter = self.tree_model.get_iter_from_string(path)
        old_name, = self.tree_model.get(treeiter, 0)
        self.tree_model.set(treeiter, 0, new_name)
        value = self.inputs[old_name]
        del self.inputs[old_name]
        self.inputs[new_name] = value


    def on_treeview_selection_changed(self, selection):
        sel = selection.count_selected_rows()
        act = self.builder.get_object('del')
        act.set_sensitive(sel != 0);
       


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
    dialog = ModelpropertiesDialog()
    dialog.show()
    Gtk.main()
