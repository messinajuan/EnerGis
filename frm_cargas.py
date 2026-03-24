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
from datetime import datetime
from PyQt6.QtWidgets import QMessageBox
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_cargas.ui'))

class frmCargas(DialogType, DialogBase):

    def __init__(self, conn, geoname, elmt):
        super().__init__()
        self.setupUi(self)
        #self.setFixedSize(self.size())
        self.conn = conn
        self.geoname = geoname
        self.elmt = elmt

        cursor = self.conn.cursor()
        cursor.execute("SELECT MIN(Desde) AS desde, MAX(Hasta) AS hasta FROM Energia_Facturada")
        #convierto el cursor en array
        energias = tuple(cursor)
        cursor.close()
        if len(energias)>0:
            try:
                self.datDesde.setDate(energias[0][0])
                self.datHasta.setDate(energias[0][1])
            except:
                desde = datetime.strptime(energias[0][0], "%Y-%m-%d")
                hasta = datetime.strptime(energias[0][1], "%Y-%m-%d")
                self.datDesde.setDate(desde)
                self.datHasta.setDate(hasta)

        cursor = self.conn.cursor()
        cursor.execute("SELECT P, Q, Fe FROM Cargas_Nodos WHERE geoname=" + str(self.geoname))
        #convierto el cursor en array
        cargas = tuple(cursor)
        cursor.close()
        if len(cargas)>0:
            self.txtP.setText(str(format(cargas[0][0], ",.4f")).replace(',','').rstrip('0').rstrip('.'))
            self.txtQ.setText(str(format(cargas[0][1], ",.4f")).replace(',','').rstrip('0').rstrip('.'))
            self.txtFe.setText(str(format(cargas[0][2], ",.4f")).replace(',','').rstrip('0').rstrip('.'))

        self.cmdCalcular.clicked.connect(self.calcular)
        self.cmdPasar.clicked.connect(self.pasar_valores)
        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)

    def calcular (self):
        fecha_desde = self.datDesde.date().toPyDate()
        fecha_hasta = self.datHasta.date().toPyDate()
        fc = self.txtFc.text()
        fp = self.txtFp.text()
        cursor = self.conn.cursor()
        cursor.execute("SELECT MIN(Desde) AS desde, MAX(Hasta) AS hasta FROM Energia_Facturada WHERE Desde>='" + str(fecha_desde).replace('-','') + "' AND Hasta<='" + str(fecha_hasta).replace('-','') + "'")
        #convierto el cursor en array
        energias = tuple(cursor)
        cursor.close()
        if len(energias) < 1:
            QMessageBox.warning(None, 'EnerGis 6', '❌ No hay energías en el período seleccionado')
            return

        if self.elmt == 4:
            #armo la lista de usuarios del trafo
            cursor = self.conn.cursor()
            cursor.execute("SELECT Usuarios.id_usuario FROM Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro INNER JOIN Suministros_Trafos ON Suministros.id_nodo = Suministros_Trafos.Geoname_s WHERE Usuarios.ES = 1 AND Suministros_Trafos.Geoname_t=" + str(self.geoname))
            usuarios = tuple(cursor)
            cursor.close()
            str_lista = '0'
            for n in range (0, len(usuarios)):
                str_lista = str_lista + ',' + str(usuarios[n][0])

        if self.elmt == 6:
            #armo la lista de usuarios del suministro
            cursor = self.conn.cursor()
            cursor.execute("SELECT Usuarios.id_usuario FROM Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro WHERE Usuarios.ES=1 AND Suministros.id_nodo=" + str(self.geoname))
            usuarios = tuple(cursor)
            cursor.close()
            str_lista = '0'
            for n in range (0, len(usuarios)):
                str_lista = str_lista + ',' + str(usuarios[n][0])

        cursor = self.conn.cursor()
        cursor.execute("EXECUTE Crear_Cargas '" + str_lista + "', " + str(fc) + ", " + str(fp) + ", '" + str(fecha_desde).replace('-','') + "', '" + str(fecha_hasta).replace('-','') + "'")
        self.conn.commit()

        cursor = self.conn.cursor()
        cursor.execute("SELECT SUM(P) AS P, SUM(Q) AS Q FROM Cargas WHERE Id_Usuario IN (" + str_lista + ")")
        cargas = tuple(cursor)
        cursor.close()

        try:
            self.txtPcalculo.setText(str(format(cargas[0][0], ",.4f")).replace(',','').rstrip('0').rstrip('.'))
            self.txtQcalculo.setText(str(format(cargas[0][1], ",.4f")).replace(',','').rstrip('0').rstrip('.'))
        except:
            self.txtPcalculo.setText('0')
            self.txtQcalculo.setText('0')

    def pasar_valores(self):
        self.txtP.setText(self.txtPcalculo.text())
        self.txtQ.setText(self.txtQcalculo.text())

    def aceptar(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO Cargas_Nodos (geoname, P, Q, Fe) VALUES (" + str(self.geoname) + ", " + self.txtP.text() + ", " + self.txtQ.text() + ", " + self.txtFe.text() + ")")
            self.conn.commit()
        except:
            self.conn.rollback()
            try:
                cursor = self.conn.cursor()
                cursor.execute("UPDATE Cargas_Nodos SET P=" + self.txtP.text() + ", Q=" + self.txtQ.text() + ", Fe=" + self.txtFe.text() + " WHERE geoname =" + str(self.geoname))
                self.conn.commit()
            except:
                self.conn.rollback()
                QMessageBox.critical(None, 'Mensaje', '❌ Error al guardar')
        self.close()

    def salir(self):
        self.close()
