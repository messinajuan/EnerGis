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

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_resumen_sistema.ui'))

class frmResumenSistema(DialogType, DialogBase):

    def __init__(self, conn):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.conn = conn
        
        str_resumen = "Fuentes de Energía" + "\n"
        cnn = self.conn
        #--------------------
        cursor = cnn.cursor()
        cursor.execute("SELECT Tension, COUNT(*) FROM Nodos WHERE elmt=1 GROUP BY Tension HAVING Tension>0")
        #convierto el cursor en array
        rst = tuple(cursor)
        cursor.close()
        for rs in rst:
            str_resumen = str_resumen + str(rs[1]) + " Fuentes de " +  str(rs[0]) + "\n"
        #--------------------
        cursor = cnn.cursor()
        cursor.execute("SELECT Val4 FROM Nodos WHERE elmt=11")
        #convierto el cursor en array
        rst = tuple(cursor)
        cursor.close()
        cant = 0
        pot = 0
        for rs in rst:
            cant = cant + 1
            pot = pot + float(rs[0].split('|')[2])
        if cant>0:
            str_resumen = str_resumen + "Generación " + str(cant) + " Equipos, Total " + str(pot) + " kW" +"\n"

        str_resumen = str_resumen + "\n"
        str_resumen = str_resumen + "Potencia Instalada" + "\n"
        cnn = self.conn
        #--------------------
        cursor = cnn.cursor()
        cursor.execute("SELECT SUM(Potencia)/1000, count(*) FROM Transformadores INNER JOIN Nodos ON Transformadores.Id_ct=Nodos.Nombre WHERE Tension>0 AND elmt=4 AND (Tension_1 >= 50000 OR Tension_2 >= 50000)")
        #convierto el cursor en array
        rst = tuple(cursor)
        cursor.close()
        if rst[0][0]!=None:
            str_resumen = str_resumen + str(rst[0][1]) + " Transformadores de Potencia : " + str(rst[0][0]) + " MVA" + "\n"
        #--------------------
        cursor = cnn.cursor()
        cursor.execute("SELECT SUM(Potencia)/1000, count(*) FROM Transformadores INNER JOIN Nodos ON Transformadores.Id_ct=Nodos.Nombre WHERE Tension>0 AND elmt=4 AND (Tension_1 < 1000 OR Tension_2 < 1000)")
        #convierto el cursor en array
        rst = tuple(cursor)
        cursor.close()
        if rst[0][0]!=None:
            str_resumen = str_resumen + str(rst[0][1]) + " Transformadores de Distribución : " + str(rst[0][0]) + " MVA" + "\n"
        #--------------------
        cursor = cnn.cursor()
        cursor.execute("SELECT SUM(Potencia)/1000, count(*) FROM Transformadores INNER JOIN Nodos ON Transformadores.Id_ct=Nodos.Nombre WHERE Tension>0 AND elmt=4 AND Tension_1 >= 1000 AND Tension_2 >= 1000 AND Tension_1 < 50000 AND Tension_2 < 50000")
        #convierto el cursor en array
        rst = tuple(cursor)
        cursor.close()
        if rst[0][0]!=None:
            str_resumen = str_resumen + str(rst[0][1])  + " Transformadores de Rebaje : " + str(rst[0][0]) + " MVA" + "\n"
        #--------------------
        cursor = cnn.cursor()
        cursor.execute("SELECT COUNT(*), SUM(CAST (Val1 AS FLOAT)) FROM Nodos WHERE Tension>0 AND elmt=9")
        #convierto el cursor en array
        rst = tuple(cursor)
        cursor.close()
        if rst[0][0]>0:
            str_resumen = str_resumen + str(rst[0][0]) + " Reguladores Total : " +  str(rst[0][1]) + " kVA" + "\n"
        #--------------------
        cursor = cnn.cursor()
        cursor.execute("SELECT COUNT(*), SUM(CAST (Val1 AS FLOAT)) FROM Nodos WHERE Tension>0 AND elmt=7")
        #convierto el cursor en array
        rs = tuple(cursor)
        cursor.close()
        if rst[0][0]>0:
            str_resumen = str_resumen + str(rst[0][0]) + " Capacitores Total : " +  str(rst[0][1]) + " kVA" + "\n"

        str_resumen = str_resumen + "\n"
        str_resumen = str_resumen + "Líneas Eléctricas" + "\n"
        cnn = self.conn
        #--------------------
        cursor = cnn.cursor()
        cursor.execute("SELECT Tension, ROUND(SUM(longitud)/1000,2) FROM Lineas WHERE Tension>0 GROUP BY Tension ORDER BY Tension DESC")
        #convierto el cursor en array
        rst = tuple(cursor)
        cursor.close()
        for rs in rst:
            str_resumen = str_resumen + str(rs[1]) + " km de " + str(rs[0]/1000) + " kV" + "\n"

        str_resumen = str_resumen + "\n"
        str_resumen = str_resumen + "Elementos de Maniobra" + "\n"
        cnn = self.conn
        #--------------------
        cursor = cnn.cursor()
        cursor.execute("SELECT Val1, Tension, COUNT(*) FROM Nodos WHERE Elmt IN (2, 3) GROUP BY Val1, Tension ORDER BY Tension, Val1")
        #convierto el cursor en array
        rst = tuple(cursor)
        cursor.close()
        for rs in rst:
            str_resumen = str_resumen + str(rs[2]) + " " + rs[0] + " de " + str(rs[1]/1000) + " kV" + "\n"

        str_resumen = str_resumen + "\n"
        str_resumen = str_resumen + "Descargadores" + "\n"
        cnn = self.conn
        #--------------------
        cursor = cnn.cursor()
        cursor.execute("SELECT Tension, SUM(D) FROM (SELECT Nodos.Tension, SUM(len(CAST(mNodos.fases AS VARCHAR))) AS D FROM Nodos INNER JOIN mNodos ON Nodos.Geoname = mNodos.geoname WHERE (Nodos.Elmt IN (2, 3)) AND (Nodos.Val4 = 'Aereo-Subt') GROUP BY Nodos.Tension UNION SELECT Nodos.Tension, SUM(Ct.descargadores*len(CAST(mNodos.fases AS VARCHAR))) AS D FROM mNodos INNER JOIN Nodos ON mNodos.geoname = Nodos.Geoname INNER JOIN Ct ON Nodos.Nombre = Ct.Id_ct WHERE (Nodos.Elmt = 4) GROUP BY Nodos.Tension UNION SELECT Tension, SUM(descargadores*3) AS D FROM Postes WHERE descargadores>0 GROUP BY Tension) A GROUP BY A.Tension HAVING A.Tension>0")
        #convierto el cursor en array
        rst = tuple(cursor)
        cursor.close()
        for rs in rst:
            if rs[1]>0:
                str_resumen = str_resumen + str(rs[1]) + " Descargadores de " + str(rs[0]/1000) + " kV" + "\n"

        str_resumen = str_resumen + "\n"
        str_resumen = str_resumen + "Soportes" + "\n"
        cnn = self.conn
        #--------------------
        cursor = cnn.cursor()
        cursor.execute("SELECT Tension, Elementos_Postes.Descripcion, COUNT(*) FROM Postes INNER JOIN Elementos_Postes ON Postes.elmt=Elementos_Postes.Id GROUP BY Tension, Elementos_Postes.Descripcion HAVING Tension>0")
        #convierto el cursor en array
        rst = tuple(cursor)
        cursor.close()
        for rs in rst:
            str_resumen = str_resumen + str(rs[2]) + " " + rs[1] + " de " + str(rs[0]/1000) + " kV" + "\n"

        str_resumen = str_resumen + "\n"
        str_resumen = str_resumen + "Usuarios" + "\n"
        cnn = self.conn
        #--------------------
        cursor = cnn.cursor()
        cursor.execute("SELECT LEFT(Tarifas.id_OCEBA,2), COUNT(Usuarios.id_usuario) FROM Usuarios INNER JOIN Tarifas ON Usuarios.tarifa = Tarifas.Tarifa GROUP BY LEFT(Tarifas.id_OCEBA,2)")
        #convierto el cursor en array
        rst = tuple(cursor)
        cursor.close()
        for rs in rst:
            str_resumen = str_resumen + str(rs[1]) + " usuarios Tarifa " + rs[0] + "\n"

        str_resumen = str_resumen + "\n"
        #--------------------
        cursor = cnn.cursor()
        cursor.execute("SELECT COUNT(*) FROM VW_CCDATOSCOMERCIALES WHERE (Tarifa_Especial = 'TS') AND Fecha_Baja IS NULL")
        #convierto el cursor en array
        rst = tuple(cursor)
        cursor.close()
        if rst[0][0]>0:
            str_resumen = str_resumen + str(rst[0][0]) + " Usuarios con Tarifa Social" + "\n"
        #--------------------
        cursor = cnn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Usuarios WHERE ES=1 AND Electrodependiente='S'")
        #convierto el cursor en array
        rst = tuple(cursor)
        cursor.close()
        if rst[0][0]>0:
            str_resumen = str_resumen + str(rst[0][0]) + " Electrodependientes" + "\n"
        #--------------------
        cursor = cnn.cursor()
        cursor.execute("SELECT LEFT(prosumidor, 20), SUM(CAST(RIGHT(prosumidor, LEN(prosumidor) - 20) AS FLOAT)), COUNT(*) FROM Usuarios WHERE prosumidor <> '' AND ES=1 GROUP BY prosumidor, LEFT(prosumidor, 20)")
        #convierto el cursor en array
        rst = tuple(cursor)
        cursor.close()
        if len(rst)>0:
            for rs in rst:
                str_resumen = str_resumen + str(rs[2]) + " Usuarios Prosumidores Energía " + rs[0].strip() + " : " + str(rs[2]) + " kW" + "\n"

        self.txtResumen.setText(str_resumen)
        self.cmdSalir.clicked.connect(self.salir)

    def salir(self):
        self.close()
