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
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem
from PyQt6 import uic
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_suministros.ui'))

class frmSuministros(DialogType, DialogBase):
        
    def __init__(self, tipo_usuario, conn, geoname):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.tipo_usuario = tipo_usuario
        self.conn = conn
        self.geoname = geoname

        if self.tipo_usuario==4:
            self.cmdAgregar.setEnabled(False)
            self.cmdQuitar.setEnabled(False)

        if self.geoname != 0:

            cnn = self.conn
            cursor = cnn.cursor()
            cursor.execute("SELECT Nodos.Nombre, Nodos.XCoord, Nodos.YCoord FROM Suministros_Trafos INNER JOIN Nodos ON Suministros_Trafos.Geoname_t = Nodos.Geoname WHERE Nodos.elmt=4 AND Suministros_Trafos.Geoname_s=" + str(self.geoname))
            #convierto el cursor en array
            recordset = tuple(cursor)
            cursor.close()

            if len(recordset)>0:
                self.lblCT.setText('CT ' + recordset[0][0])
                self.lblCoordenadas.setText(str(recordset[0][1]) + ', ' + str(recordset[0][2]))
            else:
                self.lblCT.setText('Sum MT')
                self.lblCoordenadas.setText('')

        self.lleno_lista1()
        self.lleno_lista2()

        self.cmdBuscar.clicked.connect(self.buscar)
        self.cmdSeparar.clicked.connect(self.separar)
        self.cmdAgregar.clicked.connect(self.agregar)
        self.cmdQuitar.clicked.connect(self.quitar)
        self.cmdActualizar.clicked.connect(self.actualizar)
        self.cmdCargas.clicked.connect(self.cargas)
        self.cmdUsuarios.clicked.connect(self.usuarios)
        self.cmdSalir.clicked.connect(self.salir)
        
    def lleno_lista1(self):
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT DISTINCT Suministros_Nuevos.id_suministro, ISNULL(VW_CCDATOSCOMERCIALES.Ruta,'0') AS Ruta, ISNULL(Usuarios.calle, '') AS Calle, ISNULL(Usuarios.altura, '0') AS altura, ISNULL(Usuarios.Electrodependiente,'N') AS eld, ISNULL(Usuarios.Prosumidor,'') AS P FROM (Suministros_Nuevos LEFT JOIN Usuarios ON Suministros_Nuevos.id_suministro = Usuarios.id_suministro) LEFT JOIN VW_CCDATOSCOMERCIALES ON Usuarios.id_usuario = VW_CCDATOSCOMERCIALES.Id_Usuario ORDER BY calle")
        #convierto el cursor en array
        recordset = tuple(cursor)
        cursor.close()

        self.tbl1.setRowCount(len(recordset))
        self.lblSuministrosSinUbicacion.setText(str(len(recordset)) + " Suministros sin Ubicación")
        self.tbl1.setColumnCount(6)
        self.tbl1.setHorizontalHeaderLabels(["Suministro", "Ruta", "Calle", "Número","Eld","Prosumidor"])

        self.tbl1.setColumnWidth(0, 80)
        self.tbl1.setColumnWidth(1, 60)
        self.tbl1.setColumnWidth(2, 150)
        self.tbl1.setColumnWidth(3, 60)
        self.tbl1.setColumnWidth(4, 0)
        self.tbl1.setColumnWidth(5, 0)

        for i in range (0, len(recordset)):
            for j in range (0, 5):
                self.tbl1.setItem(i, j, QTableWidgetItem(str(recordset[i][j])))
            if str(recordset[i][5])!='':
                for j in range (0, 5):
                    self.tbl1.item(i, j).setBackground(QColor(255, 255, 155))
            if str(recordset[i][4])=='S':
                for j in range (0, 5):
                    self.tbl1.item(i, j).setBackground(QColor(250, 100, 100))

        self.tbl1.clicked.connect(self.tbl1_click)

    def lleno_lista2(self):
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT DISTINCT suministros.id_suministro, ISNULL(VW_CCDATOSCOMERCIALES.Ruta,'0') AS Ruta, ISNULL(Usuarios.calle, '') AS Calle, ISNULL(Usuarios.altura, '0') AS altura, ISNULL(Usuarios.Electrodependiente,'N') AS eld, ISNULL(Usuarios.Prosumidor,'') AS P FROM (suministros INNER JOIN Usuarios ON suministros.id_suministro = Usuarios.id_suministro) LEFT JOIN VW_CCDATOSCOMERCIALES ON Usuarios.id_usuario = VW_CCDATOSCOMERCIALES.Id_Usuario WHERE id_nodo =" + str(self.geoname))
        #convierto el cursor en array
        recordset = tuple(cursor)
        cursor.close()

        self.tbl2.setRowCount(len(recordset))
        self.lblSuministrosDelNodo.setText(str(len(recordset)) + " Suministros del Nodo")
        self.tbl2.setColumnCount(6)
        self.tbl2.setHorizontalHeaderLabels(["Suministro", "Ruta", "Calle", "Número", "Eld", "Prosumidor"])

        self.tbl2.setColumnWidth(0, 80)
        self.tbl2.setColumnWidth(1, 60)
        self.tbl2.setColumnWidth(2, 150)
        self.tbl2.setColumnWidth(3, 60)
        self.tbl2.setColumnWidth(4, 0)
        self.tbl2.setColumnWidth(5, 0)

        for i in range (0, len(recordset)):
            for j in range (0, 5):
                self.tbl2.setItem(i, j, QTableWidgetItem(str(recordset[i][j])))
            if str(recordset[i][5])!='':
                for j in range (0, 5):
                    self.tbl2.item(i, j).setBackground(QColor(255, 255, 155))
            if str(recordset[i][4])=='S':
                for j in range (0, 5):
                    self.tbl2.item(i, j).setBackground(QColor(250, 100, 100))

        self.tbl2.clicked.connect(self.tbl2_click)

    def tbl1_click(self):
        self.lblElectrodependiente.setText("")
        id_suministro = self.tbl1.item(self.tbl1.currentRow(),0).text()
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT Usuarios.id_usuario, Usuarios.nombre, Usuarios.calle, ISNULL(Usuarios.altura, '0'), ISNULL(Usuarios.altura_ex, '') AS altura_ex, Usuarios.zona, electrodependiente, prosumidor FROM Usuarios INNER JOIN Suministros_Nuevos ON Usuarios.id_suministro = Suministros_Nuevos.id_suministro WHERE Suministros_Nuevos.id_suministro ='" + id_suministro + "'")
        #convierto el cursor en array
        recordset = tuple(cursor)
        cursor.close()
        self.label_3.setText(str(recordset[0][0]) + " " + recordset[0][1].strip() + " " + recordset[0][2].strip() + " " + recordset[0][3].strip() + " " + recordset[0][4].strip() + " (" + recordset[0][5].strip() + ")")

        if recordset[0][7] != '':
            self.lblElectrodependiente.setText("Posee un Prosumidor  ")
        if recordset[0][6] == "S":
            self.lblElectrodependiente.setText(self.lblElectrodependiente.text() + "Posee un Electrodependiente")

    def tbl2_click(self):
        self.lblElectrodependiente.setText("")
        id_suministro = self.tbl2.item(self.tbl2.currentRow(),0).text()
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT Usuarios.id_usuario, Usuarios.nombre, Usuarios.calle, ISNULL(Usuarios.altura, '0'), ISNULL(Usuarios.altura_ex, '') AS altura_ex, Usuarios.zona, electrodependiente, prosumidor FROM Usuarios WHERE Usuarios.id_suministro ='" + id_suministro + "'")
        #convierto el cursor en array
        recordset = tuple(cursor)
        cursor.close()
        self.label_5.setText(str(recordset[0][0]) + " " + recordset[0][1].strip() + " " + recordset[0][2].strip() + " " + recordset[0][3].strip() + " " + recordset[0][4].strip() + " (" + recordset[0][5].strip() + ")")
        if recordset[0][7] != '':
            self.lblElectrodependiente.setText("Posee un Prosumidor  ")
        if recordset[0][6] == "S":
            self.lblElectrodependiente.setText(self.lblElectrodependiente.text() + "Posee un Electrodependiente")

    def aceptar(self):
        self.close()

    def separar(self):
        cnn = self.conn
        for item in self.tbl2.selectedItems():
            if item.column()==0:
                reply = QMessageBox.question(None, 'EnerGis 6', 'Desea separar a los usuarios del suministro ' +  item.text() + ' ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    cnn = self.conn
                    cursor = cnn.cursor()
                    cursor.execute("SELECT id_usuario FROM Usuarios WHERE id_suministro ='" + item.text() + "'")
                    #convierto el cursor en array
                    usuarios = tuple(cursor)
                    self.conn.autocommit = False
                    cursor = self.conn.cursor()
                    try:
                        cursor.execute("DELETE FROM SUMINISTROS WHERE id_Suministro='" + item.text() + "'")
                        cursor.execute("UPDATE Usuarios SET id_suministro=id_usuario WHERE id_suministro='" + item.text() + "'")
                        for i in range (0, len(usuarios)):
                            cursor.execute("INSERT INTO Suministros (id_nodo, id_suministro) VALUES (" + str(self.geoname) + ", '" + str(usuarios[i][0]) + "')")
                        cnn.commit()
                        self.actualizar
                    except:
                        cnn.rollback()

    def buscar(self):
        # Buscar por columna
        items = self.tbl1.findItems(self.txtBuscar.text(), Qt.MatchContains)  # Busca coincidencias parciales
        # Seleccionar la celda si se encuentra en la columna deseada
        for item in items:
            if item.column() == 0:
                self.tbl1.setCurrentItem(item)  # Selecciona la celda
                self.tbl1.scrollToItem(item)   # Desplaza la vista hacia la celda encontrada
                return  # Salimos al encontrar la primera coincidencia
        for item in items:
            if item.column() == 2:
                self.tbl1.setCurrentItem(item)  # Selecciona la celda
                self.tbl1.scrollToItem(item)   # Desplaza la vista hacia la celda encontrada
                return  # Salimos al encontrar la primera coincidencia
        for item in items:
            if item.column() == 1:
                self.tbl1.setCurrentItem(item)  # Selecciona la celda
                self.tbl1.scrollToItem(item)   # Desplaza la vista hacia la celda encontrada
                return  # Salimos al encontrar la primera coincidencia
        for item in items:
            if item.column() == 3:
                self.tbl1.setCurrentItem(item)  # Selecciona la celda
                self.tbl1.scrollToItem(item)   # Desplaza la vista hacia la celda encontrada
                return  # Salimos al encontrar la primera coincidencia

    def agregar(self):
        cnn = self.conn
        cursor = cnn.cursor()
        for item in self.tbl1.selectedItems():
            if item.column()==0:
                try:
                    cursor.execute("INSERT INTO Suministros (id_nodo,id_suministro) VALUES (" + str(self.geoname) + ",'" + item.text() + "')")
                    cursor.execute("DELETE FROM Suministros_Nuevos WHERE id_suministro ='" + item.text() + "'")
                    cnn.commit()
                except:
                    cnn.rollback()
        self.lleno_lista1()
        self.lleno_lista2()

    def quitar(self):
        cnn = self.conn
        cursor = cnn.cursor()
        try:
            for item in self.tbl2.selectedItems():
                if item.column()==0:
                    try:
                        cursor.execute("INSERT INTO Suministros_Nuevos (id_suministro) VALUES ('" + item.text() + "')")
                        cursor.execute("DELETE FROM Suministros WHERE id_suministro ='" + item.text() + "'")
                        cnn.commit()
                    except:
                        cnn.rollback()
            self.lleno_lista1()
            self.lleno_lista2()
        except:
            QMessageBox.critical(None, 'EnerGis 6', '❌ Error - Es probable que deba actualizar suministros sin ubicación antes de ejecutar esta opción')

    def actualizar(self):
        msgBox=QMessageBox()
        msgBox.setIcon(QMessageBox.Question)
        msgBox.setWindowTitle("Nuevos Suministros")
        msgBox.setText("Esta opción actualizará la lista de suministros sin nodo asociado")
        msgBox.setInformativeText("Desea Continuar ❓")
        msgBox.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msgBox.setDefaultButton(QMessageBox.StandardButton.Yes)
        resultado = msgBox.exec()

        if resultado==QMessageBox.StandardButton.Yes:
            cnn = self.conn
            cursor = cnn.cursor()
            try:
                cursor.execute("DELETE FROM Suministros_Nuevos")
                cursor.execute("INSERT INTO Suministros_Nuevos (id_suministro) SELECT usuarios.id_suministro FROM suministros RIGHT JOIN usuarios ON suministros.id_suministro = usuarios.id_suministro WHERE usuarios.ES=1 AND suministros.id_suministro IS NULL GROUP BY usuarios.id_suministro HAVING usuarios.id_suministro IS NOT NULL")
                cursor.execute("INSERT INTO Suministros_Nuevos (id_suministro) SELECT DISTINCT movimientos.id_suministro FROM movimientos WHERE tipo_mov='A' AND incorp=0 AND id_suministro NOT IN (SELECT suministros.id_suministro FROM suministros) AND id_suministro NOT IN (SELECT suministros_nuevos.id_suministro FROM suministros_nuevos)")
                cnn.commit()
            except:
                cnn.rollback()
            self.lleno_lista1()

    def usuarios(self):
        from .frm_usuarios_suministro import frmUsuariosSuministro
        self.dialogo = frmUsuariosSuministro(self.tipo_usuario, self.conn, self.geoname)
        self.dialogo.show()

    def cargas(self):
        from .frm_cargas import frmCargas
        self.dialogo = frmCargas(self.conn, self.geoname, 6)
        self.dialogo.show()

    def salir(self):
        self.close()
