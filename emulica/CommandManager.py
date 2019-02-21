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


import gettext
from gettext import gettext as _
gettext.textdomain('emulica')


class CommandManager:
    """This class implements the pattern Command to access to create destroy and
    modify the emulation model and canvas.
    
    The command interface :
        __init__() -- create the Command object and execute the command
        undo() -- undo the command
        redo() -- redo the command
    
    Attributes:
        undo_stack -- a stack of undoable actions
        redo_stack -- a stack of redoable actions
        
    """
    def __init__(self):
        """Create a new instance of the Emulation command manager"""
        self.undo_stack = []
        self.redo_stack = []
        def fake_handler():
            pass
        self.handler = fake_handler
        
    def undo(self):
        """Undo last command."""
        cmd = self.undo_stack.pop()
        cmd.undo()
        self.redo_stack.append(cmd)
        self.handler()
        
    def redo(self):
        """Redo last redone command."""
        cmd = self.redo_stack.pop()
        cmd.redo()
        self.undo_stack.append(cmd)
        self.handler()
    
    def add_cmd(self, cmd):
        self.undo_stack.append(cmd)
        del self.redo_stack[0:len(self.redo_stack)]
        self.handler()
    
    def can_undo(self):
        return len(self.undo_stack) > 0
        
    def can_redo(self):
        return len(self.redo_stack) > 0
    
    def create_module(self, name, moduletype, model):
        """Create a new module and add it to the canvas."""
        #init : create module (it is automatically added to the model)...
        #undo : remove module from  model
        #redo : put module back in model
        
        class CreateCmd:
            def __init__(self, name, moduletype, model):
                self.module = moduletype(model, name)
                self.model = model
                
            def undo(self):
                self.model.unregister_emulation_module(self.module.fullname())
                
            def redo(self):
                model.register_emulation_module(self.module)
        
        cmd = CreateCmd(name, moduletype, model)
        self.add_cmd(cmd)
        
        
    def delete_module(self, module, model):
        """Delete a module from the model and canvas"""
        #init : remove module from canvas and model
        #undo : put module back in model and canvas
        #redo : same as do
        class DeleteCmd:
            def __init__(self, module, model):
                self.module = module
                self.model = model
                self.model.unregister_emulation_module(self.module.fullname())
                
            def undo(self):
                self.model.register_emulation_module(self.module)
                
            def redo(self):
                self.model.unregister_emulation_module(self.module.fullname())
            
        cmd = DeleteCmd(module, model)
        self.add_cmd(cmd)
        
    def rename_module(self, module, new_name):
        """Change module name"""
        class RenameCmd:
            def __init__(self, module, new_name):
                self.module = module
                self.old_name = module.name
                self.name = new_name
                self.module.rename(new_name)
            
            def undo(self):
                self.module.rename(self.old_name)
                
            def redo(self):
                self.module.rename(self.name)
        
        cmd = RenameCmd(module, new_name)
        self.add_cmd(cmd)
        
    def change_prop(self, registry, prop_name, prop_value):
        """Modify a module property"""
        #do : get property old_value (if it exists !), set new value
        #undo : set prop to old_value
        #redo : set prop to new_value
        #clear : forget old_value
        class ChangePropCmd:
            def __init__(self, registry, prop_name, value):
                self.registry = registry
                self.name = prop_name
                if self.name in registry.keys():
                    self.old_value = registry[self.name]
                else:
                    self.old_value = None
                self.value = value
                self.registry[self.name] = self.value
            
            def undo(self):
                self.registry[self.name] = self.old_value
                
            def redo(self):
                self.registry[self.name] = self.value
        
        cmd = ChangePropCmd(registry, prop_name, prop_value)
        self.add_cmd(cmd)
    
    def change_prop_name(self, registry, old_name, new_name):
        """Modify a module property"""
        #do : delete old prop, add new
        #undo : delete new add old
        #redo : same as do
        class ChangePropNameCmd:
            def __init__(self, registry, old_name, new_name):
                self.registry = registry
                self.old_name = old_name
                self.new_name = new_name
                value = self.registry[self.old_name]
                del self.registry[self.old_name]
                self.registry[self.new_name] = value
            
            def undo(self):
                value = self.registry[self.new_name]
                del self.registry[self.new_name]
                self.registry[self.old_name] = value
               
            def redo(self):
                value = self.registry[self.old_name]
                del self.registry[self.old_name]
                self.registry[self.new_name] = value
        
        cmd = ChangePropNameCmd(registry, old_name, new_name)
        self.add_cmd(cmd)
    
    
    def del_prop(self, registry, prop_name):
        """Delete a property from a Registry"""
        #do : get property old_value, delete
        #undo : add prop with old_value
        #redo : delete
        class DelPropCmd:
            def __init__(self, registry, prop_name):
                self.registry = registry
                self.name = prop_name
                self.old_value = registry[self.name]
                del self.registry[self.name]
            
            def undo(self):
                self.registry[self.name] = self.old_value
                
            def redo(self):
                del self.registry[self.name]
        
        cmd = DelPropCmd(registry, prop_name)
        self.add_cmd(cmd)
        
    def add_prop(self, registry, prop_name, prop_value):
        """Modify a module property"""
        #do : add
        #undo : delete
        #redo : add
        class AddPropCmd:
            def __init__(self, registry, prop_name, value):
                self.registry = registry
                self.name = prop_name
                self.value = value
                self.registry[self.name] = self.value
            
            def undo(self):
                del self.registry[self.name]
                
            def redo(self):
                self.registry[self.name] = self.value
        
        cmd = AddPropCmd(registry, prop_name, prop_value)
        self.add_cmd(cmd)
    
    def add_prog(self, p_table, name, delay, transform = None):
        """Add a new program in p_table"""
        #do : add prog in prog_table
        #undo : del prog from p_tbale
        #redo : add prog in p_table
        class AddProgCmd:
            def __init__(self, p_table, name, delay, transform):
                self.p_table = p_table
                self.name = name
                self.p_table.add_program(self.name, delay, transform)
                if name in self.p_table:
                    self.prog = self.p_table[name]
                else:
                    self.prog = None
            
            def undo(self):
                del self.p_table[self.name]
                
            def redo(self):
                if self.prog is None:
                    del self.p_table[self.name]
                else:
                    self.p_table[self.name] = self.prog
        
        cmd = AddProgCmd(p_table, name, delay, transform)
        self.add_cmd(cmd)
    
    def del_prog(self, p_table, name):
        """Remove program from p_table"""
        #do : del prog in prog_table, remember value
        #undo : add prog from p_tbale
        #redo : del prog in p_table
        class DelProgCmd:
            def __init__(self, p_table, name):
                self.p_table = p_table
                self.name = name
                self.prog = self.p_table[self.name]
                del self.p_table[self.name]
            
            def undo(self):
                self.p_table[self.name] = self.prog
                
            def redo(self):
                del self.p_table[self.name]
        
        cmd = DelProgCmd(p_table, name)
        self.add_cmd(cmd)
        
    def change_prog_time(self, prog, time):
        """Change the time law of the prog"""
        #do : change time, remember old val
        #undo : set old val
        #redo : set val
        class ChangeProgTimeCmd:
            def __init__(self, prog, time):
                self.prog = prog
                self.time = time
                self.old_time = prog.time_law
                self.prog.time_law = self.time
            
            def undo(self):
                self.prog.time_law = self.old_time
                
            def redo(self):
                self.prog.time_law = self.time
        
        cmd = ChangeProgTimeCmd(prog, time)
        self.add_cmd(cmd)
    
    def change_prog_name(self, t_prog, old_name, new_name):
        """Change the name of a program"""
        #do : del old_name, add new_name
        #undo : del new_name, add old_name
        #redo : same as do
        class ChangeProgNameCmd:
            def __init__(self, t_prog, old_name, new_name):
                self.t_prog = t_prog
                self.old_name = old_name
                self.new_name = new_name
                prog = t_prog[old_name]
                del t_prog[old_name]
                t_prog[new_name] = prog
            
            def undo(self):
                prog = t_prog[new_name]
                del t_prog[new_name]
                t_prog[old_name] = prog
                
            def redo(self):
                prog = t_prog[old_name]
                del t_prog[old_name]
                t_prog[new_name] = prog
        
        cmd = ChangeProgNameCmd(t_prog, old_name, new_name)
        self.add_cmd(cmd)
    
    
    def add_setup(self, t_setup, initial, final, time):
        """Add the (initial, final, time) setup in t_setup"""
        #do : add
        #undo : delete
        #redo : same as do
        class AddSetupCmd:
            def __init__(self, t_setup, initial, final, time):
                self.t_setup = t_setup
                self.setup = (initial, final, time)
                self.t_setup.add(*(self.setup))
                
            def undo(self):
                self.t_setup.remove(self.setup[0], self.setup[1])
                
            def redo(self):
                self.t_setup.add(*(self.setup))
        
        cmd = AddSetupCmd(t_setup, initial, final, time)
        self.add_cmd(cmd)
        
    def del_setup(self, t_setup, initial, final):
        """Add the (initial, final, time) setup in t_setup"""
        #do : add
        #undo : delete
        #redo : same as do
        class DelSetupCmd:
            def __init__(self, t_setup, initial, final):
                self.t_setup = t_setup
                time = self.t_setup.get(initial, final)
                self.setup = (initial, final, time)
                self.t_setup.remove(self.setup[0], self.setup[1])
                
            def undo(self):
                self.t_setup.add(*(self.setup))
                
            def redo(self):
                self.t_setup.remove(self.setup[0], self.setup[1])
        
        cmd = DelSetupCmd(t_setup, initial, final)
        self.add_cmd(cmd)
        
    def change_setup(self, t_setup, initial, final, new_initial = None, new_final = None, new_time = None):
        """Change setup"""
        #do : call change with new values
        #undo : call change with old values
        #redo : same as do
        class ChangeSetupCmd:
            def __init__(self, t_setup, initial, final, new_initial = None, new_final = None, new_time = None):
                self.t_setup = t_setup
                time = self.t_setup.get(initial, final)
                self.old = [initial, final, time]
                self.new = [new_initial or initial, new_final or final, new_time or time]
                self.t_setup.modify(*(self.__create_args(self.old, self.new)))
                
            def undo(self):
                self.t_setup.modify(*(self.__create_args(self.new, self.old)))
                
            def redo(self):
                self.t_setup.modify(*(self.__create_args(self.old, self.new))) 
        
            def __create_args(self, old, new):
                return old[0:2]+new
                
        cmd = ChangeSetupCmd(t_setup, initial, final, new_initial, new_final, new_time)
        self.add_cmd(cmd)
    
        
    def modify_canvas_layout(self, layout, canvas):
        """Modify module position"""
        pass
