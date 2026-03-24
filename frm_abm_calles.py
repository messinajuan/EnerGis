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

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_abm_calles.ui'))

class frmAbmCalles(DialogType, DialogBase):

    def __init__(self, conn):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.conn = conn
        self.cmbCiudad.addItem("<Indistinto>")
        self.arrCiudades = []
        cursor = self.conn.cursor()
        cursor.execute("SELECT RTRIM(ciudad), Cod_Postal, Descripcion, Partido FROM Ciudades ORDER BY descripcion")
        #convierto el cursor en array
        rows = tuple(cursor)
        cursor.close()
        for row in rows:
            self.arrCiudades.append(row)
            self.cmbCiudad.addItem(str(row[2]))
        self.arrCalles = []
        self.id_ciudad = '0'
        self.elijo_ciudad()
        self.cmdNueva.clicked.connect(self.agregar)
        self.cmdBorrar.clicked.connect(self.borrar)
        self.cmdGuardar.clicked.connect(self.guardar)
        self.cmbCiudad.activated.connect(self.elijo_ciudad)
        self.liwCalles.currentRowChanged.connect(self.elijo_calle)
        self.cmdSalir.clicked.connect(self.salir)

    def cargar_calles(self):
        self.liwCalles.clear()
        self.arrCalles = []
        cursor = self.conn.cursor()
        cursor.execute("SELECT Calle, Descripcion, Ciudad FROM Calles WHERE ciudad='" + self.id_ciudad + "' ORDER BY descripcion")
        #convierto el cursor en array
        rows = tuple(cursor)
        cursor.close()
        for row in rows:
            self.arrCalles.append(row)
            self.liwCalles.addItem(str(row[1]))

    def elijo_ciudad(self):
        self.id_ciudad = '0'
        try:
            for i in range (0, len(self.arrCiudades)):
                if self.cmbCiudad.currentText() == str(self.arrCiudades[i][2]):
                    self.id_ciudad = self.arrCiudades[i][0]
            self.cargar_calles()
        except:
            pass

    def elijo_calle(self):
        if self.liwCalles.currentItem()==None:
            return
        try:
            for i in range (0, len(self.arrCalles)):
                if self.liwCalles.currentItem().text()==self.arrCalles[i][1]:
                    self.id_calle=self.arrCalles[i][0]
                    self.txtNombre.setText(self.arrCalles[i][1])
                    for j in range (0, self.cmbCiudad.count()):
                        if self.cmbCiudad.itemText(j) == str(self.arrCalles[i][2]):
                            self.cmbCiudad.setCurrentIndex(j)
        except:
            pass

    def agregar(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(calle) FROM Calles")
        rows = cursor.fetchall()
        cursor.close()
        self.id_calle = rows[0][0] + 1
        reply = QMessageBox.question(None, 'EnerGis 6', 'Desea insertar una calle ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO Calles (calle, descripcion, ciudad) VALUES (" + str(self.id_calle) + ",'<calle>','" + self.id_ciudad + "')")
            self.conn.commit()
        except:
            self.conn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo agregar la calle !")
            return
        self.cargar_calles()

    def guardar(self):
        reply = QMessageBox.question(None, 'EnerGis 6', 'Desea guardar los cambios ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE Calles SET descripcion='" + self.txtNombre.text() + "', Ciudad='" + self.id_ciudad + "' WHERE Calle=" + str(self.id_calle))
            self.conn.commit()
            QMessageBox.information(None, 'EnerGis 6', "ℹ️ Grabado !")
        except:
            self.conn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo guardar la calle !")
            return
        self.cargar_calles()

    def borrar(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Ejes WHERE calle=" + str(self.id_calle))
        rows = cursor.fetchall()
        cursor.close()
        if rows[0][0]>0:
            QMessageBox.warning(None, 'EnerGis 6', "❌ No se puede borrar la calle porque está asociada a " + str(rows[0][0]) + " ejes de calle !")
            return
        reply = QMessageBox.question(None, 'EnerGis 6', 'Desea borrar la calle ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM calles WHERE calle=" + str(self.id_calle))
            self.conn.commit()
        except:
            self.conn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo borrar la calle !")
            return
        self.cargar_calles()

    def salir(self):
        self.close()
