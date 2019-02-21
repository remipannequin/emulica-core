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

from locale import gettext as _

from gi.repository import Gtk # pylint: disable=E0611
from gi.repository import Gio
from gi.repository import GLib

import logging
logger = logging.getLogger('emulica')

from emulica_lib import Window
from emulica.AboutEmulicaDialog import AboutEmulicaDialog
from emulica.PreferencesEmulicaDialog import PreferencesEmulicaDialog
from emulica.EmulicaExecDialog import EmulicaExecDialog


#my imports 
import sys, os, pickle, zipfile, random
import emuML, controler, emulation

import modelling, control, results



# See emulica_lib.Window.py for more details about how this class works
"""
emulicaWindow is a graphical application to the emulica framework, build using Gtk.
"""
class EmulicaWindow(Window):
    """Graphical application for emulica
    
    Attributes:
        window -- the main window
        builder -- GtkBuilder object
        context_menu -- the context menu
        
        emulica_model
        emulica_control
        emulica_results
        
    """
    __gtype_name__ = "EmulicaWindow"
    
    def get_menubar(self):
        return self.builder.get_object('menubar')
        
    def get_app_menu(self):
        return None
    
    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(EmulicaWindow, self).finish_initializing(builder)
        
        self.AboutDialog = AboutEmulicaDialog
        self.PreferencesDialog = PreferencesEmulicaDialog
        
        #Create Emulica application
        #Set Default values
        self.filename = None
        self.about = None
        self.adding = None
        self.changed = False
        
        self.builder = builder;
        
        self.statusbar = builder.get_object('statusbar')
        self.progressbar = builder.get_object('progressbar')
        self.status_reset(self.filename)
        
        self.props = dict()
        notebook = builder.get_object('main_notebook')
        notebook.connect('switch-page', lambda o, p, p1: self.update_undo_redo_menuitem())
        
        #Create subpart of the application
        self.model = emulation.Model()
        
        self.emulica_model = modelling.EmulicaModel(self)
        self.emulica_control = control.EmulicaControl(self)
        self.emulica_results = results.EmulicaResults(self)
        
        #Application settings management
        settings = Gio.Settings("net.launchpad.emulica")
        settings.bind('show-line-number', self.emulica_control.control_view, 'show-line-numbers', Gio.SettingsBindFlags.DEFAULT)
        settings.bind('auto-indent', self.emulica_control.control_view, 'auto-indent', Gio.SettingsBindFlags.DEFAULT)
        settings.bind('insert-spaces-instead-of-tabs', self.emulica_control.control_view, 'insert-spaces-instead-of-tabs', Gio.SettingsBindFlags.DEFAULT)
        settings.bind('indent-width', self.emulica_control.control_view, 'indent-width', Gio.SettingsBindFlags.DEFAULT)
        settings.bind('show-line-marks', self.emulica_control.control_view, 'show-line-marks', Gio.SettingsBindFlags.DEFAULT)
        #initialize props and preferences
        self.init_props()
        
    
    def init_props(self):
        """Initialize the props dictionary with the right values"""        
        clean = False
        if not 'exec' in self.props:
            self.props['exec'] =  dict()
            clean = True
        default = [('limit', 200), 
                   ('real-time', True),
                   ('rt-factor', 2), 
                   ('animate', True)]
        for (prop, val) in default:
            if clean or not prop in self.props['exec']:
                self.props['exec'][prop] = val
            
    def on_window_delete_event(self, widget, event, data = None):
        """When the window is requested to be closed, we need to check if they have 
        unsaved work. We use this callback to prompt the user to save their work 
        before they exit the application. From the 'delete-event' signal, we can 
        choose to effectively cancel the close based on the value we return."""
        if self.check_for_save(): 
            return False # Propagate event
        else:
            return True #block event !
        
    
    def on_new_activate(self, menuitem, data = None):
        """Callback for the 'New' menuitem. We need to prompt for save if 
        the file has been modified, and then delete the buffer and clear the  
        modified flag.
        """
        if self.check_for_save():        
            self.clear()

    def on_open_activate(self, menuitem, data = None):
        """Callback for the  'Open' menuitem. We need to prompt for save if 
        thefile has been modified, allow the user to choose a file to open, and 
        then call load_file() on that file.
        """    
        if self.check_for_save(): 
            filename = self.get_open_filename()
            if filename: self.load_file(filename)
      
    def on_save_activate(self, menuitem, data = None):
        """Callback for the 'Save' menu item. We need to allow the user to choose 
        a file to save if it's an untitled document, and then call write_file() on that 
        file.
        """    
        if self.filename == None: 
            filename = self.get_save_filename()
            if filename: self.write_file(filename)
        else: self.write_file(self.filename)
        
    def on_saveas_activate(self, menuitem, data = None):
        """Callback for the 'Save As' menu item. We need to allow the user 
        to choose a file to save and then call write_file() on that file.
        """    
        filename = self.get_save_filename()
        if filename: self.write_file(filename)
    
    def on_quit_activate(self, menuitem, data = None):
        """Callback for the 'Quit' menu item. We need to prompt for save if 
        the file has been modified and then break out of the Gtk+ main loop          
        """   
        if self.check_for_save(): 
            Gtk.main_quit()
    
    def on_undo_activate(self, menuitem, data = None):
        """Callback for the undo menuitem. ATM, only undo in the control code 
        is supported."""
        self.get_context().undo()
        
    def on_redo_activate(self, menuitem, data = None):
        """Callback for the redo menuitem. ATM, only undo in the control code 
        is supported."""
        self.get_context().redo()
        
    def on_cut_activate(self, menuitem, data = None):
        """Callback for the 'Cut' menuitem. Copy selected modules and delete them"""
        self.get_context().cut()
        
    def on_copy_activate(self, menuitem, data = None):
        """Callback for the 'Copy' menuitem. 
        If the modelling panel is displayed, copy the selected model into the paperclip"""
        self.get_context().copy()
        
    def on_paste_activate(self, menuitem, data = None):
        """Callback for the 'Paste' menuitem. 
        If the modelling panel is displayed, paste the content of the paperclip into the model."""
        self.get_context().paste()
       
    def on_delete_activate(self, menuitem, data = None):
        """Called when the user clicks the 'Delete' menu. """ 
        self.get_context().delete()
    
    def on_preferences_menuitem_activate(self, menuitem, data = None):
        """Callback for the 'preference' menuitem. Display the preference dialog."""
        self.preferences.edit()
    
    def on_exec_properties_menuitem_activate(self, menuitem):
        """Callback for the execution settings menuitem. Display a dialog to
        edit execution properties."""
        dialog = EmulicaExecDialog()
        dialog.set_props(self.props)
        response = dialog.run()
        if response == Gtk.ResponseType.ACCEPT:
            self.props['exec']['limit'] = dialog.get_limit()
            self.props['exec']['real-time'] = dialog.get_rt()
            self.props['exec']['rt-factor'] = dialog.get_rt_factor()
            self.props['exec']['animate'] = dialog.get_animate()
            self.emulica_model.set_animate(dialog.get_animate())
            self.changed = True
        dialog.destroy()
    
    def on_about_menuitem_activate(self, menuitem, data = None):
        """Called when the user clicks the 'About' menu. We use Gtk_show_about_dialog() 
        which is a convenience function to show a GtkAboutDialog. This dialog will
        NOT be modal but will be on top of the main application window.    
        """
        if (not self.about):
            self.about = dialogs.EmulicaAbout(self)
        else:
            self.about.present()
        
    def on_start_activate(self, widget, data = None):
        #clean results
        
        #start input redirection
        self.emulica_control.tee_stdout_to_log()
        self.emulica_control.prepare_control()
        #get parameter from preference (self.props dictionary)
        kwargs = {'until': self.props['exec']['limit'],
                  }
        rt = self.props['exec']['real-time']
        kwargs['real_time'] = rt
        if rt: 
            kwargs['rt_factor'] = self.props['exec']['rt-factor']
        else:
            kwargs['step'] = self.props['exec']['animate']
        self.time_controler = controler.TimeControler(self.model, **kwargs)
        self.time_controler.add_callback(self.on_emulation_step, controler.EVENT_TIME)
        self.time_controler.add_callback(self.on_emulation_start, controler.EVENT_START)
        self.time_controler.add_callback(self.on_emulation_finish, controler.EVENT_FINISH)
        self.time_controler.add_callback(self.emulica_results.on_emulation_finish, controler.EVENT_FINISH)
        self.time_controler.add_callback(self.on_emulation_exception, controler.EXCEPTION)
        self.time_controler.start() 
    
    def on_stop_activate(self, widget, data = None):
        self.time_controler.stop()
    
    def on_pause_toggled(self, widget, data = None):
        if widget.get_active():
            #pause simulation
            self.time_controler.pause()
        else:
            #resume simu
            self.time_controler.resume()
            
    def on_emulation_step(self, model):
        """Callback called at regular interval during emulation. Update status 
        bar. use add_idle, because this function is called from another thread."""
        GLib.idle_add(self.status_set_progress, _("running"), model.current_time(), self.props['exec']['limit'])
        
    
    def on_emulation_start(self, model):
        """Callback activated when emulation start. Make pause and stop button 
        sensible. use add_idle, because this function is called from another 
        thread."""
        for button in [self.builder.get_object(name) for name in ['pause', 'stop']]:
            GLib.idle_add(button.set_sensitive, True)
        GLib.idle_add(self.builder.get_object('start').set_sensitive, False)
        GLib.idle_add(self.builder.get_object('reinit').set_sensitive, False)       
        GLib.idle_add(self.status_set_progress, _("starting"))
    
    def on_emulation_finish(self, model):
        """Callback activated when emulation finish. use add_idle, because this 
        function is called from another thread."""
        GLib.idle_add(self.reset_execution)
        GLib.idle_add(self.status_set_progress, _("finished"), model.current_time(), model.current_time())
        GLib.idle_add(self.builder.get_object('reinit').set_sensitive, True)
    
        #stop input redirection
        GLib.idle_add(self.emulica_control.tee_stdout_to_log, False)
        
    def on_emulation_exception(self, exception, trace):
        """Callback activated when the simulation run encounters an exception.
        Warning!  This is called from an outside thread!!!"""
        #print _("Exception when runing emulation:\n") + str(exception)
        import traceback
        #TODO: format traceback using Pango markup
        GLib.idle_add(self.error_message, _("Exception when runing emulation:\n") + str(exception), "".join(traceback.format_list(trace)))
        #self.error_message(_("Exception when runing emulation:\n") + str(exception))
    
    
    def on_reinit_activate(self, widget, data = None):
        """Callback for the clear button (both in menu and tool bar). Initialize
        simulation. Only active when simulation is not running."""
        self.model.clear()
        self.emulica_results.delete_results()
        self.builder.get_object('result_tab_label').set_sensitive(False)
        self.builder.get_object('results_menuitem').set_sensitive(False)
        self.builder.get_object('reinit').set_sensitive(False)
        #we clear also statusbar !
        self.status_set_progress(_("ready"))
        self.builder.get_object('result_tab_label')
    
    def get_context(self):
        """Return emulica_model or emulica_control, according to the visible tab."""
        notebook = self.builder.get_object('main_notebook')
        if (notebook.get_current_page() == 1):
            return self.emulica_control
        else:
            return self.emulica_model
    
    def get_save_filename(self):
        """We call get_save_filename() when we want to get a filename to 
        save from the user. It will present the user with a file chooser 
        dialog and return the filename or None.
        """  
        filename = None
        chooser = Gtk.FileChooserDialog(_("Save File..."), self,
                                        Gtk.FileChooserAction.SAVE,
                                        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, 
                                         Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        chooser.set_do_overwrite_confirmation(True)
        filter_emulica = Gtk.FileFilter()
        filter_emulica.set_name("Emulica files")
        filter_emulica.add_pattern("*.emu")
        chooser.add_filter(filter_emulica)
        response = chooser.run()
        if response == Gtk.ResponseType.OK: 
            filename = chooser.get_filename()
        chooser.destroy()
        extension = os.path.splitext(filename)[1]
        if not extension:
	        filename = filename + '.emu'
        return filename
    
    def update_undo_redo_menuitem(self, *args):
        """Callback for context change (emulation/control/result)"""
        redo = self.builder.get_object('redo')
        undo = self.builder.get_object('undo')
        undo.set_sensitive(self.get_context().can_undo())
        redo.set_sensitive(self.get_context().can_redo())
        #TODO: if context is not emulation: inactivate zoom buttons
        
        
    def error_message(self, message, details = None):
        """We call error_message() any time we want to display an error message to 
        the user. It will both show an error dialog and log the error to the 
        terminal window.
        
        Arguments:
            message -- the main message to display
            details -- error details (such as traceback information)
        """
        # create an error message dialog and display modally to the user
        dialog = Gtk.MessageDialog(self,
                                   Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                   Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, message)
        if details:
            dialog.format_secondary_text(details)
        logger.warning(message)
        logger.info(details)
        #we don't spawn a new event loop, because it causes freeze when called from idle_add
        dialog.connect('response', lambda d, r: d.destroy())
        dialog.show()
        return False
        
    
        
    def check_for_save (self):
        """This function will check to see if the model has been
        modified and prompt the user to save if it has been modified.
        It return true if the action can continue, false otherwise"""
        if self.changed:
            if self.filename:
                docname = os.path.basename(self.filename)
            else:
                docname = _("untitled")
            dialog = Gtk.MessageDialog(self, 
                                Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT, 
                                Gtk.MessageType.WARNING,
                                Gtk.ButtonsType.NONE,
                                _("Do you want to save modifications in document {0} before closing?".format(docname)))
            dialog.add_buttons(_("Close without saving"), Gtk.ResponseType.REJECT,
                                 Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                 Gtk.STOCK_SAVE, Gtk.ResponseType.ACCEPT)
            dialog.format_secondary_text(_("If you don't save all modifications will be lost."))
            response = dialog.run()
            dialog.destroy()
            if response == Gtk.ResponseType.ACCEPT:
                self.on_save_menuitem_activate(None, None)
                return True
            elif response == Gtk.ResponseType.CANCEL:
                return False
            elif response == Gtk.ResponseType.REJECT:
                return True
        else:
            return True 
    
    
            
    def get_open_filename(self):
        """We call get_open_filename() when we want to get a filename to open 
        from the user. It will present the user with a file chooser dialog
        and return the filename or None.
        """
        filename = None
        chooser = Gtk.FileChooserDialog(_("Open File..."), self,
                                        Gtk.FileChooserAction.OPEN,
                                        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, 
                                         Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        filter_emulica = Gtk.FileFilter()
        filter_emulica.set_name("Emulica files")
        filter_emulica.add_pattern("*.emu")
        filter_all = Gtk.FileFilter()
        filter_all.set_name("All files")
        chooser.add_filter(filter_emulica)
        chooser.add_filter(filter_all)
        response = chooser.run()
        if response == Gtk.ResponseType.OK: 
            filename = chooser.get_filename()
        chooser.destroy()
        
        return filename
    
    
        
    def clear(self):
        """Reset the model, control and properties attributes of the 
        application."""
        while Gtk.events_pending(): Gtk.main_iteration()
        self.model = emulation.Model()
        self.props = dict()
        self.filename = None
        self.emulica_model.reset(self.model)
        self.emulica_control.reset(self.model)
        self.builder.get_object('result_tab_label').set_sensitive(False)
        self.builder.get_object('results_menuitem').set_sensitive(False)
        self.builder.get_object('main_notebook').set_current_page(0)
    
    def load_file(self, filename):
        """We call load_file() when we have a filename and want to load a model
        from that file. The previous contents are overwritten.    
        """
        # add Loading message to status bar and ensure GUI is current
        self.status_set_text(_("Loading {0}").format(filename))
        while Gtk.events_pending(): 
            Gtk.main_iteration()
        #open filename, verify archive integrity
        d = os.path.dirname(filename)
        if d != '':
            os.chdir(d)
        filename = os.path.basename(filename)
        gsfile = emuML.EmuFile(filename, 'r')
        #TODO: verify if submodels are readable, and propose to relocate them if nessecary
        try:
            (self.model, control) = gsfile.read()
            self.filename = filename
            properties = gsfile.get_properties()
            #filter layout properties: if the  module is not in the model drop the position
            top_layout = properties['main']['layout']
            for name in top_layout.keys():
                if not name in self.model.modules.keys():
                    del top_layout[name]
                    logger.warning(_("module {name} present in layout was not found. removing from layout.").format(name = name))
            #for each property, get the layout, and replace modules names by modules instances
            self.props = properties.pop('main')
            self.init_props()
            self.reset_execution()
            #introduce a function that convert module names in module instance...
            def convert_to_layout(model, d):
                r = dict()
                mod_list = [module.name for module in model.module_list()]
                for (name, position) in d.items():
                    if name in mod_list:
                        r[model.get_module(name)] = position
                return r
            if 'layout' in self.props:#some model might not have the layout property
                main_layout = convert_to_layout(self.model, self.props['layout'])
            else:
                logger.warning(_("model did not have any layout."))
                main_layout = {}
            sub_layout = dict()
            #get layouts from files
            for (name, prop) in properties.items():
                submodel = self.model.get_module(name)
                layout = convert_to_layout(submodel, prop['layout'])
                sub_layout[submodel] = layout
            #first create the widgets
            self.emulica_model.reset(self.model, main_layout, sub_layout)
            #init control buffer
            self.emulica_control.reset(self.model, control)
            
        except emuML.EmuMLError, warning:
            # error loading file, show message to user
            self.error_message (_("Could not open file: {filename}s\n {warning}").format(filename = filename, warning = warning))
        finally:
            gsfile.close()
        # clear loading status and restore default
        self.changed = False
        self.status_reset(self.filename)

    def write_file(self, filename):
        """Write model, properties and control buffer to a file."""
        
        # add Saving message to status bar and ensure GUI is current
        if filename: 
            self.status_set_text(_("Saving {0}").format(filename))
        else:
            self.status_set_text(_("Saving {0}").format(self.filename))
        while Gtk.events_pending(): 
            Gtk.main_iteration()
            
        self.props['layout'] = self.emulica_model.get_layout()  
        gsfile = emuML.EmuFile(filename, 'w')
        try:
            gsfile.write(self.model, self.emulica_control.get_text(), self.props)
        except Exception, msg:
            print msg
            self.error_message(_("Could not save file: {0}").format(filename))
        finally:
            gsfile.close()
        # clear saving status and restore default     
        self.changed = False
        self.status_reset(filename)
        self.filename = filename
    
    def reset_execution(self):
        """Reset the execution state"""
        for button in [self.builder.get_object(name) for name in ['pause', 'stop']]:
            button.set_sensitive(False)
        self.builder.get_object('start').set_sensitive(True)
        img = self.builder.get_object('syntax_check_image')
        img.set_from_stock(Gtk.STOCK_DIALOG_QUESTION, Gtk.IconSize.BUTTON)
        
        
    def on_control_add_snippet_activate(self, button, data = None):
        self.emulica_control.on_control_add_snippet_activate(button, data = None)
    
    def on_control_update_activate(self, button, data = None):
        """Callback for the Update declare function button in the control tab."""
        self.emulica_control.update_control_declare()
    
    def on_debug_togglebutton_toggled(self, button, data = None):
        self.emulica_control.on_debug_togglebutton_toggled(button, data)
    
    def on_control_check_activate(self, button, data = None):
        self.emulica_control.on_control_check_activate(button, data)
    
    def on_import_control_menuitem_activate(self, menuitem, data = None):
        self.emulica_control.on_import_control_menuitem_activate(menuitem, data)
        
    def on_export_control_menuitem_activate(self, menuitem, data = None):
        self.emulica_control.on_export_control_menuitem_activate(menuitem, data)
    
    
    def on_add_space_toggled(self, widget, data = None):
        self.emulica_model.on_add_space_toggled(widget, data)
        
    def on_add_submodel_activate(self, widget, data = None):
        self.emulica_model.on_add_submodel_activate(button)
    
    def on_add_unassy_toggled(self, widget, data = None):
        self.emulica_model.on_add_unassy_toggled(widget, data)
    
    def on_add_failure_toggled(self, widget, data = None):
        self.emulica_model.on_add_failure_toggled(widget, data)
    
    def on_add_pullobs_toggled(self, widget, data = None):
        self.emulica_model.on_add_pullobs_toggled(widget, data)
    
    def on_add_pushobs_toggled(self, widget, data = None):
        self.emulica_model.on_add_pushobs_toggled(widget, data)
    
    def on_add_dispose_toggled(self, widget, data = None):
        self.emulica_model.on_add_dispose_toggled(widget, data)
    
    def on_add_assy_toggled(self, widget, data = None):
        self.emulica_model.on_add_assy_toggled(widget, data)
    
    def on_add_holder_toggled(self, widget, data = None):
        self.emulica_model.on_add_holder_toggled(widget, data)
    
    def on_add_shape_toggled(self, widget, data = None):
        self.emulica_model.on_add_shape_toggled(widget, data)
    
    def on_add_create_toggled(self, widget, data = None):
        self.emulica_model.on_add_create_toggled(widget, data)
    
    def on_properties_activate(self, menuitem, data = None):
        self.emulica_model.on_properties_activate(menuitem, data)
    
    def on_model_properties_activate(self, menuitem, data = None):
        self.emulica_model.on_model_properties_activate(menuitem, data)
    
    def on_button_actuator_activate(self, widget, data = None):
        self.emulica_model.on_button_actuator_activate(widget, data)
    
    def on_button_observer_activate(self, widget, data = None):
        self.emulica_model.on_button_observer_activate(widget, data)
    
    def on_button_holder_activate(self, widget, data = None):
        self.emulica_model.on_button_holder_activate(widget, data)
    
    def on_import_emulation_menuitem_activate(self, menuitem, data = None):
        self.emulica_model.on_import_emulation_menuitem_activate(menuitem, data)
    
    def on_export_emulation_menuitem_activate(self, menuitem, data = None):
        self.emulica_model.on_export_emulation_menuitem_activate(menuitem, data)
    
    def on_zoom_fit_activate(self, menuitem):
        self.emulica_model.on_zoom_fit_activate(menuitem)
    
    def on_zoom_out_activate(self, menuitem):
        self.emulica_model.on_zoom_out_activate(menuitem)
    
    def on_zoom_100_activate(self, menuitem):
        self.emulica_model.on_zoom_100_activate(menuitem)
    
    def on_zoom_in_activate(self, menuitem):
        self.emulica_model.on_zoom_in_activate(menuitem)
    
    def on_result_clear_activate(self, widget, data = None):
        self.emulica_results.on_result_clear_activate(widget, data)
    
    def on_result_saveas_activate(self, widget, data = None):
        self.emulica_results.on_result_saveas_activate(widget, data)
    
    def on_result_add_activate(self, widget, data = None):
        self.emulica_results.on_result_add_activate(widget, data)
    
    def on_legend_togglebutton_toggled(self, button, data = None):
        self.emulica_results.on_legend_togglebutton_toggled(button, data)
    
    def on_add_chart_button_clicked(self, button, data = None):
        self.emulica_results.on_add_chart_button_clicked(button, data)
    
    def on_export_results_menuitem_activate(self, menuitem, data = None):
        self.emulica_results.on_export_results_menuitem_activate(menuitem, data)
    
    
    def status_reset(self, filename):
        """Reset the status bar and changed flag"""
        if filename: status = _("File: {0}").format(os.path.basename(filename))
        else: status = _("File: (UNTITLED)")
        cid = self.statusbar.get_context_id('Emulica')
        self.statusbar.push(cid, status)
    
    def status_set_text(self, message):
        """Push message on statusbar"""
        cid = self.statusbar.get_context_id('Emulica')
        self.statusbar.push(cid, message)
        
    def status_set_progress(self, state, current = 0, limit = 1):
        """Set the progressbar label and fraction"""
        
        self.progressbar.set_fraction(current / limit)
        self.progressbar.set_text("{0}, t={1:.1f}".format(state, current))
        
    def status_set_progressing(self, state):
        """Set the progress bar to the moving-bar style: used in discrete event simulation."""
        #TODO: repeditively call pulse
        
        self.progressbar.pulse()
        
        

