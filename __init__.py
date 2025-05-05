#-----------------------------------------------------------
# Copyright (C) 2015 Martin Dobias
#-----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#---------------------------------------------------------------------

from PyQt5.QtWidgets import QAction, QMessageBox

from .save_load import load_layout, save_layout


def classFactory(iface):
    return PersistWindowLayout(iface)


class PersistWindowLayout:
    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        self.save_layout = QAction('Save Layout', self.iface.mainWindow())
        self.save_layout.triggered.connect(save_layout)
        self.iface.addToolBarIcon(self.save_layout)

        self.load_layout = QAction('Load Layout', self.iface.mainWindow())
        self.load_layout.triggered.connect(load_layout)
        self.iface.addToolBarIcon(self.load_layout)

    def unload(self):
        self.iface.removeToolBarIcon(self.save_layout)
        self.iface.removeToolBarIcon(self.load_layout)
        del self.load_layout
        del self.save_layout 

