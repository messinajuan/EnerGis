# encoding: utf-8
#-----------------------------------------------------------
# Copyright (C) 2026 Juan Messina
#-----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#---------------------------------------------------------------------

import os
from PyQt6 import QtCore
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QMessageBox
from qgis.core import QgsProject
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_borrar.ui'))

class frmBorrar(DialogType, DialogBase):

    def __init__(self, capas):
        super().__init__()
        self.setupUi(self)
        #self.setFixedSize(self.size())
        self.capas = capas
        self.inicio()
        pass

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key.Key_Escape:
            self.seleccionado = ""
            self.close()
        
    def inicio(self):
        for capa in self.capas:
            item = QtWidgets.QListWidgetItem(capa.name())
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            if self.isVisible(capa)==True:
                item.setCheckState(QtCore.Qt.Checked)
            else:
                item.setCheckState(QtCore.Qt.Unchecked)
            self.liwCapas.addItem(item)
        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)
        pass

    def isVisible(self, lyr):
        lyr_tree_root = QgsProject.instance().layerTreeRoot()
        lyr_tree_lyr = lyr_tree_root.findLayer(lyr)
        return lyr_tree_lyr.isVisible()

    def aceptar(self):
        self.capas=[]
        reply = QMessageBox.question(None, 'EnerGis 6', 'Desea borrar los elementos seleccionados ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        for i in range (0, self.liwCapas.count()):
            if self.liwCapas.item(i).checkState()==QtCore.Qt.Checked:
                self.capas.append(self.liwCapas.item(i).text())
        self.close()
        pass

    def salir(self):
        self.capas=[]
        self.close()
        pass
