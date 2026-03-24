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

class herrNavegarFuente(QgsMapTool):

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
        resultado = navred_instance.Navegar_a_la_fuente(amnodos,amlineas,nodo)
        if resultado[0]!="Ok":
            QMessageBox.critical(None, 'EnerGis 6', '❌ ' + resultado[0])
            return
        lineas_ordenadas = list(resultado[1])
        nodos_ordenados = list(resultado[2])
        #--------------------------------------------
        self.seleccion_n = [[]]
        self.seleccion_l = [[]]
        for n in nodos_ordenados:
            if n!=0:
                self.seleccion_n.append([amnodos.GetValue(n,1),amnodos.GetValue(n,38),amnodos.GetValue(n,2)])
        for l in lineas_ordenadas:
            if l!=0:
                self.seleccion_l.append([amlineas.GetValue(l,1),amlineas.GetValue(l,5),amlineas.GetValue(l,6)])
        #--------------------------------------------
        from .frm_elementos_navegados import frmElementosNavegados
        self.dialogo = frmElementosNavegados(self.mapCanvas, self.seleccion_n, self.seleccion_l)
        self.dialogo.show()
