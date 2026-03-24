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
from .mod_navegacion_ant import navegar_a_la_fuente, navegar_compilar_red
from PyQt6.QtWidgets import QMessageBox
from qgis.gui import QgsMapTool

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrNavegarExtremos(QgsMapTool):
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
        #--------------------------------------------
        listanodos = [list(nodo) for nodo in self.mnodos]
        jnodos = json.dumps(listanodos)
        with open(os.path.join(tempfile.gettempdir(), "jnodos"), "w") as a:
            a.write(jnodos)
        #--------------------------------------------
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM mLineas ORDER BY Aux")
        #convierto el cursor en array
        self.mlineas = tuple(cursor)
        cursor.close()
        #--------------------------------------------
        listalineas = [list(linea) for linea in self.mlineas]
        jlineas = json.dumps(listalineas)
        with open(os.path.join(tempfile.gettempdir(), "jlineas"), "w") as a:
            a.write(jlineas)
        #--------------------------------------------
        ruta = os.path.join(tempfile.gettempdir(), "jnodos")
        # Verificar si el archivo existe antes de intentar cargarlo
        if os.path.exists(ruta):
            with open(ruta, "r") as a:
                jnodos = a.read()
            # Analizar el contenido JSON en un objeto Python
            listanodos = json.loads(jnodos)
            self.mnodos2 = tuple(listanodos)
        #--------------------------------------------
        ruta = os.path.join(tempfile.gettempdir(), "jlineas")
        # Verificar si el archivo existe antes de intentar cargarlo
        if os.path.exists(ruta):
            with open(ruta, "r") as a:
                jlineas = a.read()
            # Analizar el contenido JSON en un objeto Python
            listalineas = json.loads(jlineas)
            self.mlineas2 = tuple(listalineas)
        #--------------------------------------------
        for n in range (0, len(self.mnodos)):
            if self.mnodos[n][1]==self.nodo:
                nodo_desde = self.mnodos[n][0]
                cant_lineas_nodo = self.mnodos[n][4]
                break
        #--------------------------------------------
        navegar_a_la_fuente(self, self.mnodos, self.mlineas, self.nodo)
        #--------------------------------------------
        #el resultado es lo que tengo que anular
        lineas_anuladas=[]
        #anulo los caminos a las fuentes
        #navegar a las fuentes me modificó la mlineas, asi que para ver desde-hasta busco en la mlineas2
        for l in range (0, len(self.mlineas)):
            if self.mlineas2[l][2]==nodo_desde or self.mlineas2[l][3]==nodo_desde:
                if self.mlineas[l][12]==1:
                    lineas_anuladas.append(self.mlineas[l][0])
                    self.mlineas[l][1]=0
        #si no llego por ninguna fuente, el nodo esta desconectado, asi que no hay nada aguas abajo

        if len(lineas_anuladas)>0 and len(lineas_anuladas)==cant_lineas_nodo:
            QMessageBox.warning(None, "Mensaje", "❌ No hay nada aguas abajo")
            return

        #si hay aguas abajo, comenzamos a utilizar mnodos2 y mlineas2
        for l in range (0, len(lineas_anuladas)):
            #busco en que casillero tengo la linea y anulo esos proximos nodos en el nodo que estoy navegando
            for i in range (5, 37):
                if self.mnodos2[nodo_desde][i]==lineas_anuladas[l]:
                    self.mnodos2[nodo_desde][4]=self.mnodos2[nodo_desde][4]-1
                    for j in range (i, 36):
                        self.mnodos2[nodo_desde][j]=self.mnodos2[nodo_desde][j+1]
                    break
        for n in range(0, len(self.mnodos2)):
            self.mnodos2[n][3] = 0
        for l in range (0, len(self.mlineas2)):
            self.mlineas2[l][4] = 0
        self.monodos = [0] * len(self.mnodos2) #valores cero de longitud igual a mnodos
        #--------------------------------------------
        navegar_compilar_red(self, self.mnodos2, self.mlineas2, self.monodos, nodo_desde)
        #--------------------------------------------
        self.seleccion_n = []
        for n in range(0, len(self.mnodos2)):
            if self.mnodos2[n][3] != 0:
                self.seleccion_n.append(self.mnodos2[n][1])
        self.seleccion_l = []
        for l in range (1, len(self.mlineas2)):
            if self.mlineas2[l][4] != 0:
                self.seleccion_l.append(self.mlineas2[l][1])
        m = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(m)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyr.select(self.seleccion_n)
            if lyr.name()[:6] == 'Lineas':
                lyr.select(self.seleccion_l)

