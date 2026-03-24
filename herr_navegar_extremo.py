# encoding: utf-8
#-----------------------------------------------------------
# Copyright (C) 2025 Juan Messina
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
from .mod_navegacion import navegar_a_las_fuentes, navegar_compilar_red
from PyQt6.QtWidgets import QMessageBox
from qgis.gui import QgsMapTool

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrNavegarExtremo(QgsMapTool):

    def __init__(self, mapCanvas, conn, nodo):
        QgsMapTool.__init__(self, mapCanvas)
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.nodo = nodo
        #--------------------------------------------
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM mNodos ORDER BY Aux")
        #convierto el cursor en array
        self.mnodos = tuple(cursor)
        cursor.close()
        listanodos = [list(nodo) for nodo in self.mnodos]
        jnodos = json.dumps(listanodos)
        with open(os.path.join(tempfile.gettempdir(), "jnodos"), "w") as a:
            a.write(jnodos)
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM mLineas ORDER BY Aux")
        #convierto el cursor en array
        self.mlineas = tuple(cursor)
        cursor.close()
        listalineas = [list(linea) for linea in self.mlineas]
        jlineas = json.dumps(listalineas)
        with open(os.path.join(tempfile.gettempdir(), "jlineas"), "w") as a:
            a.write(jlineas)

        ruta = os.path.join(tempfile.gettempdir(), "jnodos")
        # Verificar si el archivo existe antes de intentar cargarlo
        if os.path.exists(ruta):
            with open(ruta, "r") as a:
                jnodos = a.read()
            # Analizar el contenido JSON en un objeto Python
            listanodos = json.loads(jnodos)
            self.mnodos2 = tuple(listanodos)
        ruta = os.path.join(tempfile.gettempdir(), "jlineas")
        # Verificar si el archivo existe antes de intentar cargarlo
        if os.path.exists(ruta):
            with open(ruta, "r") as a:
                jlineas = a.read()
            # Analizar el contenido JSON en un objeto Python
            listalineas = json.loads(jlineas)
            self.mlineas2 = tuple(listalineas)

        for n in range (0, len(self.mnodos)):
            if self.mnodos[n][1]==self.nodo:
                nodo_desde = self.mnodos[n][0]
                cant_lineas_nodo = self.mnodos[n][4]
                break
        #--------------------------------------------
        navegar_a_las_fuentes(self, self.mnodos, self.mlineas, self.nodo)
        #--------------------------------------------
        #el resultado es lo que tengo que anular
        lineas_anuladas=[]
        #anulo los caminos a las fuentes
        #navegar a las fuentes me modificó la mlineas, asi que para ver desde-hasta busco en la mlineas2
        for n in range (0, len(self.mlineas)):
            if self.mlineas2[n][2]==nodo_desde or self.mlineas2[n][3]==nodo_desde:
                if self.mlineas[n][12]==1:
                    lineas_anuladas.append(self.mlineas[n][0])
                    self.mlineas[n][1]=0
        #si no llego por ninguna fuente, el nodo esta desconectado, asi que no hay nada aguas abajo

        if len(lineas_anuladas)>0 and len(lineas_anuladas)==cant_lineas_nodo:
            QMessageBox.warning(None, "EnerGis 6", "❌ No hay nada aguas abajo")
            return

        #si hay aguas abajo, comenzamos a utilizar mnodos2 y mlineas2
        for n in range (0, len(lineas_anuladas)):
            #busco en que casillero tengo la linea y anulo esos proximos nodos en el nodo que estoy navegando
            for i in range (5, 37):
                if self.mnodos2[nodo_desde][i]==lineas_anuladas[n]:
                    self.mnodos2[nodo_desde][4]=self.mnodos2[nodo_desde][4]-1
                    for j in range (i, 36):
                        self.mnodos2[nodo_desde][j]=self.mnodos2[nodo_desde][j+1]
                    break
        for n in range(0, len(self.mnodos2)):
            self.mnodos2[n][3] = 0
        for n in range (0, len(self.mlineas2)):
            self.mlineas2[n][4] = 0
        self.monodos = [0] * len(self.mnodos2) #valores cero de longitud igual a mnodos
        #--------------------------------------------
        navegar_compilar_red(self, self.mnodos2, self.mlineas2, self.monodos, nodo_desde)
        #--------------------------------------------
        self.seleccion_n = []
        for m in range(0, len(self.mnodos2)):
            if self.mnodos2[m][3] != 0:
                self.seleccion_n.append(self.mnodos2[m][1])
        self.seleccion_l = []
        for n in range (1, len(self.mlineas2)):
            if self.mlineas2[n][4] != 0:
                self.seleccion_l.append(self.mlineas2[n][1])
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyr.select(self.seleccion_n)
            if lyr.name()[:6] == 'Lineas':
                lyr.select(self.seleccion_l)
