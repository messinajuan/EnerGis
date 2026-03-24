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
from PyQt6 import uic
from PyQt6.QtGui import QColor


DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_listados.ui'))

class frmListados(DialogType, DialogBase):

    def __init__(self, conn, str_sql):
        super().__init__()
        self.setupUi(self)
        self.conn = conn
        self.str_sql = str_sql
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute(str_sql)
        #convierto el cursor en array
        elementos = tuple(cursor)
        encabezado = [column[0] for column in cursor.description]
        cursor.close()
        self.lleno_grilla(encabezado, elementos)
        self.cmdExportar.clicked.connect(self.exportar)
        self.cmdSalir.clicked.connect(self.salir)
        #self.tblListado.cellDoubleClicked.connect(self.ordenar)

    def lleno_grilla(self, encabezado, elementos):
        self.tblListado.setRowCount(0)
        if len(elementos) > 0:
            self.tblListado.setRowCount(len(elementos))
            self.tblListado.setColumnCount(len(elementos[0]))
        for i in range (0, len(elementos)):
            for j in range (0, len(elementos[0])):
                item = QTableWidgetItem(str(elementos[i][j]))
                self.tblListado.setItem(i,j,item)
                if str(elementos[i][j])=='None':
                    self.tblListado.item(i, j).setBackground(QColor(225, 225, 100)) #100,100,150
        self.tblListado.setHorizontalHeaderLabels(encabezado)

    #def ordenar(self):
    #    self.tblListado.sortItems(self.tblListado.currentColumn(), QtCore.Qt.AscendingOrder)

    def exportar(self):
        #pip install xlwt
        import xlwt
        if self.tblListado.rowCount()==0:
            return
        filename = QFileDialog.getSaveFileName(self, 'Guardar Archivo', '', ".xls(*.xls)")
        if filename[0]=='' or filename[1]=='':
            return
        wbk = xlwt.Workbook()
        sheet = wbk.add_sheet("listado", cell_overwrite_ok=True)
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
        pass
