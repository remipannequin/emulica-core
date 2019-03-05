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
This module enable to graphically animate the execution of emulica models.

Signals:
    changed
    selection-changed
    add-done
"""

from __future__ import division
import logging

import gettext
from gettext import gettext as _
gettext.textdomain('emulica')


from gi.repository import Gdk # pylint: disable=E0611
from gi.repository import GObject # pylint: disable=E0611
from gi.repository import GLib # pylint: disable=E0611
import cairo
from gi.repository import GooCanvas as Goo # pylint: disable=E0611

import emuML
from propertiesDialog import PropertiesDialog

logger = logging.getLogger('emulica.canvas')

SIGNAL_CHANGED = "changed"
SIGNAL_SELECTION_CHANGED = "selection-changed"
SIGNAL_ADD_DONE = "add-done"

COLOR_IDLE = "deep sky blue"
COLOR_SETUP = "yellow"
COLOR_BUSY = "light green"
COLOR_FAILED = "red"
COLOR_DECORATION = "light grey"

def CanvasPoints(plist):
    obj = Goo.CanvasPoints.new(len(plist))
    i = 0
    for p in plist:
        obj.set_point(i, p[0], p[1])
        i += 1
    return obj

class EmulicaCanvas(Goo.Canvas):
    """A subclass of Goo.Canvas, that represents an emulation model, 
    during both the modelling and execution phase. A EmulicaCanvas may contains at 
    least one ModuleLayer object: the root ModuleLayer, that can itself contains
    other ModuleLayer instance to represents submodels. The connections betweens
    modules belong to a connection_layer object.
    
    Attributes:
        widgets -- a dictionary of all graph ModuleWidget in this model key is module name
        model -- the emulation model that is represented
        selection -- list of the selected modules
        animate -- True if widget are animated during emulation
        commands -- the undo/redo manager
        contextmenu -- the context menu (popup on right-click) 
    """
    
    __gsignals__ = {SIGNAL_CHANGED : (GObject.SIGNAL_RUN_LAST, None, ()),
                    SIGNAL_SELECTION_CHANGED: (GObject.SIGNAL_RUN_LAST, None, (int,)),
                    SIGNAL_ADD_DONE: (GObject.SIGNAL_RUN_LAST, None, ())}
    
    def __init__(self, model, cmd_manager, contextmenu = None, animate = True):
        """Create a new instance of a EmulicaCanvas.
        
        Arguments:
            model -- the model to represent
            cmd_manager -- The CommandManager to implement undo/redo
            contextmenu -- the Gtk.Menu to popup on right-click (default = None)
            animate -- True if widget should be animated during emulation 
                       (default = True)
        """
        Goo.Canvas.__init__(self)
        self.animate = animate
        self.contextmenu = contextmenu
        self.widgets = dict()
        self.selection = ModuleSelection(self)
        self.commands = cmd_manager
        root_item = self.get_root_item()
        self.__connection_layer = Goo.CanvasGroup(parent = root_item)
        self.__module_layer = ModuleLayer(self, root_item)
        self.__adding = False
        
        self.set_bounds(0,0, 2000, 1000)
        self.set_size_request(2000, 1000)
        self.connect('button-press-event', self.__on_model_canvas_clicked)
        
        root_item.connect('button_press_event', self.selection.on_button_press)
        root_item.connect('button_press_event', self.popup_context_menu)
        root_item.connect('motion_notify_event', self.selection.on_motion_notify)
        root_item.connect ('button_release_event', self.selection.on_button_release)
        self.setup_model(model)

    

    def popup_context_menu(self, item, target, event):
        """Callback connected to button press events. Popup the contextual menu."""
        if event.get_button()[1] == 3 and not self.contextmenu == None:
            self.contextmenu.popup(None, None, None, None, event.get_button()[1], event.time)
        return True

    def setup_model(self, model):
        """Initialize the model attribute, and create the corresponding module 
        widgets.
        
        Arguments:
            model -- the model
            
        """
        self.model = model
        #clean canvas : ie delete all modules in self.widgets
        for (module, widget) in self.widgets.items():
            widget.remove()
        self.widgets.clear()
        self.__connection_layer.remove()
        self.__connection_layer = Goo.CanvasGroup(parent = self.get_root_item())
        #add modules to the module_layer
        modules = self.model.modules.values()
        modules.sort(lambda m1, m2: m2.is_model() - m1.is_model())
        for module in modules:
            new_widget = self.__module_layer.add_module(module)
            self.widgets[module] = new_widget
        for module in modules:
            self.widgets[module].set_emulation_module(module)
        
        self.model.connect('module-added', self.on_module_added)
        self.model.connect('module-removed', self.on_module_removed)
    
    def on_module_added(self, model, module):
        """Callback for module addition in model. Add a new ModuleWidget in the
        Canvas, at self.__adding_position."""
        logger.info(_("module {0} added").format(module.name))
        args = [module]
        if self.__adding:
            args.append(self.__adding_position)
        new_widget = self.__module_layer.add_module(*args)
        self.widgets[module] = new_widget
        new_widget.set_emulation_module(module)
        
    def on_module_removed(self, model, module):
        """Callback for module removal in model. Removes the corresponding 
        widget from the canvas and from the widget dictionary."""
        logger.info(_("module {0} removed").format(module.name))
        widget = self.widgets[module]
        self.__module_layer.remove_module(widget, module)
        del self.widgets[module]
        self.selection.remove(module)
    
    def apply_layout(self, layout, submodel = None):
        """Apply a layout to the canvas.
        
        Arguments:
            layout -- a dictionary that associate modules to positions
            submodel -- the submodel to which apply the layout (defaults to 
                        top-level model)
        """
        if submodel == None:
            layer = self.__module_layer
        else:
            layer = self.widgets[submodel]
        layer.apply_layout(layout)
        
    def get_layout(self):
        """Delegate to the top-level moduleLayer"""
        return self.__module_layer.get_layout()
    
    def fit_size(self):
        """Return the coordinates of the two oposite corners of a rectangle that
        fit the widgets in the canvas"""
        return self.__module_layer.fit_size()
        
    def get_connection_layer(self):
        """Return the group the contains all the connections between modules."""
        return self.__connection_layer  
    
    def write_pdf(self, pdffile):
        """Write the canvas to a pdf file."""
        bounds = self.get_root_item().get_bounds()
        surface = cairo.PDFSurface (pdffile, 9 * 72, 10 * 72)
        cr = cairo.Context (surface)
        
        #Place it in the middle of our 9x10 page.
        cr.translate(20, 130)
        
        self.render(cr, bounds, 1.0)
        cr.show_page()
    
    def set_adding(self, adding, moduleType = None):
        """If adding is true, the next click on the canvas will add a module in 
        the model and canvas. If adding is true, cancel a previous 
        set_adding(True)."""
        self.__adding = adding
        self.__adding_type = moduleType
    
    def __on_model_canvas_clicked(self, widget, event):
        """Mouse click on the model canvas"""
        #on right-click, if a module add has been requested, add the module
        if event.button == 1 and self.__adding:
            default_name = self.__adding_type.__name__+str(len(self.model.modules))
            #change event coordinates according to current zoom level...
            s = self.get_scale()
            self.__adding_position = (event.x / s, event.y / s)
            logger.debug("click at ('{0[0]}, {0[1]}), converted to ({1[0]}, {1[1]})".format(event.get_coords(), self.__adding_position))
            self.commands.create_module(default_name, self.__adding_type, self.model)
            self.emit(SIGNAL_ADD_DONE)
            self.emit(SIGNAL_CHANGED)
            self.__adding = False
            return True #event consumed   
        return False#event passed to the other widgets
    
    def delete_selection(self):
        """Delete selected modules from the model and the canvas."""
        for module in list(self.selection):#create a new list because the selection list will change
            self.commands.delete_module(module, self.model)
        self.emit(SIGNAL_CHANGED)
    
    def cut_clipboard(self, clipboard):
        """Cut currently selected modules into clipboard"""
        self.copy_clipboard(clipboard)
        self.delete_selection()
    
    def copy_clipboard(self, clipboard):
        """Serialize to xml and add the modules in the clipboard."""
        modules = self.selection
        elt = emuML.save_modules(self.model, modules)
        clipboard.set_text(elt, -1)
        logger.debug("put {0} into (private) clipboard.".format(elt))
    
    def paste_clipboard(self, clipboard):
        """Create and add in the model the module in the clipboard (if any)"""
        #get data from clipboard (xml strings)
        #NB: how to treat reference to non-existent modules ??
        elt = clipboard.wait_for_text() 
        modules = emuML.load_modules(self.model, elt)
        
        #self.add_modules(modules, [(20 + i * 10, 20 + i * 10) for i in range(len(modules))])
        
        self.emit(SIGNAL_CHANGED)
        
        
        
class ModuleLayer(Goo.CanvasGroup):
    """A  group of modules.
    
    Attributes:
        canvas -- the EmulicaCanvas this ModuleLayer belong to
        private_widgets -- a list of widgets that are in this module layer
        layout -- a dictionary of the form (module, position), where position is
                  a two-element tuple (x,y). The position is taken relatively to
                  the ModuleLayer
    
    """
    def __init__(self, canvas, parent, outlined = False):
        """Create a new module layer. 
        
        Argument:
            canvas = the EmulicaCanvas where to draw
            parent the containning item
            outlined = if true, draw a grey outline around the layer
        """
        Goo.CanvasGroup.__init__(self, parent = parent)
        self.emulica_canvas = canvas
        if outlined:
            self.__rect = Goo.CanvasRect(parent = self,
                                         line_width = 1,
                                         stroke_color = COLOR_DECORATION,
                                         fill_color = "light grey")
        else:
            self.__rect = None
        self.private_widgets = list()
        self.layout = dict()
        self.old_layout = dict()

    def apply_layout(self, layout):
        """Apply graphic layout. convert module names to module objects.
        
        Arguments:
            layout -- a dictionary of graphical properties (position) for each 
                     module.
            
        """
        for (module, position) in layout.items():
            widget = self.emulica_canvas.widgets[module]
            #convert position to the global coordinate system
            widget.set_position_at(self.emulica_canvas.convert_from_item_space(self, position[0], position[1]))
            self.update_position(module, *position)
        self.__update_outline()
        #self.update_layout()
        #print self.layout
    
    def update_position(self, module, x, y):
        """Update the position of a module in the layout."""
        logger.debug("set position ({0:f}, {1:f}) for module {2}".format(x, y, module))
        self.layout[module] = (x, y)
    
    def update_layout(self):
        """Update the layout dictionary according to current module positions."""
        for widget in self.private_widgets:
            (b, x, y, s, r) = widget.get_simple_transform()
            self.layout[widget.module] = (x, y)
        
    def get_layout(self):
        """Return the current model layout.
        
        Returns:
            a dictionary of the position of each module, identified by its name
        
        """
        self.update_layout()
        return dict([(module.name, p) for (module, p) in self.layout.items()])
    
    def fit_size(self):
        """Return the coordinate of the bounding box that fit the modules in the
        canvas"""
        (xmax, ymax, xmin, ymin) = (0, 0, 2000, 2000)
        for widget in self.private_widgets:
            (x1, y1, x2, y2) = widget.widget_bounds
            (b, x, y, s, r) = widget.get_simple_transform()
            #(x1, y1) = self.emulica_canvas.convert_to_item_space(self, x1 + x, y1 + y)
            #(x2, y2) = self.emulica_canvas.convert_to_item_space(self, x2 + x, y2 + y)
            xmin = min(x1 + x, xmin)
            ymin = min(y1 + y, ymin)
            xmax = max(x2 + x, xmax)
            ymax = max(y2 + y, ymax)
        return (xmin - 5, ymin - 5, xmax + 5, ymax + 20)
    
    def add_module(self, module, position = (0, 0), interactive = True):
        """Add a module in the module layer. The new widget is returned 
        ininitialized (ie its set_module method is not called). It is *not* 
        added to the widgets dictionary of the canvas.
        
        Arguments:
            module -- the module to add
            position -- where to put the new widget (default = (0,0))
            interactive -- if True the newly created module can be dragged and 
                           selected (default = True)
        
        Return:
            the newly created widget
            
        """
        WidgetClass = views[module.__class__.__name__]
        if not WidgetClass == None:
            widget = WidgetClass(self.emulica_canvas, self, interactive = interactive)
            self.private_widgets.append(widget)
        if module in self.old_layout:
            position =  self.old_layout[module]
            logger.debug("found position ({pos[0]:d}, {pos[1]:d}) in layout for module {mod}".format(pos = position, mod = module))
        else:    
            self.update_position(module, *position)
        widget.set_position_at(position)
        self.__update_outline()
        return widget
                
    def remove_module(self, widget, module):
        """Remove the module from the canvas."""
        self.private_widgets.remove(widget)
        position = self.layout[module]
        self.old_layout[module] = position
        del self.layout[module]
        widget.remove()
        self.__update_outline()
    
    def __update_outline(self):
        """Re-draw the outline rectangle"""
        if not self.__rect == None:
            (x1, y1, x2, y2) = self.fit_size()
            self.__rect.props.x = x1
            self.__rect.props.y = y1
            self.__rect.props.height = y2 - y1
            self.__rect.props.width = x2 - x1

class ModuleSelection(list):
    """This class represent the currently selected modules. Its the list of the 
    module instances of the currently selected modules."""
    def __init__(self, canvas):
        list.__init__(self)
        self.__rect_corner = (0,0)
        self.emulica_canvas = canvas
        self.__rect = Goo.CanvasRect(parent = canvas.get_root_item(),
                                     x = 0,
                                     y = 0,
                                     width = 0,
                                     height = 0)
        
        
    def remove(self, module):
        """Remove a module from the selection, if present (else, do nothing)."""
        if module in self:
            list.remove(self, module)
            self.emulica_canvas.emit(SIGNAL_SELECTION_CHANGED, len(self))
        
    def reverse_search(self, item):
        """Search and Return the module associated with the widget item."""
        for (k,v) in self.emulica_canvas.widgets.items():
            if (v == item):
                return k
    
    def on_item_button_press (self, item, target, event):
        """Callback for 'button-press-event' on ModuleWidgets."""
        module = self.reverse_search(item)
        if event.get_button()[1] == 1:
            must_select = not (module in self)
            if event.state & Gdk.ModifierType.CONTROL_MASK:
                #if in multiple selection: only unselect clicked module
                if not must_select:
                    item.unselect()
                    list.remove(self, module)
            else:
                #if not in multiple selection: unselect all modules
                while len(self) > 0:
                    other = self.pop()
                    self.emulica_canvas.widgets[other].unselect()
            
        elif event.get_button()[1] == 3:
            must_select = not (module in self)
        else:
            must_select = False
        if must_select:
            item.select()
            self.append(module)
        self.emulica_canvas.emit(SIGNAL_SELECTION_CHANGED, len(self))
        return False
        
    def on_button_press (self, item, target, event):
        """Callback for 'button-press-event' on the background. Set first 
        corner of selection rectangle. Unselect modules"""
        if event.button == 1:
            if not event.state & Gdk.ModifierType.CONTROL_MASK:
                for widget in self.emulica_canvas.widgets.values():
                    widget.unselect()
                was_empty = len(self) == 0
                del self[0:len(self)]
                if not was_empty:
                    self.emulica_canvas.emit(SIGNAL_SELECTION_CHANGED, len(self))
            self.__rect_corner = (event.x, event.y)
            self.__rect.props.height = 0
            self.__rect.props.width = 0
        
    def on_motion_notify (self, item, target, event):
        """Callback for the 'button-release-event'. re-draw selection 
        rectangle and update selection.
        """
        if event.state & Gdk.EventMask.BUTTON1_MOTION_MASK:
            x = min(self.__rect_corner[0], event.x)
            y = min(self.__rect_corner[1], event.y)
            w = abs(event.x - self.__rect_corner[0])
            h = abs(event.y - self.__rect_corner[1])
            self.__rect.props.x = x
            self.__rect.props.y = y
            self.__rect.props.height = h
            self.__rect.props.width = w
            self.__rect.props.visibility = Goo.ITEM_VISIBLE
            changed = False
            for (module, widget) in self.emulica_canvas.widgets.items():
                if widget.interactive:
                    bounds = widget.get_bounds()
                    module = self.reverse_search(widget)
                    if (not module in self and
                        bounds.x1 >= x and bounds.x2 <= (x + w) and 
                        bounds.y1 >= y and bounds.y2 <= (y + h)):
                        widget.select()
                        
                        self.append(module)
                        changed = True
            if changed: 
                self.emulica_canvas.emit(SIGNAL_SELECTION_CHANGED, len(self))
            
    def on_button_release(self, item, target, event):
        """Callback for the 'button-release-event'. Hide selection 
        rectangle"""
        self.__rect.props.visibility = Goo.CanvasItemVisibility.HIDDEN#TODO: 


class ModuleWidget(Goo.CanvasGroup):
    """
    A ModuleWidget is a generic object used to represent all emulation modules.
    
    Attributes:
        canvas -- the root gui
        listeners -- a dictionary of modules that must be updated is case of position change
        name -- module's name
    """
    def __init__(self, canvas, parent, interactive = True):
        """Create a new instance of a ModuleWidget
        
        Arguments:
            canvas -- the canvas (EmulicaCanvas Object)
            parent -- the parent Widget (usually a ModuleLayer object)
            interactive -- if True, the ModuleWidget can be dragged and selected
                           (default = True)
            
        """
        Goo.CanvasGroup.__init__(self, parent = parent)
        self.emulica_canvas = canvas
        self.listeners = dict()
        self.dependants = list()
        self.__dragging = False
        self.interactive = interactive
        if self.interactive:
            self.connect("motion_notify_event", self.__on_motion_notify)
            self.connect("button_press_event", self.__on_button_press)
            self.connect("button_press_event", self.emulica_canvas.selection.on_item_button_press)
            self.connect("button_press_event", self.emulica_canvas.popup_context_menu)
            self.connect("button_release_event", self.__on_button_release)
        self.connect("enter-notify-event", self.__on_item_enter)
        self.connect("leave-notify-event", self.__on_item_leave)
        self.selected = False
        self.name = None
    
    def translate(self, x, y):
        """Wrapper around Goo's translate, that notify listeners of position changes
        
        Arguments:
            x, y -- coordinate of the translation
            
        """
        Goo.CanvasGroup.translate(self, x, y)
        #if widget has childs widget, notify them
        if 'private_widgets' in dir(self):
            for child_widget in self.private_widgets:
                child_widget.notify()
        self.notify()
        
    def set_position_at(self, point):
        """Move the widget to the given position (in the canvas global 
        coordinate system).
        
        Arguments:
            point -- a (x, y) tuple
            
        """
        (b, x, y, s, r) = self.get_simple_transform()
        (x, y) = self.emulica_canvas.convert_to_item_space(self.get_parent(), point[0], point[1])
        self.set_simple_transform(x, y, s, r)
        self.notify()
        #(delta_x, delta_y) = (point[0] - x, point[1] - y)
        #translate in the parent coordinate system
        
        #self.translate(delta_x, delta_y)
        
    def add_listener(self, listener, update_method):
        """Add a listener.
        
        Arguments:
            listener -- the listener to add
            update_method -- the method to call when an update is needed
            
        """
        self.listeners[listener] = update_method
        
    def remove_listener(self, listener):
        """Remove a listener"""
        del self.listeners[listener]
        
    def remove(self):
        """Wraps around Goo.Item.remove(), to ensure that dependant widgets are removed too"""
        for widget in self.dependants:
            widget.remove()
        Goo.CanvasItem.remove(self)
    
    def notify(self):
        """Notify listeners. The notification method is called with self as argument."""
        for method in self.listeners.values():
            method(self)

    def select(self):
        """Draw the widget as 'selected'."""
        if not self.selected:
            (x1, y1, x2, y2) = self.widget_bounds
            self.selection_rect = Goo.CanvasRect(parent = self,
                                                 x = x1 - 3,
                                                 y = y1 - 3,
                                                 width = x2 - x1 + 6,
                                                 height = y2 - y1 + 6,
                                                 radius_x = 3,
                                                 radius_y = 3,
                                                 line_width = 1)
            self.selected = True
        
    def unselect(self):
        """Draw the widget as 'unselected'."""
        if self.selected:
            self.selection_rect.remove()
            self.selected = False

    def __on_motion_notify(self, item, target, event):
        """Callback usefull to drag widget."""
        if self.__dragging and (event.state & Gdk.ModifierType.BUTTON1_MASK):
            new_x = event.x
            new_y = event.y
            item.translate(new_x - self.__drag_x, new_y - self.__drag_y)
            #also translate all selected modules
            for module in self.emulica_canvas.selection:
                widget = self.emulica_canvas.widgets[module]
                if not widget is self:
                    widget.translate(new_x - self.__drag_x, new_y - self.__drag_y)
            return True
        else:
            #convert event coord from item space
            (event.x, event.y) = self.emulica_canvas.convert_from_item_space(self, event.x, event.y)
            return False
    
    def __on_button_press(self, item, target, event):
        """Method executed when a widget is clicked"""
        #TODO: check event type (press/release/2press)
        if event.get_button()[1] == 1:
            self.__drag_x = event.x
            self.__drag_y = event.y
            fleur = Gdk.Cursor(Gdk.CursorType.FLEUR)
            canvas = item.get_canvas()
            canvas.pointer_grab(item,
                                Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK,
                                fleur,
                                event.time)
            self.__dragging = True
        if  event.get_button()[1] == 1 and event.get_click_count()[1] == 2:
            prop_win = PropertiesDialog(None, self.module, self.emulica_canvas.model, self.emulica_canvas.commands)
            prop_win.show()
        return False

    def __on_button_release(self, item, target, event):
        """Callback useful for draging"""
        canvas = item.get_canvas()
        canvas.pointer_ungrab(item, event.time)
        self.__dragging = False
        # update position in layout...
        (b, x, y, s, r) = self.get_simple_transform()
        self.get_parent().update_position(self.module, x, y)

    def __on_item_enter(self, item, t_item, event):
        """Callback called when the cursor enters a ModuleWidget"""
        (x1, y1, x2, y2) = self.widget_bounds
        if ('module' in dir(self)) and self.module:
            name = self.module.name
            if self.name is None:
                self.name = Goo.CanvasText(parent = self,
                                           x = (x2 - x1)/2,
                                           y = y2 + 5,
                                           text = name,
                                           anchor = Goo.CanvasAnchorType.N,
                                           font = 'arial')
            else:
                self.name.props.text = name
                self.name.props.visibility = Goo.CanvasItemVisibility.VISIBLE

    def __on_item_leave(self, item, t_item, event):
        """Callback called when the cursor leaves a ModuleWidget"""
        if self.name:
            self.name.props.visibility = Goo.CanvasItemVisibility.HIDDEN
            self.__rect_corner = (0,0)


class Model(ModuleWidget, ModuleLayer):
    """A Wiget that represent a submodel.
    
    Attribute:
        
        
    """
    def __init__(self, canvas, parent, interactive = True):
        """Create a new instance of Model widget"""
        ModuleWidget.__init__(self, canvas, parent, interactive)
        ModuleLayer.__init__(self, canvas, parent, outlined = True)
        #TODO: render submodel at a different scale.
        #(b, x, y, s, r) = self.get_simple_transform()
        #self.set_simple_transform(x, y, 0.5, r)
        
        
    def set_emulation_module(self, mod):
        """Associate this widget with the model."""
        self.module = mod
        modules = mod.modules.values()
        modules.sort(lambda m1, m2: m1.is_model() - m2.is_model())
        for module in modules:
            new_widget = self.add_module(module, interactive = False)
            self.emulica_canvas.widgets[module] = new_widget
        for module in modules:
            self.emulica_canvas.widgets[module].set_emulation_module(module)
        
        #TODO: connect to the module-added signal
        mod.connect('module-added', self.__on_module_added)
    
    
    def __on_module_added(self, model, module):
        """Callback called when a module is added to a submodel"""
        new_widget = self.add_module(module, interactive = False)
        self.emulica_canvas.widgets[module] = new_widget
        self.emulica_canvas.widgets[module].set_emulation_module(module)
    
    def __getattr__(self, attr):
        """Compute the actual size of the modulewidget when the widget_bounds is
        accessed."""
        if attr == 'widget_bounds':
            return self.fit_size()
        else:
            raise AttributeError, attr


class Holder(ModuleWidget):
    """Widget the represents an emulation.Holder object"""
    def __init__(self, canvas, parent, num_slot = 4, interactive = True):
        ModuleWidget.__init__(self, canvas, parent, interactive)
        self.__width = 80
        self.__height = 20
        self.__slot = list()
        self.__input_port = Goo.CanvasEllipse(parent = self,
                                              center_x = 0,
                                              center_y = self.__height/2,
                                              radius_x = 4,
                                              radius_y = 4,
                                              fill_color = 'dark green',              
                                              line_width = 0)       
        self.__output_port = Goo.CanvasEllipse(parent = self,
                                               center_x = self.__width,
                                               center_y = self.__height/2,
                                               radius_x = 4,
                                               radius_y = 4,
                                               fill_color = 'dark green',              
                                               line_width = 0) 
        self.__rect = Goo.CanvasRect(parent = self,
                                     x = 0,
                                     y = 0,
                                     width = self.__width,
                                     height = self.__height,
                                     line_width = 1,
                                     fill_color = 'pale green')
        self.__text = Goo.CanvasText(parent = self,
                                     x = 8,
                                     y = self.__height / 2,
                                     text = 0,
                                     anchor = Goo.CanvasAnchorType.W,
                                     font = 'arial')
        for i in range(num_slot - 1, -1, -1):
            self.__slot.insert(0,Goo.CanvasRect(parent = self,
                               x = (self.__width - self.__height + 3) - (i * 7),
                               y = 3,
                               width = self.__height - 6,
                               height = self.__height - 6,
                               line_width = 1,
                               radius_x = 4,
                               radius_y = 4,
                               fill_color = 'pale green',
                               stroke_color = 'dark green'))
        self.widget_bounds = (0, 0, self.__width, self.__height)
    
    def make_shape_holder(self, shape):
        #hide text and slot[>0]
        self.__text.props.visibility = Goo.CanvasItemVisibility.HIDDEN
        for s in self.__slot[1:]:
            s.props.visibility = Goo.CanvasItemVisibility.HIDDEN
        #change width
        self.__rect.props.width = 20
        self.__output_port.props.center_x = 20
        self.__slot[0].props.x = 3
        self.widget_bounds = (0, 0, 20 , self.__height)
        #listen to shape module's position
        self.set_position_at(shape.holder_coord())
        self.raise_(shape)
        shape.add_listener(self, self.update)
        self.notify()
    
    def make_normal_holder(self, shape):
        #show text and slot[>0]
        self.__text.props.visibility = Goo.CanvasItemVisibility.VISIBLE
        for s in self.__slot[1:]:
            s.props.visibility = Goo.CanvasItemVisibility.VISIBLE
        #change width
        self.__rect.props.width = 80
        self.__output_port.props.center_x = 80
        self.__slot[0].props.x = (self.__width - self.__height + 3)
        self.widget_bounds = (0, 0, self.__width, self.__height)
        #don't listen to shape module's position
        shape.remove_listener(self)
        
    
    def update(self, shape):
        self.set_position_at(shape.holder_coord())
        self.notify()
    
    def input_port_coord(self):
        """Return a tupple of the coordinate of input port, in the display 
        coordinate system."""
        (b, x, y, s, r) = self.get_simple_transform()
        return self.get_canvas().convert_from_item_space(self.get_parent(),
                                            self.__input_port.props.center_x + x,
                                            self.__input_port.props.center_y + y)
                                            

    def output_port_coord(self):
        """Return a tupple of the coordinate of output port, in the display 
        coordinate system."""
        (b, x, y, s, r) = self.get_simple_transform()
        return self.get_canvas().convert_from_item_space(self.get_parent(), 
                                                         self.__output_port.props.center_x + x,
                                                         self.__output_port.props.center_y + y)

    def observer_port_coord(self):
        slot = self.__slot[0]
        (b, x, y, s, r) = self.get_simple_transform()
        x = slot.props.x + (slot.props.width / 2) + x
        y = self.__slot[0].props.y + y
        return self.get_canvas().convert_from_item_space(self.get_parent(), x, y)

    def set_emulation_module(self, mod):
        self.module = mod
        mod.connect("state-changed", self.animate)
        
    def animate(self, state):
        """state is a integer corresponding to the number of product in the queue"""
        def change_widget(state):
            i = 0
            for s in self.__slot:            
                if i < state:
                    s.props.fill_color = 'green3'
                else:
                    s.props.fill_color = 'pale green'
                i += 1
            self.__text.props.text = str(state)
        if self.get_canvas().animate:
            GLib.idle_add(change_widget, state)
        

class Connection(Goo.CanvasPolyline):
    """A graphical connection between to Module Widgets"""
    def __init__(self, canvas, source, destination, weak = False, color = 'dark green'):
        self.source = source
        self.destination = destination
        source.add_listener(self, getattr(self,'update'))
        destination.add_listener(self, getattr(self,'update'))
        (x1, y1) = source.output_port_coord()
        (x2, y2) = destination.input_port_coord()
        p_points = CanvasPoints(self.__route(self.source, self.destination))

        Goo.CanvasPolyline.__init__(self, parent = canvas.get_connection_layer(), 
                                                  points = p_points, 
                                                  close_path = False, 
                                                  stroke_color = color)
        if weak:
            #self.props.line_dash = Goo.CanvasLineDash.newv([5.0, 3.0])#May not work with stock goocanvas typelib
            self.props.stroke_color = 'orange'
        
    def __route(self, source, dest):
        (x1, y1) = source.output_port_coord()
        (x2, y2) = dest.input_port_coord()
        #return [(x1, y1), ((x2+x1)/2, y1), ((x1+x2)/2, y2), (x2, y2)]
        return [(x1, y1), (x2, y2)]
        
    def update(self, node):
        (x1, y1) = self.source.output_port_coord()
        (x2, y2) = self.destination.input_port_coord()
        self.set_property("points", CanvasPoints(self.__route(self.source, self.destination)))



class PushObserver(ModuleWidget):
    """
    Graphical element that represent an Observer emulation module
    
    Attributes:
        holder -- the Holder Module this observer is connected to
    """
    
    def __init__(self, canvas, parent, interactive = True):
        ModuleWidget.__init__(self, canvas, parent, interactive)
        p_points = CanvasPoints([(0, 5), (20, -35), (0, -25), (15, -55)])
        Goo.CanvasPolyline(parent = self,
                           points = p_points,
                           line_width = 3,
                           end_arrow = True,
                           stroke_color = 'sienna4')
        self.__ellipse = Goo.CanvasEllipse(parent = self,
                                           center_x = 10, 
                                           center_y = -15,
                                           radius_x = 10,
                                           radius_y = 8,
                                           line_width = 1,
                                           stroke_color = 'DarkGoldenRod',
                                           fill_color = 'white')    
        self.__text = Goo.CanvasText(parent = self,
                                   x = 10,
                                   y = -15,
                                   anchor = Goo.CanvasAnchorType.CENTER,
                                   font = "sans 10",
                                   text = "")
        self.holder = None
        self.widget_bounds = (-2, -55, 22, 5)
    
    def set_emulation_module(self, mod):
        """Set letter according to observer type."""
        self.module = mod
        mod.connect('state-changed', self.animate)
        mod.connect('property-changed', self.on_property_change)
        self.set_type(mod)
        if mod['holder'] in self.emulica_canvas.widgets.keys():
            self.set_holder(self.emulica_canvas.widgets[mod['holder']])
   
    def on_property_change(self, prop, module):
        if prop == 'holder' and not module[prop] == None:
            if module[prop] in self.emulica_canvas.widgets.keys():
                holder_widget = self.emulica_canvas.widgets[module[prop]]
            else:
                holder_widget = None
            self.set_holder(holder_widget)
        elif prop in ('identify', 'observe_type'):
            self.set_type(module)
            
    def set_type(self, module):
        """Set the text in the widget according to emulation module's properties."""
        try:
            if module['identify']:
                self.__text.props.text = 'Id'
            elif module['observe_type']:
                self.__text.props.text = 'T'
            else:
                self.__text.props.text = 'b'
        except KeyError:
            self.__text.props.text = '?'
    
    def set_holder(self, new_holder):
        """Set holder widget. If new_holder is the same as self.holder, do nothing."""
        if not self.holder == new_holder:
            if not self.holder == None:
                self.holder.remove_listener(self)
            self.holder = new_holder
            if not new_holder == None:
                self.holder.add_listener(self,self.update)
                self.update()
                self.raise_(self.holder)
    
    def update(self, node = None):
        self.set_position_at(self.holder.observer_port_coord())

    def animate(self, state):
        """Animate when the observer is active (ie a report has been sent)"""
        def change_widget(state):
            if state:
                
                #TODO: how to animate observation events ??
                self.__ellipse.animate(-3, 5, 1.4, 0, True, 50, 25, Goo.CanvasAnimateType.RESET)
                
        if self.get_canvas().animate:
            GLib.idle_add(change_widget, state)


