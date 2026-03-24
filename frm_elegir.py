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
from PyQt6.QtWidgets import QTableWidgetItem, QApplication
from PyQt6.QtWidgets import QMessageBox
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_elegir.ui'))

class frmElegir(DialogType, DialogBase):

    def __init__(self, mapCanvas, conn, sql):
        super().__init__()
        self.setupUi(self)

        # Obtener la resolución de la pantalla
        screen_resolution = QApplication.primaryScreen().availableGeometry()
        screen_width = screen_resolution.width()
        screen_height = screen_resolution.height()
        # Establecer la posición a la derecha de la pantalla
        widget_width = self.width()
        widget_height = self.height()
        x_position = screen_width - widget_width
        y_position = (screen_height - widget_height) // 2  # Centramos verticalmente
        self.move(x_position, y_position)

        self.mapCanvas = mapCanvas
        self.conn = conn
        self.sql = sql
        self.seleccionado = ""
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute(self.sql)
        #convierto el cursor en array
        recordset = tuple(cursor)
        encabezado = [column[0] for column in cursor.description]
        cursor.close()
        self.tblListado.setRowCount(len(recordset))

        if len(recordset)==0:
            QMessageBox.warning(None, 'EnerGis 6', '❌ No hay registros para elegir !')
            return

        self.tblListado.setColumnCount(len(recordset[0]))
        self.tblListado.setHorizontalHeaderLabels(encabezado)
        self.tblListado.setColumnWidth(0, 60)
        self.tblListado.setColumnWidth(1, 150)
        
        for i in range (0, len(recordset)):
            for j in range (0, len(recordset[0])):
                self.tblListado.setItem(i, j, QTableWidgetItem(str(recordset[i][j])))
        
        self.tblListado.itemClicked.connect(self.elijo_elemento)
        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key.Key_Escape:
            self.seleccionado = ""
            self.close()

    def elijo_elemento(self):
        self.seleccionado = self.tblListado.item(self.tblListado.currentRow(),0).text()
        if self.tblListado.horizontalHeaderItem(0).text()!='geoname':
            return
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                sel = lyr.getFeatures()
                for ftr in sel:
                    if ftr.id()==int(self.seleccionado):
                        geom = ftr.geometry()
                        #box = geom.boundingBox()
                        box = geom.buffer(25,1).boundingBox()
                        self.mapCanvas.setExtent(box)
                        self.mapCanvas.refresh()

    def aceptar(self):
        self.seleccionado = self.tblListado.item(self.tblListado.currentRow(),0).text()
        self.close()

    def salir(self):
        self.seleccionado = ""
        self.close()
