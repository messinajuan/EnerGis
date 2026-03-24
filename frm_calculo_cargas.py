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
import json
import tempfile
from datetime import datetime

from PyQt6.QtWidgets import QMessageBox
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_calculo_cargas.ui'))

class frmCalculoCargas(DialogType, DialogBase):

    def __init__(self, conn, funcion):
        super().__init__()
        self.setupUi(self)
        #self.setFixedSize(self.size())
        self.conn = conn
        self.funcion = funcion
        cursor = self.conn.cursor()
        cursor.execute("SELECT MIN(Desde) AS desde, MAX(Hasta) AS hasta FROM Energia_Facturada")
        #convierto el cursor en array
        energias = tuple(cursor)
        cursor.close()
        try:
            self.datDesde.setDate(energias[0][0])
            self.datHasta.setDate(energias[0][1])
        except:
            desde = datetime.strptime(energias[0][0], "%Y-%m-%d")
            hasta = datetime.strptime(energias[0][1], "%Y-%m-%d")
            self.datDesde.setDate(desde)
            self.datHasta.setDate(hasta)
        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)

    def aceptar (self):
        fecha_desde = self.datDesde.date().toPyDate()
        fecha_hasta = self.datHasta.date().toPyDate()
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM mNodos ORDER BY Aux")
        #convierto el cursor en array
        self.mnodos = tuple(cursor)
        cursor.close()
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM mLineas ORDER BY Aux")
        #convierto el cursor en array
        self.mlineas = tuple(cursor)
        cursor.close()
        listanodos = [list(nodo) for nodo in self.mnodos]
        jnodos = json.dumps(listanodos)
        with open(os.path.join(tempfile.gettempdir(), "jnodos"), "w") as a:
            a.write(jnodos)
        listalineas = [list(linea) for linea in self.mlineas]
        jlineas = json.dumps(listalineas)
        with open(os.path.join(tempfile.gettempdir(), "jlineas"), "w") as a:
            a.write(jlineas)
        cursor = self.conn.cursor()
        cursor.execute("SELECT MIN(Desde) AS desde, MAX(Hasta) AS hasta FROM Energia_Facturada WHERE Desde>='" + str(fecha_desde).replace('-','') + "' AND Hasta<='" + str(fecha_hasta).replace('-','') + "'")
        #convierto el cursor en array
        energias = tuple(cursor)
        cursor.close()
        if len(energias) < 1:
            QMessageBox.warning(None, 'EnerGis 6', '❌ No hay energías en el período seleccionado')
            return

        fc = self.txtFc.text()
        cursor = self.conn.cursor()
        cursor.execute("EXECUTE Crear_Cargas '0', " + str(fc) + ", 0.9, '" + str(fecha_desde).replace('-','') + "', '" + str(fecha_hasta).replace('-','') + "'")
        self.conn.commit()

        if self.chkPotencias.isChecked()==True:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE A SET d1=o, d2=o/2 FROM (SELECT CASE WHEN Pp > Pfp THEN Pp ELSE Pfp END AS o, Cargas.P AS d1, Cargas.Q AS d2 FROM (SELECT Id_Usuario, MAX(Pp) AS Pp, MAX(Pfp) AS Pfp FROM Energias_DPE WHERE Tarifa IN ('T3BT','T5BT','T3MT','T5MT') AND (Pp > 0) AND (Pfp > 0) AND CAST (Periodo + '01' AS DATE) >= '20250101' AND CAST (Periodo + '01' AS DATE) < '20251231' GROUP BY Id_Usuario) AS P INNER JOIN Cargas ON P.Id_Usuario = Cargas.Id_Usuario) A")
            self.conn.commit()

        if self.funcion==1: #analisis de carga
            from .frm_listados import frmListados
            str_sql = "SELECT Nodos.Nombre AS CT, Nodos.Val1 AS Potencia, COUNT(Usuarios.id_usuario) AS Usuarios, SUM(Cargas.EtF / Cargas.dias / 24 / " + str(fc) + ") AS Demanda FROM Suministros_Trafos INNER JOIN Nodos ON Suministros_Trafos.Geoname_t = Nodos.Geoname INNER JOIN Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro ON Suministros_Trafos.Geoname_s = Suministros.id_nodo INNER JOIN Cargas ON Usuarios.id_usuario = Cargas.Id_Usuario WHERE Nodos.Elmt = 4 AND Usuarios.ES = 1 GROUP BY Nodos.Nombre, Nodos.Val1"
            self.dialogo = frmListados(self.conn, str_sql)
            self.dialogo.show()
        if self.funcion==2: #cálculo de de cargas
            cursor = self.conn.cursor()
            cursor.execute("TRUNCATE TABLE Cargas_Nodos")
            self.conn.commit()
            #trafos
            try:
                cursor = self.conn.cursor()
                cursor.execute("INSERT INTO Cargas_Nodos SELECT Suministros_Trafos.Geoname_t AS Geoname, SUM(Cargas.P) AS P, SUM(Cargas.Q) AS Q, 1 AS Fe FROM Cargas INNER JOIN Usuarios ON Cargas.Id_Usuario = Usuarios.id_usuario INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro INNER JOIN Suministros_Trafos ON Suministros.id_nodo = Suministros_Trafos.Geoname_s WHERE Usuarios.ES = 1 GROUP BY Suministros_Trafos.Geoname_t")
                self.conn.commit()
            except:
                self.conn.rollback()
            #suministros
            try:
                cursor = self.conn.cursor()
                cursor.execute("INSERT INTO Cargas_Nodos SELECT Suministros.id_nodo AS Geoname, SUM(Cargas.P) AS P, SUM(Cargas.Q) AS Q, 1 AS Fe FROM Cargas INNER JOIN Usuarios ON Cargas.Id_Usuario = Usuarios.id_usuario INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro WHERE Usuarios.ES = 1 GROUP BY Suministros.id_nodo")
                self.conn.commit()
            except:
                self.conn.rollback()

        QMessageBox.information(None, 'EnerGis 6', 'ℹ️ Calculado !')

    def salir(self):
        self.close()
