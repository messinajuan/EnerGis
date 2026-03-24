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
from PyQt6.QtWidgets import QApplication, QProgressDialog
from PyQt6.QtGui import QDoubleValidator
from PyQt6 import uic
import json
import tempfile
import math

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_momentos_electricos.ui'))

class frmMomentosElectricos(DialogType, DialogBase):
    def __init__(self, conn, geoname):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.conn = conn
        self.geoname = geoname
        vfloat = QDoubleValidator()
        self.txtPotencia.setValidator(vfloat)
        self.txtPotencia.setText("0")
        self.txtFp.setValidator(vfloat)
        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)

    def aceptar(self):
        #----------------------------------------------------------------------------
        progress = QProgressDialog("Procesando...", "Cancelar", 0, 100)
        progress.setWindowTitle("Progreso")
        progress.setWindowModality(True)  # Hace que la ventana de progreso sea modal
        progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
        progress.setValue(0)  # Inicia el progreso en 0
        #----------------------------------------------------------------------------
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM mNodos ORDER BY Aux")
        #convierto el cursor en array
        mnodos = tuple(cursor)
        cursor.close()
        listanodos = [list(nodo) for nodo in mnodos]
        jnodos = json.dumps(listanodos)
        with open(os.path.join(tempfile.gettempdir(), "jnodos"), "w") as a:
            a.write(jnodos)
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM mLineas ORDER BY Aux")
        #convierto el cursor en array
        mlineas = tuple(cursor)
        cursor.close()
        listalineas = [list(linea) for linea in mlineas]
        jlineas = json.dumps(listalineas)
        with open(os.path.join(tempfile.gettempdir(), "jlineas"), "w") as a:
            a.write(jlineas)
        #----------------------------------------------------------------------------
        progress.setValue(10)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        #--------------------------------------------
        #navego a la fuente y cosecho el listado de nodos que intervienen
        from .mod_navegacion_ant import navegar_a_la_fuente
        navegar_a_la_fuente(self, mnodos, mlineas, self.geoname)
        #--------------------------------------------
        nodos_camino = []
        for n in range(0, len(mnodos)):
            if mnodos[n][45] == 1:
                nodos_camino.append(n)
        lineas_camino = []
        for n in range (0, len(mlineas)):
            if mlineas[n][12] == 1:
                lineas_camino.append(n)
        if len(lineas_camino)==0:
            return
        #--------------------------------------------
        ruta = os.path.join(tempfile.gettempdir(), "jnodos")
        # Verificar si el archivo existe antes de intentar cargarlo
        if os.path.exists(ruta):
            with open(ruta, "r") as a:
                jnodos = a.read()
            # Analizar el contenido JSON en un objeto Python
            listanodos = json.loads(jnodos)
            mnodos = tuple(listanodos)
        ruta = os.path.join(tempfile.gettempdir(), "jlineas")
        # Verificar si el archivo existe antes de intentar cargarlo
        if os.path.exists(ruta):
            with open(ruta, "r") as a:
                jlineas = a.read()
            # Analizar el contenido JSON en un objeto Python
            listalineas = json.loads(jlineas)
            mlineas = tuple(listalineas)
        #--------------------------------------------
        from .mod_navegacion_ant import cadena_a_la_fuente
        nodos_asociados = cadena_a_la_fuente(self, self.conn, nodos_camino)
        #--------------------------------------------
        #----------------------------------------------------------------------------
        progress.setValue(30)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        ruta = os.path.join(tempfile.gettempdir(), "jnodos")
        # Verificar si el archivo existe antes de intentar cargarlo
        if os.path.exists(ruta):
            with open(ruta, "r") as a:
                jnodos = a.read()
            # Analizar el contenido JSON en un objeto Python
            listanodos = json.loads(jnodos)
            mnodos = tuple(listanodos)
        ruta = os.path.join(tempfile.gettempdir(), "jlineas")
        # Verificar si el archivo existe antes de intentar cargarlo
        if os.path.exists(ruta):
            with open(ruta, "r") as a:
                jlineas = a.read()
            # Analizar el contenido JSON en un objeto Python
            listalineas = json.loads(jlineas)
            mlineas = tuple(listalineas)
        #--------------------------------------------
        nodos_ordenados = []
        nodo = 0
        #voy desde el nodo seleccionado hacia la fuente y ordeno
        for n in range(0, len(nodos_camino)):
            if mnodos[nodos_camino[n]][1]==self.geoname:
                nodo = nodos_camino[n]
                nodos_ordenados.append(nodo)
                break
        #----------------------------------------------------------------------------
        progress.setValue(40)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        from .mod_navegacion_ant import buscar_lineas_segun_nodo
        cortar=False
        while mnodos[nodo][2]!=1:
            if cortar==True:
                break
            for n in range(0, len(nodos_camino)):
                if nodos_camino[n]==nodo:
                    #busco en los próximos nodos, uno que esté en la lista del camino a la fuente
                    cant_lineas_del_nodo, lineas_del_nodo, proximos_nodos = buscar_lineas_segun_nodo(self, mnodos, mlineas, nodo)
                    for i in range (0, cant_lineas_del_nodo):
                        if cortar==True: #corto el ordenamiento en el rebaje o regulador
                            break
                        for j in range (0, len(nodos_camino)):
                            if cortar==True: #corto el ordenamiento en el rebaje o regulador
                                break
                            if proximos_nodos[i]==nodos_camino[j]:
                                #tiene que estar en la lista de la seleccion pero no debe estar el nodos_ordenados
                                if not proximos_nodos[i] in nodos_ordenados:
                                    nodo = proximos_nodos[i]
                                    nodos_ordenados.append(nodo)
                                    if mnodos[nodo][2]==4:
                                        cortar=True
                                    if mnodos[nodo][2]==9:
                                        cortar=True
                                    break
        potencia_total = 0
        potencia_por_nodo = [] #array para armar la presentación
        potencia_proyecto = 0
        potencia_proyecto = float(self.txtPotencia.text())
        #el primer nodo es el del proyecto, a partir de este voy buscando las lineas con sus parametros
        nodo = nodos_ordenados[0]
        tension_proyecto = mnodos[nodo][38]
        P = 0
        if str(nodos_asociados[nodo])!="[]":
            cursor = self.conn.cursor()
            cursor.execute("SELECT SUM(Cargas_Nodos.P) FROM Cargas_Nodos INNER JOIN Nodos ON Cargas_Nodos.geoname = Nodos.Geoname WHERE Nodos.Tension > 1000 AND Nodos.geoname IN (" + str(nodos_asociados[nodo]).replace('[','').replace(']','') + ")")
            #convierto el cursor en array
            potencia = tuple(cursor)
            cursor.close()
            if potencia[0][0]!=None:
                P = potencia[0][0]
        potencia_total = P + potencia_proyecto
        #este array tiene el orden de navegacion a la fuente y no tiene la demanda del proyecto
        potencia_por_nodo.append(P)
        datos_lineas = []
        #en la primer iteacion el nodo es el del proyecto, y busco la linea entre ese y el proximo
        #luego reemplazo nodo por el siguiente y asi deberia encontrar todas las lineas
        for n in range (1, len(nodos_ordenados)):
            geoname_nodo = mnodos[nodo][1]
            #datos del tramo de linea, la potencia que pasa por la linea es la calculada previamente
            cursor = self.conn.cursor()
            cursor.execute("SELECT geoname, CAST(fase AS SMALLINT), CAST(REPLACE(ISNULL(Val3,'0,1'),',','.') AS FLOAT), CAST(REPLACE(ISNULL(Val4,'0,1'),',','.') AS FLOAT), longitud, Tension, descripcion FROM Lineas INNER JOIN Elementos_Lineas ON Lineas.elmt = Elementos_Lineas.id WHERE (desde=" + str(geoname_nodo) + " AND hasta=" + str(mnodos[nodos_ordenados[n]][1]) + ") or (desde=" + str(mnodos[nodos_ordenados[n]][1]) + " AND hasta=" + str(geoname_nodo) + ")")
            #convierto el cursor en array
            tramos = tuple(cursor)
            cursor.close()
            datos_lineas.append((tramos[0][0], tramos[0][1], tramos[0][2], tramos[0][3], tramos[0][4], tramos[0][5], potencia_total, tramos[0][6]))
            #con esa linea llego al proximo nodo, cuya potencia se calcula segun los nodos aguas abajo
            P = 0
            if str(nodos_asociados[nodos_ordenados[n]])!="[]":
                cursor = self.conn.cursor()
                cursor.execute("SELECT SUM(Cargas_Nodos.P) FROM Cargas_Nodos INNER JOIN Nodos ON Cargas_Nodos.geoname = Nodos.Geoname WHERE Nodos.Tension=" + str(tension_proyecto) + " AND Nodos.geoname IN (" + str(nodos_asociados[nodos_ordenados[n]]).replace('[','').replace(']','') + ")")
                #convierto el cursor en array
                potencia = tuple(cursor)
                cursor.close()
                P = potencia[0][0]
            if P==None:
                P=0
            potencia_por_nodo.append(P)
            #la potencia total del sistema en el nodo es
            potencia_total = potencia_total + P
            #seteamos el nodo para la proxima iteacion
            nodo = nodos_ordenados[n]
        #----------------------------------------------------------------------------
        progress.setValue(50)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        if os.path.isdir('c:/gis/energis6/Calculos/')==False:
            os.mkdir('c:/gis/energis6/Calculos/')
        f = open('c:/gis/energis6/Calculos/caida_tension_' + str(mnodos[nodos_ordenados[0]][1]) + '.txt','w')
        f.writelines("\n")
        f.writelines("CALCULO DE CAIDA DE TENSION" + "\n")
        f.writelines("---------------------------" + "\n")
        f.writelines("\n")
        f.writelines("\n")
        f.writelines("DIAGRAMA UNIFILAR" + "\n")
        f.writelines("-----------------" + "\n")
        f.writelines("\n")
        for n in range (len(nodos_ordenados)-1, -1, -1):
            if n==0:
                str_linea="       | "
                f.writelines(str_linea + "\n")
                str_linea="       P----> " + str(format(potencia_proyecto, ".2f")) + " kW  Nodo del Proyecto (" + str(mnodos[nodos_ordenados[n]][1]) + ")"
                f.writelines(str_linea + "\n")
                if potencia_por_nodo[n]>0:
                    str_linea="       | "
                    f.writelines(str_linea + "\n")
                    str_linea="       | "
                    f.writelines(str_linea + "\n")
                    str_linea="       V " + str(format(potencia_por_nodo[n], ".2f")) + " kW Aguas Abajo del Proyecto"
                    f.writelines(str_linea + "\n")
            elif mnodos[nodos_ordenados[n]][2]==1:
                str_linea="      [F] Nodo Fuente (" + str(mnodos[nodos_ordenados[n]][1]) + ")"
                f.writelines(str_linea + "\n")
                str_linea="       | "
                f.writelines(str_linea + "\n")
            elif mnodos[nodos_ordenados[n]][2]==2:
                str_linea="       | "
                f.writelines(str_linea + "\n")
                str_linea="       E  Nodo Elemento de Prot/Maniobra (" + str(mnodos[nodos_ordenados[n]][1]) + ")"
                f.writelines(str_linea + "\n")
                str_linea="       | "
                f.writelines(str_linea + "\n")
            elif mnodos[nodos_ordenados[n]][2]==4:
                if tension_proyecto<1000:
                    str_linea="      [T] Nodo Transformador (" + str(mnodos[nodos_ordenados[n]][1]) + ")"
                else:
                    str_linea="      [R] Nodo Rebaje (" + str(mnodos[nodos_ordenados[n]][1]) + ")"
                f.writelines(str_linea + "\n")
                str_linea="       | "
                f.writelines(str_linea + "\n")
            elif mnodos[nodos_ordenados[n]][2]==9:
                str_linea="      [R] Nodo Regulador (" + str(mnodos[nodos_ordenados[n]][1]) + ")"
                f.writelines(str_linea + "\n")
                str_linea="       | "
                f.writelines(str_linea + "\n")
            else:
                str_linea="       | "
                f.writelines(str_linea + "\n")
                if potencia_por_nodo[n]==None:
                    str_linea="       O  Nodo " + str(mnodos[nodos_ordenados[n]][1])
                elif potencia_por_nodo[n]>0:
                    str_linea="       O----> " + str(format(potencia_por_nodo[n], ".2f")) + " kW Nodo Derivación (" + str(mnodos[nodos_ordenados[n]][1]) + ")"
                else:
                    str_linea="       O  Nodo Unión (" + str(mnodos[nodos_ordenados[n]][1]) + ")"
                f.writelines(str_linea + "\n")
                str_linea="       | "
                f.writelines(str_linea + "\n")
            try:
                if n>0:
                    if datos_lineas[n-1][1]==1 or datos_lineas[n-1][1]==2 or datos_lineas[n-1][1]==3:
                        fases = '1 Fase'
                    if datos_lineas[n-1][1]==12 or datos_lineas[n-1][1]==13 or datos_lineas[n-1][1]==23:
                        fases = '2 Fases'
                    if datos_lineas[n-1][1]==123:
                        fases = '3 Fases'
                    longitud = datos_lineas[n-1][4]
                    potencia = datos_lineas[n-1][6]
                    descripcion = datos_lineas[n-1][7]
                    str_linea="       | " + descripcion + " (" + fases + ")"
                    f.writelines(str_linea + "\n")
                    str_linea="       V " + str(format(longitud, ".2f")) + " m"
                    f.writelines(str_linea + "\n")
                    str_linea="       | " + str(format(potencia, ".2f")) + " kW"
                    f.writelines(str_linea + "\n")
            except:
                QMessageBox.critical(None, "EnerGis 6", "❌ Error en los datos de las líneas")
        caida_total=0
        #----------------------------------------------------------------------------
        progress.setValue(75)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        f.writelines("\n")
        f.writelines("CALCULO" + "\n")
        f.writelines("-------" + "\n")
        f.writelines("\n")
        f.writelines("-------------------------------------------------------------------------------------------------------------------" + "\n")
        f.writelines("Tramo            Pot [kW]          I [A]       Long [m]      R [ohm/km]     X [ohm/km]     Caida [%]        % Total" + "\n")
        f.writelines("-------------------------------------------------------------------------------------------------------------------" + "\n")
        for n in range (len(nodos_ordenados)-1, -1, -1):
            if n > 0:
                R = datos_lineas[n-1][2]
                X = datos_lineas[n-1][3]
                longitud = datos_lineas[n-1][4]
                tension = datos_lineas[n-1][5]
                factor_potencia = 0.9
                longitud = datos_lineas[n-1][4]
                potencia = datos_lineas[n-1][6]
                descripcion = datos_lineas[n-1][7]
                if datos_lineas[n-1][1]==1 or datos_lineas[n-1][1]==2 or datos_lineas[n-1][1]==3:
                    #MRT
                    corriente = potencia * 1000 / (factor_potencia * tension / math.sqrt(3))
                    dv = 2 * (R * factor_potencia + X * math.sqrt(1 - factor_potencia**2)) * longitud / 1000 * corriente
                if datos_lineas[n-1][1]==12 or datos_lineas[n-1][1]==13 or datos_lineas[n-1][1]==23:
                    #BIFASICO
                    corriente = potencia * 1000 / (tension * factor_potencia)
                    dv = 2 * (R * factor_potencia + X * math.sqrt(1 - factor_potencia**2)) * longitud / 1000 * corriente
                if datos_lineas[n-1][1]==123:
                    #TRIFASICO
                    corriente = potencia * 1000 / (math.sqrt(3) *  tension * factor_potencia)
                    dv = math.sqrt(3) * (R * factor_potencia + X * math.sqrt(1 - factor_potencia**2)) *  longitud / 1000 * corriente
                caida = 100 * dv / tension
                caida_total = caida_total + caida
                str_linea = "Tramo " + ("    " + str(n))[-4:]
                str_linea = str_linea + ("               " + str(format(potencia, ".2f")))[-15:]
                str_linea = str_linea + ("               " + str(format(corriente, ".2f")))[-15:]
                str_linea = str_linea + ("               " + str(format(longitud, ".2f")))[-15:]
                str_linea = str_linea + ("               " + str(format(R, ".3f")))[-15:]
                str_linea = str_linea + ("               " + str(format(X, ".3f")))[-15:]
                str_linea = str_linea + ("               " + str(format(caida, ".6f")))[-15:]
                str_linea = str_linea + ("               " + str(format(caida_total, ".6f")))[-15:]
                f.writelines(str_linea + "\n")
        f.writelines("-------------------------------------------------------------------------------------------------------------------" + "\n")
        f.writelines("\n")
        f.writelines("La caída de tensión máxima considerando todas las cargas es de " + str(format(caida_total, ".6f")) + " %" + "\n")
        f.close()
        #----------------------------------------------------------------------------
        progress.setValue(100)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        #import subprocess
        #este bloquea el programa hasta que se cierre notepad
        #subprocess.run(['notepad' , 'c:/gis/energis6/Calculos/caida_tension_' + str(mnodos[nodos_ordenados[0]][1]) + '.txt'])
        #import os
        # Ruta del archivo a abrir con Notepad
        ruta_archivo = 'c:/gis/energis6/Calculos/caida_tension_' + str(mnodos[nodos_ordenados[0]][1]) + '.txt'
        os.system(f'notepad {ruta_archivo}')
        #--------------------------------------------

    def salir(self):
        self.close()