class PullObserver(ModuleWidget):
    """
    Graphical element that represent an Observer emulation module
    
    Attributes:
        holder -- the Holder Module this observer is connected to
    """
    
    def __init__(self, canvas, parent, interactive = True):
        ModuleWidget.__init__(self, canvas, parent, interactive)
        p_points = CanvasPoints([(0, 5), (20, -35), (0, -25), (15, -55)])
        Goo.CanvasPolyline(parent = self,
                           points = p_points,
                           line_width = 3,
                           end_arrow = True,
                           start_arrow = True,
                           stroke_color = 'sienna4')
        self.holder = None
        self.widget_bounds = (-2, -55, 22, 5)
    
    def set_emulation_module(self, mod):
        """Set letter according to observer type."""
        self.module = mod
        mod.connect('state-changed', self.animate)
        mod.connect('property-changed', self.on_property_change)
        if mod['holder'] in self.emulica_canvas.widgets.keys():
            self.set_holder(self.emulica_canvas.widgets[mod['holder']])
   
    def on_property_change(self, prop, module):
        if prop == 'holder' and not module[prop] == None:
            if module[prop] in self.emulica_canvas.widgets.keys():
                holder_widget = self.emulica_canvas.widgets[module[prop]]
            else:
                holder_widget = None
            self.set_holder(holder_widget)
    
    def set_holder(self, new_holder):
        """Set holder widget. If new_holder is the same as self.holder, do nothing."""
        if not self.holder == new_holder:
            if not self.holder == None:
                self.holder.remove_listener(self)
            self.holder = new_holder
            if not new_holder == None:
                self.holder.add_listener(self,self.update)
                self.update()
                self.raise_(self.holder)
    
    def update(self, node = None):
        self.set_position_at(self.holder.observer_port_coord())

    def animate(self, state):
        """Animate when the observer is active (ie a report has been sent)"""
        def change_widget(state):
            if state:
                pass
                #TODO: how to animate widget ?
        if self.get_canvas().animate:
            GLib.idle_add(change_widget, state)


