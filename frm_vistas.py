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
from PyQt6.QtWidgets import QMessageBox
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_vistas.ui'))

class frmVistas(DialogType, DialogBase):

    def __init__(self, tipo_usuario, mapCanvas, conn):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.tipo_usuario = tipo_usuario
        self.mapCanvas = mapCanvas
        self.conn = conn

        if self.tipo_usuario==4:
            self.cmdNueva.setEnabled(False)
            self.cmdEditar.setEnabled(False)
            self.cmdAceptar.setEnabled(False)

        self.lleno_lista()
        self.cmdGrabar.clicked.connect(self.grabar)
        self.cmdInicio.clicked.connect(self.inicio)
        self.cmdBorrar.clicked.connect(self.borrar)
        self.liwVistas.currentRowChanged.connect(self.elijo_vista)
        self.cmdSalir.clicked.connect(self.salir)
        pass

    def lleno_lista(self):
        self.liwVistas.clear()
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT * FROM Vistas")
        #convierto el cursor en array
        self.elementos_vistas = tuple(cursor)
        cursor.close()
        for i in range (0, len(self.elementos_vistas)):
            self.liwVistas.addItem(self.elementos_vistas[i][0])

    def grabar(self):
        nom_vista = InputBox("Ingrese el Nombre que desea darle a la vista actual", "Vistas Personalizadas")
        if nom_vista == "":
            return

        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("INSERT INTO Vistas (descripcion, CentroX, CentroY, Zoom) VALUES ()"

        self.liwVistas.addItem(self.elementos_vistas[i][0])

    def inicio(self):
        self.liwVistas.clear()
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT * FROM Vista")
        #convierto el cursor en array
        self.elementos_vista = tuple(cursor)
        cursor.close()

        rect = QgsRectangle(self.p1.x(), self.p1.y(), self.p2.x(), self.p2.y())
        ftrArea = QgsFeature()
        ftrArea.setGeometry(QgsGeometry.fromRect(rect))

        self.mapCanvas.setExtent(rect)
        self.mapCanvas.refresh()

    def borrar(self):
        If List1.List(List1.ListIndex) = "" Then Exit Sub
        If MsgBox("Desea Borrar la Vista " & List1.List(List1.ListIndex) & "?", vbQuestion + vbYesNo, "Vistas Personalizadas") = vbNo Then Exit Sub

        EjecutarSql "DELETE FROM Vistas WHERE descripcion='" & List1.List(List1.ListIndex) & "'"

        List1.RemoveItem List1.ListIndex

    def elijo_vista(self):

        Adodc1.ConnectionString = Str_Conexion
        Adodc1.CursorType = adOpenStatic
        Adodc1.LockType = adLockReadOnly
        Adodc1.CommandType = adCmdText

        Adodc1.RecordSource = "SELECT * FROM Vistas WHERE Descripcion = '" & List1.List(List1.ListIndex) & "';"
        Adodc1.Refresh

        Formulario.Map1(IdMapa).ZoomTo Adodc1.Recordset("Zoom"), Adodc1.Recordset("CentroX"), Adodc1.Recordset("CentroY")
        Formulario.Map1(IdMapa).Refresh
        Command1.Enabled = False


        rect = QgsRectangle(self.p1.x(), self.p1.y(), self.p2.x(), self.p2.y())
        ftrArea = QgsFeature()
        ftrArea.setGeometry(QgsGeometry.fromRect(rect))

        self.mapCanvas.setExtent(rect)
        self.mapCanvas.refresh()


    def salir(self):
        self.close()
