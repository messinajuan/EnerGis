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
from PyQt6.QtWidgets import QListWidgetItem, QTableWidgetItem
from PyQt6.QtWidgets import QMessageBox
from qgis.core import QgsGeometry
from PyQt6 import uic
from PyQt6.QtCore import QEvent
import winreg

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_buscar.ui'))

class frmBuscar(DialogType, DialogBase):

    def __init__(self, mapCanvas, conn):
        super().__init__()
        self.setupUi(self)
        self.installEventFilter(self)

        self.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(self.size())
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowTitleHint | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowCloseButtonHint)

        self.mapCanvas = mapCanvas
        self.conn = conn

        #basepath = os.path.dirname(os.path.realpath(__file__))
        #img_buscar = os.path.join(basepath,"icons", 'img_buscar.png')
        #self.cmdBuscar.setIcon(QtGui.QIcon(img_buscar))
        cnn = conn
        cursor = cnn.cursor()
        cursor.execute("SELECT id, Descripcion FROM Elementos_Nodos")
        #convierto el cursor en array
        elementos_nodos = tuple(cursor)
        cursor.close()
        self.liwElementos.addItem('Nodo')
        for elemento in elementos_nodos:
            #self.liwElementos.addItem(elemento[1])
            item = QListWidgetItem()
            item.setText(elemento[1])
            item.setData(QtCore.Qt.ItemDataRole.UserRole, elemento[0])
            self.liwElementos.addItem(item)
        self.liwElementos.addItem('Usuario')
        self.liwElementos.addItem('Electrodependiente')
        self.liwElementos.addItem('Prosumidor')
        self.liwElementos.addItem('Medidor')
        self.liwElementos.addItem('Poste')
        self.liwElementos.addItem('Línea')
        self.liwElementos.itemSelectionChanged.connect(self.elijo_elemento)
        self.cmdBuscar.clicked.connect(self.buscar)
        self.tblResultado.itemClicked.connect(self.elijo_item)
        try:
            # Definir la ruta de la clave del registro que quieres leer
            ruta_clave = r"SOFTWARE\EnerGis"
            # Abrir la clave del registro en modo de solo lectura
            clave_registro = winreg.OpenKey(winreg.HKEY_CURRENT_USER, ruta_clave, 0, winreg.KEY_READ)
            # Leer el valor de una entrada en la clave del registro
            valor, tipo = winreg.QueryValueEx(clave_registro, "Tipo_Buscado") #el tipo no lo usamos
            if valor!=None:
                for i in range (0, self.liwElementos.count()):
                    if self.liwElementos.item(i).text() == valor:
                        self.liwElementos.setCurrentItem(self.liwElementos.item(i))
            # Leer el valor de una entrada en la clave del registro
            valor, tipo = winreg.QueryValueEx(clave_registro, "Campo_Buscado") #el tipo no lo usamos
            if valor!=None:
                for i in range (0, self.cmbCampos.count()):
                    if self.cmbCampos.itemText(i) == valor:
                        self.cmbCampos.setCurrentIndex(i)
            # Leer el valor de una entrada en la clave del registro
            valor, tipo = winreg.QueryValueEx(clave_registro, "Elemento_Buscado") #el tipo no lo usamos
            if valor!=None:
                self.txtValor.setText(valor)
            # Cerrar la clave del registro
            winreg.CloseKey(clave_registro)
        except:
            pass

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type. Close:
            # Definir la ruta de la clave del registro en la que quieres escribir
            ruta_clave = r"SOFTWARE\EnerGis"
            try:
                # Abrir la clave del registro en modo de escritura
                clave_registro = winreg.OpenKey(winreg.HKEY_CURRENT_USER, ruta_clave, 0, winreg.KEY_WRITE)
                # Escribir un valor en la clave del registro
                nombre_valor = "Tipo_Buscado"
                valor = self.liwElementos.item(self.liwElementos.currentRow()).text()
                winreg.SetValueEx(clave_registro, nombre_valor, 0, winreg.REG_SZ, valor)
                # Escribir un valor en la clave del registro
                nombre_valor = "Campo_Buscado"
                valor = self.cmbCampos.currentText()
                winreg.SetValueEx(clave_registro, nombre_valor, 0, winreg.REG_SZ, valor)
                # Escribir un valor en la clave del registro
                nombre_valor = "Elemento_Buscado"
                valor = str(self.txtValor.text())
                winreg.SetValueEx(clave_registro, nombre_valor, 0, winreg.REG_SZ, valor)
                # Cerrar la clave del registro
                winreg.CloseKey(clave_registro)
            except:
                # Crear la clave en el registro
                try:
                    # Intentar crear la nueva clave del registro
                    winreg.CreateKey(winreg.HKEY_CURRENT_USER, ruta_clave)
                except:
                    pass
        return super().eventFilter(obj, event)

    def elijo_elemento(self):
        self.cmbCampos.clear()
        if self.liwElementos.selectedItems()[0].text() == "Suministro":
            self.cmbCampos.addItem ("Id Suministro")
            return
        if self.liwElementos.selectedItems()[0].text() == "Usuario":
            self.cmbCampos.addItem ("Id Usuario")
            self.cmbCampos.addItem ("Id Suministro")
            self.cmbCampos.addItem ("Nombre")
            return
        if self.liwElementos.selectedItems()[0].text() == "Centro Transformación":
            self.cmbCampos.addItem ("Nombre")
            self.cmbCampos.addItem ("Descripción")
            self.cmbCampos.addItem ("Número Chapa")
            self.cmbCampos.addItem ("Potencia")
            self.cmbCampos.addItem ("Id Trafo")
            self.cmbCampos.addItem ("Geoname")
            return
        if self.liwElementos.selectedItems()[0].text() == "Medidor":
            self.cmbCampos.addItem ("Id Medidor")
            self.cmbCampos.addItem ("Id Usuario")
            self.cmbCampos.addItem ("Id Suministro")
            return
        if self.liwElementos.selectedItems()[0].text() == "Poste":
            self.cmbCampos.addItem ("Geoname")
            return
        if self.liwElementos.selectedItems()[0].text() == "Línea":
            self.cmbCampos.addItem ("Geoname")
            self.cmbCampos.addItem ("Conductor")
        else:
            self.cmbCampos.addItem ("Nombre")
            self.cmbCampos.addItem ("Geoname")
            self.cmbCampos.addItem ("Descripción")

    def buscar(self):
        if len(self.liwElementos.selectedItems())==0:
            return
        if self.liwElementos.selectedItems()[0].text() == "Suministro":
            if self.cmbCampos.currentText() == "Id Suministro":
                strSql = "SELECT Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE Usuarios.id_suministro = '" + str(self.txtValor.text()) + "'"
            if str(self.txtValor.text())=="":
                strSql = "SELECT Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname"
        else:
            if self.liwElementos.selectedItems()[0].text() == "Usuario":
                if self.cmbCampos.currentText() == "Id Usuario":
                    strSql = "SELECT Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE Usuarios.id_usuario = '" + str(self.txtValor.text() + "'")
                if self.cmbCampos.currentText() == "Id Suministro":
                    strSql = "SELECT Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE Usuarios.id_suministro = '" + str(self.txtValor.text()) + "'"
                if self.cmbCampos.currentText() == "Nombre":
                    strSql = "SELECT TOP 300 Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE Usuarios.nombre LIKE '%" + str(self.txtValor.text()) + "%'"
                if str(self.txtValor.text())=="":
                    strSql = "SELECT TOP 300 Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname"
            else:
                if self.liwElementos.selectedItems()[0].text() == "Electrodependiente":
                    if self.cmbCampos.currentText() == "Id Usuario":
                        strSql = "SELECT Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE electrodependiente='S' AND Usuarios.id_usuario = '" + str(self.txtValor.text() + "'")
                    if self.cmbCampos.currentText() == "Id Suministro":
                        strSql = "SELECT Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE electrodependiente='S' AND Usuarios.id_suministro = '" + str(self.txtValor.text()) + "'"
                    if self.cmbCampos.currentText() == "Nombre":
                        strSql = "SELECT TOP 300 Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE electrodependiente='S' AND Usuarios.nombre LIKE '%" + str(self.txtValor.text()) + "%'"
                    if str(self.txtValor.text())=="":
                        strSql = "SELECT TOP 300 Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE electrodependiente='S'"
                else:
                    if self.liwElementos.selectedItems()[0].text() == "Prosumidor":
                        if self.cmbCampos.currentText() == "Id Usuario":
                            strSql = "SELECT Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE prosumidor<>'' AND Usuarios.id_usuario = '" + str(self.txtValor.text() + "'")
                        if self.cmbCampos.currentText() == "Id Suministro":
                            strSql = "SELECT Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE prosumidor<>'' AND Usuarios.id_suministro = '" + str(self.txtValor.text()) + "'"
                        if self.cmbCampos.currentText() == "Nombre":
                            strSql = "SELECT TOP 300 Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE prosumidor<>'' AND Usuarios.nombre LIKE '%" + str(self.txtValor.text()) + "%'"
                        if str(self.txtValor.text())=="":
                            strSql = "SELECT TOP 300 Nodos.Geoname, Usuarios.nombre As Nombre, Calle + ' ' + altura AS Direccion, obj.STEnvelope().ToString() FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE prosumidor<>''"
                    else:
                        if self.liwElementos.selectedItems()[0].text() == "Medidor":
                            if self.cmbCampos.currentText() == "Id Medidor":
                                strSql = "SELECT Nodos.Geoname, Usuarios.Nombre, Medidores.nro_medidor AS Medidor, obj.STEnvelope().ToString() FROM (Medidores INNER JOIN Usuarios ON Medidores.id_usuario = Usuarios.id_usuario) INNER JOIN (Nodos INNER JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo) ON Usuarios.id_suministro = Suministros.id_suministro WHERE Medidores.nro_medidor = '" + str(self.txtValor.text()) + "'"
                            if self.cmbCampos.currentText() == "Id Usuario":
                                strSql = "SELECT Nodos.Geoname, Usuarios.Nombre, Medidores.nro_medidor AS Medidor, obj.STEnvelope().ToString() FROM (Medidores INNER JOIN Usuarios ON Medidores.id_usuario = Usuarios.id_usuario) INNER JOIN (Nodos INNER JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo) ON Usuarios.id_suministro = Suministros.id_suministro WHERE Usuarios.id_usuario = '" + str(self.txtValor.text() + "'")
                            if self.cmbCampos.currentText() == "Id Suministro":
                                strSql = "SELECT Nodos.Geoname, Usuarios.Nombre, Medidores.nro_medidor AS Medidor, obj.STEnvelope().ToString() FROM (Medidores INNER JOIN Usuarios ON Medidores.id_usuario = Usuarios.id_usuario) INNER JOIN (Nodos INNER JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo) ON Usuarios.id_suministro = Suministros.id_suministro WHERE Usuarios.id_suministro = '" + str(self.txtValor.text()) + "'"
                            if str(self.txtValor.text())=="":
                                strSql = "SELECT Nodos.Geoname, Usuarios.Nombre, Medidores.nro_medidor AS Medidor, obj.STEnvelope().ToString() FROM (Medidores INNER JOIN Usuarios ON Medidores.id_usuario = Usuarios.id_usuario) INNER JOIN (Nodos INNER JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo) ON Usuarios.id_suministro = Suministros.id_suministro"
                        else:
                            if self.liwElementos.selectedItems()[0].text() == "Poste":
                                if self.cmbCampos.currentText() == "Geoname":
                                    strSql = "SELECT Postes.Geoname, Postes.Tipo, Postes.Aislacion, obj.STEnvelope().ToString() FROM Postes WHERE Postes.Geoname = " + str(self.txtValor.text())
                                if str(self.txtValor.text())=="":
                                    strSql = "SELECT Postes.Geoname, Postes.Tipo, Postes.Aislacion, obj.STEnvelope().ToString() FROM Postes"
                            else:
                                if self.liwElementos.selectedItems()[0].text() == "Línea":
                                    if self.cmbCampos.currentText() == "Geoname":
                                        strSql = "SELECT Lineas.Geoname, Elementos_Lineas.Descripcion, Lineas.Fase, obj.STEnvelope().ToString(), Lineas.Tension, Lineas.Alimentador FROM Elementos_Lineas INNER JOIN Lineas ON Elementos_Lineas.Id = Lineas.Elmt WHERE Lineas.Geoname = " + str(self.txtValor.text())
                                    if self.cmbCampos.currentText() == "Conductor":
                                        strSql = "SELECT TOP 50 Lineas.Geoname, Elementos_Lineas.Descripcion, Lineas.Fase, obj.STEnvelope().ToString(), Lineas.Tension, Lineas.Alimentador FROM Elementos_Lineas INNER JOIN Lineas ON Elementos_Lineas.Id = Lineas.Elmt WHERE Elementos_Lineas.Descripcion LIKE '%" + str(self.txtValor.text()) + "%'"
                                    if str(self.txtValor.text())=="":
                                        strSql = "SELECT Lineas.Geoname, Elementos_Lineas.Descripcion, Lineas.Fase, obj.STEnvelope().ToString(), Lineas.Tension, Lineas.Alimentador FROM Elementos_Lineas INNER JOIN Lineas ON Elementos_Lineas.Id = Lineas.Elmt"
                                else:
                                    if self.liwElementos.selectedItems()[0].text() == 'Centro Transformación':
                                        if self.cmbCampos.currentText() == "Geoname":
                                            strSql = "SELECT Nodos.Geoname, Nodos.Nombre As Nombre, Elementos_Nodos.Descripcion As Elemento, obj.STEnvelope().ToString() FROM Elementos_Nodos RIGHT JOIN Nodos ON Elementos_Nodos.Id = Nodos.Elmt WHERE Nodos.elmt=4 AND Nodos.Geoname = " + str(self.txtValor.text())
                                        if self.cmbCampos.currentText() == "Nombre":
                                            strSql = "SELECT TOP 300 Nodos.Geoname, Nodos.Nombre As Nombre, Elementos_Nodos.Descripcion As Elemento, obj.STEnvelope().ToString() FROM Elementos_Nodos RIGHT JOIN Nodos ON Elementos_Nodos.Id = Nodos.Elmt WHERE Nodos.elmt=4 AND Nodos.Nombre LIKE '%" + str(self.txtValor.text()) + "%'"
                                        if self.cmbCampos.currentText() == "Número Chapa":
                                            strSql = "SELECT TOP 300 Nodos.Geoname, Nodos.Nombre As Nombre, Elementos_Nodos.Descripcion As Elemento, obj.STEnvelope().ToString() FROM Nodos INNER JOIN Transformadores INNER JOIN Ct ON Transformadores.Id_ct = Ct.Id_ct ON Nodos.Nombre = Ct.Id_ct INNER JOIN Elementos_Nodos ON Nodos.Elmt=Elementos_Nodos.Id WHERE Nodos.elmt=4 AND Transformadores.N_Chapa LIKE '%" + str(self.txtValor.text()) + "%'"
                                        if self.cmbCampos.currentText() == "Potencia":
                                            strSql = "SELECT TOP 300 Nodos.Geoname, Nodos.Nombre As Nombre, Elementos_Nodos.Descripcion As Elemento, obj.STEnvelope().ToString() FROM Nodos INNER JOIN Transformadores INNER JOIN Ct ON Transformadores.Id_ct = Ct.Id_ct ON Nodos.Nombre = Ct.Id_ct INNER JOIN Elementos_Nodos ON Nodos.Elmt=Elementos_Nodos.Id WHERE Nodos.elmt=4 AND Transformadores.Potencia=" + str(self.txtValor.text())
                                        if self.cmbCampos.currentText() == "Id Trafo":
                                            strSql = "SELECT TOP 300 Nodos.Geoname, Nodos.Nombre As Nombre, Elementos_Nodos.Descripcion As Elemento, obj.STEnvelope().ToString() FROM Nodos INNER JOIN Transformadores INNER JOIN Ct ON Transformadores.Id_ct = Ct.Id_ct ON Nodos.Nombre = Ct.Id_ct INNER JOIN Elementos_Nodos ON Nodos.Elmt=Elementos_Nodos.Id WHERE Nodos.elmt=4 AND Transformadores.Id_trafo=" + str(self.txtValor.text())
                                        if self.cmbCampos.currentText() == "Descripción":
                                            strSql = "SELECT Nodos.Geoname, Nodos.Nombre As Nombre, Nodos.Descripcion As Descripción, obj.STEnvelope().ToString() FROM Nodos WHERE Nodos.Tension>0 AND Nodos.elmt=4 AND Nodos.Descripcion LIKE '%" + str(self.txtValor.text()) + "%'"
                                        if str(self.txtValor.text())=="":
                                            strSql = "SELECT Nodos.Geoname, Nodos.Nombre As Nombre, Elementos_Nodos.Descripcion As Elemento, obj.STEnvelope().ToString() FROM Elementos_Nodos RIGHT JOIN Nodos ON Elementos_Nodos.Id = Nodos.Elmt WHERE Nodos.elmt=4"
                                    else:
                                        if self.liwElementos.selectedItems()[0].text() == 'Nodo':
                                            if self.cmbCampos.currentText() == "Geoname":
                                                strSql = "SELECT Nodos.Geoname, Nodos.Nombre As Nombre, Elementos_Nodos.Descripcion As Elemento, obj.STEnvelope().ToString() FROM Elementos_Nodos RIGHT JOIN Nodos ON Elementos_Nodos.Id = Nodos.Elmt WHERE Nodos.Geoname = " + str(self.txtValor.text())
                                            if self.cmbCampos.currentText() == "Nombre":
                                                strSql = "SELECT TOP 300 Nodos.Geoname, Nodos.Nombre As Nombre, Elementos_Nodos.Descripcion As Elemento, obj.STEnvelope().ToString() FROM Elementos_Nodos RIGHT JOIN Nodos ON Elementos_Nodos.Id = Nodos.Elmt WHERE Nodos.Nombre LIKE '%" + str(self.txtValor.text()) + "%'"
                                            if self.cmbCampos.currentText() == "Descripción":
                                                strSql = "SELECT Nodos.Geoname, Nodos.Nombre As Nombre, Nodos.Descripcion As Descripción, obj.STEnvelope().ToString() FROM Nodos WHERE Nodos.Tension>0 AND Nodos.Descripcion LIKE '%" + str(self.txtValor.text()) + "%'"
                                            if str(self.txtValor.text())=="":
                                                strSql = "SELECT Nodos.Geoname, Nodos.Nombre As Nombre, Elementos_Nodos.Descripcion As Elemento, obj.STEnvelope().ToString() FROM Elementos_Nodos RIGHT JOIN Nodos ON Elementos_Nodos.Id = Nodos.Elmt"
                                        else:
                                            #busco en el ItemData
                                            item  = self.liwElementos.selectedItems()[0]
                                            itemdata = str(item.data(QtCore.Qt.ItemDataRole.UserRole))
                                            if self.cmbCampos.currentText() == "Geoname":
                                                strSql = "SELECT Nodos.Geoname, Nodos.Nombre As Nombre, Elementos_Nodos.Descripcion As Elemento, obj.STEnvelope().ToString() FROM Elementos_Nodos RIGHT JOIN Nodos ON Elementos_Nodos.Id = Nodos.Elmt WHERE Nodos.elmt=" + itemdata + " AND Nodos.Geoname = " + str(self.txtValor.text())
                                            if self.cmbCampos.currentText() == "Nombre":
                                                strSql = "SELECT TOP 300 Nodos.Geoname, Nodos.Nombre As Nombre, Elementos_Nodos.Descripcion As Elemento, obj.STEnvelope().ToString() FROM Elementos_Nodos RIGHT JOIN Nodos ON Elementos_Nodos.Id = Nodos.Elmt WHERE Nodos.elmt=" + itemdata + " AND Nodos.Nombre LIKE '%" + str(self.txtValor.text()) + "%'"
                                            if self.cmbCampos.currentText() == "Descripción":
                                                strSql = "SELECT Nodos.Geoname, Nodos.Nombre As Nombre, Nodos.Descripcion As Descripción, obj.STEnvelope().ToString() FROM Nodos WHERE Nodos.Tension>0 AND Nodos.elmt=" + itemdata + " AND Nodos.Descripcion LIKE '%" + str(self.txtValor.text()) + "%'"
                                            if str(self.txtValor.text())=="":
                                                strSql = "SELECT Nodos.Geoname, Nodos.Nombre As Nombre, Elementos_Nodos.Descripcion As Elemento, obj.STEnvelope().ToString() FROM Elementos_Nodos RIGHT JOIN Nodos ON Elementos_Nodos.Id = Nodos.Elmt WHERE Nodos.elmt=" + itemdata
        cnn = self.conn
        cursor = cnn.cursor()
        try:
            cursor.execute(strSql)
            #convierto el cursor en array
            encontrados = tuple(cursor)
            encabezado = [column[0] for column in cursor.description]
            cursor.close()
        except:
            QMessageBox.critical(None, 'EnerGis 6', "❌ Error en " + strSql)
            return

        self.tblResultado.setRowCount(0)
        if len(encontrados) > 0:
            self.tblResultado.setRowCount(len(encontrados))
            self.tblResultado.setColumnCount(len(encontrados[0]))
        for i in range (0, len(encontrados)):
            for j in range (len(encontrados[0])):
                item = QTableWidgetItem(str(encontrados[i][j]))
                self.tblResultado.setItem(i,j,item)
        self.tblResultado.setHorizontalHeaderLabels(encabezado)
        self.tblResultado.setColumnWidth(self.tblResultado.columnCount() - 1, 0)
    
    def elijo_item(self):
        geom = QgsGeometry.fromWkt(self.tblResultado.selectedItems()[3].text())
        box = geom.buffer(25,1).boundingBox()
        self.mapCanvas.setExtent(box)
        self.mapCanvas.refresh()
