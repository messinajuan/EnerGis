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
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem, QFileDialog
from qgis.core import QgsMapLayerType
from PyQt6 import uic
import pyodbc

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_sql.ui'))

class frmSql(DialogType, DialogBase):

    def __init__(self, mapCanvas, conn):
        super().__init__()
        self.setupUi(self)
        #self.setFixedSize(self.size())
        self.mapCanvas = mapCanvas
        self.conn=conn
        self.cmdVerificar.clicked.connect(self.verificar)
        self.cmdEjecutar.clicked.connect(self.ejecutar)
        self.cmdExportar.clicked.connect(self.exportar)
        self.cmdSalir.clicked.connect(self.salir)
        pass

    def verificar(self):
        self.tabWidget.setCurrentIndex(0)
        if self.txtSql.toPlainText().strip()=='':
            return
        self.tblResultado.setRowCount(0)
        self.txtProceso.append("\n" + "\n" + self.txtSql.toPlainText())
        try:
            cursor = self.conn.cursor()
            cursor.execute(self.txtSql.toPlainText())
            if self.txtSql.toPlainText().strip().upper()[:6]=='SELECT':
                #convierto el cursor en array
                sql = tuple(cursor)
                cursor.close()
                self.txtProceso.append("\n" + "\n" + "(" + str(len(sql)) + " filas afectadas)")
            else:
                self.txtProceso.append("\n" + "\n" + "(" + str(cursor.rowcount) + " filas afectadas)")
                self.conn.rollback()
        except pyodbc.Error as err:
            self.txtProceso.append("\n" + "\n" + str(err))
            self.tabWidget.setCurrentIndex(0)
        pass

    def ejecutar(self):
        self.tabWidget.setCurrentIndex(0)
        if self.txtSql.toPlainText().strip()=='':
            return
        cursor = self.conn.cursor()
        try:
            cursor.execute(self.txtSql.toPlainText().strip())
            if self.txtSql.toPlainText().strip().upper()[:6]=='SELECT':
                if self.txtSql.toPlainText().upper().find(" INTO ")>0:
                    mensaje = "Este comando creará una nueva tabla en la Base de Datos. Desea continuar ❓"
                    reply = QMessageBox.question(None, 'EnerGis', mensaje, QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
                    if reply == QMessageBox.StandardButton.No:
                        self.txtProceso.append("\n" + "\n" + "cancelado (sin filas afectadas)")
                        return

                #convierto el cursor en array
                elementos = tuple(cursor)
                seleccion = []
                descripcion_columnas = cursor.description
                # Iterar a través de la descripción de las columnas
                i_campo=-1
                i_geoname=-1
                i=0
                for columna in descripcion_columnas:
                    campo = columna[0]  # El primer elemento contiene el nombre de la columna
                    #formato = columna[1] # El segundo elemento tiene el data type code: 1 para tipos de datos numéricos enteros (integers). 12 para tipos de datos de cadena (strings). 91 para tipos de datos de fecha (date). 93 para tipos de datos de fecha y hora (datetime).
                    if campo.lower()=="obj":
                        i_campo=i
                    if campo.lower()=="geoname":
                        i_geoname=i
                    i=i+1
                for elemento in range(0, len(elementos)):
                    if i_campo>=0 and i_geoname>=0:
                        if elementos[elemento][i_geoname]!=None:
                            seleccion.append(elementos[elemento][i_geoname])

                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                if len(elementos)>-1:
                    self.txtProceso.append("\n" + "\n" + "(" + str(len(elementos)) + " filas afectadas)")
                else:
                    self.txtProceso.append("\n" + "\n" + "(comando ejecutado)")

                self.lleno_grilla(encabezado, elementos)
                self.tabWidget.setCurrentIndex(1)

                n = self.mapCanvas().layerCount()
                layers = [self.mapCanvas().layer(i) for i in range(n)]
                for lyr in layers:
                    if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                        lyr.removeSelection()
                    if lyr.name()[:5] == 'Nodos':
                        lyr.select(seleccion)
                        if len(lyr.selectedFeatures())>0:
                            self.txtProceso.append("\n" + "\n" + "(" + str(len(lyr.selectedFeatures())) + " nodos seleccionados en la capa " + lyr.name())
                    if lyr.name()[:6] == 'Lineas':
                        lyr.select(seleccion)
                        if len(lyr.selectedFeatures())>0:
                            self.txtProceso.append("\n" + "\n" + "(" + str(len(lyr.selectedFeatures())) + " líneas seleccionadas en la capa " + lyr.name())
                    if lyr.name()[:6] == 'Postes':
                        lyr.select(seleccion)
                        if len(lyr.selectedFeatures())>0:
                            self.txtProceso.append("\n" + "\n" + "(" + str(len(lyr.selectedFeatures())) + " postes seleccionados en la capa " + lyr.name())
            else:

                if self.txtSql.toPlainText().strip().upper()[:6]=='INSERT':
                    mensaje = "Este comando insertará registros en la Base de Datos. Desea continuar ❓"
                if self.txtSql.toPlainText().strip().upper()[:6]=='UPDATE':
                    mensaje = "Este comando actualizará registros en la Base de Datos. Desea continuar ❓"
                if self.txtSql.toPlainText().strip().upper()[:6]=='DELETE':
                    mensaje = "Este comando borrará registros en la Base de Datos. Desea continuar ❓"
                if self.txtSql.toPlainText().strip().upper()[:8]=='TRUNCATE':
                    mensaje = "Este comando borrará registros en la Base de Datos. Desea continuar ❓"
                if self.txtSql.toPlainText().strip().upper()[:4]=='DROP':
                    mensaje = "Este comando borrará elementos de la Base de Datos. Desea continuar ❓"

                reply = QMessageBox.question(None, 'EnerGis', mensaje, QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.No:
                    self.txtProceso.append("\n" + "\n" + "cancelado (sin filas afectadas)")
                    return

                if cursor.rowcount>-1:
                    self.txtProceso.append("\n" + "\n" + "(" + str(cursor.rowcount) + " filas afectadas)")
                else:
                    self.txtProceso.append("\n" + "\n" + "(comando ejecutado)")

                self.conn.commit()
        except pyodbc.Error as err:
            self.txtProceso.append("\n" + "\n" + str(err))
            self.conn.rollback()
            self.tabWidget.setCurrentIndex(0)

    def lleno_grilla(self, encabezado, elementos):
        self.tblResultado.setRowCount(0)
        if len(elementos) > 0:
            self.tblResultado.setRowCount(len(elementos))
            self.tblResultado.setColumnCount(len(elementos[0]))
        for i in range (0, len(elementos)):
            for j in range (len(elementos[0])):
                item = QTableWidgetItem(str(elementos[i][j]))
                self.tblResultado.setItem(i,j,item)
        self.tblResultado.setHorizontalHeaderLabels(encabezado)
        pass

    def exportar(self):
        #pip install xlwt
        import xlwt
        if self.tblResultado.rowCount()==0:
            return
        filename = QFileDialog.getSaveFileName(self, 'Guardar Archivo', '', ".xls(*.xls)")
        if filename[0]=='' or filename[1]=='':
            return
        wbk = xlwt.Workbook()
        sheet = wbk.add_sheet("sheet", cell_overwrite_ok=True)
        for currentColumn in range(self.tblResultado.columnCount()):
            for currentRow in range(self.tblResultado.rowCount()):
                teext = str(self.tblResultado.item(currentRow, currentColumn).text())
                sheet.write(currentRow, currentColumn, teext)
        wbk.save(filename[0])
        QMessageBox.information(None, 'EnerGis 6', 'ℹ️ Exportado !')

    def salir(self):
        self.close()
