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
emulica is a graphical application to the emulica framework, build using GTK. This (sub) module 
contains functions that pertaining to modelling.
"""

import gettext
from gettext import gettext as _
gettext.textdomain('emulica')

import sys, os, logging
import canvas, emuML, emulation
from CommandManager import CommandManager
from propertiesDialog import PropertiesDialog
from emulica.ModelPropertiesDialog import ModelPropertiesDialog

from gi.repository import Gtk # pylint: disable=E0611
from gi.repository import Gdk as gdk # pylint: disable=E0611
from gi.repository import GObject as gobject # pylint: disable=E0611

logger = logging.getLogger('emulica.emulicapp.modelling')

class EmulicaModel:
    """Graphical application for emulica: Modelling part.
    
    Attributes:
        main -- the Emulica main application
        builder -- the GtkBuilder object
        cmd_manager -- undo/redo manager
        canvas -- the model canvas  (EmulicaCanvas)
        clipboard -- the module clipboard
    """

    def __init__(self, main_app):
        """Create the modeling widget, connect signal, and add an empty model"""
        self.main = main_app
        self.builder = main_app.builder
        self.model = main_app.model
        self.cmd_manager = CommandManager()
        self.cmd_manager.handler = self.main.update_undo_redo_menuitem
        self.canvas = canvas.EmulicaCanvas(self.model, self.cmd_manager)
        self.canvas.connect('selection-changed', self.on_emulation_selection_changed)
        self.canvas.connect('add-done', self.on_emulation_add_done)
        #self.clipboard = Gtk.Clipboard(selection = '_SEME_MODULE_CLIPBOARD')
        self.clipboard = Gtk.Clipboard.get(gdk.SELECTION_CLIPBOARD)
        gobject.timeout_add(1500, self.check_clipboard)
        model_view = self.builder.get_object('model_view')
        #TODO: connect signal changed
        self.canvas.contextmenu = self.builder.get_object('emulation_contextmenu')
        model_view.add(self.canvas)
        self.canvas.show()
        
    def reset(self, model, main_layout = None, sub_layout = None):
        """Reset the model"""
        self.model = model
        self.canvas.setup_model(self.model)
        #then apply the layouts
        if (main_layout != None):
            self.canvas.apply_layout(main_layout)
        if (sub_layout != None):    
            for (submodel, layout) in sub_layout.items():
                self.canvas.apply_layout(layout, submodel = submodel)   
        #TODO: clear the command stack
    
    def get_layout(self):
        """Wrapper around the canvas get_layout function"""
        return self.canvas.get_layout()
       
    def set_animate(self, option):
        """Set wether the simulation should be animated or not"""
        self.canvas.animate = option
       
    def check_clipboard(self):
        """This method repetitively check for text in the special 
        _SEME_MODULE_CLIPBOARD clipboard, and set paste button accordingly
        """
        widget = self.builder.get_object('paste')
        def callback(clipboard, text, data):
            if text == None or text == '':
                widget.set_sensitive(False)
            else:
                widget.set_sensitive(True)
        self.clipboard.request_text(callback, None)
        return True
    
    def on_import_emulation_menuitem_activate(self, menuitem, data = None):
        """Callback for the imports emulation model menuitem."""
        chooser = Gtk.FileChooserDialog(_("Import emulation model..."), self.main,
                                        Gtk.FileChooserAction.OPEN,
                                        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, 
                                         Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        response = chooser.run()
        if response == Gtk.ResponseType.OK:
            #change dir to the dir of the imported model
            filename = chooser.get_filename()
            os.chdir(os.path.dirname(filename))
            self.model = emuML.load(filename)
            self.canvas.setup_model(self.model)
        chooser.destroy()
        
    def on_export_emulation_menuitem_activate(self, menuitem, data = None):
        """Callback for the export emulation menuitem."""
        chooser = Gtk.FileChooserDialog(_("Export emulation model..."), self.main,
                                        Gtk.FileChooserAction.SAVE,
                                        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, 
                                         Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        if self.main.filename:
            chooser.set_filename(os.path.splitext(self.main.filename)[0]+'.xml')
        response = chooser.run()
        if response == Gtk.ResponseType.OK: 
            emuML.save(self.model, chooser.get_filename())
        chooser.destroy()

    def undo(self):
        """Undo"""
        self.cmd_manager.undo()
        
    def redo(self):
        """Redo"""
        self.cmd_manager.redo()
        
    def can_undo(self):
        """Return True if there are undoable actions."""
        return self.cmd_manager.can_undo()
        
    def can_redo(self):
        """Return True if there are rendoable actions."""
        return self.cmd_manager.can_redo()
        
    def cut(self):
        """Cut"""
        self.canvas.cut_clipboard(self.clipboard)
        
    def copy(self):
        """Copy"""
        self.canvas.copy_clipboard(self.clipboard)

    def paste(self):
        """Paste"""
        self.canvas.paste_clipboard(self.clipboard)
        
    def delete(self):
        """Delete""" 
        self.canvas.delete_selection()

    def on_zoom_in_activate(self, menuitem):
        """Callback for the zoom in menuitem. increment scale."""
        scale = self.canvas.get_scale() * 1.25
        self.canvas.set_scale(scale)
        self.adjust_canvas_size()
        
    def on_zoom_out_activate(self, menuitem):
        """Callback for the zoom in menuitem. increment scale."""
        scale = self.canvas.get_scale() / 1.25
        self.canvas.set_scale(scale)
        self.adjust_canvas_size()
    
    def on_zoom_100_activate(self, menuitem):
        """Callback for the zoom in menuitem. increment scale."""
        self.canvas.set_scale(1)
        self.adjust_canvas_size()
    
    def on_zoom_fit_activate(self, menuitem):
        """Callback for the zoom fit menuitem. Set scale and scrolled window
        adjustment to fit the model canvas."""
        (x1, y1, x2, y2) = self.canvas.fit_size() 
        vp = self.builder.get_object('model_view')
        vadj = vp.get_vadjustment()
        hadj = vp.get_hadjustment()
        hscale = hadj.get_page_size() / float(x2 - x1)
        vscale = vadj.get_page_size() / float(y2 - y1)
        self.canvas.set_scale(min(hscale, vscale))
        self.adjust_canvas_size()
        s = self.canvas.get_scale()
        hadj.value = x1 * s
        vadj.value = y1 * s
    
    def adjust_canvas_size(self): 
        scale = self.canvas.get_scale()
        (x1, y1, x2, y2) = self.canvas.get_bounds()#fit_size or get_bounds ??
        self.canvas.set_size_request(int((x2 - x1) * scale), int((y2 - y1) * scale))
        
    def on_button_actuator_activate(self, widget, data = None):
        """Change arrow orientation and change visibility of table"""
        palette_actuator_table = self.builder.get_object('table_actuator')
        palette_actuator_arrow = self.builder.get_object('arrow_actuator')
        if palette_actuator_table.props.visible:
            palette_actuator_table.hide()
            palette_actuator_arrow.set(Gtk.ArrowType.RIGHT, Gtk.ShadowType.OUT)
        else:
            palette_actuator_table.show()
            palette_actuator_arrow.set(Gtk.ArrowType.DOWN, Gtk.ShadowType.OUT)
    
    def on_button_holder_activate(self, widget, data = None):
        """Change arrow orientation and change visibility of table"""
        palette_holder_arrow = self.builder.get_object('arrow_holder')
        palette_holder_table = self.builder.get_object('table_holder')
        
        if palette_holder_table.props.visible:
            palette_holder_table.hide()
            palette_holder_arrow.set(Gtk.ArrowType.RIGHT, Gtk.ShadowType.OUT)
        else:
            palette_holder_table.show()
            palette_holder_arrow.set(Gtk.ArrowType.DOWN, Gtk.ShadowType.OUT)
    
    def on_button_observer_activate(self, widget, data = None):
        """Change arrow orientation and change visibility of table"""
        palette_observer_arrow = self.builder.get_object('arrow_observer')
        palette_observer_table = self.builder.get_object('table_observer')
        if palette_observer_table.props.visible:
            palette_observer_table.hide()
            palette_observer_arrow.set(Gtk.ArrowType.RIGHT, Gtk.ShadowType.OUT)
        else:
            palette_observer_table.show()
            palette_observer_arrow.set(Gtk.ArrowType.DOWN, Gtk.ShadowType.OUT)
    
    def on_add_submodel_activate(self, button):
        """Callback for the 'add submodel' button"""
        #display file chooser, and parse file
        sub_file = self.main.get_open_filename()
        #make subfile a relative path
        name = "Submodel"+str(len(self.model.modules))
        gsf = emuML.EmuFile(sub_file, 'r', parent_model = self.model, name = name)
        (submodel, subcontrol) = gsf.read()   
        for (name, prop) in gsf.get_properties().items():
            submodel = self.model.get_module(name)
            layout = dict()
            for (mod_name, position) in prop['layout'].items():
                if submodel.has_module(mod_name):
                    module = submodel.get_module(mod_name)
                    layout[module] = position
            #then apply the layouts
            self.canvas.apply_layout(layout, submodel = submodel)
        emuML.compile_control(submodel, subcontrol)
        
    def on_add_create_toggled(self, widget, data = None):
        self.add_module(widget, 'add_create', emulation.CreateAct)
    
    def on_add_dispose_toggled(self, widget, data = None):
        self.add_module(widget, 'add_dispose', emulation.DisposeAct)
    
    def on_add_shape_toggled(self, widget, data = None):
        self.add_module(widget, 'add_shape', emulation.ShapeAct)
            
    def on_add_space_toggled(self, widget, data = None):
        self.add_module(widget, 'add_space', emulation.SpaceAct)
            
    def on_add_assy_toggled(self, widget, data = None):
        self.add_module(widget, 'add_assy', emulation.AssembleAct)
    
    def on_add_unassy_toggled(self, widget, data = None):
        self.add_module(widget, 'add_unassy', emulation.DisassembleAct)
                
    def on_add_holder_toggled(self, widget, data = None):
        self.add_module(widget, 'add_holder', emulation.Holder)
    
    def on_add_failure_toggled(self, widget, data = None):
        self.add_module(widget, 'add_failure', emulation.Failure)
    
    def on_add_pushobs_toggled(self, widget, data = None):
        self.add_module(widget, 'add_pushobs', emulation.PushObserver)
    
    def on_add_pullobs_toggled(self, widget, data = None):
        self.add_module(widget, 'add_pullobs', emulation.PullObserver)
    
    def add_module(self, widget, my_act, mod_type):
        """Set the canvas in 'adding mode'."""
        act_list = ['add_create', 'add_dispose', 'add_shape', 'add_space', 'add_assy', 'add_unassy', 'add_holder', 'add_failure', 'add_pushobs', 'add_pullobs']
        act_list.remove(my_act)
        if widget.get_active():
            for act_name in act_list:
                act = self.builder.get_object(act_name)
                act.set_active(False)
                self.canvas.set_adding(True, mod_type)
        else:
            self.canvas.set_adding(False)
            
    def on_properties_activate(self, menuitem, data = None):
        """Properties button or menuitem is activated (or clicked)"""
        #get module from selection
        for module in self.canvas.selection:
            prop_win = PropertiesDialog(self.main, module, self.model, self.cmd_manager)
            prop_win.show()
            self.changed = True
            
    def on_model_properties_activate(self, menuitem, data = None):
        """Properties of a model"""
        dialog = ModelPropertiesDialog()
        dialog.set_model(self.model)
        self.changed = True
        response = dialog.run()
            
    def on_emulation_selection_changed(self, source, num_selected):
        """Callback for change in the selection of modules.
        Change sensitivity of some buttons
        """
        value = not (num_selected == 0)
        widgets_names = ['properties', 
                         'cut', 
                         'copy',
                         'delete']
        for name in widgets_names:
            widget = self.builder.get_object(name)
            widget.set_sensitive(value)
    
    def on_emulation_add_done(self, source):
        """Callback connect to the add-done signal of the model canvas."""
        act_list = ['add_create', 'add_dispose', 'add_shape', 'add_space', 'add_assy', 'add_unassy', 'add_holder', 'add_pushobs', 'add_pullobs']
        for act_name in act_list:
            act = self.builder.get_object(act_name)
            act.set_active(False)
    
    

    