class Create(ModuleWidget):
    def __init__(self, canvas, parent, holder = None, interactive = True):
        ModuleWidget.__init__(self, canvas, parent, interactive)
        p_points = CanvasPoints([(0, 0), (40, 0), (60, 20), (40, 40), (0, 40)])
        
        self.output_port = Goo.CanvasEllipse(parent = self,
                                             center_x = 60,
                                             center_y = 20,
                                             radius_x = 4,
                                             radius_y = 4,
                                             fill_color = "dark blue",
                                             line_width = 0)
        Goo.CanvasPolyline(parent = self,
                           points = p_points,
                           stroke_color = "dark blue",
                           fill_color = "SlateBlue1",
                           line_width = 1,
                           close_path = True)
        self.__light = Goo.CanvasEllipse(parent = self,
                                         center_x = 10,
                                         center_y = 10,
                                         radius_x = 5,
                                         radius_y = 5,
                                         fill_color = COLOR_BUSY,
                                         line_width = 1,
                                         stroke_color = "black")
        self.__text = Goo.CanvasText(parent = self,
                                     x = 3,
                                     y = 33,
                                     anchor = Goo.CanvasAnchorType.W,
                                     font = "sans 6",
                                     text = "")
        self.__num = Goo.CanvasText(parent = self,
                                    x = 53,
                                    y = 33,
                                    anchor = Goo.CanvasAnchorType.W,
                                    font = "sans 6",
                                    text = "0")
        self.widget_bounds = (0, 0, 60, 40)
        self.connection = None
        self.__set_holder(holder)
    
    def set_emulation_module(self, mod):
        self.module = mod
        mod.connect("state-changed", self.animate)
        mod.connect("property-changed", self.__on_property_change)
        if not mod['destination'] == None:
            holder = self.emulica_canvas.widgets[mod['destination']]
            self.__set_holder(holder)
    
    def __on_property_change(self, prop, module):
        if prop == "destination" and not module[prop] == None and not self.emulica_canvas.widgets[module[prop]] == self.holder:
            self.__set_holder(self.emulica_canvas.widgets[module[prop]])
    
    def __set_holder(self, holder):
        self.holder = holder
        if not self.connection == None:
            self.connection.remove()
        if not holder == None:    
            self.connection = Connection(self.emulica_canvas, self, holder)
            self.dependants.append(self.connection)
            
    def output_port_coord(self):
        """Return a tupple of the coordinate of output port"""
        return self.get_canvas().convert_from_item_space(self.output_port, 
                                                         self.output_port.props.center_x,
                                                         self.output_port.props.center_y)
                                                         
    def animate(self, state):
        """Animate the widget when emulation module change"""
        #self.__light.animate(-5, -5, 1.5, 0, True, 150, 25, Goo.CanvasAnimateType.RESET)
        def change_widget(state):
            self.__text.props.text = str(state)
            self.__num.props.text = str(self.module.quantity_created)
        if self.get_canvas().animate:
            GLib.idle_add(change_widget, state)

