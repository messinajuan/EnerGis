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

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_abm_postes.ui'))

class frmAbmPostes(DialogType, DialogBase):

    def __init__(self, conn, tipo_usuario, apoyo, estructura, rienda):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.conn = conn
        self.tipo_usuario = tipo_usuario

        self.cmbMaterial.addItem('Madera')
        self.cmbMaterial.addItem('Hierro Columna')
        self.cmbMaterial.addItem('Hierro Riel')
        self.cmbMaterial.addItem('Hierro Perfil')
        self.cmbMaterial.addItem('Hormigón Armado')
        self.cmbMaterial.addItem('PRFV')
        self.cmbMaterial.addItem('Compuesto')

        self.cmbTipo.addItem('Poste')
        self.cmbTipo.addItem('Ménsula')
        self.cmbTipo.addItem('Grampa')
        self.cmbTipo.addItem('Portico')

        self.arrApoyo = []
        self.arrEstructura = []
        self.arrRienda = []

        self.cargar_estructuras(estructura)
        self.cargar_apoyos(apoyo)
        self.cargar_riendas(rienda)

        self.id_apoyo=0
        self.id_estructura=0
        self.id_rienda=0

        if self.tipo_usuario==4:
            self.cmdGuardarEstructura.setEnabled(False)
            self.cmdGuardarApoyo.setEnabled(False)
            self.cmdGuardarRienda.setEnabled(False)

            self.txtEstructura.setReadOnly(True)
            self.txtApoyo.setReadOnly(True)
            self.txtRienda.setReadOnly(True)

        self.liwApoyos.currentRowChanged.connect(self.elijo_apoyo)
        self.liwEstructuras.currentRowChanged.connect(self.elijo_estructura)
        self.liwRiendas.currentRowChanged.connect(self.elijo_rienda)

        self.cmdGuardarEstructura.clicked.connect(self.guardar_estructura)
        self.cmdGuardarApoyo.clicked.connect(self.guardar_apoyo)
        self.cmdGuardarRienda.clicked.connect(self.guardar_rienda)

        self.cmdNuevaEstructura.clicked.connect(self.agregar_estructura)
        self.cmdNuevoApoyo.clicked.connect(self.agregar_apoyo)
        self.cmdNuevaRienda.clicked.connect(self.agregar_rienda)

        self.cmdBorrarEstructura.clicked.connect(self.borrar_estructura)
        self.cmdBorrarApoyo.clicked.connect(self.borrar_apoyo)
        self.cmdBorrarRienda.clicked.connect(self.borrar_rienda)

        self.cmdGuardarEstructura.clicked.connect(self.guardar_estructura)
        self.cmdGuardarApoyo.clicked.connect(self.guardar_apoyo)
        self.cmdGuardarRienda.clicked.connect(self.guardar_rienda)

        self.cmdSalir.clicked.connect(self.salir)
        pass

    def cargar_estructuras(self, estructura):
        self.liwEstructuras.clear()
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, descripcion FROM Estructuras")
        #convierto el cursor en array
        rows = tuple(cursor)
        cursor.close()
        i=0
        iestructura=0
        for row in rows:
            self.arrEstructura.append(row)
            self.liwEstructuras.addItem(str(row[1]))
            if row[0] == estructura:
                iestructura=i
            i=i+1
        self.liwEstructuras.setCurrentRow(iestructura)

    def cargar_apoyos(self, apoyo):
        self.liwApoyos.clear()
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, descripcion, estilo, Value1, Value2 FROM Elementos_Postes")
        #convierto el cursor en array
        rows = tuple(cursor)
        cursor.close()
        i=0
        iapoyo=0
        for row in rows:
            self.arrApoyo.append(row)
            self.liwApoyos.addItem(str(row[1]))
            if row[0] == apoyo:
                iapoyo=i
            i=i+1
        self.liwApoyos.setCurrentRow(iapoyo)

    def cargar_riendas(self, rienda):
        self.liwRiendas.clear()
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, descripcion FROM Riendas")
        #convierto el cursor en array
        rows = tuple(cursor)
        cursor.close()
        i=0
        irienda=0
        for row in rows:
            self.arrRienda.append(row)
            self.liwRiendas.addItem(str(row[1]))
            if row[0] == rienda:
                irienda=i
            i=i+1
        self.liwRiendas.setCurrentRow(irienda)

    def elijo_apoyo(self):
        if self.liwApoyos.currentItem()==None:
            return
        for i in range (0, len(self.arrApoyo)):
            if self.liwApoyos.currentItem().text()==self.arrApoyo[i][1]:
                self.id_apoyo=self.arrApoyo[i][0]
                self.txtApoyo.setText(self.arrApoyo[i][1])
                for j in range (0, self.cmbMaterial.count()):
                    if self.cmbMaterial.itemText(j) == str(self.arrApoyo[i][3]):
                        self.cmbMaterial.setCurrentIndex(j)
                for j in range (0, self.cmbTipo.count()):
                    if self.cmbTipo.itemText(j) == str(self.arrApoyo[i][4]):
                        self.cmbTipo.setCurrentIndex(j)

    def elijo_estructura(self):
        if self.liwEstructuras.currentItem()==None:
            return
        for i in range (0, len(self.arrEstructura)):
            if self.liwEstructuras.currentItem().text()==self.arrEstructura[i][1]:
                self.id_estructura=self.arrEstructura[i][0]
                self.txtEstructura.setText(self.arrEstructura[i][1])

    def elijo_rienda(self):
        if self.liwRiendas.currentItem()==None:
            return
        for i in range (0, len(self.arrRienda)):
            if self.liwRiendas.currentItem().text()==self.arrRienda[i][1]:
                self.id_rienda=self.arrRienda[i][0]
                self.txtRienda.setText(self.arrRienda[i][1])

    def agregar_estructura(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(id) FROM Estructuras")
        rows = cursor.fetchall()
        cursor.close()
        id = rows[0][0] + 1
        reply = QMessageBox.question(None, 'EnerGis 6', 'Desea insertar un nuevo tipo de estructura ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO Estructuras (id, descripcion, estilo) VALUES (" + str(id) + ",'Nueva Estructura','39-MapInfo Oil&Gas-16777215-0-12')")
            self.conn.commit()
        except:
            self.conn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo agregar el tipo de estructura !")
            return
        self.cargar_estructuras(id)

    def guardar_estructura(self):
        descripcion = self.txtEstructura.text()
        reply = QMessageBox.question(None, 'EnerGis 6', 'Desea guardar los cambios ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE Estructuras SET descripcion='" + descripcion + "' WHERE id=" + str(self.id_estructura))
            self.conn.commit()
        except:
            self.conn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo guardar el tipo de estructura !")
            return
        self.cargar_estructuras(0)

    def borrar_estructura(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Postes WHERE Estructura=" + str(self.id_estructura))
        rows = cursor.fetchall()
        cursor.close()
        if rows[0][0]>0:
            QMessageBox.warning(None, 'EnerGis 6', "❌ No  se puede borrar el tipo de estructura porque está asociada a " + str(rows[0][0]) + " elementos del mapa !")
            return
        reply = QMessageBox.question(None, 'EnerGis 6', 'Desea borrar el tipo de estructura ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM Estructuras WHERE id=" + str(self.id_estructura))
            self.conn.commit()
        except:
            self.conn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', "❌ No  se pudo borrar el tipo de estructura !")
            return
        self.cargar_estructuras(0)

    def agregar_apoyo(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(id) FROM Elementos_Postes")
        rows = cursor.fetchall()
        cursor.close()
        id = rows[0][0] + 1
        value1 = self.cmbMaterial.currentText()
        value2 = self.cmbTipo.currentText()
        reply = QMessageBox.question(None, 'EnerGis 6', 'Desea insertar un nuevo tipo de apoyo ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO Elementos_Postes (id, descripcion, estilo, value1, value2) VALUES (" + str(id) + ",'Nuevo Apoyo','38-Map Symbols-16777215-255-6-0','" + value1 + "','" + value2 + "')")
            self.conn.commit()
        except:
            self.conn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', "❌ No  se pudo agregar el tipo de apoyo !")
            return
        self.cargar_apoyos(id)

    def guardar_apoyo(self):
        descripcion = self.txtApoyo.text()
        value1 = self.cmbMaterial.currentText()
        value2 = self.cmbTipo.currentText()
        reply = QMessageBox.question(None, 'EnerGis 6', 'Desea guardar los cambios ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE Elementos_Postes SET descripcion='" + descripcion + "', value1='" + value1 + "', value2='" + value2 + "' WHERE id=" + str(self.id_apoyo))
            self.conn.commit()
        except:
            self.conn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', "❌ No  se pudo guardar el tipo de apoyo !")
            return
        self.cargar_apoyos(0)

    def borrar_apoyo(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Postes WHERE Elmt=" + str(self.id_apoyo))
        rows = cursor.fetchall()
        cursor.close()
        if rows[0][0]>0:
            QMessageBox.warning(None, 'EnerGis 6', "❌ No  se puede borrar el tipo de apoyo porque está asociado a " + str(rows[0][0]) + " elementos del mapa !")
            return
        reply = QMessageBox.question(None, 'EnerGis 6', 'Desea borrar el tipo de apoyo ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM Elementos_Postes WHERE id=" + str(self.id_apoyo))
            self.conn.commit()
        except:
            self.conn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', "❌ No  se pudo borrar el tipo de apoyo !")
            return
        self.cargar_apoyos(0)

    def agregar_rienda(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(id) FROM Riendas")
        rows = cursor.fetchall()
        cursor.close()
        id = rows[0][0] + 1
        reply = QMessageBox.question(None, 'EnerGis 6', 'Desea insertar un nuevo tipo de rienda ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO Riendas (id, descripcion) VALUES (" + str(id) + ",'Nueva Rienda')")
            self.conn.commit()
        except:
            self.conn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', "❌ No  se pudo agregar el tipo de rienda !")
            return
        self.cargar_riendas(id)

    def guardar_rienda(self):
        descripcion = self.txtRienda.text()
        reply = QMessageBox.question(None, 'EnerGis 6', 'Desea guardar los cambios ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE Riendas SET descripcion='" + descripcion + "' WHERE id=" + str(self.id_rienda))
            self.conn.commit()
        except:
            self.conn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', "❌ No  se pudo guardar el tipo de rienda !")
            return
        self.cargar_riendas(0)

    def borrar_rienda(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Postes WHERE Rienda=" + str(self.id_rienda))
        rows = cursor.fetchall()
        cursor.close()
        if rows[0][0]>0:
            QMessageBox.warning(None, 'EnerGis 6', "❌ No  se puede borrar el tipo de rienda porque está asociada a " + str(rows[0][0]) + " elementos del mapa !")
            return
        reply = QMessageBox.question(None, 'EnerGis 6', 'Desea borrar el tipo de rienda ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM Riendas WHERE id=" + str(self.id_rienda))
            self.conn.commit()
        except:
            self.conn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', "❌ No  se pudo borrar el tipo de rienda !")
            return
        self.cargar_riendas(0)

    def salir(self):
        self.close()
        pass