class herrActualizarAlimentador(QgsMapTool):
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
        #--------------------------------------------
        listanodos = [list(nodo) for nodo in self.mnodos]
        jnodos = json.dumps(listanodos)
        with open(os.path.join(tempfile.gettempdir(), "jnodos"), "w") as a:
            a.write(jnodos)
        #--------------------------------------------
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM mLineas ORDER BY Aux")
        #convierto el cursor en array
        self.mlineas = tuple(cursor)
        cursor.close()
        #--------------------------------------------
        listalineas = [list(linea) for linea in self.mlineas]
        jlineas = json.dumps(listalineas)
        with open(os.path.join(tempfile.gettempdir(), "jlineas"), "w") as a:
            a.write(jlineas)
        #--------------------------------------------
        ruta = os.path.join(tempfile.gettempdir(), "jnodos")
        # Verificar si el archivo existe antes de intentar cargarlo
        if os.path.exists(ruta):
            with open(ruta, "r") as a:
                jnodos = a.read()
            # Analizar el contenido JSON en un objeto Python
            listanodos = json.loads(jnodos)
            self.mnodos2 = tuple(listanodos)
        #--------------------------------------------
        ruta = os.path.join(tempfile.gettempdir(), "jlineas")
        # Verificar si el archivo existe antes de intentar cargarlo
        if os.path.exists(ruta):
            with open(ruta, "r") as a:
                jlineas = a.read()
            # Analizar el contenido JSON en un objeto Python
            listalineas = json.loads(jlineas)
            self.mlineas2 = tuple(listalineas)
        #--------------------------------------------
        for n in range (0, len(self.mnodos)):
            if self.mnodos[n][1]==self.nodo:
                nodo_desde = self.mnodos[n][0]
                cant_lineas_nodo = self.mnodos[n][4]
                break
        #--------------------------------------------
        navegar_a_la_fuente(self, self.mnodos, self.mlineas, self.nodo)
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

        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("INSERT INTO Alimentadores (Id, Id_Alim,Tension,Cd,SSEE) SELECT DISTINCT Aux, LEFT(Val1,15) AS Id_Alim, Tension,'0' AS Cd,'0' AS SSEE FROM Nodos WHERE Nodos.Tension>0 AND elmt=8 AND LEFT(Val1,15) NOT IN (SELECT Id_Alim FROM Alimentadores)")
        cnn.commit()

        cursor = self.conn.cursor()
        cursor.execute("SELECT Id, Id_Alim, Alimentadores.Tension FROM Nodos INNER JOIN Alimentadores ON Nodos.Val1=Alimentadores.Id_Alim AND Nodos.Tension=Alimentadores.Tension WHERE geoname=" + str(self.nodo))
        #convierto el cursor en array
        alim = tuple(cursor)
        cursor.close()
        id_alimentador = alim[0][0]
        str_alimentador = alim[0][1]
        tension = alim[0][2]

        str_nodos = '0'
        for m in range(0, len(self.mnodos2)):
            if self.mnodos2[m][3] != 0 and self.mnodos[m][38]==tension:
                str_nodos = str_nodos + ',' + str(self.mnodos2[m][1])

        cursor = cnn.cursor()
        cursor.execute("UPDATE Nodos SET Alimentador='" + str_alimentador + "' WHERE geoname IN (" + str_nodos + ")")
        cursor.execute("UPDATE mNodos SET alim=" + str(id_alimentador) + " WHERE geoname IN (" + str_nodos + ")")
        cnn.commit()

        str_lineas = '0'
        for n in range (1, len(self.mlineas2)):
            if self.mlineas2[n][4] != 0 and self.mlineas2[n][5]==tension:
                str_lineas = str_lineas + ',' + str(self.mlineas2[n][1])

        cursor = cnn.cursor()
        cursor.execute("UPDATE Lineas SET Alimentador='" + str_alimentador + "' WHERE geoname IN (" + str_lineas + ")")
        cursor.execute("UPDATE mLineas SET alim=" + str(id_alimentador) + " WHERE geoname IN (" + str_lineas + ")")
        cnn.commit()

        QMessageBox.information(None, 'EnerGis 6', "ℹ️ Actualizado !")