class Dispose(ModuleWidget):
    def __init__(self, canvas, parent, holder = None, interactive = True):
        ModuleWidget.__init__(self, canvas, parent, interactive)
        p_points = CanvasPoints([(0, 20), (20, 0), (60, 0), (60, 40), (20, 40)])
        
        self.input_port = Goo.CanvasEllipse(parent = self,
                                             center_x = 0,
                                             center_y = 20,
                                             radius_x = 4,
                                             radius_y = 4,
                                             fill_color = "dark blue",              
                                             line_width = 0)
        self.line = Goo.CanvasPolyline(parent = self,
                                       points = p_points,
                                       line_width = 1,
                                       fill_color = "SlateBlue1",
                                       stroke_color = "dark blue",
                                       close_path = True)
        self.__light = Goo.CanvasEllipse(parent = self,
                                         center_x = 50,
                                         center_y = 10,
                                         radius_x = 5,
                                         radius_y = 5,
                                         fill_color = COLOR_BUSY,
                                         line_width = 1,
                                         stroke_color = "black")
        self.widget_bounds = (0, 0, 60, 40)
        self.connection = None
        self.__set_holder(holder)
    
    def set_emulation_module(self, mod):
        self.module = mod
        mod.connect("state-changed", self.animate)
        mod.connect("property-changed", self.__on_property_change)
        emu_holder = mod['source']
        if not emu_holder == None:
            holder = self.emulica_canvas.widgets[emu_holder]
            self.__set_holder(holder)
    
    def __on_property_change(self, prop, module):
        if prop == "source" and not module[prop] == None and not self.emulica_canvas.widgets[module[prop]] == self.holder:
            self.__set_holder(self.emulica_canvas.widgets[module[prop]])
    
    def __set_holder(self, holder):
        self.holder = holder
        if not self.connection == None:
            self.connection.remove()
        if not holder == None:
            self.connection = Connection(self.emulica_canvas, holder, self)
            self.dependants.append(self.connection)
            
    def input_port_coord(self):
        """Return a tupple of the coordinate of output port"""
        return self.get_canvas().convert_from_item_space(self.input_port, 
                                                         self.input_port.props.center_x,
                                                         self.input_port.props.center_y)
                                                         
    def animate(self, state):
        """animate object when emulation module is active"""
        def change_widget(state):
            self.__light.animate(-25, -5, 1.5, 0, True, 150, 25, Goo.CanvasAnimateType.RESET)
        if self.get_canvas().animate:
            GLib.idle_add(change_widget, state)
        
        
