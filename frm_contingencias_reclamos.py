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
from PyQt6.QtCore import QDate
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_contingencias_reclamos.ui'))

class frmContingenciasReclamos(DialogType, DialogBase):
        
    def __init__(self, tipo_usuario, conn, contingencia):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.conn = conn
        self.contingencia = contingencia

        if tipo_usuario==4:
            self.cmdAceptar.setEnabled(False)

        current_date = QDate.currentDate()
        self.datFecha.setDate(current_date)

        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT MIN(Importo_Operaciones.fechahora) AS fecha FROM Importo_Operaciones WHERE incorporada = 0 AND contingencia=" + str(contingencia))
        #convierto el cursor en array
        rs = tuple(cursor)
        cursor.close()

        if rs[0][0]!=None:
            self.datFecha.setDate(rs[0][0])

        self.lleno_tablas()

        self.datFecha.dateChanged.connect(self.lleno_tablas)
        self.cmdAgregar.clicked.connect(self.agregar)
        self.cmdQuitar.clicked.connect(self.quitar)
        self.cmdSalir.clicked.connect(self.salir)
        
    def lleno_tablas(self):
        cnn = self.conn
        try:
            cursor = cnn.cursor()
            cursor.execute("SELECT id, fecha, usuario, motivo_origen, zona, localidad, orden_atencion FROM VW_GISRECLAMOS WHERE id NOT IN (SELECT id_reclamo FROM Reclamos_Contingencias) AND fecha>='" + str(self.datFecha.date().toPyDate()).replace('-','') + "' AND  fecha<='" + str(self.datFecha.date().toPyDate()).replace('-','') + " 23:59' ORDER BY id")
            #convierto el cursor en array
            recordset = tuple(cursor)
            cursor.close()

            self.tbl1.setRowCount(len(recordset))
            self.tbl1.setColumnCount(7)
            self.tbl1.setHorizontalHeaderLabels(["id", "fecha", "usuario", "motivo","zona","localidad","oa"])

            self.tbl1.setColumnWidth(0, 50)
            self.tbl1.setColumnWidth(1, 120)
            self.tbl1.setColumnWidth(2, 60)
            self.tbl1.setColumnWidth(3, 150)
            self.tbl1.setColumnWidth(4, 70)
            self.tbl1.setColumnWidth(5, 100)
            self.tbl1.setColumnWidth(6, 50)

            for i in range (0, len(recordset)):
                for j in range (0, 5):
                    self.tbl1.setItem(i, j, QTableWidgetItem(str(recordset[i][j])))

            cnn = self.conn
            cursor = cnn.cursor()
            cursor.execute("SELECT id, fecha, usuario, motivo_origen, zona, localidad, orden_atencion FROM VW_GISRECLAMOS INNER JOIN Reclamos_Contingencias ON VW_GISRECLAMOS.id=Reclamos_Contingencias.id_reclamo WHERE id_contingencia=" + str(self.contingencia))
            #convierto el cursor en array
            recordset = tuple(cursor)
            cursor.close()

            self.tbl2.setRowCount(len(recordset))
            self.tbl2.setColumnCount(6)
            self.tbl2.setHorizontalHeaderLabels(["id", "fecha", "usuario", "motivo", "zona", "localidad", "oa"])

            self.tbl2.setColumnWidth(0, 50)
            self.tbl2.setColumnWidth(1, 120)
            self.tbl2.setColumnWidth(2, 60)
            self.tbl2.setColumnWidth(3, 150)
            self.tbl2.setColumnWidth(4, 70)
            self.tbl2.setColumnWidth(5, 100)
            self.tbl2.setColumnWidth(6, 50)

            for i in range (0, len(recordset)):
                for j in range (0, 5):
                    self.tbl2.setItem(i, j, QTableWidgetItem(str(recordset[i][j])))
        except:
            self.tbl2.setColumnCount(6)
            self.tbl2.setHorizontalHeaderLabels(["id", "fecha", "usuario", "motivo", "zona", "localidad", "oa"])

    def agregar(self):
        cnn = self.conn
        cursor = cnn.cursor()
        try:
            cursor.execute("INSERT INTO Reclamos_Contingencias (id_contingencia, id_reclamo) VALUES (" + str(self.contingencia) + "," + self.tbl1.item(self.tbl1.currentRow(),0).text() + ")")
            cnn.commit()
        except:
            QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo agregar !")
            cnn.rollback()

        self.lleno_tablas()

    def quitar(self):
        cnn = self.conn
        cursor = cnn.cursor()
        try:
            cursor.execute("DELETE FROM Reclamos_Contingencias WHERE id_contingencia=" +  str(self.contingencia) + " AND id_reclamo=" + self.tbl2.item(self.tbl2.currentRow(),0).text())
            cnn.commit()
        except:
            QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo quitar !")
            cnn.rollback()

        self.lleno_tablas()

    def salir(self):
        self.close()
