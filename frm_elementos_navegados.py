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
    
DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_elementos_navegados.ui'))

class frmElementosNavegados(DialogType, DialogBase):

    def __init__(self, mapCanvas, seleccion_n, seleccion_l):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowTitleHint | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowCloseButtonHint)
        #self.setFixedSize(self.size())
        self.mapCanvas = mapCanvas

        self.seleccion_n = seleccion_n
        self.seleccion_l = seleccion_l

        self.cmbTensionNodos.addItem('Todos')
        self.cmbTensionNodos.addItem('AT')
        self.cmbTensionNodos.addItem('MT')
        self.cmbTensionNodos.addItem('BT')
        self.cmbTensionLineas.addItem('Todas')
        self.cmbTensionLineas.addItem('AT')
        self.cmbTensionLineas.addItem('MT')
        self.cmbTensionLineas.addItem('BT')
        self.cmbElementosNodos.addItem('Todos')
        self.cmbElementosNodos.addItem('Transformadores')
        self.cmbElementosNodos.addItem('Seccionadores')
        self.cmbElementosNodos.addItem('Suministros')
        self.cmbFasesLineas.addItem('Todas')
        self.cmbFasesLineas.addItem('Trifásicas')
        self.cmbFasesLineas.addItem('Bifásicas')
        self.cmbFasesLineas.addItem('Monofásicas')

        self.cargar_lista_nodos()
        self.cargar_lista_lineas()

        self.liwNodos.itemClicked.connect(self.elijo_nodo)
        self.liwLineas.itemClicked.connect(self.elijo_linea)

        self.cmbTensionNodos.activated.connect(self.cargar_lista_nodos)
        self.cmbElementosNodos.activated.connect(self.cargar_lista_nodos)

        self.cmbTensionLineas.activated.connect(self.cargar_lista_lineas)
        self.cmbFasesLineas.activated.connect(self.cargar_lista_lineas)

        self.cmdSeleccionarNodos.clicked.connect(self.seleccionar_nodos)
        self.cmdSeleccionarLineas.clicked.connect(self.seleccionar_lineas)
        self.cmdSalir.clicked.connect(self.salir)

    def cargar_lista_nodos(self):
        elemento=0
        if self.cmbElementosNodos.currentText()=='Transformadores':
            elemento=4
        if self.cmbElementosNodos.currentText()=='Seccionadores':
            elemento=2
        if self.cmbElementosNodos.currentText()=='Suministros':
            elemento=6
        self.liwNodos.clear()
        for n in range (1, len(self.seleccion_n)):
            if self.cmbTensionNodos.currentText()=='Todos':
                if self.cmbElementosNodos.currentText()=='Todos':
                    self.liwNodos.addItem(QListWidgetItem(str(self.seleccion_n[n][0])))
                else:
                    if self.seleccion_n[n][2] == elemento:
                        self.liwNodos.addItem(QListWidgetItem(str(self.seleccion_n[n][0])))
            elif self.cmbTensionNodos.currentText()=='AT':
                if self.seleccion_n[n][1] >= 50000:
                    if self.cmbElementosNodos.currentText()=='Todos':
                        self.liwNodos.addItem(QListWidgetItem(str(self.seleccion_n[n][0])))
                    else:
                        if self.seleccion_n[n][2] == elemento:
                            self.liwNodos.addItem(QListWidgetItem(str(self.seleccion_n[n][0])))
            elif self.cmbTensionNodos.currentText()=='MT':
                if self.seleccion_n[n][1] >= 1000 and self.seleccion_n[n][1] < 50000:
                    if self.cmbElementosNodos.currentText()=='Todos':
                        self.liwNodos.addItem(QListWidgetItem(str(self.seleccion_n[n][0])))
                    else:
                        if self.seleccion_n[n][2] == elemento:
                            self.liwNodos.addItem(QListWidgetItem(str(self.seleccion_n[n][0])))
            elif self.cmbTensionNodos.currentText()=='BT':
                if self.seleccion_n[n][1] < 1000:
                    if self.cmbElementosNodos.currentText()=='Todos':
                        self.liwNodos.addItem(QListWidgetItem(str(self.seleccion_n[n][0])))
                    else:
                        if self.seleccion_n[n][2] == elemento:
                            self.liwNodos.addItem(QListWidgetItem(str(self.seleccion_n[n][0])))

    def cargar_lista_lineas(self):
        fases=0
        if self.cmbFasesLineas.currentText()=='Trifásicas':
            fases=3
        if self.cmbFasesLineas.currentText()=='Bifásicas':
            fases=2
        if self.cmbFasesLineas.currentText()=='Monofásicas':
            fases=1

        self.liwLineas.clear()
        for l in range (1, len(self.seleccion_l)):
            if self.cmbTensionLineas.currentText()=='Todas':
                if self.cmbFasesLineas.currentText()=='Todas':
                    self.liwLineas.addItem(QListWidgetItem(str(self.seleccion_l[l][0])))
                else:
                    if len(str(self.seleccion_l[l][2])) == fases:
                        self.liwLineas.addItem(QListWidgetItem(str(self.seleccion_l[l][0])))
            elif self.cmbTensionLineas.currentText()=='AT':
                if self.seleccion_l[l][1] >= 50000:
                    if self.cmbFasesLineas.currentText()=='Todas':
                        self.liwLineas.addItem(QListWidgetItem(str(self.seleccion_l[l][0])))
                    else:
                        if len(str(self.seleccion_l[l][2])) == fases:
                            self.liwLineas.addItem(QListWidgetItem(str(self.seleccion_l[l][0])))
            elif self.cmbTensionLineas.currentText()=='MT':
                if self.seleccion_l[l][1] >= 1000 and self.seleccion_l[l][1] < 50000:
                    if self.cmbFasesLineas.currentText()=='Todas':
                        self.liwLineas.addItem(QListWidgetItem(str(self.seleccion_l[l][0])))
                    else:
                        if len(str(self.seleccion_l[l][2])) == fases:
                            self.liwLineas.addItem(QListWidgetItem(str(self.seleccion_l[l][0])))
            elif self.cmbTensionLineas.currentText()=='BT':
                if self.seleccion_l[l][1] < 1000:
                    if self.cmbFasesLineas.currentText()=='Todas':
                        self.liwLineas.addItem(QListWidgetItem(str(self.seleccion_l[l][0])))
                    else:
                        if len(str(self.seleccion_l[l][2])) == fases:
                            self.liwLineas.addItem(QListWidgetItem(str(self.seleccion_l[l][0])))

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

    def seleccionar_nodos(self):
        seleccion_n=[]
        for i in range(self.liwNodos.count()):
            item = self.liwNodos.item(i)
            seleccion_n.append(int(item.text()))
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyr.select(seleccion_n)

    def seleccionar_lineas(self):
        seleccion_l=[]
        for i in range(self.liwLineas.count()):
            item = self.liwLineas.item(i)
            seleccion_l.append(int(item.text()))
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:6] == 'Lineas':
                lyr.select(seleccion_l)

    def salir(self):
        self.close()