class Space(ModuleWidget):
    def __init__(self, emulica_canvas, parent, interactive = True):
        ModuleWidget.__init__(self, emulica_canvas, parent, interactive)
        self.connections = dict()
        Goo.CanvasRect(parent = self,
                       height = 60,
                       width = 60,
                       radius_x = 15,
                       radius_y = 15,
                       fill_color = "SlateBlue1",
                       line_width = 1,
                       stroke_color = "dark blue")
        Goo.CanvasPolyline(parent = self,
                           points = CanvasPoints([(25, 25), (55, 55)]),
                           line_width = 4,
                           arrow_length = 2.5,
                           arrow_tip_length = 2.5,
                           arrow_width = 2.5,
                           end_arrow = True,
                           start_arrow = True,
                           stroke_color = COLOR_DECORATION)
        Goo.CanvasPolyline(parent = self,
                           points = CanvasPoints([(25, 55), (55, 25)]),
                           line_width = 4,
                           arrow_length = 2.5,
                           arrow_tip_length = 2.5,
                           arrow_width = 2.5,
                           end_arrow = True,
                           start_arrow = True,
                           stroke_color = COLOR_DECORATION)
        self.__light = Goo.CanvasEllipse(parent = self,
                                         center_x = 15,
                                         center_y = 15,
                                         radius_x = 5,
                                         radius_y = 5,
                                         fill_color = COLOR_IDLE,
                                         line_width = 1,
                                         stroke_color = "black")
        self.__text = Goo.CanvasText(parent = self,
                                     x = 10,
                                     y = 50,
                                     anchor = Goo.CanvasAnchorType.W,
                                     font = "sans 6",
                                     text = "")
        self.widget_bounds = (0, 0, 60, 60)
                                     
    def set_emulation_module(self, mod):
        self.module = mod
        for (name, prog) in mod['program_table'].items():
            self.__create_connection(name, prog)
        mod.connect("state-changed", self.animate)
        mod.connect("property-changed", self.__on_property_change)
    
    def __create_connection(self, name, prog):
        if 'source' in prog.transform.keys() and 'destination' in prog.transform.keys() \
        and not prog.transform['source'] is None and not prog.transform['destination'] is None:
            
            src = self.emulica_canvas.widgets[prog.transform['source']]
            dst = self.emulica_canvas.widgets[prog.transform['destination']]
            connec_widget = Connection(self.emulica_canvas, src, dst, weak = True)
            self.connections[name] = (src, dst, connec_widget)
            self.dependants.append(connec_widget)
    
    def __on_property_change(self, prop, module):
        if prop == "program_table" and not module[prop] == None:
            for (name, prog) in module[prop].items():
                #if a prog is not in the connection dict, create it
                if not name in self.connections.keys():
                    self.__create_connection(name, prog)
                #if it is present but has changed, remove/create
                elif not self.connections[name][:2] == (prog.transform['source'], prog.transform['destination']):
                    self.connections[name][2].remove()
                    self.__create_connection(name, prog)
            #if some connection are not used, remove
            for (name, (src, dst, widget)) in self.connections.items():
                if not name in module[prop].keys():
                    widget.remove()
    
    def animate(self, state):
        def change_widget(state):
            if state == 'idle':
                self.__light.props.fill_color = COLOR_IDLE
            elif state == 'setup':
                self.__light.props.fill_color = COLOR_SETUP
            elif state == 'failed':
                self.__light.props.fill_color = COLOR_FAILED
            else:
                self.__light.props.fill_color = COLOR_BUSY
            self.__text.props.text = str(state)
        if self.get_canvas().animate:
            GLib.idle_add(change_widget, state)

