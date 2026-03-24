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
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import QThread, pyqtSignal, QStringListModel
from PyQt6.QtCore import QVariant
from PyQt6 import uic, QtCore #, QtWidgets

from pandapower.control import DiscreteTapControl
import pandapower.control as control
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

class FlujoWorker(QThread):
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

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_flujo_potencias_trifasico.ui'))

class frmFlujoPotencias(DialogType, DialogBase):
    def __init__(self, id_usuario_sistema, conn, fuente, amnodos, amlineas, monodos):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.id_usuario_sistema = id_usuario_sistema
        self.conn = conn
        self.fuente = fuente
        self.factor_escala = 1
        self.carga_original = 0
        self.carga_total = 0
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
        vfloat = QDoubleValidator()
        self.txtFactorGlobal.setValidator(vfloat)
        self.txtFactorTension.setValidator(vfloat)

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
                self.actualizar_carga()
        else:
            self.seleccionar_red(amnodos, amlineas, monodos, fuente)

        self.cmdCalcular.clicked.connect(self.iniciar_calculo)
        self.cmdCalcularCargas.clicked.connect(self.calculo_cargas)
        self.cmdAplicarFe.clicked.connect(self.aplicar_fe)
        self.txtFactorGlobal.textChanged.connect(self.recalcular_cargas)

        self.cmdSalir.clicked.connect(self.salir)

    def calculo_cargas(self):
        from .frm_calculo_cargas import frmCalculoCargas
        dialogo = frmCalculoCargas(self.conn, 2)
        dialogo.exec()
        self.actualizar_carga()
        dialogo.close()

    def aplicar_fe(self):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE Cargas_Nodos SET Fe=Fe * " + str(self.factor_escala) + " WHERE geoname IN (SELECT geoname FROM Selecciones WHERE id_usuario_sistema = " + self.id_usuario_sistema + ")")
        self.carga_original = self.carga_original * self.factor_escala
        self.carga_total = self.carga_original
        self.lblCarga.setText(f"Carga Total del Sistema [kW]: {self.carga_total:.1f}")
        self.txtFactorGlobal.setText("1.000")
        self.conn.commit()

    def recalcular_cargas(self):
        try:
            self.factor_escala = float(self.txtFactorGlobal.text())
            self.carga_total = self.carga_original * self.factor_escala
            self.lblCarga.setText(f"Carga Total del Sistema [kW]: {self.carga_total:.1f}")
        except:
            pass

    def actualizar_carga(self):
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT SUM(Cargas_Nodos.P * Cargas_Nodos.Fe) FROM Selecciones INNER JOIN Cargas_Nodos ON Selecciones.geoname = Cargas_Nodos.geoname INNER JOIN Nodos ON Selecciones.geoname = Nodos.geoname WHERE elmt=6 AND Selecciones.id_usuario_sistema=" + str(self.id_usuario_sistema))
        #convierto el cursor en array
        carga_original = tuple(cursor)
        cursor.close()
        if not carga_original is None:
            self.carga_original = carga_original[0][0]
            self.carga_total = self.carga_original
            self.lblCarga.setText(f"Carga Total del Sistema [kW]: {self.carga_total:.1f}")

    def setup_logging(self):
        handler = QListHandler(self.signaler)
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        #logger propio
        logger = logging.getLogger("MiFlujo")
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
        logger = logging.getLogger("MiFlujo")
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

        self.actualizar_carga()

    def iniciar_calculo(self):
        # Desactivamos el botón para evitar múltiples clics
        self.cmdCalcular.setEnabled(False)
        self.progressBar.show()
        #Conectar señales del Worker
        self.worker = FlujoWorker(self)
        self.worker.finished.connect(self.finalizar_calculo)
        self.worker.error.connect(self.finalizar_con_error)
        #self.worker.error.connect(lambda e: logger.error(f"Error: {e}"))
        self.worker.start()

    def proceso_calculo(self):
        logger = logging.getLogger("MiFlujo")
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
            sql_gens = "SELECT Nodos.geoname AS node_id, Nodos.Nombre AS name, 0 AS p_a_mw, 0 AS p_b_mw, 0 AS p_c_mw, CAST(REPLACE(Val2,',','.') AS FLOAT) AS vm_pu, 0 AS q_max, 0 AS q_min, 1 AS tipo_slack, '' AS tipo_generador" \
                        " FROM Nodos INNER JOIN Selecciones ON Nodos.geoname = Selecciones.geoname" \
                        " WHERE Nodos.Tension>1000 AND Nodos.elmt=1 AND elemento=1 AND id_usuario_sistema=" + str(self.id_usuario_sistema) + "" \
                        " UNION SELECT Nodos.geoname AS node_id, Nodos.Nombre AS name," \
                        " CASE fases WHEN 123 THEN CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[3]', 'float')/3000 WHEN 12 THEN CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[3]', 'float')/2000 WHEN 31 THEN CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[3]', 'float')/2000 WHEN 1 THEN CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[3]', 'float')/1000 ELSE 0 END AS p_a_mw," \
                        " CASE fases WHEN 123 THEN CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[3]', 'float')/3000 WHEN 12 THEN CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[3]', 'float')/2000 WHEN 23 THEN CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[3]', 'float')/2000 WHEN 2 THEN CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[3]', 'float')/1000 ELSE 0 END AS p_b_mw," \
                        " CASE fases WHEN 123 THEN CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[3]', 'float')/3000 WHEN 23 THEN CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[3]', 'float')/2000 WHEN 31 THEN CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[3]', 'float')/2000 WHEN 3 THEN CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[3]', 'float')/1000 ELSE 0 END AS p_c_mw," \
                        " CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[4]', 'float') AS vm_pu," \
                        " CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[5]', 'float')/1000 AS q_max," \
                        " CAST('<x>' + REPLACE(Val4, '|', '</x><x>') + '</x>' AS XML).value('/x[6]', 'float')/1000 AS q_min, 0 AS tipo_slack, Val5 AS tipo_generador" \
                        " FROM Nodos INNER JOIN Selecciones ON Nodos.geoname = Selecciones.geoname INNER JOIN mNodos ON Nodos.Geoname = mNodos.geoname" \
                        " WHERE Nodos.elmt=11 AND elemento=1 AND id_usuario_sistema=" + str(self.id_usuario_sistema)
            df_gens = get_df(sql_gens, self.conn)

            # --- SWITCHES ---
            #sql_sw = "SELECT Nodos.Geoname AS bus, Lineas.Geoname AS element, 'l' AS tipo_elem, CASE WHEN nodos.elmt = 2 THEN 1 ELSE 0 END AS closed FROM Nodos INNER JOIN Selecciones ON Nodos.Geoname = Selecciones.geoname INNER JOIN Lineas ON Nodos.Geoname = Lineas.Desde INNER JOIN Nodos AS Nodos_1 ON Lineas.Hasta = Nodos_1.Geoname WHERE (Nodos.Tension > 1000) AND (Nodos.Estado = 2) AND (Selecciones.elemento = 1) AND (Nodos_1.Estado <> 1) AND id_usuario_sistema=" + str(self.id_usuario_sistema)
            #df_switches = get_df(sql_sw, self.conn)

            # --- CARGAS ---
            sql_cargas = "SELECT Cargas_Nodos.geoname AS node_id," \
                        " CASE fases WHEN 123 THEN Cargas_Nodos.P * Cargas_Nodos.Fe * " + str(self.factor_escala) + " / 3000 WHEN 12 THEN Cargas_Nodos.P * Cargas_Nodos.Fe * " + str(self.factor_escala) + " / 2000 WHEN 31 THEN Cargas_Nodos.P * Cargas_Nodos.Fe * " + str(self.factor_escala) + " / 2000 WHEN 1 THEN Cargas_Nodos.P * Cargas_Nodos.Fe * " + str(self.factor_escala) + " / 1000 ELSE 0 END AS p_a_mw," \
                        " CASE fases WHEN 123 THEN Cargas_Nodos.P * Cargas_Nodos.Fe * " + str(self.factor_escala) + " / 3000 WHEN 12 THEN Cargas_Nodos.P * Cargas_Nodos.Fe * " + str(self.factor_escala) + " / 2000 WHEN 23 THEN Cargas_Nodos.P * Cargas_Nodos.Fe * " + str(self.factor_escala) + " / 2000 WHEN 2 THEN Cargas_Nodos.P * Cargas_Nodos.Fe * " + str(self.factor_escala) + " / 1000 ELSE 0 END AS p_b_mw," \
                        " CASE fases WHEN 123 THEN Cargas_Nodos.P * Cargas_Nodos.Fe * " + str(self.factor_escala) + " / 3000 WHEN 23 THEN Cargas_Nodos.P * Cargas_Nodos.Fe * " + str(self.factor_escala) + " / 2000 WHEN 31 THEN Cargas_Nodos.P * Cargas_Nodos.Fe * " + str(self.factor_escala) + " / 2000 WHEN 3 THEN Cargas_Nodos.P * Cargas_Nodos.Fe * " + str(self.factor_escala) + " / 1000 ELSE 0 END AS p_c_mw," \
                        " CASE fases WHEN 123 THEN Cargas_Nodos.Q * Cargas_Nodos.Fe * " + str(self.factor_escala) + " / 3000 WHEN 12 THEN Cargas_Nodos.Q * Cargas_Nodos.Fe * " + str(self.factor_escala) + " / 2000 WHEN 31 THEN Cargas_Nodos.Q * Cargas_Nodos.Fe * " + str(self.factor_escala) + " / 2000 WHEN 1 THEN Cargas_Nodos.Q * Cargas_Nodos.Fe * " + str(self.factor_escala) + " / 1000 ELSE 0 END AS q_a_mvar, " \
                        " CASE fases WHEN 123 THEN Cargas_Nodos.Q * Cargas_Nodos.Fe * " + str(self.factor_escala) + " / 3000 WHEN 12 THEN Cargas_Nodos.Q * Cargas_Nodos.Fe * " + str(self.factor_escala) + " / 2000 WHEN 23 THEN Cargas_Nodos.Q * Cargas_Nodos.Fe * " + str(self.factor_escala) + " / 2000 WHEN 2 THEN Cargas_Nodos.Q * Cargas_Nodos.Fe * " + str(self.factor_escala) + " / 1000 ELSE 0 END AS q_b_mvar," \
                        " CASE fases WHEN 123 THEN Cargas_Nodos.Q * Cargas_Nodos.Fe * " + str(self.factor_escala) + " / 3000 WHEN 23 THEN Cargas_Nodos.Q * Cargas_Nodos.Fe * " + str(self.factor_escala) + " / 2000 WHEN 31 THEN Cargas_Nodos.Q * Cargas_Nodos.Fe * " + str(self.factor_escala) + " / 2000 WHEN 3 THEN Cargas_Nodos.Q * Cargas_Nodos.Fe * " + str(self.factor_escala) + " / 1000 ELSE 0 END AS q_c_mvar" \
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
        fet = float(self.txtFactorTension.text())
        df_gens['vm_pu'] = df_gens['vm_pu'] * fet
        # Red Externa (Slack) - Extraemos los que tengan el flag tipo_slack
        slack_data = df_gens[df_gens['tipo_slack'].astype(int) == 1]
        for _, sl in slack_data.iterrows():
            pp.create_ext_grid(net,
                bus=mapping[sl['node_id']],
                vm_pu=sl['vm_pu'],
                s_sc_max_mva = 100,
                rx_min = 0.1, #valor para AT, 0.3 para MT, 0.7 para BT
                rx_max = 0.2, #valor para AT, 0.5 para MT, >=1 para BT
                r0x0_max = 0.4,
                x0x_max = 1
            )

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
        df_catalogo['r_ohm_per_km'] = df_catalogo['r_ohm_per_km'].clip(lower=0.1)
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
                logger.critical(f"❌ Líneas con impedancia muy baja (posible corto): {ids_lineas}")

            #Intento de ejecución del flujo de potencia
            logger.info("Iniciando cálculo de flujo de potencia (Newton-Raphson) ...")

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

            # Usamos init='dc' para mayor estabilidad inicial
            if self.chkRegulacion.isChecked()==True:
                # Limpiamos controladores previos por seguridad
                net.controller = net.controller.iloc[0:0]
                for _, reg in df_reguladores.iterrows():
                    # Buscamos el índice interno que Pandapower le asignó a este trafo
                    tid = mapping_trafos2w.get(reg['node_id'])
                    orden = int(reg['orden'])
                    tolerance = 0.01 + (orden - 1) * 0.005
                    #sacamos: , order=orden
                    ct = DiscreteTapControl(net, element_index=tid, vm_lower_pu=1, vm_upper_pu=1.05, side='lv', element='trafo', tol=tolerance, in_service=True, drop_same_existing_ctrl=True)
                    # Esto asegura que el controlador lea el estado actual de la red
                    ct.initialize_control(net)
                    logger.info(f"Controlador inicializado para el regulador {reg['node_id']}")
                #try:
                #    pp.to_excel(net, f"c:/gis/energis6/calculos/red_completa_debug_{self.fuente}.xlsx")
                #except Exception as e:
                #    logger.error(f"No se pudo exportar a Excel: {e}")

                # Definimos los argumentos para el flujo trifásico
                # Es vital usar init='flat' o 'y' como vimos antes
                kwargs = {
                    "init": "flat",
                    "algorithm": "nr",
                    "v_debug":True,
                    "calculate_voltage_angles": True,
                    "check_connectivity": True, #"numba": True,
                    "ctrl_variables": None,
                    "tolerance_mva=1e": 3,
                    "max_iter": 30,
                    "continue_on_divergence": True,
                    "check_each_level": True
                }

                logger.info("...")

                control.run_control(net, run=pp.runpp_3ph, **kwargs)
            else:
                #try:
                #    pp.to_excel(net, f"c:/gis/energis6/calculos/red_completa_debug_{self.fuente}.xlsx")
                #except Exception as e:
                #    logger.error(f"No se pudo exportar a Excel: {e}")

                pp.runpp_3ph(net, init='flat', v_debug=False, algorithm='nr', calculate_voltage_angles=True, enforce_q_lims=True, check_connectivity=True, numba=True)
                #pp.runpp_3ph(net, init='y', algorithm='nr')

            logger.info("✅ Flujo de potencia completado con éxito.")

            return net, df_nodos, df_lineas, df_trafos2w, df_reguladores, df_trafos3w, df_gens, df_cargas, mapping

        except pp.LoadflowNotConverged:

            logger.error("❌ Error: El flujo de potencia NO convergió (Newton-Raphson falló).")
            self.exportar_log()
            return None, None, None, None, None, None, None

        except KeyError as e:

            logger.error(f"❌ Error de Mapeo: El nodo {e} mencionado en una rama no existe en la tabla de nodos.")

            self.exportar_log()
            return None, None, None, None, None, None, None

        except Exception as e:

            logger.error(f"❌ Error inesperado: {str(e)}")
            self.exportar_log()
            return None, None, None, None, None, None, None

    def calcular(self):
        logger = logging.getLogger("MiFlujo")
        logger.info("Calculando flujo ...")
        net, df_nodos, df_lineas, df_trafos2w, df_reguladores, df_trafos3w, df_gens, df_cargas, mapping = self.proceso_calculo()
        if not net is None:
            #Guardamos
            logger.info("Obteniendo resultados ...")
            #Extraemos resultados de ramas y nodos
            n_final, l_final, t_final, t3_final, g_final = self.resultados(net, df_nodos, df_lineas, df_trafos2w, df_reguladores, df_trafos3w, df_gens, df_cargas, mapping)

            logger.info("Valores finales ...")

            # Aseguramos que n_final tenga node_id como índice para el mapeo
            n_final.set_index('node_id', inplace=True)
            n_final['p_mw'] = 0.0
            n_final['q_mvar'] = 0.0

            # Sumamos CARGAS (Consumo: P > 0)
            res_load = getattr(net, 'res_load_3ph', pd.DataFrame()) #Si no existe, devuelve un DataFrame vacío en lugar de lanzar error
            if not res_load.empty:
                # Importante: mapear usando 'geoname' que es el node_id
                res_load['node_id'] = net.bus.loc[net.load.bus.values, 'geoname'].values
                cargas_a_sum = res_load.groupby('node_id')[['p_a_mw', 'q_a_mvar']].sum()
                n_final['p_mw'] = n_final['p_mw'].add(cargas_a_sum['p_a_mw'], fill_value=0)
                n_final['q_mvar'] = n_final['q_mvar'].add(cargas_a_sum['q_a_mvar'], fill_value=0)
                cargas_b_sum = res_load.groupby('node_id')[['p_b_mw', 'q_b_mvar']].sum()
                n_final['p_mw'] = n_final['p_mw'].add(cargas_b_sum['p_b_mw'], fill_value=0)
                n_final['q_mvar'] = n_final['q_mvar'].add(cargas_b_sum['q_b_mvar'], fill_value=0)
                cargas_c_sum = res_load.groupby('node_id')[['p_c_mw', 'q_c_mvar']].sum()
                n_final['p_mw'] = n_final['p_mw'].add(cargas_c_sum['p_c_mw'], fill_value=0)
                n_final['q_mvar'] = n_final['q_mvar'].add(cargas_c_sum['q_c_mvar'], fill_value=0)

            res_load = getattr(net, 'res_asymmetric_load_3ph', pd.DataFrame()) #Si no existe, devuelve un DataFrame vacío en lugar de lanzar error
            if not res_load.empty:
                # Importante: mapear usando 'geoname' que es el node_id
                res_load['node_id'] = net.bus.loc[net.asymmetric_load.bus.values, 'geoname'].values
                cargas_a_sum = res_load.groupby('node_id')[['p_a_mw', 'q_a_mvar']].sum()
                n_final['p_mw'] = n_final['p_mw'].add(cargas_a_sum['p_a_mw'], fill_value=0)
                n_final['q_mvar'] = n_final['q_mvar'].add(cargas_a_sum['q_a_mvar'], fill_value=0)
                cargas_b_sum = res_load.groupby('node_id')[['p_b_mw', 'q_b_mvar']].sum()
                n_final['p_mw'] = n_final['p_mw'].add(cargas_b_sum['p_b_mw'], fill_value=0)
                n_final['q_mvar'] = n_final['q_mvar'].add(cargas_b_sum['q_b_mvar'], fill_value=0)
                cargas_c_sum = res_load.groupby('node_id')[['p_c_mw', 'q_c_mvar']].sum()
                n_final['p_mw'] = n_final['p_mw'].add(cargas_c_sum['p_c_mw'], fill_value=0)
                n_final['q_mvar'] = n_final['q_mvar'].add(cargas_c_sum['q_c_mvar'], fill_value=0)

            # Restamos GENERADORES
            # Restamos porque inyección es potencia saliendo del nodo hacia la red
            res_sgen = getattr(net, 'res_sgen_3ph', pd.DataFrame()) #Si no existe, devuelve un DataFrame vacío en lugar de lanzar error
            if not res_sgen.empty:
                res_sgen['node_id'] = net.bus.loc[net.res_sgen.bus.values, 'geoname'].values
                gen_a_sum = res_sgen.groupby('node_id')[['p_a_mw', 'q_a_mvar']].sum()
                n_final['p_mw'] = n_final['p_mw'].subtract(gen_a_sum['p_a_mw'], fill_value=0)
                n_final['q_mvar'] = n_final['q_mvar'].subtract(gen_a_sum['q_a_mvar'], fill_value=0)
                gen_b_sum = res_sgen.groupby('node_id')[['p_b_mw', 'q_b_mvar']].sum()
                n_final['p_mw'] = n_final['p_mw'].subtract(gen_b_sum['p_b_mw'], fill_value=0)
                n_final['q_mvar'] = n_final['q_mvar'].subtract(gen_b_sum['q_b_mvar'], fill_value=0)
                gen_c_sum = res_sgen.groupby('node_id')[['p_c_mw', 'q_c_mvar']].sum()
                n_final['p_mw'] = n_final['p_mw'].subtract(gen_c_sum['p_c_mw'], fill_value=0)
                n_final['q_mvar'] = n_final['q_mvar'].subtract(gen_c_sum['q_c_mvar'], fill_value=0)

            res_gen = getattr(net, 'res_gen_3ph', pd.DataFrame()) #Si no existe, devuelve un DataFrame vacío en lugar de lanzar error
            if not res_gen.empty:
                res_gen['node_id'] = net.bus.loc[net.gen.bus.values, 'geoname'].values
                gen_a_sum = res_gen.groupby('node_id')[['p_a_mw', 'q_a_mvar']].sum()
                n_final['p_mw'] = n_final['p_mw'].subtract(gen_a_sum['p_a_mw'], fill_value=0)
                n_final['q_mvar'] = n_final['q_mvar'].subtract(gen_a_sum['q_a_mvar'], fill_value=0)
                gen_b_sum = res_gen.groupby('node_id')[['p_b_mw', 'q_b_mvar']].sum()
                n_final['p_mw'] = n_final['p_mw'].subtract(gen_b_sum['p_b_mw'], fill_value=0)
                n_final['q_mvar'] = n_final['q_mvar'].subtract(gen_b_sum['q_b_mvar'], fill_value=0)
                gen_c_sum = res_gen.groupby('node_id')[['p_c_mw', 'q_c_mvar']].sum()
                n_final['p_mw'] = n_final['p_mw'].subtract(gen_c_sum['p_c_mw'], fill_value=0)
                n_final['q_mvar'] = n_final['q_mvar'].subtract(gen_c_sum['q_c_mvar'], fill_value=0)

            res_gen = getattr(net, 'res_asymmetric_sgen_3ph', pd.DataFrame()) #Si no existe, devuelve un DataFrame vacío en lugar de lanzar error
            if not res_gen.empty:
                indices_generadores = res_gen.index
                #Buscamos a qué BUS pertenece cada uno en la tabla de ENTRADA (net.asymmetric_sgen)
                buses_indices = net.asymmetric_sgen.loc[indices_generadores, 'bus'].values
                #Mapeamos esos índices de bus a sus nombres originales (geoname) en net.bus
                res_gen['node_id'] = net.bus.loc[buses_indices, 'geoname'].values
                gen_a_sum = res_gen.groupby('node_id')[['p_a_mw', 'q_a_mvar']].sum()
                n_final['p_mw'] = n_final['p_mw'].subtract(gen_a_sum['p_a_mw'], fill_value=0)
                n_final['q_mvar'] = n_final['q_mvar'].subtract(gen_a_sum['q_a_mvar'], fill_value=0)
                gen_b_sum = res_gen.groupby('node_id')[['p_b_mw', 'q_b_mvar']].sum()
                n_final['p_mw'] = n_final['p_mw'].subtract(gen_b_sum['p_b_mw'], fill_value=0)
                n_final['q_mvar'] = n_final['q_mvar'].subtract(gen_b_sum['q_b_mvar'], fill_value=0)
                gen_c_sum = res_gen.groupby('node_id')[['p_c_mw', 'q_c_mvar']].sum()
                n_final['p_mw'] = n_final['p_mw'].subtract(gen_c_sum['p_c_mw'], fill_value=0)
                n_final['q_mvar'] = n_final['q_mvar'].subtract(gen_c_sum['q_c_mvar'], fill_value=0)

            # Restamos la RED EXTERNA (Slack)
            if not net.res_ext_grid_3ph.empty:
                res_ext = net.res_ext_grid_3ph.copy()
                res_ext['node_id'] = net.bus.loc[net.ext_grid.bus.values, 'geoname'].values
                slack_a_sum = res_ext.groupby('node_id')[['p_a_mw', 'q_a_mvar']].sum()
                n_final['p_mw'] = n_final['p_mw'].subtract(slack_a_sum['p_a_mw'], fill_value=0)
                n_final['q_mvar'] = n_final['q_mvar'].subtract(slack_a_sum['q_a_mvar'], fill_value=0)
                slack_b_sum = res_ext.groupby('node_id')[['p_b_mw', 'q_b_mvar']].sum()
                n_final['p_mw'] = n_final['p_mw'].subtract(slack_b_sum['p_b_mw'], fill_value=0)
                n_final['q_mvar'] = n_final['q_mvar'].subtract(slack_b_sum['q_b_mvar'], fill_value=0)
                slack_c_sum = res_ext.groupby('node_id')[['p_c_mw', 'q_c_mvar']].sum()
                n_final['p_mw'] = n_final['p_mw'].subtract(slack_c_sum['p_c_mw'], fill_value=0)
                n_final['q_mvar'] = n_final['q_mvar'].subtract(slack_c_sum['q_c_mvar'], fill_value=0)

            # Finalizamos el DataFrame
            n_final.reset_index(inplace=True)

            #Recuperamos el nombre (line_id) que guardamos en la red
            l_final = net.res_line_3ph.copy()
            l_final['line_id'] = net.line['geoname'].values

            # En res_line_3ph, las potencias tienen sufijos _from_mw o _to_mw
            # Usamos las de entrada (from) para el balance y sentido
            fases = ['a', 'b', 'c']
            p_cols = [f'p_{f}_from_mw' for f in fases]
            q_cols = [f'q_{f}_from_mvar' for f in fases]

            # Verificamos que las columnas existan antes de sumar
            if all(col in l_final.columns for col in p_cols):
                p_total_mw = l_final[p_cols[0]] + l_final[p_cols[1]] + l_final[p_cols[2]]
                q_total_mvar = l_final[q_cols[0]] + l_final[q_cols[1]] + l_final[q_cols[2]]
                l_final['p_kw'] = 1000 * p_total_mw.abs()
                l_final['q_kvar'] = 1000 * q_total_mvar.abs()
                # Sentido del flujo
                l_final['way_p'] = np.where(p_total_mw >= 0, 1, -1)
                l_final['way_q'] = np.where(q_total_mvar >= 0, 1, -1)
            else:
                logger.error("No se encontraron las columnas de potencia esperadas en res_line_3ph")
                # Valores por defecto para evitar que el script falle después
                l_final['p_kw'] = 0.0
                l_final['q_kvar'] = 0.0
                l_final['way_p'] = 1
                l_final['way_q'] = 1

            # Corrientes en Amperes (ka -> A)
            # En líneas 3ph, las corrientes suelen ser i_a_ka, i_b_ka, i_c_ka (promedio de la línea)
            for fase in fases:
                col_ka = f'i_{fase}_ka'
                if col_ka in l_final.columns:
                    l_final[f'i_{fase}'] = l_final[col_ka] * 1000
                else:
                    # Si no están, intentamos con i_fase_from_ka
                    col_from_ka = f'i_{fase}_from_ka'
                    if col_from_ka in l_final.columns:
                        l_final[f'i_{fase}'] = l_final[col_from_ka] * 1000
                    else:
                        l_final[f'i_{fase}'] = 0.0

            # --- UNIÓN DE GEOMETRÍAS (WKT) ---
            df_nodos['node_id'] = df_nodos['node_id'].astype(str)
            n_final['node_id'] = n_final['node_id'].astype(str)
            n_final = n_final.merge(df_nodos[['node_id', 'wkt']], on='node_id', how='left')

            df_lineas['line_id'] = df_lineas['line_id'].astype(str)
            l_final['line_id'] = l_final['line_id'].astype(str)
            l_final = l_final.merge(df_lineas[['line_id', 'wkt']], on='line_id', how='left')

            logger.info("Generando capas de resultado ...")

            # Definir qué columnas queremos ver en QGIS
            campos_nodos = ['node_id','type','vn_kv','vm_a_pu','vm_b_pu','vm_c_pu','p_mw','q_mvar']
            campos_lineas = ['line_id','p_kw','q_kvar','i_a','i_b','i_c','loading_percent','way_p','way_q']

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

            try:
                capa_nodos = self.crear_capa_memory("Tensiones", n_final, campos_nodos)
                capa_lineas = self.crear_capa_memory("Corrientes", l_final, campos_lineas)
                if capa_nodos:
                    self.aplicar_estilo_qml(capa_nodos, "estilo_flujo_nodos_3f.qml")
                if capa_lineas:
                    self.aplicar_estilo_qml(capa_lineas, "estilo_flujo_lineas3f.qml")
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
            logger.error("❌ El flujo no converje.")
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
        logger = logging.getLogger("MiFlujo")
        logger.info("Exportando datos de depuración...")
        self.exportar_resultados_debug(net)
        try:
            inv_mapping = {v: k for k, v in mapping.items()}
            #NODOS: Unimos el resultado al DataFrame original
            logger.info("Resultados ...")

            nodos_final = df_nodos.copy()
            # Usamos el índice de bus para asegurar que cada tensión vaya a su fila correcta
            nodos_final['vm_a_pu'] = net.res_bus_3ph.sort_index().vm_a_pu.values
            nodos_final['vm_b_pu'] = net.res_bus_3ph.sort_index().vm_b_pu.values
            nodos_final['vm_c_pu'] = net.res_bus_3ph.sort_index().vm_c_pu.values
            nodos_final['va_a_degree'] = net.res_bus_3ph.sort_index().va_a_degree.values
            nodos_final['va_b_degree'] = net.res_bus_3ph.sort_index().va_b_degree.values
            nodos_final['va_c_degree'] = net.res_bus_3ph.sort_index().va_c_degree.values
            nodos_final = nodos_final[['node_id', 'name', 'vn_kv', 'type', 'vm_a_pu', 'va_a_degree', 'vm_b_pu', 'va_b_degree', 'vm_c_pu', 'va_c_degree']]
            #LÍNEAS: Mapeo por orden de creación

            lineas_final = df_lineas.copy()
            lineas_final['p_a_mw'] = net.res_line_3ph.p_a_from_mw.values
            lineas_final['p_b_mw'] = net.res_line_3ph.p_b_from_mw.values
            lineas_final['p_c_mw'] = net.res_line_3ph.p_c_from_mw.values
            lineas_final['q_a_mvar'] = net.res_line_3ph.q_a_from_mvar.values
            lineas_final['q_b_mvar'] = net.res_line_3ph.q_b_from_mvar.values
            lineas_final['q_c_mvar'] = net.res_line_3ph.q_c_from_mvar.values
            lineas_final['i_a_ka'] = net.res_line_3ph.i_a_ka.values
            lineas_final['i_b_ka'] = net.res_line_3ph.i_b_ka.values
            lineas_final['i_c_ka'] = net.res_line_3ph.i_c_ka.values
            lineas_final['i_n_ka'] = net.res_line_3ph.i_n_ka.values
            #PERDIDAS
            lineas_final['pl_mw'] = net.res_line_3ph.pl_a_mw.values + net.res_line_3ph.pl_b_mw.values + net.res_line_3ph.pl_c_mw.values
            lineas_final['ql_mvar'] = net.res_line_3ph.ql_a_mvar.values + net.res_line_3ph.ql_b_mvar.values + net.res_line_3ph.ql_c_mvar.values
            lineas_final['loading_percent'] = net.res_line_3ph.loading_percent.values
            # Mapeo de nodos originales
            lineas_final['from_node'] = net.line.from_bus.map(inv_mapping).values
            lineas_final['to_node'] = net.line.to_bus.map(inv_mapping).values
            #TRANSFORMADORES 2W

            if not net.res_trafo_3ph.empty:
                # UNIFICAR DATOS DE ENTRADA: Trafo + Reguladores
                df_trafos_unificados = pd.concat([df_trafos2w, df_reguladores], ignore_index=True)
                trafos2w_final = df_trafos_unificados.copy()
                trafos2w_final['i_a_hv_ka'] = net.res_trafo_3ph.i_a_hv_ka.values
                trafos2w_final['i_a_lv_ka'] = net.res_trafo_3ph.i_a_lv_ka.values
                trafos2w_final['i_b_hv_ka'] = net.res_trafo_3ph.i_b_hv_ka.values
                trafos2w_final['i_b_lv_ka'] = net.res_trafo_3ph.i_b_lv_ka.values
                trafos2w_final['i_c_hv_ka'] = net.res_trafo_3ph.i_c_hv_ka.values
                trafos2w_final['i_c_lv_ka'] = net.res_trafo_3ph.i_c_lv_ka.values
                trafos2w_final['p_hv_mw'] = net.res_trafo_3ph.p_a_hv_mw.values + net.res_trafo_3ph.p_b_hv_mw.values + net.res_trafo_3ph.p_c_hv_mw.values
                trafos2w_final['q_hv_mvar'] = net.res_trafo_3ph.q_a_hv_mvar.values + net.res_trafo_3ph.q_b_hv_mvar.values + net.res_trafo_3ph.q_c_hv_mvar.values
                trafos2w_final['p_lv_mw'] = net.res_trafo_3ph.p_a_lv_mw.values + net.res_trafo_3ph.p_b_lv_mw.values + net.res_trafo_3ph.p_c_lv_mw.values
                trafos2w_final['q_lv_mvar'] = net.res_trafo_3ph.q_a_lv_mvar.values + net.res_trafo_3ph.q_b_lv_mvar.values + net.res_trafo_3ph.q_c_lv_mvar.values
                trafos2w_final['p_perdidas_mw'] = net.res_trafo_3ph.pl_a_mw.values + net.res_trafo_3ph.pl_b_mw.values + net.res_trafo_3ph.pl_c_mw.values
                trafos2w_final['q_perdidas_mvar'] = net.res_trafo_3ph.ql_a_mvar.values + net.res_trafo_3ph.ql_b_mvar.values + net.res_trafo_3ph.ql_c_mvar.values
                trafos2w_final['loading_percent'] = net.res_trafo_3ph.loading_percent.values
            else:
                trafos2w_final = pd.DataFrame()

            trafos3w_final = pd.DataFrame()

            #GENERADORES Y SLACK (Red Externa)
            logger.info("Generadores ...")
            #Separamos los resultados de generación
            res_gen_final = df_gens.copy()
            #Creamos columnas vacías para llenar
            res_gen_final['p_despacho_mw'] = 0.0
            res_gen_final['q_despacho_mvar'] = 0.0
            # vm_pu y va_degree vienen del resultado del bus donde está el generador
            # Mapeamos el bus del generador al resultado de tensiones
            bus_indices_gen = [mapping[bid] for bid in res_gen_final.node_id]
            res_gen_final['vm_a_pu'] = net.res_bus_3ph.loc[bus_indices_gen, 'vm_a_pu'].values
            res_gen_final['vm_b_pu'] = net.res_bus_3ph.loc[bus_indices_gen, 'vm_b_pu'].values
            res_gen_final['vm_c_pu'] = net.res_bus_3ph.loc[bus_indices_gen, 'vm_c_pu'].values
            res_gen_final['va_a_degree'] = net.res_bus_3ph.loc[bus_indices_gen, 'va_a_degree'].values
            res_gen_final['va_b_degree'] = net.res_bus_3ph.loc[bus_indices_gen, 'va_b_degree'].values
            res_gen_final['va_c_degree'] = net.res_bus_3ph.loc[bus_indices_gen, 'va_c_degree'].values

            #Mapeo de Generadores PQ
            pq_mask = res_gen_final['tipo_slack'] == False
            logger.info("Generadores estaticos ...")
            res_sgen_3ph = getattr(net, 'res_sgen_3ph', pd.DataFrame())
            if not res_sgen_3ph.empty:
                res_gen_final.loc[pq_mask, 'p_despacho_mw'] = res_sgen_3ph.p_a_mw.values + res_sgen_3ph.p_b_mw.values + res_sgen_3ph.p_c_mw.values
                res_gen_final.loc[pq_mask, 'q_despacho_mvar'] = res_sgen_3ph.q_a_mvar.values + res_sgen_3ph.q_b_mvar.values + res_sgen_3ph.q_c_mvar.values

            res_asymmetric_sgen_3ph = getattr(net, 'res_asymmetric_sgen_3ph', pd.DataFrame())
            if not res_asymmetric_sgen_3ph.empty:
                res_gen_final.loc[pq_mask, 'p_despacho_mw'] = res_asymmetric_sgen_3ph.p_a_mw.values + res_asymmetric_sgen_3ph.p_b_mw.values + res_asymmetric_sgen_3ph.p_c_mw.values
                res_gen_final.loc[pq_mask, 'q_despacho_mvar'] = res_asymmetric_sgen_3ph.q_a_mvar.values + res_asymmetric_sgen_3ph.q_b_mvar.values + res_asymmetric_sgen_3ph.q_c_mvar.values

            #Mapeo de Generadores PV
            pv_mask = res_gen_final['tipo_slack'] == False
            logger.info("Generadores rotantes ...")
            res_gen_3ph = getattr(net, 'res_gen_3ph', pd.DataFrame())
            if not res_gen_3ph.empty:
                res_gen_final.loc[pv_mask, 'p_despacho_mw'] = res_gen_3ph.p_a_mw.values + res_gen_3ph.p_b_mw.values + res_gen_3ph.p_c_mw.values
                res_gen_final.loc[pv_mask, 'q_despacho_mvar'] = res_gen_3ph.q_a_mvar.values + res_gen_3ph.q_b_mvar.values + res_gen_3ph.q_c_mvar.values

            #Mapeo de Red Externa (Slack)
            logger.info("Redes externas ...")
            slack_mask = res_gen_final['tipo_slack'] == True
            if not net.res_ext_grid_3ph.empty:
                res_gen_final.loc[slack_mask, 'p_despacho_mw'] = net.res_ext_grid_3ph.p_a_mw.values + net.res_ext_grid_3ph.p_b_mw.values + net.res_ext_grid_3ph.p_c_mw.values
                res_gen_final.loc[slack_mask, 'q_despacho_mvar'] = net.res_ext_grid_3ph.q_a_mvar.values + net.res_ext_grid_3ph.q_b_mvar.values + net.res_ext_grid_3ph.q_c_mvar.values

            self.exportar_resultados_txt(nodos_final, lineas_final, trafos2w_final, res_gen_final)

        except Exception as e:
            logger.error(f"Error en la obtención de resultados : {e}")
            self.exportar_log()

        # --- Cálculo de Resumen para lstResultados ---
        try:

            p_inyectada = 0
            p_demanda = 0
            #Inyección Total (Generadores + Red Externa)
            #GENERADORES ROTANTES
            p_gen = 0
            if hasattr(net, 'res_gen_3ph') and not net.res_gen_3ph.empty:
                p_gen = net.res_gen_3ph.p_a_mw.sum() + net.res_gen_3ph.p_b_mw.sum() + net.res_gen_3ph.p_c_mw.sum()
            #CON INVERTER - ESTATICOS
            p_sgen = 0
            if hasattr(net, 'res_sgen_3ph') and not net.res_sgen_3ph.empty:
                p_sgen = net.res_sgen_3ph.p_a_mw.sum() + net.res_sgen_3ph.p_b_mw.sum() + net.res_sgen_3ph.p_c_mw.sum()
            if hasattr(net, 'res_asymmetric_sgen_3ph') and not net.res_asymmetric_sgen_3ph.empty:
                p_sgen = p_sgen + net.res_asymmetric_sgen_3ph.p_a_mw.sum() + net.res_asymmetric_sgen_3ph.p_b_mw.sum() + net.res_asymmetric_sgen_3ph.p_c_mw.sum()
            #SLACK
            p_ext= 0
            if hasattr(net, 'res_ext_grid_3ph') and not net.res_ext_grid_3ph.empty:
                p_ext = net.res_ext_grid_3ph.p_a_mw.sum() + net.res_ext_grid_3ph.p_b_mw.sum() + net.res_ext_grid_3ph.p_c_mw.sum()
            p_inyectada = p_gen + p_sgen + p_ext

            # Demanda Total (Cargas)
            p_demanda = 0
            # Cargas asimétricas
            if hasattr(net, 'res_asymmetric_load_3ph') and not net.res_asymmetric_load_3ph.empty:
                p_demanda = p_demanda + net.res_asymmetric_load_3ph.p_a_mw.sum() + net.res_asymmetric_load_3ph.p_b_mw.sum() + net.res_asymmetric_load_3ph.p_c_mw.sum()
            # Cargas estándar (trifásicas)
            if hasattr(net, 'res_load_3ph') and not net.res_load_3ph.empty:
                p_demanda = p_demanda + net.res_load_3ph.p_a_mw.sum() + net.res_load_3ph.p_b_mw.sum() + net.res_load_3ph.p_c_mw.sum()

            #Pérdidas
            # Pérdidas totales en líneas
            perd_lineas = net.res_line_3ph.pl_a_mw.sum() + net.res_line_3ph.pl_b_mw.sum() + net.res_line_3ph.pl_c_mw.sum()
            perd_trafos = net.res_trafo_3ph.pl_a_mw.sum() + net.res_trafo_3ph.pl_b_mw.sum() + net.res_trafo_3ph.pl_c_mw.sum()

            #Tensiones Extremas
            min_v_val = 0.0
            node_min_v = "N/A"
            idx_min_v = None
            max_load_line = 0.0
            id_linea = "N/A"

            if hasattr(net, 'res_bus_3ph') and not net.res_bus_3ph.empty:
                # Seleccionamos solo las columnas de tensión que existan
                cols_v = [c for c in ['vm_a_pu', 'vm_b_pu', 'vm_c_pu'] if c in net.res_bus_3ph.columns]
                if cols_v:
                    v_min_fases = net.res_bus_3ph[cols_v].min(axis=1)
                    min_v_val = v_min_fases.min()
                    idx_min_v = v_min_fases.idxmin()
                    # Usamos el inv_mapping que definiste antes
                    node_min_v = inv_mapping.get(idx_min_v, "N/A")
                else:
                    min_v_val, node_min_v = 0, "N/A"
            else:
                min_v_val, node_min_v = 0, "N/A"

            #Sobrecargas Máximas
            max_load_line = 0.0
            id_linea = "N/A"
            max_load_trafo = 0.0
            id_trafo = "N/A"

            # 1. LÍNEAS (Usando res_line_3ph)
            if hasattr(net, 'res_line_3ph') and not net.res_line_3ph.empty:
                max_load_line = net.res_line_3ph.loading_percent.max()
                if max_load_line > 0:
                    idx_max_line = net.res_line_3ph.loading_percent.idxmax()
                    # validamos el índice en df_lineas
                    if idx_max_line in df_lineas.index:
                        id_linea = df_lineas.loc[idx_max_line, 'line_id']

            # 2. TRANSFORMADORES (Usando res_trafo_3ph)
            if hasattr(net, 'res_trafo_3ph') and not net.res_trafo_3ph.empty:
                max_load_trafo = net.res_trafo_3ph.loading_percent.max()
                if max_load_trafo > 0:
                    idx_max_trafo = net.res_trafo_3ph.loading_percent.idxmax()
                    # validamos el índice en df_trafos2w
                    if idx_max_trafo in df_trafos2w.index:
                        id_trafo = df_trafos2w.loc[idx_max_trafo, 'node_id']

            # --- Crear la lista de strings para el QListView ---
            resumen = []
            resumen.append(f"Potencia total inyectada: {p_inyectada:.1f} MW")
            resumen.append(f"Demanda total del sistema: {p_demanda:.1f} MW")

        except Exception as e:
            logger.error(f"Error al generar resumen: {e}")

        #Demanda por Alimentador
        #Suponiendo que df_nodos mantiene el mismo orden o usando el mapping
        nodos_alimentadores = df_nodos[df_nodos['type'] == 8]
        for _, nodo in nodos_alimentadores.iterrows():
            nid = nodo['node_id']
            id_alimentador = mapping.get(nid)
            if id_alimentador is not None:
                # Buscamos las líneas conectadas a este bus (ya sea en el extremo 'from' o 'to')
                lineas_conectadas = net.line[(net.line.from_bus == id_alimentador) | (net.line.to_bus == id_alimentador)]
                if not lineas_conectadas.empty:
                    # dado que aguas abajo de rebajes y reguladores pueden estar las salidas, los datos van a estar en esos
                    # casos sólo en una de las líneas de la salida, ya que la otra se saca
                    for l in range (0, 1):
                        idx_linea = int(lineas_conectadas.index[l])
                        # Si el bus es el 'from_bus', la potencia que pasa es p_from_mw
                        if net.line.at[idx_linea, 'from_bus'] == id_alimentador:
                            suma_potencias = net.res_line_3ph.at[idx_linea, 'p_a_from_mw'] + net.res_line_3ph.at[idx_linea, 'p_b_from_mw'] + net.res_line_3ph.at[idx_linea, 'p_c_from_mw']
                            p_transito = abs(suma_potencias)
                            if suma_potencias > 0:
                                direccion = "Demanda"
                            else:
                                direccion = "Inyección"
                        else:
                            # Si el bus es el 'to_bus', la potencia que llega es p_to_mw
                            suma_potencias = net.res_line_3ph.at[idx_linea, 'p_a_to_mw'] + net.res_line_3ph.at[idx_linea, 'p_b_to_mw'] + net.res_line_3ph.at[idx_linea, 'p_c_to_mw']
                            p_transito = abs(suma_potencias)
                            if suma_potencias > 0:
                                direccion = "Demanda"
                            else:
                                direccion = "Inyección"
                        resumen.append(f"{direccion} en Alimentador {nodo['name']} (Nodo {nid}) = {p_transito:.3f} MW")
                        # Si ya encontré datos en una de las líneas de la salida corto el for
                        break

        try:

            resumen.append(f"Pérdidas en conductores: {perd_lineas:.3f} MW")
            resumen.append(f"Pérdidas en transformación: {perd_trafos:.3f} MW")
            resumen.append(f"Mínima tensión: {min_v_val:.4f} p.u. (Nodo: {node_min_v})")
            resumen.append(f"Máxima sobrecarga líneas: {max_load_line:.2f} % (ID: {id_linea})")
            resumen.append(f"Máxima sobrecarga trafos: {max_load_trafo:.2f} % (ID: {id_trafo})")

            # Cargar en el QListView (lstResultados)
            model = QStringListModel()
            model.setStringList(resumen)
            self.lstResultados.setModel(model)
        except Exception as e:
            logger.error(f"Error al generar resumen: {e}")
        return nodos_final, lineas_final, trafos2w_final, trafos3w_final, res_gen_final

    def exportar_log (self):
        logs = self.log_model.stringList()
        try:
            with open('c:/gis/energis6/calculos/log.txt', 'w', encoding='utf-8') as f:
                for linea in logs:
                    f.write(linea + '\n')
        except:
            pass

    def exportar_resultados_txt(self, n_final, l_final, t_final, g_final):
        logger = logging.getLogger("MiFlujo")
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
            #Exportar Transformadores (t_final)
            ruta_trafos = os.path.join(carpeta_destino, "t_final.txt")
            t_final.to_csv(ruta_trafos, **opciones)
            # 3. Exportar Generadores (g_final)
            ruta_generadores = os.path.join(carpeta_destino, "g_final.txt")
            g_final.to_csv(ruta_generadores, **opciones)
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
                f.write(f"CONVERGENCIA: {net.converged}\n")
                f.write(f"ELEMENTOS EN NET: {net.bus.shape[0]} buses, {net.line.shape[0]} lineas\n\n")

                # Intentar ver tablas MONOFÁSICAS (Por si acaso)
                for tabla in ['res_ext_grid', 'res_bus', 'res_line', 'res_trafo', 'res_gen', 'res_sgen', 'res_load']:
                    f.write(f"--- {tabla} ---\n")
                    df = getattr(net, tabla, pd.DataFrame())
                    f.write(df.to_string() if not df.empty else "VACÍA")
                    f.write("\n\n")

                # Intentar ver tablas trifásicas
                for tabla in ['res_ext_grid_3ph', 'res_bus_3ph', 'res_line_3ph', 'res_trafo_3ph', 'res_gen_3ph', 'res_sgen_3ph', 'res_asymmetric_sgen_3ph', 'res_load_3ph', 'res_asymmetric_load_3ph']:
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
