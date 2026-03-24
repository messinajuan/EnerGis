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
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QListWidgetItem
#from PyQt6.QtWidgets import QMessageBox
from PyQt6 import uic
    
DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_seleccion.ui'))

class frmSeleccion(DialogType, DialogBase):

    def __init__(self, mapCanvas):
        super().__init__()
        self.setupUi(self)

        self.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowTitleHint | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowCloseButtonHint)

        self.setFixedSize(self.size())
        self.mapCanvas = mapCanvas

        self.seleccion_n = []
        self.seleccion_l = []

        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                for ftr in lyr.selectedFeatures():
                    b_existe=False
                    for i in range (0, len(self.seleccion_n)):
                        if self.seleccion_n[i]==ftr.id():
                            b_existe=True
                    if b_existe==False and ftr.id()!=0:
                        self.seleccion_n.append(ftr.id())
            if lyr.name()[:6] == 'Lineas':
                for ftr in lyr.selectedFeatures():
                    b_existe=False
                    for i in range (0, len(self.seleccion_l)):
                        if self.seleccion_l[i]==ftr.id():
                            b_existe=True
                    if b_existe==False and ftr.id()!=0:
                        self.seleccion_l.append(ftr.id())

        for m in range (0, len(self.seleccion_n)):
            self.liwNodos.addItem(QListWidgetItem(str(self.seleccion_n[m])))
        for m in range (0, len(self.seleccion_l)):
            self.liwLineas.addItem(QListWidgetItem(str(self.seleccion_l[m])))

        self.liwNodos.itemClicked.connect(self.elijo_nodo)
        self.liwLineas.itemClicked.connect(self.elijo_linea)

    def elijo_nodo(self):
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                sel = lyr.getFeatures()
                id = int(self.liwNodos.selectedItems()[0].text())
                for ftr in sel:
                    if ftr.id()==id:
                        geom = ftr.geometry()
                        #box = geom.boundingBox()
                        box = geom.buffer(25,1).boundingBox()
                        self.mapCanvas.setExtent(box)
                        self.mapCanvas.refresh()

    def elijo_linea(self):
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:6] == 'Lineas':
                sel = lyr.getFeatures()
                id = int(self.liwLineas.selectedItems()[0].text())
                for ftr in sel:
                    if ftr.id()==id:
                        geom = ftr.geometry()
                        box = geom.boundingBox()
                        self.mapCanvas.setExtent(box)
                        self.mapCanvas.refresh()