class Shape(ModuleWidget):
    def __init__(self, canvas, parent, interactive = True):
        ModuleWidget.__init__(self, canvas, parent, interactive)
        self.holder = None
        self.__rect = Goo.CanvasRect(parent = self,
                       height = 60,
                       width = 60,
                       fill_color = "SlateBlue1",
                       line_width = 1,
                       stroke_color = "dark blue")
        self.__gear = Goo.CanvasGroup(parent = self)
        points = CanvasPoints([(-8, -20), (-8, -30), (-5, -40), (5, -40), (8, -30), (8, -20)])
        for i in range(0, 7):
            teeth = Goo.CanvasPolyline(parent = self.__gear,
                               points = points,
                               close_path = True,
                               fill_color = COLOR_DECORATION,
                               line_width = 0)
            teeth.rotate(i*360/7, 0, 0)
        Goo.CanvasEllipse(parent = self.__gear,
                          center_x = 0, center_y = 0,
                          radius_x = 27, radius_y = 27,
                          fill_color = COLOR_DECORATION,
                          line_width = 0)
        Goo.CanvasEllipse(parent = self.__gear,
                          center_x = 0, center_y = 0,
                          radius_x = 10, radius_y = 10,
                          fill_color = "SlateBlue1",
                          line_width = 0)
        self.__gear.set_simple_transform(40, 40, 0.4, 20)
        self.__light = Goo.CanvasEllipse(parent = self,
                                         center_x = 15,
                                         center_y = 15,
                                         radius_x = 5,
                                         radius_y = 5,
                                         fill_color = COLOR_IDLE,
                                         line_width = 1,
                                         stroke_color = "black")
        self.__text = Goo.CanvasText(parent = self,
                                     x = 3,
                                     y = 53,
                                     anchor = Goo.CanvasAnchorType.W,
                                     font = "sans 6",
                                     text = "")
        self.widget_bounds = (0, 0, 60, 60)
                                     

    def set_emulation_module(self, mod):
        self.module = mod
        if mod['holder'] in self.emulica_canvas.widgets.keys():
            self.__set_holder(self.emulica_canvas.widgets[mod['holder']])
        else:
            self.__set_holder(None)
        mod.connect("state-changed", self.animate)
        mod.connect("property-changed", self.__on_property_change)
    
    def __set_holder(self, new_holder):
        if not self.holder == new_holder:
            if not self.holder == None:
                self.holder.make_normal_holder(self)
            self.holder = new_holder
            if not new_holder == None:
                new_holder.make_shape_holder(self)
    
    def __on_property_change(self, prop, module):
        if prop == 'holder':
            if module[prop] in self.emulica_canvas.widgets.keys():
                self.__set_holder(self.emulica_canvas.widgets[module[prop]])
            else:
                self.__set_holder(None)
            
    
    def holder_coord(self):
        """Return the center of the module, where the holder should be"""
        (b, x, y, s, r) = self.get_simple_transform()
        return self.get_canvas().convert_from_item_space(self.get_parent(), 
                                                         self.__rect.props.x + 30 + x,
                                                         self.__rect.props.y + 10 + y)
    
    def animate(self, state):
        def change_widget(state):
            if state == 'idle':
                self.__light.props.fill_color = COLOR_IDLE
            elif state == 'setup':
                self.__light.props.fill_color = COLOR_SETUP
            elif state == 'failed':
                self.__light.props.fill_color = COLOR_FAILED
            else:
                self.__light.props.fill_color = COLOR_BUSY
            self.__text.props.text = str(state)
        if self.get_canvas().animate:
            GLib.idle_add(change_widget, state)


