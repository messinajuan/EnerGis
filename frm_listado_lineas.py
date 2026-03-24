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
from PyQt6.QtWidgets import QTableWidgetItem, QFileDialog
from PyQt6.QtWidgets import QMessageBox
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_listado_lineas.ui'))

class frmListadoLineas(DialogType, DialogBase):

    def __init__(self, conn):
        super().__init__()
        self.setupUi(self)

        self.setFixedSize(self.size())
        self.conn = conn
        
        self.cmbTension.addItem ("Todos")
        self.cmbTension.addItem ("AT")
        self.cmbTension.addItem ("MT")
        self.cmbTension.addItem ("BT")

        self.cmbAgrupar1.addItem ("")
        self.cmbAgrupar1.addItem ("Descripción")
        self.cmbAgrupar1.addItem ("Fase")
        self.cmbAgrupar1.addItem ("Tensión")
        self.cmbAgrupar1.addItem ("Zona")
        self.cmbAgrupar1.addItem ("Alimentador")
        self.cmbAgrupar1.addItem ("Sección")
        self.cmbAgrupar1.addItem ("Tipo")
        self.cmbAgrupar1.addItem ("Material")

        self.cmbAgrupar2.addItem ("")
        self.cmbAgrupar2.addItem ("Descripción")
        self.cmbAgrupar2.addItem ("Fase")
        self.cmbAgrupar2.addItem ("Tensión")
        self.cmbAgrupar2.addItem ("Zona")
        self.cmbAgrupar2.addItem ("Alimentador")
        self.cmbAgrupar2.addItem ("Sección")
        self.cmbAgrupar2.addItem ("Tipo")
        self.cmbAgrupar2.addItem ("Material")

        self.cmbTension.currentIndexChanged.connect(self.elijo_tension)
        self.cmbAgrupar1.currentIndexChanged.connect(self.elijo_agrupamiento1)
        self.cmbAgrupar2.currentIndexChanged.connect(self.elijo_agrupamiento2)

        self.cmdExportar.clicked.connect(self.exportar)
        self.cmdSalir.clicked.connect(self.salir)

    def elijo_tension(self):
        self.acltualizar_lista()

    def elijo_agrupamiento1(self):
        #self.cmbAgrupar2.clear()
        #for i in range (0, self.cmbAgrupar1.count()):
        #    if self.cmbAgrupar1.currentText() != self.cmbAgrupar1.itemText(i):
        #        self.cmbAgrupar2.addItem (self.cmbAgrupar1.itemText(i))
        self.acltualizar_lista()

    def elijo_agrupamiento2(self):
        self.acltualizar_lista()

    def acltualizar_lista(self):
        if self.cmbTension.currentText()=='Todos':
            minV='50'
            maxV='1000000'
        if self.cmbTension.currentText()=='AT':
            minV='50001'
            maxV='1000000'
        if self.cmbTension.currentText()=='MT':
            minV='1001'
            maxV='50000'
        if self.cmbTension.currentText()=='BT':
            minV='50'
            maxV='1000'

        if self.cmbAgrupar1.currentText() != "" and self.cmbAgrupar2.currentText() != "":
            str_sql = "SELECT " + self.cmbAgrupar1.currentText() + "," + self.cmbAgrupar2.currentText() + ", ROUND(Sum(longitud/1000),3) As Longitud FROM (SELECT Elementos_Lineas.Descripcion As [Descripción], Lineas.Fase As [Fase], Lineas.Tension As [Tensión], Lineas.Zona As [Zona], Lineas.Alimentador As [Alimentador], Elementos_Lineas.Val2 As [Sección], Elementos_Lineas.Val8 As [Tipo], Elementos_Lineas.Val9 As [Material], Lineas.Longitud As [Longitud] FROM Lineas INNER JOIN Elementos_Lineas ON Lineas.Elmt = Elementos_Lineas.Id WHERE Tension>50) C WHERE [Tensión]>=" + minV + " AND [Tensión] <=" + maxV + " GROUP BY [" + self.cmbAgrupar1.currentText() + "],[" + self.cmbAgrupar2.currentText() + "]"

        if self.cmbAgrupar1.currentText() != "" and self.cmbAgrupar2.currentText() == "":
            str_sql = "SELECT " + self.cmbAgrupar1.currentText() + ", ROUND(Sum(longitud/1000),3) As Longitud FROM (SELECT Elementos_Lineas.Descripcion As [Descripción], Lineas.Fase As [Fase], Lineas.Tension As [Tensión], Lineas.Zona As [Zona], Lineas.Alimentador As [Alimentador], Elementos_Lineas.Val2 As [Sección], Elementos_Lineas.Val8 As [Tipo], Elementos_Lineas.Val9 As [Material], Lineas.Longitud As [Longitud] FROM Lineas INNER JOIN Elementos_Lineas ON Lineas.Elmt = Elementos_Lineas.Id WHERE Tension>50) C WHERE [Tensión]>=" + minV + " AND [Tensión] <=" + maxV + " GROUP BY [" + self.cmbAgrupar1.currentText() + "]"

        if self.cmbAgrupar1.currentText() == "" and self.cmbAgrupar2.currentText() == "":
            str_sql = "SELECT ROUND(Sum(longitud/1000),3) As Longitud FROM (SELECT Elementos_Lineas.Descripcion As [Descripción], Lineas.Fase As [Fase], Lineas.Tension As [Tensión], Lineas.Zona As [Zona], Lineas.Alimentador As [Alimentador], Elementos_Lineas.Val2 As [Sección], Elementos_Lineas.Val8 As [Tipo], Elementos_Lineas.Val9 As [Material], Lineas.Longitud As [Longitud] FROM Lineas INNER JOIN Elementos_Lineas ON Lineas.Elmt = Elementos_Lineas.Id WHERE Tension>50) C WHERE [Tensión]>=" + minV + " AND [Tensión] <=" + maxV

        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute(str_sql)
        #convierto el cursor en array
        encontrados = tuple(cursor)
        encabezado = [column[0] for column in cursor.description]
        cursor.close()
        self.tblListado.setRowCount(0)
        if len(encontrados) > 0:
            self.tblListado.setRowCount(len(encontrados))
            self.tblListado.setColumnCount(len(encontrados[0]))
        total=0
        try:
            for i in range (0, len(encontrados)):
                total=total+encontrados[i][len(encontrados[0])-1]
                for j in range (0, len(encontrados[0])):
                    item = QTableWidgetItem(str(encontrados[i][j]))
                    self.tblListado.setItem(i,j,item)
        except:
            pass

        self.txtLongitud.setText(str(format(total, ",.2f")))
        self.tblListado.setHorizontalHeaderLabels(encabezado)
        #self.tblListado.setColumnWidth(self.tblListado.columnCount() - 1, 0)

    def exportar(self):
        #pip install xlwt
        import xlwt
        if self.tblListado.rowCount()==0:
            return

        filename = QFileDialog.getSaveFileName(self, 'Guardar Archivo', '', ".xls(*.xls)")

        if filename[0]=='' or filename[1]=='':
            return

        wbk = xlwt.Workbook()
        sheet = wbk.add_sheet("lineas", cell_overwrite_ok=True)

        for currentColumn in range(self.tblListado.columnCount()):
            teext = self.tblListado.horizontalHeaderItem(currentColumn).text()
            sheet.write(0, currentColumn, teext)

        for currentColumn in range(self.tblListado.columnCount()):
            for currentRow in range(self.tblListado.rowCount()):
                teext = str(self.tblListado.item(currentRow, currentColumn).text())
                sheet.write(currentRow + 1, currentColumn, teext)
        wbk.save(filename[0])

        QMessageBox.information(None, 'EnerGis 6', 'ℹ️ Exportado !')

    def salir(self):
        self.close()
