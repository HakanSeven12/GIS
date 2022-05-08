# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2022 Hakan Seven <hakanseven12@gmail.com>               *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

"""Initialization of the GIS workbench (GUI interface)."""

import FreeCADGui


class GISWorkbench(FreeCADGui.Workbench):
    """
    Class which gets initiated at startup of the GUI.
    """
    from GIS_libs import icons_path

    MenuText = 'GIS'
    ToolTip = 'GIS Tools Workbench'
    Icon = icons_path + '/workbench.svg'

    def __init__(self):
        #dictionary key = name of command / command group.
        #'gui' - locations in gui where commands are accessed, (summed bitflags)
        #'cmd' - list of commands to display
        #'group' - Tuple containing the subgroup description and type.  None/undefined if no group

        self.menu = 1
        self.toolbar = 2
        self.context = 4
        self.group = 8

        self.command_ui = {
            'Geodata Tools': {
                'gui': self.menu + self.toolbar,
                'cmd': []},

            'Web Service Tools': {
                'gui': self.menu + self.toolbar,
                'cmd': []},

            'Other Tools': {
                'gui': self.menu + self.toolbar,
                'cmd': []},
        }

    def GetClassName(self):
        """
        Return the workbench classname.
        """
        return 'Gui::PythonWorkbench'

    def Initialize(self):
        """
        Called when the workbench is first activated.
        """
        from GIS_libs import CommandGroup
        from GIS import gui

        for palette, tool in self.command_ui.items():
            if tool['gui'] & self.toolbar:
                self.appendToolbar(palette, tool['cmd'])

            if tool['gui'] & self.menu:
                self.appendMenu(palette, tool['cmd'])

            if tool['gui'] & self.group:
                FreeCADGui.addCommand(palette, CommandGroup(
                    tool['cmd'], tool['tooltip'], tool['type']))

    def Activated(self):
        """
        Called when switching to this workbench
        """
        pass

    def Deactivated(self):
        """
        Called when switiching away from this workbench
        """
        pass

    def ContextMenu(self, recipient):
        """
        Right-click menu options
        """
        # "recipient" will be either "view" or "tree"

        for _k, _v in self.fn.items():
            if _v['gui'] & self.context:
                self.appendContextMenu(_k, _v['cmds'])

FreeCADGui.addWorkbench(GISWorkbench())
