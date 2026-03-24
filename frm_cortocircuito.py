# encoding: utf-8
#-----------------------------------------------------------
# Copyright (C) 2026 Juan Messina - Gemini IA
#-----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#---------------------------------------------------------------------

import os
import logging
import pandas as pd
import pandapower as pp
import numpy as np
from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsProject, QgsField
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QIntValidator
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtCore import QVariant
from PyQt6 import uic, QtCore #, QtWidgets

import pandapower.shortcircuit as sc
import clr
from System import Int64

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class QtSignaler(QtCore.QObject):
    # Definimos una señal que transporta el texto del log
    log_signal = QtCore.pyqtSignal(str)

class QListHandler(logging.Handler):
    def __init__(self, signaler):
        super().__init__()
        self.signaler = signaler

    def emit(self, record):
        mensaje = self.format(record)
        # Emitimos la señal para que la UI la reciba de forma segura
        self.signaler.log_signal.emit(mensaje)

class CortoWorker(QThread):
    # Señales para comunicación segura con la UI
    finished = pyqtSignal()
    error = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        """Aquí es donde ocurre la magia sin bloquear la UI"""
        try:
            # Ejecutamos el flujo
            self.parent().calcular()
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_cortocircuito.ui'))

class frmCortocircuito(DialogType, DialogBase):
    def __init__(self, id_usuario_sistema, conn, fuente, amnodos, amlineas, monodos):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.id_usuario_sistema = id_usuario_sistema
        self.conn = conn
        self.fuente = fuente
        #Configurar Modelo para el QListView
        self.log_model = QtCore.QStringListModel()
        self.lstCalculo.setModel(self.log_model)
        #Configurar la Barra de Progreso (QProgressBar)
        self.progressBar.setRange(0, 0) # Modo "indeterminado" (animación infinita)
        self.progressBar.hide() # Oculta al inicio
        #Instanciar el señalador y conectarlo a una función local
        self.signaler = QtSignaler()
        self.signaler.log_signal.connect(self.agregar_log_a_pantalla)
        #Configurar los loggers (Propio y Pandapower)
        self.setup_logging()
        vint = QIntValidator()
        self.txtNodos.setValidator(vint)

        cursor = self.conn.cursor()
        cursor.execute("SELECT count(*) FROM Selecciones WHERE geoname = " + str(fuente) + " AND id_usuario_sistema = " + self.id_usuario_sistema)
        #convierto el cursor en array
        rs = tuple(cursor)
        if rs[0][0]!=0:
            reply = QMessageBox.question(None, 'EnerGis 6', 'Hay un set de datos guardados\n\n' + 'Desea utilizarlo ❓ (nodos y líneas seleccionados previamente)', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
               self.seleccionar_red(amnodos, amlineas, monodos, fuente)
               if len(self.seleccion_n)==0:
                   return
        else:
            self.seleccionar_red(amnodos, amlineas, monodos, fuente)

        self.cmdCalcular.clicked.connect(self.iniciar_calculo)
        self.cmdSalir.clicked.connect(self.salir)

    def setup_logging(self):
        handler = QListHandler(self.signaler)
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        #logger propio
        logger = logging.getLogger("MiCorto")
        if logger.hasHandlers():
            logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO) #Para capturar v_info
        #logger.setLevel(logging.DEBUG) #Para capturar v_debug
        # Logger de Pandapower
        pp_logger = logging.getLogger("pandapower")
        pp_logger.addHandler(handler)
        pp_logger.setLevel(logging.DEBUG)

    def agregar_log_a_pantalla(self, mensaje):
        lista_actual = self.log_model.stringList()
        lista_actual.append(mensaje)
        self.log_model.setStringList(lista_actual)
        # Auto-scroll al final
        self.lstCalculo.scrollToBottom()

    def seleccionar_red(self, amnodos, amlineas, monodos, fuente):
        logger = logging.getLogger("MiCorto")
        self.seleccion_n = []
        self.seleccion_l = []
        logger.info("Navegando red ...")
        if fuente==-1:
            #----------------------------------------------------------------------------
            # Cargar el ensamblado
            clr.AddReference(os.path.join(basepath, 'NavRed6.dll'))
            from EnerGis6.NavRed6 import NavRed
            #----------------------------------------------------------------------------
            # Instanciar la clase NavRed
            navred_instance = NavRed()
            #----------------------------------------------------------------------------
            nodo=Int64(0)
            for f in range(amnodos.GetLength(0)):
                if amnodos[f,2] == 1:
                    nodo = amnodos.GetValue(f,0)
                    #----------------------------------------------------------------------------
                    for n in range(amnodos.GetLength(0)):
                        amnodos[n,41] = 0
                    for l in range(amlineas.GetLength(0)):
                        amlineas[l,7] = 0
                    #----------------------------------------------------------------------------
                    # Llamar a la función
                    resultado = navred_instance.Navegar_a_los_extremos(amnodos,amlineas,nodo)
                    if resultado[0]!="Ok":
                        QMessageBox.critical(None, 'EnerGis 6', '❌ ' + resultado[0])
                        return
                    #--------------------------------------------
                    for n in range(amnodos.GetLength(0)):
                        #seleccion de nodos de MT + generadores
                        if amnodos.GetValue(n,41) == 1 and (amnodos.GetValue(n,38) > 1000 or amnodos.GetValue(n,2) == 11):
                            self.seleccion_n.append(amnodos.GetValue(n,1))
                    for l in range(amlineas.GetLength(0)):
                        if amlineas.GetValue(l,7) == 1 and amlineas.GetValue(l,5) >1000:
                            self.seleccion_l.append(amlineas.GetValue(l,1))
                    #--------------------------------------------
        else:
            #----------------------------------------------------------------------------
            nodo=Int64(0)
            for n in range(amnodos.GetLength(0)):
                if amnodos[n,1] == Int64(fuente):
                    nodo = amnodos.GetValue(n,0)
                    break
                if amnodos[n,1] == fuente:
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
            for n in range(amnodos.GetLength(0)):
                if amnodos.GetValue(n,41) == 1 and amnodos.GetValue(n,38) > 1000:
                    self.seleccion_n.append(amnodos.GetValue(n,1))
            for l in range(amlineas.GetLength(0)):
                if amlineas.GetValue(l,7) == 1 and amlineas.GetValue(l,5) >1000:
                    self.seleccion_l.append(amlineas.GetValue(l,1))
            #--------------------------------------------

        cnn = self.conn
        cnn.autocommit = False

        cursor = cnn.cursor()
        cursor.execute ("DELETE FROM Transformacion WHERE id_usuario_sistema=" + str(self.id_usuario_sistema))
        cnn.commit()
        for n in range (0, len(monodos)):
            desde = monodos.GetValue(n)
            if amnodos.GetValue(desde,2) == 9: #Regulador MT
                hasta = monodos.GetValue(n+1)
                cursor.execute ("INSERT INTO Transformacion (id_usuario_sistema, desde, hasta) VALUES (" + str(self.id_usuario_sistema) + ',' + str(amnodos.GetValue(desde,1)) + ',' + str(amnodos.GetValue(hasta,1)) + ")")
                cnn.commit()
            if amnodos.GetValue(desde,2) == 4: #Rebaje
                hasta = monodos.GetValue(n+1)
                if amnodos.GetValue(desde,38)>1000 and amnodos.GetValue(hasta,38)>1000: #Rebaje MT-MT
                    cursor.execute ("INSERT INTO Transformacion (id_usuario_sistema, desde, hasta) VALUES (" + str(self.id_usuario_sistema) + ',' + str(amnodos.GetValue(desde,1)) + ',' + str(amnodos.GetValue(hasta,1)) + ")")
                    cnn.commit()

        cursor = cnn.cursor()
        cursor.fast_executemany = True
        logger.info(str(len(self.seleccion_n)) + ' nodos navegados')
        logger.info(str(len(self.seleccion_l)) + ' lineas navegadas')
        # Preparamos los datos en una lista de tuplas
        datos_n = [(self.id_usuario_sistema, 1, n) for n in self.seleccion_n]
        datos_l = [(self.id_usuario_sistema, 2, l) for l in self.seleccion_l]
        todos_los_datos = datos_n + datos_l

        query = "INSERT INTO Selecciones (id_usuario_sistema, elemento, geoname) VALUES (?, ?, ?)"
        try:
            cursor.execute("DELETE FROM Selecciones WHERE id_usuario_sistema = ?", (self.id_usuario_sistema,))
            # Un solo comando para los miles de registros
            cursor.executemany(query, todos_los_datos)
            cnn.commit()
        except Exception as e:
            cnn.rollback()
            logger.error(f"Error en la carga masiva: {e}")

        #----------------------------------------------------------------------------
        #-------------------------------- GENERADORES -------------------------------
        #----------------------------------------------------------------------------
        self.seleccion_n = []
        self.seleccion_l = []
        self.seleccion_t = []
        #vamos a navegar desde los generadores seleccionados a la fuente
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute ("SELECT Nodos.geoname FROM Nodos INNER JOIN Selecciones ON Nodos.Geoname = Selecciones.geoname WHERE elmt=11 AND id_usuario_sistema = " + str(self.id_usuario_sistema))
        #convierto el cursor en array
        generadores = tuple(cursor)
        cursor.close()

        for i in range (0, len(generadores)):
            geoname = generadores[i][0]
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
            # Cargar el ensamblado
            clr.AddReference(os.path.join(basepath, 'NavRed6.dll'))
            #from EnerGis6.NavRed6 import NavRed
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
            for n in nodos_ordenados:
                if amnodos.GetValue(n,38) < 1000 and amnodos.GetValue(n,1) != 0:
                    self.seleccion_n.append(amnodos.GetValue(n,1))
                #aca guardamos todos los trafos que encontramos en la navegada a la fuente
                if amnodos.GetValue(n,2) == 4:
                    self.seleccion_t.append(amnodos.GetValue(n,1))
            for l in lineas_ordenadas:
                if amlineas.GetValue(l,5) < 1000 and amlineas.GetValue(l,1) != 0:
                    self.seleccion_l.append(amlineas.GetValue(l,1))

        cursor = cnn.cursor()
        cursor.fast_executemany = True
        # Preparamos los datos en una lista de tuplas
        datos_n = [(self.id_usuario_sistema, 11, n) for n in self.seleccion_n]
        datos_l = [(self.id_usuario_sistema, 12, l) for l in self.seleccion_l]
        todos_los_datos = datos_n + datos_l

        query = "INSERT INTO Selecciones (id_usuario_sistema, elemento, geoname) VALUES (?, ?, ?)"
        try:
            # Un solo comando para los miles de registros
            cursor.executemany(query, todos_los_datos)
            cnn.commit()
        except Exception as e:
            cnn.rollback()
            logger.error(f"Error en la carga masiva 2: {e}")

        cursor = cnn.cursor()
        for n in range (0, len(monodos)):
            desde = monodos.GetValue(n)
            if amnodos.GetValue(desde,1) in self.seleccion_t:
                hasta = monodos.GetValue(n+1)
                if amnodos.GetValue(desde,38)>1000 and amnodos.GetValue(hasta,38)<1000: #Trafo
                    cursor.execute ("INSERT INTO Transformacion (id_usuario_sistema, desde, hasta) VALUES (" + str(self.id_usuario_sistema) + ',' + str(amnodos.GetValue(desde,1)) + ',' + str(amnodos.GetValue(hasta,1)) + ")")
                    cnn.commit()

    def iniciar_calculo(self):
        # Desactivamos el botón para evitar múltiples clics
        self.cmdCalcular.setEnabled(False)
        self.progressBar.show()
        #Conectar señales del Worker
        self.worker = CortoWorker(self)
        self.worker.finished.connect(self.finalizar_calculo)
        self.worker.error.connect(self.finalizar_con_error)
        #self.worker.error.connect(lambda e: logger.error(f"Error: {e}"))
        self.worker.start()

    def proceso_calculo(self):
        logger = logging.getLogger("MiCorto")
        #Ejecución de las 5 consultas SQL
        logger.info("Extrayendo datos ...")
        try:
            #Función auxiliar para convertir recordset a DataFrame rápidamente
            def get_df(sql, connection):
                cursor = connection.cursor()
                cursor.execute(sql)
                columns = [column[0] for column in cursor.description]
                data = cursor.fetchall()
                # Convertimos las filas de pyodbc a una lista de listas
                return pd.DataFrame.from_records(data, columns=columns)
            # --- CATÁLOGO ---
            sql_cat = "SELECT Id AS id_tipo, CAST(REPLACE(Val3, ',', '.') AS FLOAT) AS r_ohm_per_km, CAST(REPLACE(Val4, ',', '.') AS FLOAT) AS x_ohm_per_km, CAST(REPLACE(Val7, ',', '.') AS FLOAT) * 1000 AS c_nf_per_km, CAST(REPLACE(Val5, ',', '.') AS FLOAT) AS r0_ohm_per_km, CAST(REPLACE(Val6, ',', '.') AS FLOAT) AS x0_ohm_per_km, 1 AS c0_nf_per_km, CAST(Val1 AS FLOAT) / 1000 AS max_i_ka FROM Elementos_Lineas"
            df_catalogo = get_df(sql_cat, self.conn)
            df_catalogo.set_index('id_tipo', inplace=True)

            # --- NODOS ---
            sql_nodos = "SELECT Nodos.geoname AS node_id, CASE WHEN elmt=8 THEN Val1 ELSE nombre END AS name, estado AS type, 'alimentador' as zone, CAST(CAST(tension AS decimal(8,2))/1000 AS FLOAT) AS vn_kv, 1 AS in_service, xcoord AS x, ycoord AS y, obj.STAsText() AS wkt" \
                        " FROM Nodos INNER JOIN Selecciones ON Nodos.Geoname = Selecciones.Geoname" \
                        " WHERE (Estado<>3 AND Tension>1000 AND elemento=1 OR Estado<>3 AND Tension<1000 AND elemento=11) AND id_usuario_sistema=" + str(self.id_usuario_sistema)
            df_nodos = get_df(sql_nodos, self.conn)

            # --- LÍNEAS ---
            sql_lineas = "SELECT Lineas.Geoname AS line_id, Lineas.Desde AS from_node, Lineas.Hasta AS to_node, Lineas.Elmt AS id_tipo, Lineas.Longitud / 1000 AS length_km, Lineas.obj.STAsText() AS wkt" \
                        " FROM Lineas INNER JOIN Selecciones ON Lineas.geoname = Selecciones.geoname INNER JOIN Nodos ON Lineas.Desde = Nodos.Geoname INNER JOIN Nodos AS Nodos_1 ON Lineas.Hasta = Nodos_1.Geoname" \
                        " WHERE Nodos.Estado<>3 AND Nodos_1.Estado<>3 AND id_usuario_sistema=" + str(self.id_usuario_sistema) + " AND (Lineas.Tension > 1000 AND elemento=2 OR Lineas.Tension < 1000 AND elemento=12)" \
                        " AND Lineas.Geoname NOT IN (SELECT Lineas.Geoname FROM Lineas INNER JOIN Transformacion ON Lineas.Desde = Transformacion.desde AND Lineas.Hasta = Transformacion.hasta WHERE id_usuario_sistema=" + str(self.id_usuario_sistema) + "" \
                        " UNION SELECT Lineas.Geoname FROM Lineas INNER JOIN Transformacion ON Lineas.Desde = Transformacion.hasta AND Lineas.Hasta = Transformacion.desde WHERE id_usuario_sistema=" + str(self.id_usuario_sistema) + ")"
            df_lineas = get_df(sql_lineas, self.conn)

            # --- GENERADORES / SLACK ---
            #En el caso de generadores, de todas las tensiones
            sql_gens = "SELECT Nodos.geoname AS node_id, Nodos.Nombre AS name, 0 AS p_a_mw, 0 AS p_b_mw, 0 AS p_c_mw, CAST(REPLACE(Val2,',','.') AS FLOAT) AS vm_pu, 0 AS q_max, 0 AS q_min, 1 AS tipo_slack, '' AS tipo_generador, CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[7]', 'float') AS sk2" \
                        " FROM Nodos INNER JOIN Selecciones ON Nodos.geoname = Selecciones.geoname" \
                        " WHERE Nodos.Tension>1000 AND Nodos.elmt=1 AND elemento=1 AND id_usuario_sistema=" + str(self.id_usuario_sistema) + "" \
                        " UNION SELECT Nodos.geoname AS node_id, Nodos.Nombre AS name," \
                        " CASE fases WHEN 123 THEN CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[3]', 'float')/3000 WHEN 12 THEN CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[3]', 'float')/2000 WHEN 31 THEN CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[3]', 'float')/2000 WHEN 1 THEN CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[3]', 'float')/1000 ELSE 0 END AS p_a_mw," \
                        " CASE fases WHEN 123 THEN CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[3]', 'float')/3000 WHEN 12 THEN CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[3]', 'float')/2000 WHEN 23 THEN CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[3]', 'float')/2000 WHEN 2 THEN CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[3]', 'float')/1000 ELSE 0 END AS p_b_mw," \
                        " CASE fases WHEN 123 THEN CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[3]', 'float')/3000 WHEN 23 THEN CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[3]', 'float')/2000 WHEN 31 THEN CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[3]', 'float')/2000 WHEN 3 THEN CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[3]', 'float')/1000 ELSE 0 END AS p_c_mw," \
                        " CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[4]', 'float') AS vm_pu," \
                        " CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[5]', 'float')/1000 AS q_max," \
                        " CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[6]', 'float')/1000 AS q_min, 0 AS tipo_slack, Val5 AS tipo_generador, 0 AS sk2" \
                        " FROM Nodos INNER JOIN Selecciones ON Nodos.geoname = Selecciones.geoname INNER JOIN mNodos ON Nodos.Geoname = mNodos.geoname" \
                        " WHERE Nodos.elmt=11 AND elemento=1 AND id_usuario_sistema=" + str(self.id_usuario_sistema)
            df_gens = get_df(sql_gens, self.conn)

            # --- SWITCHES ---
            #sql_sw = "SELECT Nodos.Geoname AS bus, Lineas.Geoname AS element, 'l' AS tipo_elem, CASE WHEN nodos.elmt = 2 THEN 1 ELSE 0 END AS closed FROM Nodos INNER JOIN Selecciones ON Nodos.Geoname = Selecciones.geoname INNER JOIN Lineas ON Nodos.Geoname = Lineas.Desde INNER JOIN Nodos AS Nodos_1 ON Lineas.Hasta = Nodos_1.Geoname WHERE (Nodos.Tension > 1000) AND (Nodos.Estado = 2) AND (Selecciones.elemento = 1) AND (Nodos_1.Estado <> 1) AND id_usuario_sistema=" + str(self.id_usuario_sistema)
            #df_switches = get_df(sql_sw, self.conn)

            # --- CARGAS ---
            sql_cargas = "SELECT Cargas_Nodos.geoname AS node_id," \
                        " CASE fases WHEN 123 THEN Cargas_Nodos.P * Cargas_Nodos.Fe / 3000 WHEN 12 THEN Cargas_Nodos.P * Cargas_Nodos.Fe / 2000 WHEN 31 THEN Cargas_Nodos.P * Cargas_Nodos.Fe / 2000 WHEN 1 THEN Cargas_Nodos.P * Cargas_Nodos.Fe / 1000 ELSE 0 END AS p_a_mw," \
                        " CASE fases WHEN 123 THEN Cargas_Nodos.P * Cargas_Nodos.Fe / 3000 WHEN 12 THEN Cargas_Nodos.P * Cargas_Nodos.Fe / 2000 WHEN 23 THEN Cargas_Nodos.P * Cargas_Nodos.Fe / 2000 WHEN 2 THEN Cargas_Nodos.P * Cargas_Nodos.Fe / 1000 ELSE 0 END AS p_b_mw," \
                        " CASE fases WHEN 123 THEN Cargas_Nodos.P * Cargas_Nodos.Fe / 3000 WHEN 23 THEN Cargas_Nodos.P * Cargas_Nodos.Fe / 2000 WHEN 31 THEN Cargas_Nodos.P * Cargas_Nodos.Fe / 2000 WHEN 3 THEN Cargas_Nodos.P * Cargas_Nodos.Fe / 1000 ELSE 0 END AS p_c_mw," \
                        " CASE fases WHEN 123 THEN Cargas_Nodos.Q * Cargas_Nodos.Fe / 3000 WHEN 12 THEN Cargas_Nodos.Q * Cargas_Nodos.Fe / 2000 WHEN 31 THEN Cargas_Nodos.Q * Cargas_Nodos.Fe / 2000 WHEN 1 THEN Cargas_Nodos.Q * Cargas_Nodos.Fe / 1000 ELSE 0 END AS q_a_mvar, " \
                        " CASE fases WHEN 123 THEN Cargas_Nodos.Q * Cargas_Nodos.Fe / 3000 WHEN 12 THEN Cargas_Nodos.Q * Cargas_Nodos.Fe / 2000 WHEN 23 THEN Cargas_Nodos.Q * Cargas_Nodos.Fe / 2000 WHEN 2 THEN Cargas_Nodos.Q * Cargas_Nodos.Fe / 1000 ELSE 0 END AS q_b_mvar," \
                        " CASE fases WHEN 123 THEN Cargas_Nodos.Q * Cargas_Nodos.Fe / 3000 WHEN 23 THEN Cargas_Nodos.Q * Cargas_Nodos.Fe / 2000 WHEN 31 THEN Cargas_Nodos.Q * Cargas_Nodos.Fe / 2000 WHEN 3 THEN Cargas_Nodos.Q * Cargas_Nodos.Fe / 1000 ELSE 0 END AS q_c_mvar" \
                        " FROM Nodos INNER JOIN Selecciones ON Nodos.geoname = Selecciones.geoname INNER JOIN Cargas_Nodos ON Nodos.Geoname = Cargas_Nodos.geoname INNER JOIN mNodos ON Nodos.Geoname = mNodos.geoname" \
                        " WHERE Nodos.Tension > 1000 AND Nodos.geoname NOT IN (SELECT Nodos.Geoname FROM Nodos INNER JOIN Transformadores ON Nodos.Nombre = Transformadores.Id_ct WHERE Nodos.Tension>1000 AND Nodos.Elmt = 4 AND Transformadores.Tension_1 > 1000 AND Transformadores.Tension_2 > 1000) AND elemento=1 AND id_usuario_sistema=" + str(self.id_usuario_sistema)
            df_cargas = get_df(sql_cargas, self.conn)

            # --- TRAFOS2W ---
            """ POR AHORA LOS TRAFOS SON TODOS TRIFASICOS, EN CASO DE QUERER MODELAR MONO Y BI, HAY QUE ARMAR OTRA SQL
            vector_group = I0 para monofasicos y bifasicos
            monofasicos hv_phase=[0] y lv_phase=[0] para fase R, para S seri [1] y para T seria [2]
            trafo bifasico RS hv_phase=[0,1]S """
            #Incluye trafos de MTBT a generadores
            #vector_group = Dyn; YNyn; Yzn
            sql_trafos2w = "SELECT Nodos.Geoname AS node_id, Nodos.Geoname AS hv_node, Transformacion.hasta AS lv_node, 'YNyn' AS vector_group, Transformadores.Potencia / 1000 AS sn_mva, CASE WHEN Nodos.Tension = Transformadores.Tension_1 THEN CAST(Nodos.Tension AS FLOAT) / 1000 ELSE CAST(Transformadores.Tension_1 AS FLOAT) / 1000 END AS vn_hv_kv, CASE WHEN Nodos.Tension = Transformadores.Tension_2 THEN CAST(Nodos.Tension AS FLOAT) / 1000 ELSE CAST(Transformadores.Tension_2 AS FLOAT) / 1000 END AS vn_lv_kv, SQRT(POWER(Transformadores_Parametros.R1, 2) + POWER(Transformadores_Parametros.X1, 2)) * 100 AS vk_percent, Transformadores_Parametros.R1 * 100 AS vkr_percent, Transformadores_Parametros.P01 / 1000 AS pfe_kw, Transformadores_Parametros.P01 / Transformadores.Potencia AS i0_percent, 2 AS tap_max, 0 AS tap_neutral, - 2 AS tap_min, - (1 * FLOOR((Transformadores_Parametros.Tap1 - 100) / 2.5)) AS tap_pos, 2.5 AS tap_step_percent, 0 AS tap_step_degree, 'hv' AS tap_side, 'Ratio' AS tap_changer_type" \
                            " FROM Nodos INNER JOIN Selecciones ON Nodos.Geoname = Selecciones.geoname INNER JOIN Transformadores ON Nodos.Nombre = Transformadores.Id_ct INNER JOIN Transformadores_Parametros ON Transformadores.Id_trafo = Transformadores_Parametros.Id_Trafo INNER JOIN Transformacion ON Selecciones.id_usuario_sistema = Transformacion.id_usuario_sistema AND Nodos.Geoname = Transformacion.desde" \
                            " WHERE Nodos.Elmt = 4 AND Transformadores.Tension_1 > 1000 AND Transformadores.Tension_2 > 1000 AND elemento = 1 AND Selecciones.id_usuario_sistema = " + str(self.id_usuario_sistema) + "" \
                            " UNION SELECT Nodos.Geoname AS node_id, Nodos.Geoname AS hv_node, Transformacion.hasta AS lv_node, 'Dyn' AS vector_group, Transformadores.Potencia / 1000 AS sn_mva, CASE WHEN Nodos.Tension = Transformadores.Tension_1 THEN CAST(Nodos.Tension AS FLOAT) / 1000 ELSE CAST(Transformadores.Tension_1 AS FLOAT) / 1000 END AS vn_hv_kv, CASE WHEN Nodos.Tension = Transformadores.Tension_2 THEN CAST(Nodos.Tension AS FLOAT) / 1000 ELSE CAST(Transformadores.Tension_2 AS FLOAT) / 1000 END AS vn_lv_kv, SQRT(POWER(Transformadores_Parametros.R1, 2) + POWER(Transformadores_Parametros.X1, 2)) * 100 AS vk_percent, Transformadores_Parametros.R1 * 100 AS vkr_percent, Transformadores_Parametros.P01 / 1000 AS pfe_kw, Transformadores_Parametros.P01 / Transformadores.Potencia AS i0_percent, 2 AS tap_max, 0 AS tap_neutral, - 2 AS tap_min, - (1 * FLOOR((Transformadores_Parametros.Tap1 - 100) / 2.5)) AS tap_pos, 2.5 AS tap_step_percent, 0 AS tap_step_degree, 'hv' AS tap_side, 'Ratio' AS tap_changer_type" \
                            " FROM Nodos INNER JOIN Transformadores ON Nodos.Nombre = Transformadores.Id_ct INNER JOIN Transformadores_Parametros ON Transformadores.Id_trafo = Transformadores_Parametros.Id_Trafo INNER JOIN Transformacion ON Nodos.Geoname = Transformacion.desde INNER JOIN" \
                            " (SELECT Selecciones.id_usuario_sistema, Transformacion_1.desde AS geoname" \
                            " FROM Selecciones INNER JOIN Transformacion AS Transformacion_1 ON Selecciones.geoname = Transformacion_1.hasta AND Selecciones.id_usuario_sistema = Transformacion_1.id_usuario_sistema" \
                            " WHERE Selecciones.elemento = 11) AS Trafos" \
                            " ON Transformacion.id_usuario_sistema = Trafos.id_usuario_sistema AND Nodos.Geoname = Trafos.geoname" \
                            " WHERE Transformacion.id_usuario_sistema=" + str(self.id_usuario_sistema)
            df_trafos2w = get_df(sql_trafos2w, self.conn)

            # --- REGULADORES ---
            #POR AHORA LOS PONEMOS TODOS EN ESTRELLA YNyn
            sql_reg = "SELECT Nodos.Geoname AS node_id, Nodos.Nombre AS name, Nodos.Geoname AS hv_node, Transformacion.hasta AS lv_node, 'YNyn' AS vector_group, CAST(Nodos.Val1 AS FLOAT) / 1000 AS sn_mva, CAST(Nodos.Tension AS FLOAT) / 1000 AS vn_hv_kv, CAST(Nodos.Tension AS FLOAT) / 1000 AS vn_lv_kv, 2 AS vk_percent, 0.5 AS vkr_percent, 0.12 * CAST(Nodos.Tension AS FLOAT) / 1000 AS pfe_kw, 0.1 AS i0_percent, CAST(Nodos.Val3 AS float) AS tap_max, 0 AS tap_neutral, - (1 * CAST(Nodos.Val3 AS float)) AS tap_min, 0 AS tap_pos, CAST(Nodos.Val4 AS float) AS tap_step_percent, 0 AS tap_step_degree, 'lv' AS tap_side, 'Ratio' AS tap_changer_type, CAST(Nodos.Val2 AS INT) AS orden FROM Nodos INNER JOIN Selecciones ON Nodos.Geoname = Selecciones.geoname INNER JOIN Transformacion ON Nodos.Geoname = Transformacion.desde AND Selecciones.id_usuario_sistema = Transformacion.id_usuario_sistema WHERE (Nodos.Tension > 1000) AND (Nodos.Elmt = 9) AND (Selecciones.elemento = 1) AND (Selecciones.id_usuario_sistema = " + str(self.id_usuario_sistema) + ")"
            df_reguladores = get_df(sql_reg, self.conn)
            # --- TRAFOS3W ---
            sql_trafos3w = "SELECT 0 AS hv_node, 0 AS mv_node, 0 AS lv_node, 0 AS sn_hv_mva, 0 AS sn_mv_mva, 0 AS sn_lv_mva, 0 AS vn_hv_kv, 0 AS vn_mv_kv, 0 AS vn_lv_kv, 0 AS vk_hv_percent, 0 AS vk_mv_percent, 0 AS vk_lv_percent, 0 AS vkr_hv_percent, 0 AS vkr_mv_percent, 0 AS vkr_lv_percent, 0 AS pfe_kw, 0 AS i0_percent, 0 AS tap_neutral, 0 AS tap_pos, 0 AS tap_step_percent, 'lv' AS tap_side FROM Nodos INNER JOIN Selecciones ON Nodos.geoname = Selecciones.geoname WHERE Tension>1000 AND Nodos.Geoname<0 AND elemento=1 AND id_usuario_sistema=" + str(self.id_usuario_sistema)
            df_trafos3w = get_df(sql_trafos3w, self.conn)
        except Exception as e:
            logger.error(f"Error en la conexión o extracción: {e}")

        logger.info("Creando red ...")
        #Inicialización de la red Pandapower
        net = pp.create_empty_network()
        net.asymmetric = True

        # Construcción de la Red (Mapeo de Nodos)
        bus_indices = pp.create_buses(net,
            nr_buses=len(df_nodos),
            name=df_nodos['name'].values,
            type=df_nodos['type'].values,
            zone=df_nodos['zone'].values,
            vn_kv=df_nodos['vn_kv'].values,
            in_service=df_nodos['in_service'].astype(bool).values
        )
        net.bus['geoname'] = df_nodos['node_id'].values
        mapping = dict(zip(df_nodos['node_id'], bus_indices))

        #Cargas y Generadores
        df_gens['vm_pu'] = df_gens['vm_pu']
        # Red Externa (Slack) - Extraemos los que tengan el flag tipo_slack
        slack_data = df_gens[df_gens['tipo_slack'].astype(int) == 1]
        for _, sl in slack_data.iterrows():
            pp.create_ext_grid(net,
                bus=mapping[sl['node_id']],
                vm_pu=sl['vm_pu'],
                s_sc_max_mva = sl['sk2'],
                rx_min = 0.1, #valor para AT, 0.3 para MT, 0.7 para BT
                rx_max = 0.2, #valor para AT, 0.5 para MT, >=1 para BT
                r0x0_max = 0.4,
                x0x_max = 1
            )

        """ x0x1_max (Relación de Reactancias)
        Este parámetro define la relación entre la reactancia de secuencia cero ($X_0$) y la de secuencia positiva ($X_1$).
        Es el valor que más influye en el desplazamiento del neutro ante cargas monofásicas.Valores típicos: 2.0 a 3.0.
        Redes con neutro rígidamente a tierra: Se usa 2.0 o 2.5.
        Es lo más común en salidas de subestaciones de distribución.
        Redes con neutro impedante: El valor puede subir a 4.0 o 5.0.
        Si no tienes el dato: Usa 3.0.
        Es el estándar "conservador" (IEEE) para representar una red de transmisión vista desde la media tensión.

        r0x0_max (Relación R/X de secuencia cero)Define la proporción entre la resistencia y la reactancia de la malla de secuencia cero.
        Valores típicos: 0.3 a 0.5.
        Significado: Un valor bajo (0.1) indica una conexión a tierra muy inductiva (transformadores grandes).
        Un valor más alto (1.0) indica que la resistencia de la malla de tierra o de los conductores de retorno tiene un peso significativo.
        Si no tienes el dato: Usa 0.4. """

        # Generadores (excluyendo el slack) - EQUILIBRADOS -
        # Definimos el mapeo de categorías a tipos de Pandapower
        mapa_tipos = {
            "Combustión Interna": "Motor",
            "Eólica": "WP",
            "Hidroeléctrica": "Motor",
            "Biomasa": "Motor",
            "Solar": "PV",
            "Otro": "Motor"
        }

        gen_data = df_gens[df_gens['tipo_slack'].astype(int) == 0]
        for _, gen in gen_data.iterrows():
            tipo_generador = gen['tipo_generador']
            tipo_maquina = mapa_tipos.get(tipo_generador, "Motor")
            id_bus = mapping.get(gen['node_id'])
            # Si es Solar o Eólica, usamos SGEN (Inyección de potencia PQ)
            if tipo_generador in ["Solar", "Eólica"]:
                pp.create_asymmetric_sgen(
                    net,
                    bus=id_bus,
                    name=gen['name'],
                    p_a_mw=gen['p_a_mw'],
                    p_b_mw=gen['p_b_mw'],
                    p_c_mw=gen['p_c_mw'],
                    q_a_mvar=0,  # Los inversores suelen operar a cos phi = 1 por defecto
                    q_b_mvar=0,  # Los inversores suelen operar a cos phi = 1 por defecto
                    q_c_mvar=0,  # Los inversores suelen operar a cos phi = 1 por defecto
                    type=tipo_maquina
                )
                logger.info(f"Creado SGEN (PQ) para {tipo_generador} en {gen['name']}")
            # Para el resto (Hidro, Biomasa, Motores), usamos GEN (Control de tensión PV)
            else:
                pp.create_asymmetric_sgen(
                    net,
                    bus=id_bus,
                    name=gen['name'],
                    p_a_mw=gen['p_a_mw'],
                    p_b_mw=gen['p_b_mw'],
                    p_c_mw=gen['p_c_mw'],
                    vm_pu=gen['vm_pu'],
                    max_q_mvar=gen['q_max'],
                    min_q_mvar=gen['q_min'],
                    type=tipo_maquina
                )
                logger.info(f"Creado GEN (PV) para {tipo_generador} en {gen['name']}")

        # Cargas PQ
        for _, carga in df_cargas.iterrows():
            id_bus = mapping.get(carga['node_id'])
            pp.create_asymmetric_load(net,
                bus=id_bus,
                p_a_mw=carga['p_a_mw'],
                q_a_mvar=carga['q_a_mvar'],
                p_b_mw=carga['p_b_mw'],
                q_b_mvar=carga['q_b_mvar'],
                p_c_mw=carga['p_c_mw'],
                q_c_mvar=carga['q_c_mvar']
            )

        #Ramas: Líneas
        #Convertimos el DataFrame a diccionario y lo cargamos en la red
        df_catalogo['r_ohm_per_km'] = df_catalogo['r_ohm_per_km'].clip(lower=0.05)
        df_catalogo['x_ohm_per_km'] = df_catalogo['x_ohm_per_km'].clip(lower=0.1)
        df_catalogo['c_nf_per_km'] = df_catalogo['c_nf_per_km'].clip(lower=1)
        df_catalogo['r0_ohm_per_km'] = df_catalogo['r0_ohm_per_km'].clip(lower=0.1)
        df_catalogo['x0_ohm_per_km'] = df_catalogo['x0_ohm_per_km'].clip(lower=0.1)
        df_catalogo['c0_nf_per_km'] = df_catalogo['c0_nf_per_km'].clip(lower=1)
        df_catalogo['max_i_ka'] = df_catalogo['max_i_ka'].clip(lower=0.1)
        for nombre_tipo, datos in df_catalogo.iterrows():
            pp.create_std_type(net, data=datos.to_dict(), name=nombre_tipo, element='line')
        df_lineas['length_km'] = df_lineas['length_km'].clip(lower=0.01) # Mínimo 10 m

        for idx, row in df_lineas.iterrows():
            pp.create_line(net,
                           from_bus=mapping[row.from_node],
                           to_bus=mapping[row.to_node],
                           length_km=row.length_km,
                           std_type=row.id_tipo,
                           name=row.line_id,
                           index=idx,
                           in_service=True)
        net.line['geoname'] = df_lineas['line_id'].values

        """for _, sw in df_switches.iterrows():
            pp.create_switch(
                net,
                bus=mapping[sw.bus],
                element=mapping_lineas[sw.element],
                et=sw.tipo_elem,
                closed=bool(sw.closed),
                type="LBS",
                name=f"SW_{sw.element}",
                z_ohm=0,      # Añade impedancia cero (ideal)
                in_ka=0.4     # O el valor nominal de tus seccionadores (ej. 400A)
                )
        """

        #Ramas: Transformadores
        # Transformadores 2 Arrollamientos (con Taps)
        mapping_trafos2w = {}
        df_trafos2w['i0_percent'] = df_trafos2w['i0_percent'].clip(upper=0.15)
        for _, tr in df_trafos2w.iterrows():
            trafo2w_indices = pp.create_transformer_from_parameters(
                net,
                hv_bus=mapping[tr['hv_node']],
                lv_bus=mapping[tr['lv_node']],
                sn_mva=float(tr['sn_mva']),
                vn_hv_kv=float(tr['vn_hv_kv']),
                vn_lv_kv=float(tr['vn_lv_kv']),
                vk_percent=float(tr['vk_percent']), #Tensión de cortocircuito (impedancia total).
                vk0_percent=float(tr['vk_percent']),
                vkr_percent=float(tr['vkr_percent']), #Tensión de cortocircuito (parte real/pérdidas en cobre)
                vkr0_percent=float(tr['vkr_percent']),
                pfe_kw=float(tr['pfe_kw']),
                i0_percent=float(tr['i0_percent']),
                mag0_percent=100,
                mag0_rx=0,
                si0_hv_partial=0.9,
                vector_group=tr['vector_group'],
                tap_min=int(tr['tap_min']),
                tap_neutral=int(tr['tap_neutral']),
                tap_max=int(tr['tap_max']),
                tap_pos=int(tr['tap_pos']),
                tap_step_percent=float(tr['tap_step_percent']),
                tap_step_degree=float(tr['tap_step_degree']),
                tap_side=str(tr['tap_side']),
                tap_changer_type=str(tr['tap_changer_type'])
            )
            mapping_trafos2w[tr['node_id']] = trafo2w_indices

            # Transformadores 3 Arrollamientos
            df_trafos3w['i0_percent'] = df_trafos3w['i0_percent'].clip(upper=0.15)
            for _, tr3 in df_trafos3w.iterrows():
                pp.create_transformer3w_from_parameters(
                    net,
                    hv_bus=mapping[tr3['hv_node']],
                    mv_bus=mapping[tr3['mv_node']],
                    lv_bus=mapping[tr3['lv_node']],
                    sn_hv_mva=tr3['sn_hv_mva'],
                    sn_mv_mva=tr3['sn_mv_mva'],
                    sn_lv_mva=tr3['sn_lv_mva'],
                    vn_hv_kv=tr3['vn_hv_kv'],
                    vn_mv_kv=tr3['vn_mv_kv'],
                    vn_lv_kv=tr3['vn_lv_kv'],
                    vk_hv_percent=tr3['vk_hv_percent'],
                    vk_mv_percent=tr3['vk_mv_percent'],
                    vk_lv_percent=tr3['vk_lv_percent'],
                    vkr_hv_percent=tr3['vkr_hv_percent'],
                    vkr_mv_percent=tr3['vkr_mv_percent'],
                    vkr_lv_percent=tr3['vkr_lv_percent'],
                    pfe_kw=tr3['pfe_kw'],
                    i0_percent=tr3['i0_percent'],
                    vector_group=tr3['vector_group'],
                    tap_max=tr['tap_max'],
                    tap_neutral=tr['tap_neutral'],
                    tap_min=tr['tap_min'],
                    tap_pos=tr3['tap_pos'],
                    tap_step_percent=tr3['tap_step_percent'],
                    tap_side=tr3['tap_side'] #'hv', 'mv' o 'lv'
                )

        #REGULADORES
        df_trafos2w['i0_percent'] = df_trafos2w['i0_percent'].clip(upper=0.15)
        for _, reg in df_reguladores.iterrows():
            trafo2w_indices = pp.create_transformer_from_parameters(
                net,
                hv_bus=mapping[reg['hv_node']],
                lv_bus=mapping[reg['lv_node']],
                sn_mva=float(reg['sn_mva']),
                vn_hv_kv=float(reg['vn_hv_kv']),
                vn_lv_kv=float(reg['vn_lv_kv']),
                vk_percent=float(reg['vk_percent']), #Tensión de cortocircuito (impedancia total).
                vk0_percent=float(reg['vk_percent']),
                vkr_percent=float(reg['vkr_percent']), #Tensión de cortocircuito (parte real/pérdidas en cobre)
                vkr0_percent=float(reg['vkr_percent']),
                pfe_kw=float(reg['pfe_kw']),
                i0_percent=float(reg['i0_percent']),
                mag0_percent=100,
                mag0_rx=0,
                si0_hv_partial=0.9,
                vector_group=reg['vector_group'],
                tap_min=int(reg['tap_min']),
                tap_neutral=int(reg['tap_neutral']),
                tap_max=int(reg['tap_max']),
                tap_pos=int(reg['tap_pos']),
                tap_step_percent=float(reg['tap_step_percent']),
                tap_step_degree=float(reg['tap_step_degree']),
                tap_side=str(reg['tap_side']),
                tap_changer_type=str(reg['tap_changer_type'])
            )
            mapping_trafos2w[reg['node_id']] = trafo2w_indices

            logger.info(f"Regulador {reg['name']} creado")

        #Ejecución del Flujo de Potencia
        logger.info("Verificando red ...")

        try:
            #Verificación previa (Sanity Check)
            # Líneas con Reactancia o Resistencia casi cero
            lineas_criticas = net.line[(net.line.x_ohm_per_km < 0.001) | (net.line.r_ohm_per_km < 0.001)]
            if not lineas_criticas.empty:
                ids_lineas = lineas_criticas['id_sql'].values # Usando el ID que guardamos
                logger.warning(f"❌ Líneas con impedancia muy baja (posible corto): {ids_lineas}")

            #Intento de ejecución del flujo de potencia
            logger.info("Iniciando cálculo de cortocircuito (IEC 60909) ...")

            logger.info("Exportando datos de depuración...")

            def exportar_debug_data(escenario, **tablas):
                carpeta_destino = "c:/gis/energis6/calculos/"
                if not os.path.exists(carpeta_destino):
                    os.makedirs(carpeta_destino)
                for nombre, df in tablas.items():
                    if df is not None:
                        path = os.path.join(carpeta_destino, f"{nombre}.txt")
                        # Usamos tabulaciones para que sea legible en bloc de notas
                        df.to_csv(path, sep='\t', index=True)

            exportar_debug_data(self.fuente, nodos=df_nodos, lineas=df_lineas, cargas=df_cargas, trafos2w=df_trafos2w, reguladores=df_reguladores, trafos3w=df_trafos3w, gens=df_gens)

            logger.info("Datos de depuración exportados !")

            #try:
            #    pp.to_excel(net, f"c:/gis/energis6/calculos/red_completa_debug_{self.fuente}.xlsx")
            #except Exception as e:
            #    logger.error(f"No se pudo exportar a Excel: {e}")

            falla = "3ph"
            if self.rbtMonofasico.isChecked():
                falla = "1ph"

            # Obtener el texto del QLineEdit
            nodos_input = self.txtNodos.text().strip()

            try:
                if nodos_input in ['', '*']:
                    # Caso: Toda la red
                    sc.calc_sc(net, fault=falla, case="max", branch_results=True)
                    logger.info("✅ Cortocircuito completado con éxito.")
                else:
                    # Convertir el texto en una lista de nombres (limpiando espacios)
                    geonames = [n.strip() for n in nodos_input.split(',')]
                    # Buscar los índices (IDs) que corresponden a esos geonames
                    # Usamos isin() para buscar todos de golpe en la columna geoname
                    indices_encontrados = net.bus[net.bus['geoname'].astype(str).isin(geonames)].index.tolist()
                    if not indices_encontrados:
                        logger.error(f"❌ No se encontró ningún nodo con los geonames: {geonames}")
                        return
                    # Ejecutar el corto usando los IDs numéricos encontrados
                    sc.calc_sc(net, fault=falla, case="max", branch_results=True, bus=indices_encontrados)
                    logger.info(f"✅ Corto ejecutado en {len(indices_encontrados)} nodos: {geonames}")

            except Exception as e:
                logger.error(f"❌ Error en el cálculo: {e}")

            return net, df_nodos, df_lineas, df_trafos2w, df_reguladores, df_trafos3w, df_gens, df_cargas, mapping

        except KeyError as e:

            logger.error(f"❌ Error de Mapeo: El nodo {e} mencionado en una rama no existe en la tabla de nodos.")

            self.exportar_log()
            return None, None, None, None, None, None, None

        except Exception as e:

            logger.error(f"❌ Error inesperado: {str(e)}")
            self.exportar_log()
            return None, None, None, None, None, None, None

    def calcular(self):
        logger = logging.getLogger("MiCorto")
        logger.info("Calculando cortocircuito ...")
        net, df_nodos, df_lineas, df_trafos2w, df_reguladores, df_trafos3w, df_gens, df_cargas, mapping = self.proceso_calculo()
        if not net is None:
            #Guardamos
            logger.info("Obteniendo resultados ...")
            #Extraemos resultados de ramas y nodos
            n_final, l_final = self.resultados(net, df_nodos, df_lineas, df_trafos2w, df_reguladores, df_trafos3w, df_gens, df_cargas, mapping)

            logger.info("Valores finales ...")

            # Aseguramos que n_final tenga node_id como índice para el mapeo
            n_final.set_index('node_id', inplace=True)

            # ACA SE AGREGAN O CALCULAN CAMPOS A LOS FINALES

            # Finalizamos el DataFrame
            n_final.reset_index(inplace=True)

            #Recuperamos el nombre (line_id) que guardamos en la red
            l_final = net.res_line_sc.copy()
            l_final['line_id'] = net.line['geoname'].values
            l_final['ikss_ka'] = net.res_line_sc.ikss_ka.values
            condicion_cero = np.isclose(net.res_line_sc.p_from_mw, 0, atol=1e-6)
            #Asignamos Potencia (P) y Tensión (Vm) dinámicamente
            #Si la condición es True -> toma el valor 'to', si es False -> toma el 'from'
            l_final['p_mw_oper'] = np.where(condicion_cero, net.res_line_sc.p_to_mw , net.res_line_sc.p_from_mw)
            l_final['vm_pu_oper'] = np.where(condicion_cero, net.res_line_sc.vm_to_pu, net.res_line_sc.vm_to_pu)

            self.exportar_resultados_txt(n_final, l_final)

            # --- UNIÓN DE GEOMETRÍAS (WKT) ---
            df_nodos['node_id'] = df_nodos['node_id'].astype(str)
            n_final['node_id'] = n_final['node_id'].astype(str)
            n_final = n_final.merge(df_nodos[['node_id', 'wkt']], on='node_id', how='left')

            df_lineas['line_id'] = df_lineas['line_id'].astype(str)
            l_final['line_id'] = l_final['line_id'].astype(str)
            l_final = l_final.merge(df_lineas[['line_id', 'wkt']], on='line_id', how='left')

            logger.info("Generando capas de resultado ...")

            # Definir qué columnas queremos ver en QGIS
            if self.rbtMonofasico.isChecked():
                campos_nodos = ['node_id','type','vn_kv','skss_mw','ikss_ka','rk_ohm','xk_ohm','rk0_ohm','xk0_ohm']
            else:
                campos_nodos = ['node_id','type','vn_kv','skss_mw','ikss_ka','rk_ohm','xk_ohm']
            campos_lineas = ['line_id','ikss_ka']

            root = QgsProject.instance().layerTreeRoot()
            nombre_grupo = "Resultados"

            # --- LIMPIEZA DE CORRIDAS ANTERIORES ---
            # Buscar si el grupo ya existe
            grupo = root.findGroup(nombre_grupo)
            if grupo:
                logger.info("Eliminando resultados de la corrida anterior...")
                # Obtenemos las capas de forma segura (copiando la lista de IDs)
                # No iteramos directamente sobre los objetos del árbol mientras borramos
                capas_ids = [layer_node.layerId() for layer_node in grupo.findLayers()]
                # Eliminamos las capas del proyecto (esto las quita del mapa y del grupo)
                if capas_ids:
                    QgsProject.instance().removeMapLayers(capas_ids)
            else:
                # Crear el grupo de la corrida
                grupo = root.insertGroup(0, nombre_grupo)

            # Aseguramos que la interfaz se refresque antes de seguir
            QgsProject.instance().setDirty(True)

            capa_nodos = self.crear_capa_memory("Potencias", n_final, campos_nodos)
            capa_lineas = self.crear_capa_memory("Corrientes", l_final, campos_lineas)
            try:
                if capa_nodos:
                    self.aplicar_estilo_qml(capa_nodos, "estilo_corto_nodos.qml")
                if capa_lineas:
                    self.aplicar_estilo_qml(capa_lineas, "estilo_corto_lineas.qml")
            except:
                logger.error("❌ Error al armar las capas.")
                return

            QgsProject.instance().addMapLayer(capa_nodos, False)
            grupo.addLayer(capa_nodos)
            QgsProject.instance().addMapLayer(capa_lineas, False)
            grupo.addLayer(capa_lineas)

            logger.info("🚀 Proceso terminado con éxito.")
            self.exportar_log()
        else:
            logger.error("❌ El cálculo falló.")
            self.exportar_log()

    def finalizar_calculo(self):
        self.cmdCalcular.setEnabled(True)
        self.progressBar.hide()
        QMessageBox.information(None, 'EnerGis 6', '🚀 Fin')
        self.exportar_log()

    def finalizar_con_error(self, mensaje):
        self.cmdCalcular.setEnabled(True)
        self.progressBar.hide()
        QMessageBox.critical(None, 'EnerGis 6', f"❌ Ocurrió un error inesperado:\n{mensaje}")
        self.exportar_log()

    def resultados(self, net, df_nodos, df_lineas, df_trafos2w, df_reguladores, df_trafos3w, df_gens, df_cargas, mapping):
        logger = logging.getLogger("MiCorto")
        logger.info("Exportando datos de depuración...")
        self.exportar_resultados_debug(net)
        try:
            #NODOS: Unimos el resultado al DataFrame original
            logger.info("Resultados ...")

            # Creamos el DataFrame basándonos SOLO en los buses que tienen resultados de SC
            nodos_final = pd.DataFrame(index=net.res_bus_sc.index)
            # Traemos los identificadores que guardamos en la red
            nodos_final['node_id'] = net.bus.loc[nodos_final.index, 'geoname']
            nodos_final['type'] = net.bus.loc[nodos_final.index, 'type']
            nodos_final['vn_kv'] = net.bus.loc[nodos_final.index, 'vn_kv']
            # Insertamos los resultados técnicos de la tabla de cortocircuito
            nodos_final['ikss_ka'] = net.res_bus_sc['ikss_ka']
            nodos_final['rk_ohm'] = net.res_bus_sc['rk_ohm']
            nodos_final['xk_ohm'] = net.res_bus_sc['xk_ohm']

            if self.rbtMonofasico.isChecked():
                nodos_final['rk0_ohm'] = net.res_bus_sc['rk0_ohm']
                nodos_final['xk0_ohm'] = net.res_bus_sc['xk0_ohm']
                nodos_final['skss_mw'] = net.res_bus_sc['ikss_ka'] * nodos_final['vn_kv'] * 1.73
            else:
                nodos_final['skss_mw'] = net.res_bus_sc['skss_mw']

            if self.rbtMonofasico.isChecked():
                nodos_final = nodos_final[['node_id', 'vn_kv', 'type', 'skss_mw', 'ikss_ka', 'rk_ohm', 'xk_ohm', 'rk0_ohm', 'xk0_ohm']]
            else:
                nodos_final = nodos_final[['node_id', 'vn_kv', 'type', 'skss_mw', 'ikss_ka', 'rk_ohm', 'xk_ohm']]

            """
            nodos_final = df_nodos.copy()
            # Usamos el índice de bus para asegurar que cada tensión vaya a su fila correcta
            nodos_final['rk_ohm'] = net.res_bus_sc.sort_index().rk_ohm.values
            nodos_final['xk_ohm'] = net.res_bus_sc.sort_index().xk_ohm.values
            nodos_final['ikss_ka'] = net.res_bus_sc.sort_index().ikss_ka.values
            if self.rbtMonofasico.isChecked():
                nodos_final['rk0_ohm'] = net.res_bus_sc.sort_index().rk0_ohm.values
                nodos_final['xk0_ohm'] = net.res_bus_sc.sort_index().xk0_ohm.values
                nodos_final['skss_mw'] = net.res_bus_sc.sort_index().ikss_ka.values * net.bus.vn_kv.values * 1.73
            else:
                nodos_final['skss_mw'] = net.res_bus_sc.sort_index().skss_mw.values

            if self.rbtMonofasico.isChecked():
                nodos_final = nodos_final[['node_id', 'vn_kv', 'type', 'skss_mw', 'ikss_ka', 'rk_ohm', 'xk_ohm', 'rk0_ohm', 'xk0_ohm']]
            else:
                nodos_final = nodos_final[['node_id', 'vn_kv', 'type', 'skss_mw', 'ikss_ka', 'rk_ohm', 'xk_ohm']]
            """

            #LÍNEAS: Mapeo por orden de creación
            lineas_final = df_lineas.copy()

        except Exception as e:
            logger.error(f"Error en la obtención de resultados : {e}")
            self.exportar_log()

        return nodos_final, lineas_final

    def exportar_log (self):
        logs = self.log_model.stringList()
        try:
            with open('c:/gis/energis6/calculos/log.txt', 'w', encoding='utf-8') as f:
                for linea in logs:
                    f.write(linea + '\n')
        except:
            pass

    def exportar_resultados_txt(self, n_final, l_final):
        logger = logging.getLogger("MiCorto")
        # Creamos la carpeta si no existe
        carpeta_destino = "c:/gis/energis6/calculos/"
        if not os.path.exists(carpeta_destino):
            os.makedirs(carpeta_destino)
        # Configuraciones de formato
        opciones = {'sep': '\t', 'index': False, 'decimal': ',', 'float_format': '%.6f'}
        try:
            #Exportar Nodos (n_final)
            ruta_nodos = os.path.join(carpeta_destino, "n_final.txt")
            n_final.to_csv(ruta_nodos, **opciones)
            #Exportar Líneas (l_final)
            ruta_lineas = os.path.join(carpeta_destino, "l_final.txt")
            l_final.to_csv(ruta_lineas, **opciones)
        except Exception as e:
            logger.error(f"Error al exportar txt: {e}")

    def exportar_resultados_debug(self, net):
        try:
            # Creamos la carpeta si no existe
            carpeta_destino = "c:/gis/energis6/calculos/"
            if not os.path.exists(carpeta_destino):
                os.makedirs(carpeta_destino)
            ruta_archivo = os.path.join(carpeta_destino, "debug_resultados.txt")
            with open(ruta_archivo, "w", encoding="utf-8") as f:
                f.write(f"ELEMENTOS EN NET: {net.bus.shape[0]} buses, {net.line.shape[0]} lineas\n\n")
                for tabla in ['res_bus_sc', 'res_line_sc']:
                    f.write(f"--- {tabla} ---\n")
                    df = getattr(net, tabla, pd.DataFrame())
                    f.write(df.to_string() if not df.empty else "VACÍA")
                    f.write("\n\n")
        except:
            pass

    def crear_capa_memory(self, nombre_capa, df, esquema_campos):
        if df.empty or 'wkt' not in df.columns:
            return None
        # Definir tipo de geometría
        wkt_test = str(df['wkt'].iloc[0]).upper()
        tipo_geom = "Point" if "POINT" in wkt_test else "LineString"
        # Crear la capa de memoria (Asegúrate que el EPSG coincida con tu proyecto)
        uri = f"{tipo_geom}?crs=EPSG:22195&index=yes"
        layer = QgsVectorLayer(uri, nombre_capa, "memory")
        pr = layer.dataProvider()
        # Agregar campos con detección de tipo
        campos_qgis = []
        for nombre in esquema_campos:
            if nombre not in df.columns: continue # Saltar si el campo no existe en el DF
            if "id" in nombre.lower():
                campos_qgis.append(QgsField(nombre, QVariant.String))
            elif "way" in nombre.lower():
                campos_qgis.append(QgsField(nombre, QVariant.Int))
            else:
                campos_qgis.append(QgsField(nombre, QVariant.Double))
        pr.addAttributes(campos_qgis)
        layer.updateFields()
        # Agregar Features
        features = []
        for _, fila in df.iterrows():
            f = QgsFeature(layer.fields())
            geom = QgsGeometry.fromWkt(fila['wkt'])
            if geom.isNull(): continue
            f.setGeometry(geom)
            # Mapear valores convirtiendo tipos de Numpy a nativos de Python
            attrs = []
            for campo in esquema_campos:
                val = fila[campo]
                if pd.isna(val):
                    attrs.append(0)
                elif isinstance(val, (np.integer, np.floating)):
                    attrs.append(val.item()) # .item() convierte numpy.float64 a float de Python
                else:
                    attrs.append(val)
            f.setAttributes(attrs)
            features.append(f)
        pr.addFeatures(features)
        layer.updateExtents()
        return layer

    def aplicar_estilo_qml(self, capa, nombre_archivo):
        if capa is None:
            return
        ruta_qml = os.path.join(basepath,"styles", nombre_archivo)
        if os.path.exists(ruta_qml):
            capa.loadNamedStyle(ruta_qml)
            capa.triggerRepaint()

    def salir(self):
        self.close()
