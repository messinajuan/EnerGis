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

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_abm_ciudades.ui'))

class frmAbmCiudades(DialogType, DialogBase):

    def __init__(self, conn):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.conn = conn
        self.arrCiudades = []
        self.cargar_ciudades()
        self.cmdNueva.clicked.connect(self.agregar)
        self.cmdBorrar.clicked.connect(self.borrar)
        self.cmdGuardar.clicked.connect(self.guardar)
        self.liwCiudades.currentRowChanged.connect(self.elijo_ciudad)
        self.cmdSalir.clicked.connect(self.salir)

    def cargar_ciudades(self):
        self.liwCiudades.clear()
        self.arrCiudades = []
        cursor = self.conn.cursor()
        cursor.execute("SELECT RTRIM(Ciudad), Cod_Postal, Descripcion, Partido FROM Ciudades")
        #convierto el cursor en array
        rows = tuple(cursor)
        cursor.close()
        for row in rows:
            self.arrCiudades.append(row)
            self.liwCiudades.addItem(str(row[2]))

    def elijo_ciudad(self):
        for i in range (0, len(self.arrCiudades)):
            if self.liwCiudades.currentItem().text()==self.arrCiudades[i][2]:
                self.id_ciudad=self.arrCiudades[i][0]
                self.txtNombre.setText(self.arrCiudades[i][2])
                self.txtCp.setText(self.arrCiudades[i][1])
                self.txtPartido.setText(self.arrCiudades[i][3])

    def agregar(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(ciudad) FROM Ciudades WHERE ISNUMERIC(Ciudad)>0")
        rows = cursor.fetchall()
        cursor.close()
        self.id_ciudad = str(int(rows[0][0]) + 1)
        reply = QMessageBox.question(None, 'EnerGis 6', 'Desea insertar una ciudad ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO Ciudades (ciudad, cod_postal, descripcion, partido) VALUES ('" + self.id_ciudad + "','<cp>','<ciudad>','<partido>')")
            self.conn.commit()
            QMessageBox.information(None, 'EnerGis 6', "ℹ️ Ciudad agregada !")
        except:
            self.conn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo agregar la ciudad !")
            return
        self.cargar_ciudades()

    def guardar(self):
        reply = QMessageBox.question(None, 'EnerGis 6', 'Desea guardar los cambios ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE Ciudades SET cod_postal='" + self.txtCp.text() + "', descripcion='" + self.txtNombre.text() + "', partido='" + self.txtPartido.text() + "' WHERE Ciudad='" + self.id_ciudad + "'")
            self.conn.commit()
            QMessageBox.information(None, 'EnerGis 6', "ℹ️ Grabado !")
        except:
            self.conn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo guardar la ciudad !")
            return
        self.cargar_ciudades()

    def borrar(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Ejes WHERE ciudad='" + self.id_ciudad + "'")
        rows = cursor.fetchall()
        cursor.close()
        if rows[0][0]>0:
            QMessageBox.warning(None, 'EnerGis 6', "❌ No se puede borrar la ciudad porque está asociada a " + str(rows[0][0]) + " ejes de calle !")
            return
        reply = QMessageBox.question(None, 'EnerGis 6', 'Desea borrar la ciudad ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Calles WHERE ciudad='" + self.id_ciudad + "'")
        rows = cursor.fetchall()
        cursor.close()
        if rows[0][0]>0:
            QMessageBox.warning(None, 'EnerGis 6', "❌ No se puede borrar la ciudad porque está asociada a " + str(rows[0][0]) + " calles !")
            return
        reply = QMessageBox.question(None, 'EnerGis 6', 'Desea borrar la ciudad ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM ciudades WHERE ciudad='" + self.id_ciudad + "'")
            self.conn.commit()
        except:
            self.conn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo borrar la ciudad !")
            return
        self.cargar_ciudades()

    def salir(self):
        self.close()
