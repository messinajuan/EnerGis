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
from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtWidgets import QMessageBox
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_elegir_uucc.ui'))

class frmElegirUUCC(DialogType, DialogBase):

    def __init__(self, conn, tensiones, where, uucc):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.conn = conn
        self.tensiones = tensiones
        self.where = where
        self.uucc = uucc
        self.inicio()

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key.Key_Escape:
            self.uucc = ""
            self.close()
        
    def inicio(self):
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT Familia, Tipo_Instalacion, Codigo, Descripcion FROM UUCC WHERE Nivel_Tension IN (" + str(self.tensiones) + ") AND " + self.where)
        #convierto el cursor en array
        recordset = tuple(cursor)
        cursor.close()

        self.tblUUCC.setRowCount(len(recordset))
        self.tblUUCC.setColumnCount(4)
        self.tblUUCC.setHorizontalHeaderLabels(["Familia", "Tipo_Instalación", "Código", "Descripción"])
        
        self.tblUUCC.setColumnWidth(0, 80)
        self.tblUUCC.setColumnWidth(1, 100)
        self.tblUUCC.setColumnWidth(2, 160)
        self.tblUUCC.setColumnWidth(3, 500)

        for i in range (0, len(recordset)):
            self.tblUUCC.setItem(i, 0, QTableWidgetItem(recordset[i][0]))
            self.tblUUCC.setItem(i, 1, QTableWidgetItem(recordset[i][1]))
            self.tblUUCC.setItem(i, 2, QTableWidgetItem(recordset[i][2]))
            if recordset[i][2]==self.uucc:
                self.tblUUCC.selectRow(i)
            self.tblUUCC.setItem(i, 3, QTableWidgetItem(recordset[i][3]))

        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)

    def aceptar(self):
        if self.tblUUCC.currentRow()>-1:
            self.uucc = self.tblUUCC.item(self.tblUUCC.currentRow(),2).text()
        self.close()

    def salir(self):
        self.uucc = ""
        self.close()