class Assemble(ModuleWidget):
    def __init__(self, canvas, parent, interactive = True):
        ModuleWidget.__init__(self, canvas, parent, interactive)
        self.holder = None
        self.connections = dict()
        self.__rect = Goo.CanvasRect(parent = self,
                       height = 60,
                       width = 60,
                       fill_color = "SlateBlue1",
                       line_width = 1,
                       stroke_color = "dark blue")
        Goo.CanvasPolyline(parent = self,
                           points = CanvasPoints([(25, 27), (37, 40), (55, 40)]),
                           line_width = 4,
                           arrow_length = 2.5,
                           arrow_tip_length = 2.5,
                           arrow_width = 2.5,
                           end_arrow = True,
                           start_arrow = False,
                           stroke_color = COLOR_DECORATION)
        Goo.CanvasPolyline(parent = self,
                           points = CanvasPoints([(25, 52), (37, 40)]),
                           line_width = 4,
                           end_arrow = False,
                           start_arrow = False,
                           stroke_color = COLOR_DECORATION)
        self.__light = Goo.CanvasEllipse(parent = self,
                                         center_x = 15,
                                         center_y = 15,
                                         radius_x = 5,
                                         radius_y = 5,
                                         fill_color = COLOR_IDLE,
                                         line_width = 1,
                                         stroke_color = "black")
        self.__text = Goo.CanvasText(parent = self,
                                     x = 3,
                                     y = 53,
                                     anchor = Goo.CanvasAnchorType.W,
                                     font = "sans 6",
                                     text = "")
        self.widget_bounds = (0, 0, 60, 60)

    def set_emulation_module(self, mod):
        self.module = mod
        for (name, prog) in mod['program_table'].items():
            self.__create_connection(name, prog)
        if mod['holder'] in self.emulica_canvas.widgets.keys():
            self.__set_holder(self.emulica_canvas.widgets[mod['holder']])
        else:
            self.__set_holder(None)
        mod.connect("state-changed", self.animate)
        mod.connect("property-changed", self.__on_property_change)
    
    def __set_holder(self, new_holder):
        if not self.holder == new_holder:
            if not self.holder == None:
                self.holder.make_normal_holder(self)
            self.holder = new_holder
            if not new_holder == None:
                new_holder.make_shape_holder(self)
                
    
    def __create_connection(self, name, prog):
        if 'source' in prog.transform.keys() and not self.holder == None:
            src = self.emulica_canvas.widgets[prog.transform['source']]
            dst = self.holder
            connec_widget = Connection(self.emulica_canvas, src, dst, weak = True, color = 'purple')
            self.connections[name] = (src, dst, connec_widget)
            self.dependants.append(connec_widget)
    
    def __update_program(self, table):
        for (name, prog) in table.items():
            #if a prog is not in the connection dict, create it
            if not name in self.connections.keys():
                self.__create_connection(name, prog)
            #if it is present but has changed, remove/create
            elif not self.connections[name][:2] == (self.emulica_canvas.widgets[prog.transform['source']], self.holder):
                self.connections[name][2].remove()
                self.__create_connection(name, prog)
        #if some connection are not used, remove
        for (name, (src, dst, widget)) in self.connections.items():
            if not name in table.keys():
                widget.remove() 
    
    def __on_property_change(self, prop, module):
        if prop == 'holder':
            if module[prop] in self.emulica_canvas.widgets.keys():
                self.__set_holder(self.emulica_canvas.widgets[module[prop]])
                self.__update_program(module['program_table'])
            else:
                self.__set_holder(None)
        if prop == 'program_table' and not module[prop] == None:
             self.__update_program(module[prop])
    
    def holder_coord(self):
        """Return the center of the module, where the holder should be"""
        return self.get_canvas().convert_from_item_space(self.__rect, 
                                                         self.__rect.props.x + 30,
                                                         self.__rect.props.y + 10)
    
    def animate(self, state):
        def change_widget(state):
            if state == 'idle':
                self.__light.props.fill_color = COLOR_IDLE
            elif state == 'setup':
                self.__light.props.fill_color = COLOR_SETUP
            elif state == 'failed':
                self.__light.props.fill_color = COLOR_FAILED
            else:
                self.__light.props.fill_color = COLOR_BUSY
            self.__text.props.text = str(state)
        if self.get_canvas().animate:
            GLib.idle_add(change_widget, state)


