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

"""Initialization libs of the GIS workbench."""

import os
path   = os.path.dirname(__file__)
icons_path = os.path.join(path, 'GIS/resources/icons')
ui_path = os.path.join(path, 'GIS/resources/ui')

class CommandGroup:
    def __init__(self, cmdlist, menu, Type=None, tooltip=None):
        self.cmdlist = cmdlist
        self.menu = menu
        self.Type = Type
        if tooltip is None:
            self.tooltip = menu
        else:
            self.tooltip = tooltip

    def GetCommands(self):
        return tuple(self.cmdlist)

    def GetResources(self):
        return {'MenuText': self.menu, 'ToolTip': self.tooltip}

    def IsActive(self):
        """
        Define tool button activation situation
        """
        return True