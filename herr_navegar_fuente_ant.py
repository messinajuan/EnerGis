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
from .mod_navegacion_ant import navegar_a_la_fuente
from PyQt6.QtWidgets import QMessageBox
from qgis.gui import QgsMapTool


#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrNavegarFuente(QgsMapTool):
    def __init__(self, mapCanvas, conn, nodo):
        QgsMapTool.__init__(self, mapCanvas)
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.nodo = nodo
        #--------------------------------------------
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM mLineas ORDER BY Aux")
        #convierto el cursor en array
        self.mlineas = tuple(cursor)
        cursor.close()
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM mNodos ORDER BY Aux")
        #convierto el cursor en array
        self.mnodos = tuple(cursor)
        cursor.close()
        #--------------------------------------------
        navegar_a_la_fuente(self, self.mnodos, self.mlineas, self.nodo)
        #--------------------------------------------
        self.seleccion_n = []
        for n in range(1, len(self.mnodos)):
            if self.mnodos[n][45] == 1:
                self.seleccion_n.append(self.mnodos[n][1])
        self.seleccion_l = []
        for n in range (1, len(self.mlineas)):
            if self.mlineas[n][12] == 1:
                self.seleccion_l.append(self.mlineas[n][1])
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyr.select(self.seleccion_n)
            if lyr.name()[:6] == 'Lineas':
                lyr.select(self.seleccion_l)
