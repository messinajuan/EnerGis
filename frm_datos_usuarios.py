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
#from PyQt6 import QtCore
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem
from PyQt6.QtGui import QColor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_datos_usuarios.ui'))

class frmDatosUsuarios(DialogType, DialogBase):

    def __init__(self, conn, id):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.conn = conn
        self.cmbProsumidor.addItem('')
        self.cmbProsumidor.addItem('Biomasa')
        self.cmbProsumidor.addItem('Eólica')
        self.cmbProsumidor.addItem('Solar')
        self.cmbProsumidor.addItem('Otro')
        self.figure = plt.Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.ax = self.figure.add_subplot(111) #111 para un unico grafico
        self.cmdBuscar.clicked.connect(self.buscar)
        self.tableWidget.itemClicked.connect(self.elijo_usuario)
        if id!=0:
            self.txtBusqueda.setText(str(id))
            self.buscar()
            self.tableWidget.setCurrentCell(0,0)
            self.elijo_usuario()

    def buscar(self):
        busqueda = self.txtBusqueda.text()
        cnn = self.conn
        cursor = cnn.cursor()
        if busqueda.isnumeric()==False:
            id=0
        else:
            id=int(busqueda)
        cursor.execute("SELECT id_usuario, Nombre, ES, Electrodependiente, Prosumidor FROM Usuarios WHERE id_usuario='" + str(id) + "' OR nombre LIKE '%" + busqueda + "%'")
        #convierto el cursor en array
        recordset = tuple(cursor)
        cursor.close()
        self.tableWidget.setRowCount(len(recordset))
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setHorizontalHeaderLabels(["Id", "Nombre"])
        self.tableWidget.setColumnWidth(0, 70)
        self.tableWidget.setColumnWidth(1, 250)
        for i in range (0, len(recordset)):
            self.tableWidget.setItem(i, 0, QTableWidgetItem(str(recordset[i][0])))
            self.tableWidget.setItem(i, 1, QTableWidgetItem(str(recordset[i][1])))
            if recordset[i][2]!=1:
                self.tableWidget.item(i, 0).setBackground(QColor(211, 211, 211))
                self.tableWidget.item(i, 1).setBackground(QColor(211, 211, 211))
            else:
                if recordset[i][3]=='S':
                    self.tableWidget.item(i, 0).setBackground(QColor(250, 100, 100))
                    self.tableWidget.item(i, 1).setBackground(QColor(250, 100, 100))
                else:
                    if recordset[i][4]!='':
                        self.tableWidget.item(i, 0).setBackground(QColor(255, 255, 155))
                        self.tableWidget.item(i, 1).setBackground(QColor(255, 255, 155))

    def elijo_usuario(self):
        cnn = self.conn
        try:
            usuario = self.tableWidget.item(self.tableWidget.currentRow(),0).text()
            self.txtId.setText(str(usuario))
            cursor = cnn.cursor()
            cursor.execute("SELECT tarifa, id_suministro, calle, altura, zona, es, electrodependiente, fae, prosumidor FROM usuarios WHERE id_usuario=" + str(usuario))
            #convierto el cursor en array
            recordset = tuple(cursor)
            cursor.close()
            self.txtTarifa.setText(recordset[0][0])
            self.txtSuministro.setText(recordset[0][1])
            self.txtDireccion.setText(recordset[0][2] + ' ' + recordset[0][3] + ' ' + recordset[0][4])
            if recordset[0][5] == 1:
                self.chkEs.setChecked(True)
            else:
                self.chkEs.setChecked(False)
            if recordset[0][6] == "S":
                self.chkElectrodependiente.setChecked(True)
            else:
                self.chkElectrodependiente.setChecked(False)
            if recordset[0][7] == "S":
                self.chkFae.setChecked(True)
            else:
                self.chkFae.setChecked(False)
            prosumidor = recordset[0][8][:20].strip()
            for i in range (0, self.cmbProsumidor.count()):
                if self.cmbProsumidor.itemText(i) == prosumidor:
                    self.cmbProsumidor.setCurrentIndex(i)
            i = len(recordset[0][8])-20
            self.txtPotencia.setText(recordset[0][8][-i:].strip())
            cursor = cnn.cursor()
            cursor.execute("SELECT DNI, nro_medidor FROM VW_CCDATOSCOMERCIALES WHERE id_usuario=" + str(usuario))
            #convierto el cursor en array
            recordset = tuple(cursor)
            cursor.close()
            self.txtDocumento.setText(str(recordset[0][0]))
            self.txtMedidor.setText(str(recordset[0][1]))
            cursor = cnn.cursor()
            cursor.execute("SELECT geoname, Alimentador FROM Nodos LEFT JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo WHERE Suministros.id_suministro='"  + self.txtSuministro.text() + "'")
            #convierto el cursor en array
            recordset = tuple(cursor)
            cursor.close()
            geoname = recordset[0][0]
            self.txtSalida.setText(recordset[0][1])
            cursor = cnn.cursor()
            cursor.execute("SELECT nombre, alimentador FROM suministros_trafos INNER JOIN Nodos ON suministros_trafos.Geoname_t = Nodos.Geoname WHERE Nodos.Elmt=4 AND suministros_trafos.Geoname_s=" + str(geoname))
            #convierto el cursor en array
            recordset = tuple(cursor)
            cursor.close()
            self.txtCT.setText(recordset[0][0])
            self.txtAlimentador.setText(recordset[0][1])
            self.grafico.addWidget(self.canvas)
            self.plot_bar_chart(usuario)
        except:
            pass

    def plot_bar_chart(self, usuario):
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT Periodo, Etf FROM (SELECT TOP 12 Periodo, Etf FROM Energia_Facturada WHERE id_usuario = " + str(usuario) + " ORDER BY Periodo DESC) E ORDER BY Periodo")
        #convierto el cursor en array
        energias = tuple(cursor)
        cursor.close()
        # Convertir el recordset en una lista de diccionarios
        data_diccionario = {}
        for e in energias:
            periodo, etf = e
            data_diccionario[periodo] = etf
        self.ax.clear()
        self.ax.bar(data_diccionario.keys(), data_diccionario.values())
        self.ax.set_xlabel('Período')
        self.ax.set_ylabel('kWh')
        self.ax.set_title('Consumos')
        # Ajustar el tamaño del cuerpo del gráfico para mostrar las etiquetas del eje inferior
        plt.subplots_adjust(bottom=0.2)
        self.canvas.draw()
