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
emulica is a graphical application to the emulica framework, build using GTK. 
This (sub) module contains functions that pertainng to modelling.
"""

import sys, os, logging, re
from emulica import emuML, controler
from gi.repository import Gtk # pylint: disable=E0611
from gi.repository import GtkSource# pylint: disable=E0611

from ModuleSelectionDialog import ModuleSelectionDialog

logger = logging.getLogger('emulica.emulicapp.control')

class EmulicaControl:
    """Graphical application for emulica: Control editor part
    
    Attributes:
        main -- 
        model -- 
        buffer -- 
        control_view --
        clipboard -- 
        debug_buffer -- an DebugBuffer that can be used by a logging.StreamHandler
        
    """

    def __init__(self, main_app):
        """Create the source view window and init its properties"""
        self.main = main_app
        self.model = main_app.model
        self.clipboard = Gtk.Clipboard()
        control_viewport = self.main.builder.get_object('control_view')
        manager = GtkSource.LanguageManager()
        lang_python = manager.get_language('python')
        self.buffer = GtkSource.Buffer(language = lang_python)
        self.buffer.props.highlight_syntax = True
        self.control_view = GtkSource.View(buffer = self.buffer)
        self.buffer.place_cursor(self.buffer.get_start_iter())
        self.control_view.connect('button-press-event', self.on_control_view_clicked)
        self.buffer.connect('changed', self.on_buffer_changed)
        self.buffer.connect('notify::can-undo', lambda o, p: self.main.update_undo_redo_menuitem())
        self.buffer.connect('notify::can-redo', lambda o, p: self.main.update_undo_redo_menuitem())
        self.tag_error = self.buffer.create_tag("error", background="red")
        debug_textview = self.main.builder.get_object('trace_textview')
        self.debug_buffer = LogBuffer(sys.stdout)
        sys.stdout = self.debug_buffer
        debug_textview.set_buffer(self.debug_buffer)
        self.control_view.show()
        #hide trace window by default
        #self.main.builder.get_object('hboxdebug').hide()
        control_viewport.add(self.control_view)
    
    def reset(self, model, text = ""):
        """Reset the control buffer"""
        self.model = model
        self.buffer.begin_not_undoable_action()
        self.buffer.set_text(text)
        self.buffer.end_not_undoable_action()
        self.buffer.place_cursor(self.buffer.get_start_iter())
        
    def get_text(self):
        """Return the text currently in the buffer."""
        return self.buffer.props.text
    
    def on_import_control_menuitem_activate(self, menuitem, data = None):
        """Callback for the import control menuitem. (filter .py)"""
        chooser = Gtk.FileChooserDialog(_("Import emulation model..."), self.window,
                                        Gtk.FILE_CHOOSER_ACTION_OPEN,
                                        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, 
                                         Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        response = chooser.run()
        if response == Gtk.ResponseType.OK: 
            try:
                control = open(chooser.get_filename(), 'r')
                self.buffer.set_text(control.read())
            finally:
                control.close()
        chooser.destroy()
        
        
    def on_export_control_menuitem_activate(self, menuitem, data = None):
        """Callback for the export control menuitem."""
        chooser = Gtk.FileChooserDialog(_("Export control model..."), self.window,
                                        Gtk.FILE_CHOOSER_ACTION_SAVE,
                                        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, 
                                         Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        if self.main.filename:
            chooser.set_filename(os.path.splitext(self.main.filename)[0]+'.py')
        response = chooser.run()
        if response == Gtk.ResponseType.OK: 
            chooser.get_filename()
            try:
                control_file = open(chooser.get_filename(), 'w')
                control_file.write(self.buffer.props.text)
            except IOError:
                self.main.error_message(_("export failed"))
            finally:
                control_file.close()
        chooser.destroy()

    def on_debug_togglebutton_toggled(self, button, data = None):
        """Called when the trace togglebutton is toggled."""
        arrow = self.main.builder.get_object('trace_arrow')
        box = self.main.builder.get_object('hboxdebug')
        if button.get_active():
            arrow.set(Gtk.ArrowType.DOWN, Gtk.ShadowType.NONE)
            box.show_all()
        else:
            arrow.set(Gtk.ArrowType.RIGHT, Gtk.ShadowType.NONE)
            box.hide()

    def debug_clear(self):
        """Clear the debug textview buffer. Called when a new sim begin"""
        self.debug_buffer.clear()

    def undo(self):
        """Undo"""
        self.buffer.undo()
        
    def redo(self):
        """Redo"""
        self.buffer.redo()
        
    def can_undo(self):
        """Return True if there are undoable actions."""
        return self.buffer.can_undo()
        
    def can_redo(self):
        """Return True if there are rendoable actions."""
        return self.buffer.can_redo()
        
    def cut(self):
        """Cut"""
        self.buffer.cut_clipboard(self.clipboard, True)
        
    def copy(self):
        """Copy"""
        self.buffer.copy_clipboard(self.clipboard)

    def paste(self):
        """Paste"""
        self.buffer.paste_clipboard(self.control_clipboard, None, True)
        
    def delete(self):
        """Delete""" 
        self.buffer.delete_selection(True, True)

    def on_control_view_clicked(self, view, ev):
        """Callback for click on the control view. Remove an error mark if the 
        left margin is clicked."""
        #TODO : review this code, if source mark are not used...
        mark_type = "emulica_error"
        if not view.get_show_line_marks():
            return False
        # check that the click was on the left gutter
        if ev.window == view.get_window(Gtk.TextWindowType.LEFT):
            x_buf, y_buf = view.window_to_buffer_coords(Gtk.TextWindowType.LEFT,
                                                        int(ev.x), int(ev.y))
            line_start = view.get_line_at_y(y_buf)[0]
            mark_list = self.buffer.get_source_marks_at_line(line_start.get_line(),  mark_type)
            if mark_list:
                self.buffer.delete_mark (mark_list[0])
        return False
    
    def on_buffer_changed(self, buffer):
        """Callback called when the control buffer is changed"""
        self.main.changed = True
        self.update_control_state(False, False)

    def control_add_import(self):
        """Add import line at the top of the control buffer"""
        start_iter = self.buffer.get_start_iter()
        snippet = """from emulation import Process\n"""
        self.buffer.insert(start_iter, snippet)
    
    def control_add_class(self):
        """Add a new empty class at cursor"""
        iter_here = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        snippet = """class ControlProcess(Process):\n    def run(self, model):\n        from emulation import Process, put, get, Report, Request, wait_idle\n        """
        self.buffer.insert(iter_here, snippet)
    
    def move_iter_at_indent_level(self, cursor_iter, num = 0):
        """move text iter to the correct insertion position, and indentation level (in number of spaces)
           Correct insertion position:
            * if on a line with code : go to the next line, with good indent level
            * if on a line with only whitespaces : move to the right indent level
           Indent context is taken from the line above : if an empty line is above, level is zero
           
           Arguments:
            * cursor-iter = a Text_iter where the text should be inserted
            * num = number of line we have go up with recursive call
            
        codecodecode
          codecodecdeo
        X => returns 2
        
        codecodecode
          deocodecodecode
              X => still reurns 2
              
              
        codeocedoceod
          coedoedoeo
          
        X => returns 0
        
        """
        lineno = cursor_iter.get_line()
        start = self.buffer.get_iter_at_line(lineno)
        end = start.copy()
        end.forward_to_line_end()
        line = self.buffer.get_text(start, end, False)
        empty = not re.match(".*(\S).*", line)
        if empty:
            #TODO: if first line, move to the start of line and return 0
            if lineno == 0:
                insert_iter = cursor_iter.forward_lines(num)
                return 0
            #if num is below threshold, move up
            if num < 5: # this is the number of line to look "up"
                cursor_iter.backward_lines(1)
                return self.move_iter_at_indent_level(cursor_iter, num + 1)
            else:
                insert_iter = cursor_iter.forward_lines(num)
                return 0
            #else, move forward num line, return 0
        else:
            regex = re.compile("^(\s*)(\S+)")
            r = regex.search(line)
            indent_level = len(r.groups()[0])
            if num==0:#i.e. the insertion must be done on the next line
                insert_iter = cursor_iter.forward_line()
            else:
                insert_iter = cursor_iter.forward_lines(num)
            return indent_level
    
    def control_add_modules(self):
        """Add some declaration useful to control some modules."""
        dialog = ModuleSelectionDialog()
        dialog.set_modules_list(self.model.modules)
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.ACCEPT:
            iter_here = self.buffer.get_iter_at_mark(self.buffer.get_insert())
            snippet = ""
            for name in dialog.selected():
                #get indentation level...
                indent_level = self.move_iter_at_indent_level(iter_here)
                snippet += """{indent}{name} = model.get_module('{name}')\n{indent}rp_{name} = {name}.create_report_socket()\n""".format(name = name, indent = ' '*indent_level)
            self.buffer.insert(iter_here, snippet)
        
    def control_add_put_request(self):
        """Add control line to send a request to a module"""
        #create dialog with combo to select the module to send request to and set the Request parameters.
        dialog = Gtk.Dialog(_("Select request parameters"),
                            self.main,
                            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                             Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        table = Gtk.Table(7, 2)
        for (label, row) in [(Gtk.Label(_("Receiver:")),0), (Gtk.Label(_("Action:")), 2), (Gtk.Label(_("Date:")), 3)]:
            label.set_alignment(1, 0.5)
            label.set_padding(8, 0)
            table.attach(label, 0, 1, row , row + 1)
        combo = Gtk.ComboBoxText()
        for (name, module) in self.model.modules.items():
            #a module is able to receive Request if and only if it has a request_params (list) that give the possible request parameters
            if 'request_params' in dir(module):
                combo.append_text(name)
        table.attach(combo, 1, 2, 0, 1)
        table.attach(Gtk.HSeparator(), 0, 2, 1, 2)
        action_entry = Gtk.ComboBoxText()
        table.attach(action_entry, 1, 2, 2, 3)
        date_entry = Gtk.Entry()
        table.attach(date_entry, 1, 2, 3, 4)
        #action = action_entry.child
        
        dialog.vbox.pack_start(table, False, False, 0)
        dialog.show_all()
        
        #hidden widgets...
        labels = {4: Gtk.Label(_("Program:")), 5: Gtk.Label(_("Product type:")), 6: Gtk.Label(_("Product ID:"))}
        for (row, label) in labels.items():
            label.set_alignment(1, 0.5)
            label.set_padding(8, 0)
            table.attach(label, 0, 1, row , row + 1)
        program_combo = Gtk.ComboBoxText()
        table.attach(program_combo, 1, 2, 4, 5)
        ptype_entry = Gtk.Entry()
        table.attach(ptype_entry, 1, 2, 5, 6)
        pid_entry = Gtk.Entry()
        table.attach(pid_entry, 1, 2, 6, 7)
        
        
        def selected(combo):
            """When a module is selected, update the rest of the dialog"""
            module = self.model.get_module(combo.get_active_text())
            #dialog cleaning
            action_entry.get_model().clear()
            for i in range(4, 7):
                labels[i].hide()
            ptype_entry.hide()
            pid_entry.hide()
            program_combo.hide()
            program_combo.get_model().clear()
            
            #add produce key
            action_entry.append_text(module.produce_keyword)
            #add 'setup' if it is in properties
            if 'setup' in module.properties.keys():
                action_entry.append_text('setup')
            #display possible parameters...
            for p in module.request_params:
                if p == 'program':
                    for prog in module['program_table'].keys():
                        program_combo.append_text(prog)
                    program_combo.show()
                    labels[4].show()
                    
                elif p == 'productType':
                    ptype_entry.show()
                    labels[5].show()
                elif p == 'productID':
                    pid_entry.show()
                    labels[6].show()
        combo.connect('changed', selected)
        response = dialog.run()
        try:
            if response == Gtk.ResponseType.ACCEPT:
                iter_here = self.buffer.get_iter_at_mark(self.buffer.get_insert())
                if not date_entry.get_text() == "":
                    date = ", date = {0}".format(date_entry.get_text())
                else:
                    date = ""
                ptype = ptype_entry.get_text()
                pid = pid_entry.get_text()
                if program_combo.props.visible:
                    params = ", params = {{'program': '{0}'}}".format(program_combo.get_active_text())
                elif not len(ptype) + len(pid) == 0:
                    params = ", params = {"
                    content = []
                    if not ptype == "":
                        content.append("'productType': '{0}'".format(ptype))
                    if not pid == "":
                        content.append("'productID': {0}".format(pid))
                    params = params + ", ".join(content)
                    params = params + "}"
                else:
                    params = ""
                indent_level = self.move_iter_at_indent_level(iter_here)
                snippet = """{indent}yield put, self, {name}.request_socket, [Request('{name}', '{action}'{date}{params})]\n""".format(name = combo.get_active_text(), action = action_entry.get_active_text(), date = date, params = params, indent = ' '*indent_level)
                self.buffer.insert(iter_here, snippet)
        finally:
            dialog.destroy()
    
    def control_add_wait_idle(self):
        """Add a wait_idle line for the specified actuator"""
        dialog = Gtk.Dialog(_("Select request parameters"),
                            self.main,
                            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                             Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        box = Gtk.HBox()
        label = Gtk.Label(_("Module to monitor:"))
        label.set_alignment(1, 0.5)
        box.pack_start(label, False, False, 0)
        combo = Gtk.ComboBoxText()
        for (name, module) in self.model.modules.items():
            if 'degrade' in dir(module):
                #TODO: find a better way to test if the module is an actuator ?
                combo.append_text(name)
        box.pack_start(combo, False, False, 0)
        dialog.vbox.pack_start(box, False, False, 0)
        dialog.show_all()
        response = dialog.run()
        actuator = combo.get_active_text()
        dialog.destroy()
        if response == Gtk.ResponseType.ACCEPT:
            iter_here = self.buffer.get_iter_at_mark(self.buffer.get_insert())
            indent_level = self.move_iter_at_indent_level(iter_here)
            snippet = "{indent}for e in wait_idle(self, rp_{name}): yield e\n".format(name = actuator, indent = ' '*indent_level)
            self.buffer.insert(iter_here, snippet)
        
    
    def on_control_check_activate(self, button, data = None):
        """Callback for the "check syntax" button. run prepare control. Display 
        a Message if no syntax error are found
        """
        res = self.prepare_control()
        if res:
            self.main.status_set_text(_("Control code compiled succefully."))
        else:
            self.main.status_set_text(_("Control code compilation failed."))
            
    def on_control_add_snippet_activate(self, button, data = None):
        """Callback for the add button in the control tab. Call the function 
        corresponding to the selected row in model"""
        dialog = Gtk.Dialog(_("Select control snippet to insert"),
                            self.main,
                            Gtk.DialogFlags.DESTROY_WITH_PARENT,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                             Gtk.STOCK_ADD, Gtk.ResponseType.ACCEPT))
        snippets = [(_("Main Import"), self.control_add_import),
                    (_("Empty control class"), self.control_add_class),
                    (_("Emulation module"), self.control_add_modules),
                    (_("Put request"), self.control_add_put_request),
                    (_("Get report"), self.control_add_get_report),
                    (_("Wait idle state"), self.control_add_wait_idle)]
        model = Gtk.ListStore(str, object)
        for row in snippets:
            model.append(row)
        treeview = Gtk.TreeView(model)
        cell = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_("Availlable Snippets"), cell, text = 0)
        column.set_expand(True)
        treeview.append_column(column)
        dialog.vbox.pack_start(treeview, False, False, 0)
        def on_treeview_row_activated(widget, event, data):
            model, treeiter, = treeview.get_selection().get_selected()
            (add_func, ) = model.get(treeiter, 1)
            add_func()
            
        treeview.connect('row-activated', on_treeview_row_activated)
        dialog.show_all()
        response = dialog.run()
        model, treeiter, = treeview.get_selection().get_selected()
        dialog.destroy()
        if response == Gtk.ResponseType.ACCEPT:
            
            (add_func, ) = model.get(treeiter, 1)
            add_func()
        
    
    def control_add_get_report(self):
        """Add control line to get report from a module"""
        #create dialog with combo to select the module frow which to get report
        dialog = Gtk.Dialog(_("Select request parameters"),
                            self.main,
                            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                             Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        box = Gtk.HBox()
        label = Gtk.Label(_("Get report from module:"+"  "))
        label.set_alignment(1, 0.5)
        box.pack_start(label, False, False, 0)
        combo = Gtk.ComboBoxText()
        for (name, module) in self.model.modules.items():
            combo.append_text(name)
        box.pack_start(combo, False, False, 0)
        dialog.vbox.pack_start(box, False, False, 0)
        dialog.show_all()
        response = dialog.run()
        selection = combo.get_active_text()
        dialog.destroy()
        if response == Gtk.ResponseType.ACCEPT:
            iter_here = self.buffer.get_iter_at_mark(self.buffer.get_insert())
            indent_level = self.move_iter_at_indent_level(iter_here)
            snippet = """{indent}yield get, self, rp_{name}, 1\n{indent}ev = self.got[0]\n""".format(name = selection, indent = ' '*indent_level)
            self.buffer.insert(iter_here, snippet)
        
    def update_control_state(self, compilation_done, sucessfull):
        """Update the widget indicating the control buffer state. ATM, it is 
        only the icon in the check control button."""
        #TODO: do this only if old state is not the same as new state
        img = self.main.builder.get_object('syntax_check_image')
        if compilation_done:
            if sucessfull:
                img.set_from_stock(Gtk.STOCK_YES, Gtk.IconSize.BUTTON)
            else:
                img.set_from_stock(Gtk.STOCK_NO, Gtk.IconSize.BUTTON)
        else:
            img.set_from_stock(Gtk.STOCK_DIALOG_QUESTION, Gtk.IconSize.BUTTON)
            
    def tee_stdout_to_log(self, do_redirect = True):
        """This method should be called when emulation start and stop. It will
        redirect the standard output of the whole application (including 'print'
        statement in the control code) to the log buffer. If do_redirect is 
        false, it will reset the redirection back to normal.
        
        Keyword arguments:
            * do_redirect: defaults to True, set to False to end redirection
            
        """
        if do_redirect : self.debug_buffer.start_tee()
        else: self.debug_buffer.stop_tee()
    
    def prepare_control(self):
        """compile code in the control buffer. Display error message in case of
        error and return False. Return True if no error are found."""
        #first remove previous mark (if any)
        self.buffer.remove_tag(self.tag_error, self.buffer.get_start_iter(), self.buffer.get_end_iter())
        try:
            emuML.compile_control(self.model, self.buffer.props.text)
        except StandardError, e:
            if 'lineno' in dir(e):
                lineno = max(e.lineno - 1, 0)
                if 'offset' in dir(e) and not e.offset == None:
                    colno = max(e.offset - 1, 0)
                else:
                    colno = 0
                error_start = self.buffer.get_iter_at_line_offset(lineno, colno)
                error_end = self.buffer.get_iter_at_line_offset(lineno, colno)
                error_end.forward_to_line_end()
                self.buffer.apply_tag(self.tag_error, error_start, error_end)
                
            self.main.error_message(_("{name}: {message}").format(name = e.__class__.__name__, message = str(e)))
            self.update_control_state(True, False)
            return False
        except emuML.EmuMLError, msg:
            self.main.error_message(msg.message)
            self.update_control_state(True, False)
            return False
        self.update_control_state(True, True)
        logger.info(_("control code compilation sucessfull"))
        return True
        
        
    def update_control_declare(self):
        """Update the initialize_control function"""
        #get the list of control class
        rx = re.compile(r"[ ]*class[ ]*(.*)\(Process\)[ ]*:[ ]*")
        control_classes = rx.findall(self.buffer.props.text)
        #search the declaration line in the control buffer
        start_iter = self.buffer.get_start_iter()
        end_iter = self.buffer.get_end_iter()
        decl_line = "def initialize_control(locals_, model):\n"
        position = start_iter.forward_search(decl_line, Gtk.TextSearchFlags.VISIBLE_ONLY, end_iter)
        #if not found, add it
        if position == None:
            end_iter = self.buffer.get_end_iter()
            self.buffer.insert(end_iter, decl_line)
            to_insert = control_classes
            text_iter = end_iter
        else:
            to_insert = []
            #check that each control class appear at least once in the function
            zone = self.buffer.get_text(position[1], self.buffer.get_end_iter())
            for c in control_classes:
                found = re.search(c, zone)
                if found == None:
                    to_insert.append(c)
            text_iter = position[1]
        #for each class not appearing, add "\tmodel.register_control(_locals('%s'))" % class_name
        for c in to_insert:
            snippet = "    model.register_control(locals_['{0}'])\n"
            self.buffer.insert(text_iter, snippet.format(c))
        
        
        
        
class LogBuffer(Gtk.TextBuffer):
    """A TextBuffer, that can be displayed by a TextView, and can be used as a 
    logging handler. When created it must have the original stdout.
    
    Attributes:
        * tee : boolean, if true, write out message to the buffer.
    
    """
    
    def __init__(self, out):
        self.stdout = out
        Gtk.TextBuffer.__init__(self)
        self.tee = False
        
    def start_tee(self):
        """Start intercepting all messages to stdout, and write them to the 
        TextBuffer
        """
        self.tee = True;
        self.write_to_buffer("emulation started\n")
    
    def stop_tee(self):
        """Stop intercepting all messages to stdout.
        """
        self.tee = False;
        self.write_to_buffer("emulation stopped\n")
    
    def write_to_buffer(self, message):
        end_iter = self.get_end_iter()
        self.insert(end_iter, message)
    
    def write(self, message):
        """Write message into the buffer"""
        if self.tee:
            self.write_to_buffer(message)
        self.stdout.write(message)
        
        
    def clear(self):
        """Clear the buffer"""
        end_iter = self.get_end_iter()
        start_iter = self.get_start_iter()
        self.delete(start_iter, end_iter)

