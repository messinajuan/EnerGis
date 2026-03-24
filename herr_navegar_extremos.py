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
import clr
from PyQt6.QtWidgets import QMessageBox
from qgis.gui import QgsMapTool
from System import Int64

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrNavegarExtremos(QgsMapTool):
    def __init__(self, mapCanvas, geoname, amnodos, amlineas):
        QgsMapTool.__init__(self, mapCanvas)
        self.mapCanvas = mapCanvas
        #----------------------------------------------------------------------------
        nodo=Int64(0)
        for n in range(amnodos.GetLength(0)):
            if amnodos[n,1] == Int64(geoname):
                nodo = amnodos.GetValue(n,0)
                break
            if amnodos[n,1] == geoname:
                nodo = amnodos.GetValue(n,0)
                break
        if nodo==Int64(0):
            return
        #----------------------------------------------------------------------------
        for n in range(amnodos.GetLength(0)):
            amnodos[n,41] = 0
        for l in range(amlineas.GetLength(0)):
            amlineas[l,7] = 0
        #----------------------------------------------------------------------------
        # Cargar el ensamblado
        from pythonnet import load
        load("coreclr")
        # Cargar el ensamblado
        clr.AddReference(os.path.join(basepath, 'Microsoft.VisualBasic.Core.dll'))
        clr.AddReference(os.path.join(basepath, 'NavRed6.dll'))
        from EnerGis6.NavRed6 import NavRed
        #----------------------------------------------------------------------------
        # Instanciar la clase NavRed
        navred_instance = NavRed()
        # Llamar a la función
        resultado = navred_instance.Navegar_a_los_extremos(amnodos,amlineas,nodo)
        if resultado[0]!="Ok":
            QMessageBox.critical(None, 'EnerGis 6', '❌ ' + resultado[0])
            return
        #--------------------------------------------
        self.seleccion_n = [[]]
        self.seleccion_l = [[]]
        for n in range(amnodos.GetLength(0)):
            if amnodos.GetValue(n,41) == 1:
                self.seleccion_n.append([amnodos.GetValue(n,1),amnodos.GetValue(n,38),amnodos.GetValue(n,2)])
        for l in range(amlineas.GetLength(0)):
            if amlineas.GetValue(l,7) == 1:
                self.seleccion_l.append([amlineas.GetValue(l,1),amlineas.GetValue(l,5),amlineas.GetValue(l,6)])
        #--------------------------------------------
        from .frm_elementos_navegados import frmElementosNavegados
        self.dialogo = frmElementosNavegados(self.mapCanvas, self.seleccion_n, self.seleccion_l)
        self.dialogo.show()

class herrActualizarAlimentador(QgsMapTool):
    def __init__(self, mapCanvas, conn, geoname, amnodos, amlineas):
        self.conn = conn
        QgsMapTool.__init__(self, mapCanvas)
        self.mapCanvas = mapCanvas
        #----------------------------------------------------------------------------
        nodo=Int64(0)
        for n in range(amnodos.GetLength(0)):
            if amnodos[n,1] == Int64(geoname):
                nodo = amnodos.GetValue(n,0)
                break
            if amnodos[n,1] == geoname:
                nodo = amnodos.GetValue(n,0)
                break
        if nodo==Int64(0):
            return
        #----------------------------------------------------------------------------
        for n in range(amnodos.GetLength(0)):
            amnodos[n,41] = 0
        for l in range(amlineas.GetLength(0)):
            amlineas[l,7] = 0
        #----------------------------------------------------------------------------
        # Cargar el ensamblado
        from pythonnet import load
        load("coreclr")
        # Cargar el ensamblado
        clr.AddReference(os.path.join(basepath, 'Microsoft.VisualBasic.Core.dll'))
        clr.AddReference(os.path.join(basepath, 'NavRed6.dll'))
        from EnerGis6.NavRed6 import NavRed
        #----------------------------------------------------------------------------
        # Instanciar la clase NavRed
        navred_instance = NavRed()
        # Llamar a la función
        resultado = navred_instance.Navegar_a_los_extremos(amnodos,amlineas,nodo)
        if resultado[0]!="Ok":
            QMessageBox.critical(None, 'EnerGis 6', '❌ ' + resultado[0])
            return
        #--------------------------------------------

        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("INSERT INTO Alimentadores (Id, Id_Alim,Tension,Cd,SSEE) SELECT DISTINCT Aux, LEFT(Val1,15) AS Id_Alim, Tension,'0' AS Cd,'0' AS SSEE FROM Nodos WHERE Nodos.Tension>0 AND elmt=8 AND LEFT(Val1,15) NOT IN (SELECT Id_Alim FROM Alimentadores)")
        cnn.commit()

        cursor = self.conn.cursor()
        cursor.execute("SELECT Id, Id_Alim, Alimentadores.Tension FROM Nodos INNER JOIN Alimentadores ON Nodos.Val1=Alimentadores.Id_Alim AND Nodos.Tension=Alimentadores.Tension WHERE geoname=" + str(geoname))
        #convierto el cursor en array
        alim = tuple(cursor)
        cursor.close()
        id_alimentador = alim[0][0]
        str_alimentador = alim[0][1]
        tension = alim[0][2]

        str_nodos = '0'
        for n in range(amnodos.GetLength(0)):
            if amnodos.GetValue(n,41)==1 and amnodos.GetValue(n,38)==tension:
                str_nodos = str_nodos + ',' + str(amnodos.GetValue(n,1))

        cursor = cnn.cursor()
        cursor.execute("UPDATE Nodos SET Alimentador='" + str_alimentador + "' WHERE geoname IN (" + str_nodos + ")")
        cursor.execute("UPDATE mNodos SET alim=" + str(id_alimentador) + " WHERE geoname IN (" + str_nodos + ")")
        cnn.commit()

        str_lineas = '0'
        for l in range(amlineas.GetLength(0)):
            if amlineas.GetValue(l,7)==1 and amlineas.GetValue(l,5)==tension:
                str_lineas = str_lineas + ',' + str(amlineas.GetValue(l,1))

        cursor = cnn.cursor()
        cursor.execute("UPDATE Lineas SET Alimentador='" + str_alimentador + "' WHERE geoname IN (" + str_lineas + ")")
        cursor.execute("UPDATE mLineas SET alim=" + str(id_alimentador) + " WHERE geoname IN (" + str_lineas + ")")
        cnn.commit()

        QMessageBox.information(None, 'EnerGis 6', "ℹ️ Actualizado !")
