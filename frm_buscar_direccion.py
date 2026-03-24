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
from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtGui import QIntValidator
#from PyQt6.QtWidgets import QMessageBox
from qgis.core import QgsGeometry
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_buscar_direccion.ui'))

class frmBuscarDireccion(DialogType, DialogBase):

    def __init__(self, mapCanvas, conn):
        super().__init__()
        self.setupUi(self)

        self.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(self.size())
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowTitleHint | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowCloseButtonHint)

        self.mapCanvas = mapCanvas
        self.conn = conn
        
        vint = QIntValidator()
        self.txtNumero.setValidator(vint)

        basepath = os.path.dirname(os.path.realpath(__file__))
        img_buscar = os.path.join(basepath,"icons", 'img_buscar.png')
        self.cmdBuscar.setIcon(QtGui.QIcon(img_buscar))

        cnn = conn
        cursor = cnn.cursor()
        cursor.execute("SELECT DISTINCT Calles.calle, Calles.descripcion FROM Calles INNER JOIN Ejes ON Calles.calle = Ejes.Calle")
        #convierto el cursor en array
        self.arrCalles = tuple(cursor)
        cursor.close()
        for i in range (0, len(self.arrCalles)):
            self.cmbCalle.addItem(self.arrCalles[i][1])
            self.cmbInterseccion.addItem(self.arrCalles[i][1])

        self.cmbInterseccion.setCurrentText('')
        self.cmdBuscar.clicked.connect(self.buscar)
        self.tblResultado.itemClicked.connect(self.elijo_item)
        
    def buscar(self):
        self.tblResultado.setRowCount(0)
        id_calle=0
        id_interseccion=0

        if self.txtNumero.text()!='':
            for i in range (0, len(self.arrCalles)):
                if self.arrCalles[i][1]==self.cmbCalle.currentText():
                    id_calle = self.arrCalles[i][0]

            cnn = self.conn
            cursor = cnn.cursor()
            cursor.execute("SELECT ISNULL(Ciudades.Descripcion, '<Desc>') AS Localidad, Calles.descripcion AS Calle, Ejes.IzqDe, Ejes.obj.STEnvelope().ToString() FROM Ejes INNER JOIN Calles ON Ejes.Calle = Calles.calle LEFT OUTER JOIN Ciudades ON Ejes.Ciudad = Ciudades.Ciudad WHERE Ejes.Calle=" + str(id_calle) + " AND IzqDe<= " + self.txtNumero.text() + " AND IzqA>" + self.txtNumero.text())
            #convierto el cursor en array
            encontrados = tuple(cursor)
            encabezado = [column[0] for column in cursor.description]
            cursor.close()

            if len(encontrados) > 0:
                self.tblResultado.setRowCount(len(encontrados))
                self.tblResultado.setColumnCount(len(encontrados[0]))
            for i in range (0, len(encontrados)):
                for j in range (len(encontrados[0])):
                    item = QTableWidgetItem(str(encontrados[i][j]))
                    self.tblResultado.setItem(i,j,item)

            self.tblResultado.setHorizontalHeaderLabels(encabezado)
            self.tblResultado.setColumnWidth(self.tblResultado.columnCount() - 1, 0)

        if self.cmbInterseccion.currentText()!='':
            filas_anteriores=self.tblResultado.rowCount()

            for i in range (0, len(self.arrCalles)):
                if self.arrCalles[i][1]==self.cmbInterseccion.currentText():
                    id_interseccion = self.arrCalles[i][0]

            cnn = self.conn
            cursor = cnn.cursor()
            cursor.execute("SELECT Ciudades.Descripcion AS Localidad, Calles.descripcion AS Calle, A.IzqDe AS Numero, obj.STEnvelope().ToString() FROM (SELECT Geoname AS geoname2, Calle AS calle2, IzqDe AS IzqDe2, obj AS obj2 FROM Ejes AS E WHERE Calle = " + str(id_calle) + ") AS B INNER JOIN Calles AS Calles_1 ON B.calle2 = Calles_1.calle CROSS JOIN Calles INNER JOIN (SELECT Geoname, Calle, IzqDe, obj FROM Ejes WHERE Calle = " + str(id_interseccion) + ") AS A ON Calles.calle = A.Calle INNER JOIN Ciudades ON Calles.ciudad = Ciudades.Ciudad WHERE (A.obj.STDistance(B.obj2) < 100) ORDER BY A.obj.STDistance(B.obj2)")
            encontrados = tuple(cursor)
            cursor.close()

            if len(encontrados) > 0:
                self.tblResultado.setRowCount(len(encontrados)+filas_anteriores)

            for i in range (0, len(encontrados)):
                for j in range (len(encontrados[0])):
                    item = QTableWidgetItem(str(encontrados[i][j]))
                    self.tblResultado.setItem(i+filas_anteriores,j,item)

            self.tblResultado.setHorizontalHeaderLabels(encabezado)
            self.tblResultado.setColumnWidth(self.tblResultado.columnCount() - 1, 0)

    def elijo_item(self):
        geom = QgsGeometry.fromWkt(self.tblResultado.selectedItems()[3].text())
        box = geom.buffer(25,1).boundingBox()
        self.mapCanvas.setExtent(box)
        self.mapCanvas.refresh()
