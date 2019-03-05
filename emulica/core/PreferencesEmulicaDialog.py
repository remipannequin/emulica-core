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

# This is your preferences dialog.
#
# Define your preferences in
# data/glib-2.0/schemas/net.launchpad.emulica.gschema.xml
# See http://developer.gnome.org/gio/stable/GSettings.html for more info.

from gi.repository import Gio # pylint: disable=E0611

from locale import gettext as _

import logging
logger = logging.getLogger('emulica')

from emulica_lib.PreferencesDialog import PreferencesDialog

class PreferencesEmulicaDialog(PreferencesDialog):
    __gtype_name__ = "PreferencesEmulicaDialog"

    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the preferences dialog"""
        super(PreferencesEmulicaDialog, self).finish_initializing(builder)

        # Bind each preference widget to gsettings
        settings = Gio.Settings("net.launchpad.emulica")
        widget = self.builder.get_object('show_line_number_edit')
        settings.bind("show-line-number", widget, "active", Gio.SettingsBindFlags.DEFAULT)
        
        widget = self.builder.get_object('auto_indent_edit')
        settings.bind("auto-indent", widget, "active", Gio.SettingsBindFlags.DEFAULT)
        
        widget = self.builder.get_object('insert_space_edit')
        settings.bind("insert-spaces-instead-of-tabs", widget, "active", Gio.SettingsBindFlags.DEFAULT)
        
        widget = self.builder.get_object('show_line_marks_edit')
        settings.bind("show-line-marks", widget, "active", Gio.SettingsBindFlags.DEFAULT)
        
        widget = self.builder.get_object('indent_width_edit')
        settings.bind("indent-width", widget, "value", Gio.SettingsBindFlags.DEFAULT)