class Disassemble(ModuleWidget):
    def __init__(self, canvas, parent, interactive = True):
        ModuleWidget.__init__(self, canvas, parent, interactive)
        self.holder = None
        self.connections = dict()
        self.__rect = Goo.CanvasRect(parent = self,
                       height = 60,
                       width = 60,
                       fill_color = "SlateBlue1",
                       line_width = 1,
                       stroke_color = "dark blue")
        Goo.CanvasPolyline(parent = self,
                           points = CanvasPoints([(25, 40), (40, 40), (55, 25)]),
                           line_width = 4,
                           arrow_length = 2.5,
                           arrow_tip_length = 2.5,
                           arrow_width = 2.5,
                           end_arrow = True,
                           start_arrow = False,
                           stroke_color = COLOR_DECORATION)
        Goo.CanvasPolyline(parent = self,
                           points = CanvasPoints([(40, 40), (55, 55)]),
                           line_width = 4,
                           arrow_length = 2.5,
                           arrow_tip_length = 2.5,
                           arrow_width = 2.5,
                           end_arrow = True,
                           start_arrow = False,
                           stroke_color = COLOR_DECORATION)
        self.__light = Goo.CanvasEllipse(parent = self,
                                         center_x = 15,
                                         center_y = 15,
                                         radius_x = 5,
                                         radius_y = 5,
                                         fill_color = COLOR_IDLE,
                                         line_width = 1,
                                         stroke_color = "black")
        self.__text = Goo.CanvasText(parent = self,
                                     x = 3,
                                     y = 53,
                                     anchor = Goo.CanvasAnchorType.W,
                                     font = "sans 6",
                                     text = "")
        self.widget_bounds = (0, 0, 60, 60)

    def set_emulation_module(self, mod):
        self.module = mod
        for (name, prog) in mod['program_table'].items():
            self.__create_connection(name, prog)
        if mod['holder'] in self.emulica_canvas.widgets.keys():
            self.__set_holder(self.emulica_canvas.widgets[mod['holder']])
        else:
            self.__set_holder(None)
        mod.connect("state-changed", self.animate)
        mod.connect("property-changed", self.__on_property_change)
    
    def __set_holder(self, new_holder):
        if not self.holder == new_holder:
            if not self.holder == None:
                self.holder.make_normal_holder(self)
            self.holder = new_holder
            if not new_holder == None:
                new_holder.make_shape_holder(self)
                
    def __create_connection(self, name, prog):
        if 'destination' in prog.transform.keys() and not self.holder == None:
            dst = self.emulica_canvas.widgets[prog.transform['destination']]
            src = self.holder
            connec_widget = Connection(self.emulica_canvas, src, dst, weak = True, color = 'purple')
            self.connections[name] = (src, dst, connec_widget)
            self.dependants.append(connec_widget)
    
    def __update_program(self, table):
        for (name, prog) in table.items():
            #if a prog is not in the connection dict, create it
            if not name in self.connections.keys():
                self.__create_connection(name, prog)
            #if it is present but has changed, remove/create
            elif not self.connections[name][:2] == (self.emulica_canvas.widgets[prog.transform['destination']], self.holder):
                self.connections[name][2].remove()
                self.__create_connection(name, prog)
        #if some connection are not used, remove
        for (name, (src, dst, widget)) in self.connections.items():
            if not name in table.keys():
                widget.remove() 
    
    def __on_property_change(self, prop, module):
        if prop == 'holder':
            if module[prop] in self.emulica_canvas.widgets.keys():
                self.__set_holder(self.emulica_canvas.widgets[module[prop]])
                self.__update_program(module['program_table'])
            else:
                self.__set_holder(None)
        if prop == 'program_table' and not module[prop] == None:
             self.__update_program(module[prop])
    
    def holder_coord(self):
        """Return the center of the module, where the holder should be"""
        return self.get_canvas().convert_from_item_space(self.__rect, 
                                                         self.__rect.props.x + 30,
                                                         self.__rect.props.y + 10)
    
    def animate(self, state):
        def change_widget(state):
            if state == 'idle':
                self.__light.props.fill_color = COLOR_IDLE
            elif state == 'setup':
                self.__light.props.fill_color = COLOR_SETUP
            elif state == 'failed':
                self.__light.props.fill_color = COLOR_FAILED
            else:
                self.__light.props.fill_color = COLOR_BUSY
            self.__text.props.text = str(state)
        if self.get_canvas().animate:
            GLib.idle_add(change_widget, state)

class Failure(ModuleWidget):
    def __init__(self, canvas, parent, interactive = True):
        ModuleWidget.__init__(self, canvas, parent, interactive)
        self.__rect = Goo.CanvasRect(parent = self,
                       height = 30,
                       width = 30,
                       fill_color = "red",
                       line_width = 1,
                       stroke_color = "dark red")
        self.widget_bounds = (0, 0, 30, 30)

    def set_emulation_module(self, mod):
        self.module = mod

        
views = {'Holder': Holder,
         'CreateAct': Create,
         'DisposeAct': Dispose,
         'PushObserver': PushObserver,
         'PullObserver': PullObserver,
         'SpaceAct': Space,
         'ShapeAct': Shape,
         'AssembleAct': Assemble,
         'DisassembleAct': Disassemble,
         'Failure': Failure,
         'Model': Model}


    

    
