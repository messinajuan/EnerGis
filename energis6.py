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
import pyodbc
import json
import tempfile
import subprocess

from qgis.core import QgsApplication, QgsLayerTreeLayer, QgsField, QgsFields
from qgis.core import QgsProject, QgsMapLayerType, QgsVectorFileWriter, QgsSimpleMarkerSymbolLayerBase
from qgis.core import QgsVectorLayer, QgsFeature, QgsPoint, QgsGeometry, QgsCoordinateReferenceSystem

from datetime import datetime
from PyQt6 import QtGui, QtWidgets
from PyQt6.QtCore import Qt, QVariant, QTimer

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class EnerGis6(object):

    def __init__(self, iface):
        #da acceso a la interfaz QGIS
        self.iface = iface
        self.mapCanvas = iface.mapCanvas()
        #self.utils = iface.mapCanvas().snappingUtils()
        # create action that will start plugin configuration
        self.energis_action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'energis.ico')), "EnerGis", self.iface.mainWindow())
        self.energis_action.setWhatsThis("")
        self.energis_action.setStatusTip("Detenido")
        self.energis_action.triggered.connect(self.run)
        # add toolbar button and menu item
        self.iface.addToolBarIcon(self.energis_action)
        self.iface.addPluginToMenu("EnerGis 6", self.energis_action)
        self.id_usuario_sistema = 0
        self.tipo_usuario = 4
        self.tension = '0'
        self.mnodos=()
        self.mlineas=()
        self.seleccion_n = []
        self.seleccion_l = []
        self.tensiones = []
        self.proyecto = ''
        self.conn = None
        self.red_verificada=False
        self.tipo_navegacion = 0
        self.conn = None

    def initGui(self):
        #llamado cuando se carga el complemento
        #La versión cambiará cuando cambie la db
        self.version = '6.0.0'
        self.seleccion = []
        self.lyrSeleccion = None

    def detecto_cambio_seleccion(self):
        n=0
        n = self.iface.mapCanvas().layerCount()
        if n<1:
            return
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        if len(self.seleccion)==0:
            self.seleccion.append([])
        i = 0
        s = 0
        for lyr in layers:
            if i + 1 > len(self.seleccion):
                self.seleccion.append([])
            if lyr.name() == 'Areas' or lyr.name() == 'Parcelas' or lyr.name()[:5] == 'Nodos' or lyr.name()[:6] == 'Lineas' or lyr.name()[:6] == 'Postes':
                if lyr.selectedFeatures():
                    s = s + len(lyr.selectedFeatures())
                    if len(self.seleccion[i])>0:
                        if lyr.selectedFeatures() != self.seleccion[i]:
                            ftr = lyr.selectedFeatures()[0]
                            self.lleno_combo_propiedades(lyr, ftr)
                            self.seleccion[i] = lyr.selectedFeatures()
                    else:
                        ftr = lyr.selectedFeatures()[0]
                        self.lleno_combo_propiedades(lyr, ftr)
                        self.seleccion[i] = lyr.selectedFeatures()
                else:
                    self.seleccion[i]=[]
            i = i + 1
        if s == 0:
            try:
                self.tblPropiedades.setRowCount(0)
                self.cmbPropiedades.clear()
            except:
                pass

    def lleno_combo_propiedades(self, lyr, ftr):
        try:
            self.cmbPropiedades.clear()
            self.tblPropiedades.setRowCount(0)
            if lyr.name()[:5] == 'Nodos':
                self.cmbPropiedades.addItem('Nodo')
                conn = self.conn
                cursor = conn.cursor()
                cursor.execute("SELECT elmt FROM Nodos WHERE Geoname=" + str(ftr.id()))
                elemento = tuple(cursor)
                cursor.close()
                if elemento[0][0]==1:
                    self.cmbPropiedades.addItem('Fuente')
                if elemento[0][0]==2:
                    self.cmbPropiedades.addItem('Elemento de Maniobra')
                if elemento[0][0]==3:
                    self.cmbPropiedades.addItem('Elemento de Maniobra')
                if elemento[0][0]==4:
                    self.cmbPropiedades.addItem('Centro de Transformación')
                    conn = self.conn
                    cursor = conn.cursor()
                    cursor.execute("SELECT id_trafo FROM Transformadores INNER JOIN Nodos ON Transformadores.id_ct=Nodos.Nombre WHERE elmt=4 AND geoname=" + str(ftr.id()))
                    encontrados = tuple(cursor)
                    cursor.close()
                    for i in range (0, len(encontrados)):
                        self.cmbPropiedades.addItem('Transformador ' + str(encontrados[i][0]))
                if elemento[0][0]==5:
                    self.cmbPropiedades.addItem('Luminaria')
                if elemento[0][0]==6:
                    self.cmbPropiedades.addItem('Suministro')
                    conn = self.conn
                    cursor = conn.cursor()
                    cursor.execute("SELECT id_suministro FROM Suministros WHERE id_suministro IN (SELECT id_suministro FROM Usuarios) AND id_nodo=" + str(ftr.id()))
                    encontrados = tuple(cursor)
                    cursor.close()
                    for i in range (0, len(encontrados)):
                        self.cmbPropiedades.addItem('Suministro ' + encontrados[i][0])
                if elemento[0][0]==7:
                    self.cmbPropiedades.addItem('Capacitor')
                if elemento[0][0]==9:
                    self.cmbPropiedades.addItem('Regulador')
                if elemento[0][0]==11:
                    self.cmbPropiedades.addItem('Generador')
            if lyr.name()[:6] == 'Lineas':
                self.cmbPropiedades.addItem('Linea')
            if lyr.name()[:6] == 'Postes':
                self.cmbPropiedades.addItem('Poste')
            if lyr.name() == 'Areas':
                self.cmbPropiedades.addItem('Area')
            if lyr.name() == 'Parcelas':
                self.cmbPropiedades.addItem('Parcela')
            self.id_seleccionado = ftr.id()
            self.cmbPropiedades.activated.connect(self.elijo_elemento_propiedad)
            if self.cmbPropiedades.count()>0:
                #self.cmbPropiedades.setCurrentIndex(0)
                self.elijo_elemento_propiedad()
        except:
            pass

    def elijo_elemento_propiedad(self):
        font = QtGui.QFont()
        font.setPointSize(8)
        self.tblPropiedades.setFont(font)
        self.tblPropiedades.verticalHeader().setVisible(False)
        self.tblPropiedades.setColumnCount(2)
        self.tblPropiedades.setHorizontalHeaderLabels(['Propiedad','Valor'])
        self.tblPropiedades.setColumnWidth(1, self.tblPropiedades.viewport().width() - self.tblPropiedades.columnWidth(0))
        self.tblPropiedades.setRowCount(0)
        if self.cmbPropiedades.currentText() == 'Nodo':
            conn = self.conn
            cursor = conn.cursor()
            cursor.execute("SELECT Geoname, Nombre, Descripcion, ROUND(XCoord, 1) AS X, ROUND(YCoord, 1) AS Y, Tension, Zona, Alimentador, UUCC FROM Nodos WHERE Geoname=" + str(self.id_seleccionado))
            encontrados = tuple(cursor)
            encabezado = [column[0] for column in cursor.description]
            cursor.close()
            if len(encontrados) > 0:
                self.tblPropiedades.setRowCount(len(encontrados[0])+1)
            for i in range (0, len(encontrados[0])):
                propiedad = QtWidgets.QTableWidgetItem(encabezado[i])
                valor = QtWidgets.QTableWidgetItem(str(encontrados[0][i]))
                self.tblPropiedades.setRowHeight(i, 9)
                self.tblPropiedades.setItem(i,0,propiedad)
                self.tblPropiedades.setItem(i,1,valor)
            i = i + 1
            from .mod_coordenadas import convertir_coordenadas
            coordenadas = str(convertir_coordenadas(self, encontrados[0][3], encontrados[0][4], self.srid, 4326)).replace('[','').replace(']','')
            propiedad = QtWidgets.QTableWidgetItem('Coordenadas')
            valor = QtWidgets.QTableWidgetItem(coordenadas)
            self.tblPropiedades.setRowHeight(i, 9)
            self.tblPropiedades.setItem(i,0,propiedad)
            self.tblPropiedades.setItem(i,1,valor)
        if self.cmbPropiedades.currentText() == 'Elemento de Maniobra':
            conn = self.conn
            cursor = conn.cursor()
            cursor.execute("SELECT Nodos.Val1 AS Aparato, CASE WHEN elmt=3 THEN 'NA' ELSE 'NC' END AS Estado_Normal, CASE WHEN estado=3 THEN 'NA' ELSE 'NC' END AS Estado_Actual, LTRIM(LEFT(Nodos.Val2,15)) AS Tipo, LTRIM(LEFT(RIGHT(Nodos.Val2,35),5)) AS Corriente, LTRIM(RIGHT(Nodos.Val2,15)) AS PAT, Val3 AS Telemando, Val4 AS Descargadores, Val5 AS Poder_corte FROM Nodos WHERE geoname=" + str(self.id_seleccionado))
            encontrados = tuple(cursor)
            encabezado = [column[0] for column in cursor.description]
            cursor.close()
            if len(encontrados) > 0:
                self.tblPropiedades.setRowCount(len(encontrados[0]))
            for i in range (0, len(encontrados[0])):
                propiedad = QtWidgets.QTableWidgetItem(encabezado[i])
                valor = QtWidgets.QTableWidgetItem(str(encontrados[0][i]))
                self.tblPropiedades.setRowHeight(i, 9)
                self.tblPropiedades.setItem(i,0,propiedad)
                self.tblPropiedades.setItem(i,1,valor)
        if self.cmbPropiedades.currentText()[:13] == 'Transformador':
            conn = self.conn
            cursor = conn.cursor()
            cursor.execute("SELECT id_trafo, potencia, conexionado, marca, Tension_1, Tension_2, n_chapa, anio_fabricacion AS año, aceite AS lts_aceite, Cromatografia, Certificado FROM Transformadores WHERE id_trafo=" + self.cmbPropiedades.currentText()[14:])
            encontrados = tuple(cursor)
            encabezado = [column[0] for column in cursor.description]
            cursor.close()
            if len(encontrados) > 0:
                self.tblPropiedades.setRowCount(len(encontrados[0]))
            for i in range (0, len(encontrados[0])):
                propiedad = QtWidgets.QTableWidgetItem(encabezado[i])
                valor = QtWidgets.QTableWidgetItem(str(encontrados[0][i]))
                self.tblPropiedades.setRowHeight(i, 9)
                self.tblPropiedades.setItem(i,0,propiedad)
                self.tblPropiedades.setItem(i,1,valor)
        if self.cmbPropiedades.currentText() == 'Centro de Transformación':
            conn = self.conn
            cursor = conn.cursor()
            cursor.execute("SELECT Geoname, Elementos_Nodos.Descripcion AS Tipo, Ct.Tipo_ct, Ct.Mat_plataf, Ct.Tipo_oceba, Ct.Fecha_alta, caeis+caeies+caees+caeees AS Entradas, casis+casies+cases+casees AS Salidas, Exp, tipo_oceba, Ct.Conservacion, SUM(Transformadores.Potencia) AS Pot_Instalada, MAX(Transformadores.Conexionado) AS Conexionado, MAX(Transformadores.Tension_1) AS V1, MAX(Transformadores.Tension_2) AS V2 FROM Ct LEFT OUTER JOIN Transformadores ON Ct.Id_ct = Transformadores.Id_ct RIGHT OUTER JOIN Nodos ON Ct.Id_ct = Nodos.Nombre RIGHT OUTER JOIN Elementos_Nodos ON Nodos.Elmt = Elementos_Nodos.Id WHERE geoname=" + str(self.id_seleccionado) + " GROUP BY Nodos.Geoname, Elementos_Nodos.Descripcion, Ct.Tipo_ct, Ct.Mat_plataf, Ct.tipo_oceba, Ct.fecha_alta, Ct.conservacion, caeis+caeies+caees+caeees, casis+casies+cases+casees, Exp, tipo_oceba")
            encontrados = tuple(cursor)
            encabezado = [column[0] for column in cursor.description]
            cursor.close()
            if len(encontrados) > 0:
                self.tblPropiedades.setRowCount(len(encontrados[0]))
            for i in range (0, len(encontrados[0])):
                propiedad = QtWidgets.QTableWidgetItem(encabezado[i])
                valor = QtWidgets.QTableWidgetItem(str(encontrados[0][i]))
                self.tblPropiedades.setRowHeight(i, 9)
                self.tblPropiedades.setItem(i,0,propiedad)
                self.tblPropiedades.setItem(i,1,valor)
        if self.cmbPropiedades.currentText()[:10] == 'Suministro':
            conn = self.conn
            cursor = conn.cursor()
            if self.cmbPropiedades.currentText() == 'Suministro':
                cursor.execute("SELECT Geoname, COUNT(Suministros.id_suministro) AS Cant_Sum, COUNT(Usuarios.id_usuario) AS Cant_Usuarios FROM Elementos_Nodos LEFT OUTER JOIN Nodos ON Elementos_Nodos.Id = Nodos.Elmt LEFT OUTER JOIN Usuarios RIGHT OUTER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro ON Nodos.Geoname = Suministros.id_nodo WHERE geoname=" + str(self.id_seleccionado) + " GROUP BY Nodos.Geoname")
            else:
                cursor.execute("SELECT 'Cant Usuarios' AS Tarifa, T1AP,T1GAC,T1GBC,T1R,T2BT,T2MT,T3BT,T3MT,T4NR,T4R,T5BT,T5MT,T6BT,T6MT FROM (SELECT Tarifas.id_OCEBA AS Tarifa, Usuarios.id_usuario FROM Usuarios INNER JOIN Tarifas ON Usuarios.tarifa = Tarifas.Tarifa WHERE (Usuarios.id_suministro = '" + self.cmbPropiedades.currentText()[11:] + "')) AS S PIVOT (COUNT(id_usuario) FOR Tarifa IN (T1AP,T1GAC,T1GBC,T1R,T2BT,T2MT,T3BT,T3MT,T4NR,T4R,T5BT,T5MT,T6BT,T6MT)) AS P")
            encontrados = tuple(cursor)
            encabezado = [column[0] for column in cursor.description]
            cursor.close()
            if len(encontrados) > 0:
                self.tblPropiedades.setRowCount(1)
                n=1
                for i in range (1, len(encontrados[0])):
                    if encontrados[0][i]>0:
                        n=n+1
                self.tblPropiedades.setRowCount(n)
                j=0
                for i in range (0, len(encontrados[0])):
                    if i==0:
                        propiedad = QtWidgets.QTableWidgetItem(encabezado[i])
                        valor = QtWidgets.QTableWidgetItem(str(encontrados[0][i]))
                        self.tblPropiedades.setRowHeight(i, 9)
                        self.tblPropiedades.setItem(i,0,propiedad)
                        self.tblPropiedades.setItem(i,1,valor)
                    else:
                        if encontrados[0][i]>0:
                            j=j+1
                            propiedad = QtWidgets.QTableWidgetItem(encabezado[i])
                            valor = QtWidgets.QTableWidgetItem(str(encontrados[0][i]))
                            self.tblPropiedades.setRowHeight(j, 9)
                            self.tblPropiedades.setItem(j,0,propiedad)
                            self.tblPropiedades.setItem(j,1,valor)
        if self.cmbPropiedades.currentText() == 'Fuente' or self.cmbPropiedades.currentText() == 'Generador':
            conn = self.conn
            cursor = conn.cursor()
            cursor.execute("SELECT ISNULL(Descripcion, '') AS SSEE, Val1 AS Tension, Val5 AS tipo_generacion, Val4 FROM Nodos WHERE Nodos.Tension>0 AND geoname=" + str(self.id_seleccionado))
            #convierto el cursor en array
            encontrados = tuple(cursor)
            encabezado = [column[0] for column in cursor.description]
            cursor.close()
            str_matriz = str(encontrados[0][3]).split("|")
            tipo_fuente = str_matriz[0]
            if tipo_fuente=='0':
                self.tblPropiedades.setRowCount(6)
            else:
                self.tblPropiedades.setRowCount(10)
            #-----------------------------------------------
            propiedad = QtWidgets.QTableWidgetItem("SSEE")
            valor = QtWidgets.QTableWidgetItem(encontrados[0][0])
            self.tblPropiedades.setRowHeight(0, 9)
            self.tblPropiedades.setItem(0,0,propiedad)
            self.tblPropiedades.setItem(0,1,valor)
            #-----------------------------------------------
            propiedad = QtWidgets.QTableWidgetItem("Tension [V]")
            valor = QtWidgets.QTableWidgetItem(encontrados[0][1])
            self.tblPropiedades.setRowHeight(1, 9)
            self.tblPropiedades.setItem(1,0,propiedad)
            self.tblPropiedades.setItem(1,1,valor)
            if tipo_fuente=='0':
                #-----------------------------------------------
                propiedad = QtWidgets.QTableWidgetItem("Tipo")
                valor = QtWidgets.QTableWidgetItem("Punto de Compra")
                self.tblPropiedades.setRowHeight(2, 9)
                self.tblPropiedades.setItem(2,0,propiedad)
                self.tblPropiedades.setItem(2,1,valor)
            else:
                #-----------------------------------------------
                propiedad = QtWidgets.QTableWidgetItem("Tipo")
                valor = QtWidgets.QTableWidgetItem("Generación")
                self.tblPropiedades.setRowHeight(2, 9)
                self.tblPropiedades.setItem(2,0,propiedad)
                self.tblPropiedades.setItem(2,1,valor)
            #-----------------------------------------------
            propiedad = QtWidgets.QTableWidgetItem("Tipo_generacion")
            valor = QtWidgets.QTableWidgetItem(encontrados[0][2])
            self.tblPropiedades.setRowHeight(3, 9)
            self.tblPropiedades.setItem(3,0,propiedad)
            self.tblPropiedades.setItem(3,1,valor)
            #-----------------------------------------------
            propiedad = QtWidgets.QTableWidgetItem("Expediente")
            valor = QtWidgets.QTableWidgetItem(str_matriz[1])
            self.tblPropiedades.setRowHeight(4, 9)
            self.tblPropiedades.setItem(4,0,propiedad)
            self.tblPropiedades.setItem(4,1,valor)
            #-----------------------------------------------
            propiedad = QtWidgets.QTableWidgetItem("Scc [MVA]")
            valor = QtWidgets.QTableWidgetItem(str_matriz[6])
            self.tblPropiedades.setRowHeight(5, 9)
            self.tblPropiedades.setItem(5,0,propiedad)
            self.tblPropiedades.setItem(5,1,valor)
            #-----------------------------------------------
            if tipo_fuente=='1':
                propiedad = QtWidgets.QTableWidgetItem("P [kW]")
                valor = QtWidgets.QTableWidgetItem(str_matriz[2])
                self.tblPropiedades.setRowHeight(5, 9)
                self.tblPropiedades.setItem(5,0,propiedad)
                self.tblPropiedades.setItem(5,1,valor)
                #-----------------------------------------------
                propiedad = QtWidgets.QTableWidgetItem("Vmax [p.u.]")
                valor = QtWidgets.QTableWidgetItem(str_matriz[3])
                self.tblPropiedades.setRowHeight(6, 9)
                self.tblPropiedades.setItem(6,0,propiedad)
                self.tblPropiedades.setItem(6,1,valor)
                #-----------------------------------------------
                propiedad = QtWidgets.QTableWidgetItem("Qmax [kVAr]")
                valor = QtWidgets.QTableWidgetItem(str_matriz[4])
                self.tblPropiedades.setRowHeight(7, 9)
                self.tblPropiedades.setItem(7,0,propiedad)
                self.tblPropiedades.setItem(7,1,valor)
                #-----------------------------------------------
                propiedad = QtWidgets.QTableWidgetItem("Qmin [kVAr]")
                valor = QtWidgets.QTableWidgetItem(str_matriz[5])
                self.tblPropiedades.setRowHeight(8, 9)
                self.tblPropiedades.setItem(8,0,propiedad)
                self.tblPropiedades.setItem(8,1,valor)
                #-----------------------------------------------
        if self.cmbPropiedades.currentText() == 'Capacitor':
            #strSql = "SELECT geoname, elmt FROM Nodos WHERE geoname=" + str(self.id_seleccionado)
            pass
        if self.cmbPropiedades.currentText() == 'Regulador':
            #strSql = "SELECT geoname, elmt FROM Nodos WHERE geoname=" + str(self.id_seleccionado)
            pass
        if self.cmbPropiedades.currentText() == 'Linea':
            conn = self.conn
            cursor = conn.cursor()
            cursor.execute("SELECT Geoname, Elementos_Lineas.Descripcion, Fase, CASE Val8 WHEN 'A' THEN 'Aéreo' WHEN 'S' THEN 'Subterráneo' WHEN 'P' THEN 'Preensamblado' ELSE 'Otro' END AS Tipo, Disposicion, Ternas, Conservacion, ROUND(Longitud, 2) AS Longitud, Tension, Zona, CASE WHEN CHARINDEX('-', Alimentador) > 0 THEN LEFT(Alimentador, CHARINDEX('-', Alimentador) - 1) ELSE Alimentador END AS Alimentador, CASE Acometida WHEN '0' THEN 'Línea' ELSE 'Acometida' END AS Uso, UUCC FROM Lineas INNER JOIN Elementos_Lineas ON Lineas.Elmt = Elementos_Lineas.Id WHERE Geoname=" + str(self.id_seleccionado))
            encontrados = tuple(cursor)
            encabezado = [column[0] for column in cursor.description]
            cursor.close()
            if len(encontrados) > 0:
                self.tblPropiedades.setRowCount(len(encontrados[0]))
            for i in range (0, len(encontrados[0])):
                propiedad = QtWidgets.QTableWidgetItem(encabezado[i])
                valor = QtWidgets.QTableWidgetItem(str(encontrados[0][i]))
                self.tblPropiedades.setRowHeight(i, 9)
                self.tblPropiedades.setItem(i,0,propiedad)
                self.tblPropiedades.setItem(i,1,valor)
                #propiedad.setFlags(valor.flags() & ~Qt.ItemIsEditable)
                #valor.setFlags(valor.flags() & ~Qt.ItemIsEditable)
                #if i == -1:
                #    valor.setFlags(valor.flags() | Qt.ItemIsEditable)
            #aca va a ver si tiene opciones de combo
            #cmbCelda = QComboBox()
            #cmbCelda.addItems(["Opción 1", "Opción 2", str(encontrados[i][j]), "Opción 3"])
            #cmbCelda.setCurrentIndex(2)
            #self.tblPropiedades.setCellWidget(i, j, cmbCelda)
        if self.cmbPropiedades.currentText() == 'Poste':
            #strSql = "SELECT geoname, elmt FROM Postes WHERE geoname=" + str(self.id_seleccionado)
            pass
        if self.cmbPropiedades.currentText() == 'Area':
            #strSql = "SELECT geoname, nombre FROM Areas WHERE geoname=" + str(self.id_seleccionado)
            pass
        if self.cmbPropiedades.currentText() == 'Parcela':
            #strSql = "SELECT geoname, parcela FROM Parcelas WHERE geoname=" + str(self.id_seleccionado)
            pass

    def conectar_db(self):
        if self.conn==None or self.conn.close:
            try:
                self.conn = pyodbc.connect(self.str_conexion)
            except:
                QtWidgets.QMessageBox.critical(None, 'EnerGis 6', "❌ Debe abrir un modelo de EnerGis")

    def run(self):
        if os.path.isdir('c:/gis/energis6/')==False:
            os.mkdir('c:/gis/energis6/')
        if self.energis_action.statusTip()=="Detenido":
            self.energis_action.setStatusTip("Iniciado")
            wt = str(self.energis_action.whatsThis())
            conexiones = wt.split('|')
            if len(conexiones)<2:
                return
            str_conexion = conexiones[0]
            self.str_conexion_seguridad = conexiones[1]
            self.nombre_modelo = QgsProject.instance().title()
            #----------------------------------------------
            self.timer = QTimer()
            self.timer.timeout.connect(self.detecto_cambio_seleccion)
            self.timer.start(500)  # 0.5 segundos
            #----------------------------------------------
        else:
            self.energis_action.setStatusTip("Detenido")
            str_conexion = ""
            try:
                self.timer.stop()
            except:
                pass

        if self.energis_action.statusTip()=="Iniciado":
            try:
                if str_conexion!="":
                    self.str_conexion = str_conexion
                    self.actualizar_base_datos()
                else:
                    return
            except:
                QtWidgets.QMessageBox.critical(None, 'EnerGis 6', "❌ No se pudo conectar al modelo " + str_conexion)
                self.energis_action.setStatusTip("Detenido")
                str_conexion = ""
                return
            cursor = self.conn.cursor()
            cursor.execute("SELECT Valor FROM Configuracion WHERE Variable='SRID'")
            rows = cursor.fetchall()
            cursor.close()
            self.srid = rows[0][0]
            #Creo barras de herramientas
            self.actions = []
            self.menu = ('EnerGIS')
            self.iface.mainWindow().addToolBarBreak()
            self.toolbar_h = self.iface.addToolBar('EnerGis Dibujo')
            #------------------------------------------
            #Creo paneles
            # Crear el DockWidget 1 - Panel de Propiedades
            #try:
            self.dock_widget = QtWidgets.QDockWidget('Propiedades', self.iface.mainWindow())
            self.dock_widget.setFeatures(QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetFloatable | QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetClosable)
            self.dock_widget.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
            # Agregar varios widgets al layout
            self.cmbPropiedades = QtWidgets.QComboBox()
            self.tblPropiedades = QtWidgets.QTableWidget()
            dock_widget_content = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)  # Márgenes: izquierdo, superior, derecho, inferior
            layout.addWidget(self.cmbPropiedades)
            layout.addWidget(self.tblPropiedades)
            # Configurar el contenido del DockWidget
            dock_widget_content.setLayout(layout)
            #except:
            #    pass
            # Agregar el contenido al QDockWidget
            self.dock_widget.setWidget(dock_widget_content)
            #self.dock_widget.setMinimumHeight(300)
            self.dock_widget.resize(self.dock_widget.width(), 300)
            self.iface.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_widget)
            #------------------------------------------
            # Crear el DockWidget 2 - Panel de Nuevos Usuarios
            try:
                self.dock_widget2 = QtWidgets.QDockWidget('Usuarios Nuevos', self.iface.mainWindow())
                self.dock_widget2.setFeatures(QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetFloatable | QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetClosable)
                self.dock_widget2.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
                # Crear el widget principal
                dock_widget_content = QtWidgets.QWidget()
                layout = QtWidgets.QVBoxLayout()
                layout.setContentsMargins(0, 0, 0, 0)  # Márgenes: izquierdo, superior, derecho, inferior
                dock_widget_content.setLayout(layout)
            except:
                pass
            # 1. Agregar un menú en la parte superior
            menu_bar = QtWidgets.QMenuBar()
            m_acciones = menu_bar.addMenu('Acciones')
            action = QtGui.QAction('🔀 ️Separar Usuarios del Suministro', self.iface.mainWindow())
            action.triggered.connect(self.m_separar_suministros)
            m_acciones.addAction(action)
            action = QtGui.QAction('🎯 Seleccionar Suministros sin Usuarios', self.iface.mainWindow())
            action.triggered.connect(self.m_suministros_sin_usuarios)
            m_acciones.addAction(action)
            m_dibujar = menu_bar.addMenu('✍️ Dibujar')
            action = QtGui.QAction('👤 Suministros con Coordenadas Externas', self.iface.mainWindow())
            action.triggered.connect(self.m_suministros_con_coordenadas_externas)
            m_dibujar.addAction(action)
            action = QtGui.QAction('👤 Suministros con Ejes de Calle', self.iface.mainWindow())
            action.triggered.connect(self.m_suministros_con_ejes_de_calle)
            m_dibujar.addAction(action)
            action = QtGui.QAction('👤 Suministros por Catastro', self.iface.mainWindow())
            action.triggered.connect(self.m_suministros_por_catastro)
            m_dibujar.addAction(action)
            m_dibujar.addSeparator()
            action = QtGui.QAction('🔀 Conectar Suministros Aislados', self.iface.mainWindow())
            action.triggered.connect(self.m_conectar_suministros_aislados)
            m_dibujar.addAction(action)
            layout.addWidget(menu_bar)
            # 2. Agregar un QTableWidget debajo del menú
            self.tblUsuariosNuevos = QtWidgets.QTableWidget()  # Crear una tabla
            self.tblUsuariosNuevos. setAlternatingRowColors(True)
            #self.tblUsuariosNuevos.setSortingEnabled(True)
            # 3. Agregar el primer QHBoxLayout con dos QTextEdit
            hbox_layout1 = QtWidgets.QHBoxLayout()
            self.txtUsuario = QtWidgets.QLineEdit("")
            self.txtUsuario.setReadOnly(True)  # Hacer solo lectura
            self.txtNombre = QtWidgets.QLineEdit("")
            self.txtNombre.setReadOnly(True)  # Hacer solo lectura
            hbox_layout1.addWidget(self.txtUsuario)
            hbox_layout1.addWidget(self.txtNombre)
            # Establecer los tamaños de los textos
            hbox_layout1.setStretch(0, 3)  # txtUsuario ocupa 3 partes
            hbox_layout1.setStretch(1, 7)  # txtNombre ocupa 7 partes
            # 4. Agregar el segundo QHBoxLayout con dos QTextEdit
            hbox_layout2 = QtWidgets.QHBoxLayout()
            self.txtCalle = QtWidgets.QLineEdit("")
            self.txtCalle.setReadOnly(True)  # Hacer solo lectura
            self.txtNumero = QtWidgets.QLineEdit("")
            self.txtNumero.setReadOnly(True)  # Hacer solo lectura
            hbox_layout2.addWidget(self.txtCalle)
            hbox_layout2.addWidget(self.txtNumero)
            # Establecer los tamaños de los textos
            hbox_layout2.setStretch(0, 7)  # txtCalle ocupa 7 partes
            hbox_layout2.setStretch(1, 3)  # txtNumero ocupa 3 partes
            # 5. Agregar el tercer QHBoxLayout con dos QPushButton
            hbox_layout3 = QtWidgets.QHBoxLayout()
            self.cmdActualizar = QtWidgets.QPushButton("Actualizar 🔄")
            self.cmdAproximar = QtWidgets.QPushButton("Aproximar 🔀")
            hbox_layout3.addWidget(self.cmdActualizar)
            hbox_layout3.addWidget(self.cmdAproximar)
            # Agregar un espacio flexible después de los botones
            hbox_layout3.addStretch()
            # Configurar layout principal con stretch
            layout.addWidget(self.tblUsuariosNuevos)
            layout.setStretch(1, 8)  # QTableWidget ocupa 8 partes
            layout.addLayout(hbox_layout1)
            layout.setStretch(2, 1)  # Primer QHBoxLayout ocupa 1 parte
            layout.addLayout(hbox_layout2)
            layout.setStretch(3, 1)  # Segundo QHBoxLayout ocupa 1 parte
            layout.addLayout(hbox_layout3)
            layout.setStretch(4, 1)  # Tercer QHBoxLayout ocupa 1 parte
            self.cmdActualizar.clicked.connect(self.actualizar_usuarios)
            self.cmdAproximar.clicked.connect(self.aproximar_usuarios)            
            # Configurar el contenido del DockWidget
            dock_widget_content.setLayout(layout)
            # Agregar el contenido al QDockWidget
            self.dock_widget2.setWidget(dock_widget_content)
            #self.dock_widget2.setMinimumHeight(300)
            self.dock_widget2.resize(self.dock_widget2.width(), 300)
            self.iface.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_widget2)
            font = QtGui.QFont()
            font.setPointSize(8)
            self.tblUsuariosNuevos.setFont(font)
            self.tblUsuariosNuevos.verticalHeader().setVisible(False)
            self.tblUsuariosNuevos.setColumnCount(4)
            self.tblUsuariosNuevos.setHorizontalHeaderLabels(['Calle','Numero','Ruta','Suministro'])
            self.dock_widget2.resize(self.dock_widget2.width(), 260)
            self.tblUsuariosNuevos.setRowCount(0)
            self.tblUsuariosNuevos.clicked.connect(self.elijo_suministro)
            self.dock_widget2.setVisible(False)
            #------------------------------------------
            main_window = self.iface.mainWindow()
            self.toolbar_v = QtWidgets.QToolBar('EnerGis Busqueda')
            self.toolbar_v.setOrientation(Qt.Orientation.Vertical)
            main_window.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.toolbar_v)
            self.toolbar_p = QtWidgets.QToolBar('EnerGis Proyectos')
            self.toolbar_e = self.iface.addToolBar('EnerGis Ejes')
            main_window.addToolBar(Qt.ToolBarArea.BottomToolBarArea, self.toolbar_p)
            main_window.addToolBar(Qt.ToolBarArea.BottomToolBarArea, self.toolbar_e)
            #self.elijo_tension()
            #------------------------------------------
            #icon = QtGui.QIcon(os.path.join(basepath,"icons", 'img_vivo.png'))
            #self.action_vivo = QAction(icon, 'Vivo', None)
            #self.action_vivo.triggered.connect(self.vivo)
            #self.action_vivo.setCheckable(True)
            #self.action_vivo.setChecked(True)
            #self.toolbar_h.addAction(self.action_vivo)
            #------------------------------------------
            inicio = QtWidgets.QPushButton("▶️ Menú")
            self.toolbar_h.addWidget(inicio)
            menu = QtWidgets.QMenu()
            #------------------------------------------
            self.m_listados = menu.addMenu('📋 Listados')
            #------------------------------------------
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_seccionador.png')), 'Elem. de Prot. y Maniobra', self.iface.mainWindow())
            action.triggered.connect(self.listado_seccionadores)
            self.m_listados.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_poste.png')), 'Postes', self.iface.mainWindow())
            action.triggered.connect(self.listado_postes)
            self.m_listados.addAction(action)
            #------------------------------------------
            self.m_listado_transformadores = self.m_listados.addMenu('📋 Transformadores')
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_transformador.png')), 'Centros de Transformación', self.iface.mainWindow())
            action.triggered.connect(self.listado_cts)
            self.m_listado_transformadores.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_transformador.png')), 'Transformadores', self.iface.mainWindow())
            action.triggered.connect(self.listado_transformadores)
            self.m_listado_transformadores.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_transformador.png')), 'Transformadores en la Red', self.iface.mainWindow())
            action.triggered.connect(self.listado_transformadores_red)
            self.m_listado_transformadores.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_listados.png')), 'Movimientos de Transformadores', self.iface.mainWindow())
            action.triggered.connect(self.listado_movimiento_transformadores)
            self.m_listado_transformadores.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_listados.png')), 'Movimientos de un Transformador', self.iface.mainWindow())
            action.triggered.connect(self.listado_movimientos_trafo)
            self.m_listado_transformadores.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_listados.png')), 'Movimientos en un CT', self.iface.mainWindow())
            action.triggered.connect(self.listado_movimientos_ct)
            self.m_listado_transformadores.addAction(action)
            #------------------------------------------
            self.m_listado_usuarios = self.m_listados.addMenu('👤 Usuarios')
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_usuarios.png')), 'Usuarios', self.iface.mainWindow())
            action.triggered.connect(self.listado_usuarios)
            self.m_listado_usuarios.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_usuarios.png')), 'Usuarios en la Red', self.iface.mainWindow())
            action.triggered.connect(self.listado_usuarios_red)
            self.m_listado_usuarios.addAction(action)
            #------------------------------------------
            self.m_listado_usuarios = self.m_listados.addMenu('📋 Líneas')
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_linea.png')), 'Lineas', self.iface.mainWindow())
            action.triggered.connect(self.listado_lineas)
            self.m_listado_usuarios.addAction(action)
            #------------------------------------------
            self.m_analisis = menu.addMenu('⚡ Análisis')
            #------------------------------------------
            #action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_transformador.png')), 'Carga de Transformadores', self.iface.mainWindow())
            #action.triggered.connect(self.analisis_carga)
            #self.m_analisis.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_usuarios.png')), 'Cálculo de Cargas', self.iface.mainWindow())
            action.triggered.connect(self.calculo_cargas)
            self.m_analisis.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_caida_tension.png')), 'Momentos Eléctricos', self.iface.mainWindow())
            action.triggered.connect(self.momentos_electricos)
            self.m_analisis.addAction(action)
            #------------------------------------------
            self.m_modelo = menu.addMenu('📋Modelo')
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_energias.png')), 'Resumen Sistema', self.iface.mainWindow())
            action.triggered.connect(self.resumen_sistema)
            self.m_modelo.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_verificar.png')), 'Reiniciar Conectividad', self.iface.mainWindow())
            action.triggered.connect(self.crear_red)
            self.m_modelo.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_seccionador.png')), 'Llevar Red al Estado Normal', self.iface.mainWindow())
            action.triggered.connect(self.red_a_estado_normal)
            self.m_modelo.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_seccionador.png')), 'Definir Configuración Actual como Normal', self.iface.mainWindow())
            action.triggered.connect(self.establecer_estado_normal)
            self.m_modelo.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_seccionador.png')), 'Ver Elementos en Estado Distinto al Normal', self.iface.mainWindow())
            action.triggered.connect(self.ver_elementos_estado_anormal)
            self.m_modelo.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_vertices.png')), 'Actualizar Postes de Líneas', self.iface.mainWindow())
            action.triggered.connect(self.actualizar_postes_lineas)
            self.m_modelo.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_area.png')), 'Actualizar Zonas', self.iface.mainWindow())
            action.triggered.connect(self.actualizar_zonas)
            self.m_modelo.addAction(action)
            #------------------------------------------
            if self.tipo_navegacion!=0:
                action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_caida_tension.png')), 'Actualizar Alimentadores', self.iface.mainWindow())
                action.triggered.connect(self.actualizar_alimentadores)
                self.m_modelo.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_transformador.png')), 'Transformadores en Almacén', self.iface.mainWindow())
            action.triggered.connect(self.transformadores_almacen)
            self.m_modelo.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_transformador.png')), 'Centros de Transformación', self.iface.mainWindow())
            action.triggered.connect(self.centros_transformacion)
            self.m_modelo.addAction(action)
            #------------------------------------------
            self.m_exportar = self.m_modelo.addMenu('📤 Exportar')
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_esri.png')), 'ESRI shp', self.iface.mainWindow())
            action.triggered.connect(self.exportar_esri)
            self.m_exportar.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_mapinfo')), 'MapInfo tab', self.iface.mainWindow())
            action.triggered.connect(self.exportar_mapinfo)
            self.m_exportar.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_qfield.png')), 'QField', self.iface.mainWindow())
            action.triggered.connect(self.exportar_qfield)
            self.m_exportar.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_coordenadas.png')), 'Google', self.iface.mainWindow())
            action.triggered.connect(self.exportar_google)
            self.m_exportar.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_linea.png')), 'Demitec', self.iface.mainWindow())
            action.triggered.connect(self.exportar_demitec)
            self.m_exportar.addAction(action)
            #------------------------------------------
            #action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_editar.png')), 'Texto', self.iface.mainWindow())
            #action.triggered.connect(self.exportar_txt)
            #self.m_exportar.addAction(action)
            #------------------------------------------
            self.m_importar = self.m_modelo.addMenu('📥 Importar')
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_access.png')), 'MS Access', self.iface.mainWindow())
            action.triggered.connect(self.importar_access)
            self.m_importar.addAction(action)
            #------------------------------------------
            self.m_administrador = menu.addMenu('ℹ️ Administrador')
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_sql.png')), 'Ejecutar SQL', self.iface.mainWindow())
            action.triggered.connect(self.ejecutar_sql)
            self.m_administrador.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_seguridad.png')), 'Seguridad', self.iface.mainWindow())
            action.triggered.connect(self.seguridad)
            self.m_administrador.addAction(action)
            #------------------------------------------
            if self.tipo_navegacion==0:
                action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'abajo.png')), 'Actualizar a .NET', self.iface.mainWindow())
                action.triggered.connect(self.actualizar_a_net)
                self.m_administrador.addAction(action)
            #------------------------------------------
            self.m_archivos = menu.addMenu('🗂 Datos Comerciales')
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_usuarios3.png')), 'Usuarios (OCEBA)', self.iface.mainWindow())
            action.triggered.connect(self.importar_usuarios_oceba)
            self.m_archivos.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_energias.png')), 'Energias Facturadas (DPE)', self.iface.mainWindow())
            action.triggered.connect(self.importar_energias_dpe)
            self.m_archivos.addAction(action)
            #------------------------------------------
            self.m_oceba = menu.addMenu('📋 OCEBA')
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_transformador.png')), 'Transformadores Res 811', self.iface.mainWindow())
            action.triggered.connect(self.res_811)
            self.m_oceba.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_usuarios.png')), 'Usuarios', self.iface.mainWindow())
            action.triggered.connect(self.exportar_usuarios_oceba)
            self.m_oceba.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_transformador.png')), 'CTs', self.iface.mainWindow())
            action.triggered.connect(self.cts_oceba)
            self.m_oceba.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_caida_tension.png')), 'Cadena Eléctrica 1', self.iface.mainWindow())
            action.triggered.connect(self.cadena1)
            self.m_oceba.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_caida_tension.png')), 'Cadena Eléctrica 2', self.iface.mainWindow())
            action.triggered.connect(self.cadena2)
            self.m_oceba.addAction(action)
            #------------------------------------------
            self.m_dpe = menu.addMenu('📋 DPE')
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_provincia.png')), 'kml DPE', self.iface.mainWindow())
            action.triggered.connect(self.exportar_kml)
            self.m_dpe.addAction(action)
            #------------------------------------------
            action = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_provincia.png')), 'Res2/2022', self.iface.mainWindow())
            action.triggered.connect(self.exportar_dpe)
            self.m_dpe.addAction(action)
            #------------------------------------------
            inicio.setMenu(menu)
            #------------------------------------------
            self.toolbar_h.addSeparator()
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_usuarios.png'), 'Usuarios', self.usuarios, True, False, True, True, None, None, self.iface.mainWindow())
            self.toolbar_h.addSeparator()
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_verificar.png'), 'Verificar Red', self.h_verificar_red, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_elementos_seleccionados.png'), 'Ubicar Selección', self.h_elementos_seleccionados, True, False, True, True, None, None, self.iface.mainWindow())
            self.toolbar_h.addSeparator()
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_seleccion.png'), 'Selección', self.h_seleccion, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_seleccion_aleatoria.png'), 'Selección por Area', self.h_seleccion_aleatoria, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_seleccion_circular.png'), 'Selección Circular', self.h_seleccion_circular, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_seleccionar_elementos.png'), 'Seleccionar Elementos', self.h_seleccionar_elementos, True, False, True, True, None, None, self.iface.mainWindow())
            self.toolbar_h.addSeparator()
            #--------------------------------------------------
            self.cmbTension  = QtWidgets.QComboBox(self.iface.mainWindow())
            #--------------------------------------------------
            cursor = self.conn.cursor()
            cursor.execute("SELECT Tension FROM Niveles_Tension WHERE Tension>=50")
            #convierto el cursor en array
            self.tensiones = tuple(cursor)
            cursor.close()
            self.cmbTension.clear()
            for t in range (0, len(self.tensiones)):
                self.cmbTension.addItem(str(self.tensiones[t][0]))
            n = self.iface.mapCanvas().layerCount()
            layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
            for lyr in layers:
                if lyr.name() == 'Nodos Proyectos' or lyr.name() == 'Lineas Proyectos' or lyr.name() == 'Postes Proyectos':
                    lyr.setSubsetString('"Alimentador" = ' + "'@@'")
                if lyr.name() == 'Cotas':
                    lyr.setSubsetString('"proyecto" = ' + "'@@'")
            #--------------------------------------------------
            self.cmbTensionAction = self.toolbar_h.addWidget(self.cmbTension)
            self.cmbTension.currentIndexChanged.connect(self.elijo_tension)
            self.cmbTension.setToolTip("Capa")
            self.toolbar_h.addSeparator()
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_nodo.png'), 'Nodo', self.h_nodo, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_linea.png'), 'Linea', self.h_linea, True, False, True, True, None, None, self.iface.mainWindow())
            #boton desplegable
            self.tool_button = QtWidgets.QToolButton()
            self.tool_button.setText("Vertices")
            self.tool_button.setIcon(QtGui.QIcon(os.path.join(basepath,"icons", 'img_vertices.png')))
            menu_boton = QtWidgets.QMenu()
            self.vertices_1 = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_agregar_vertice.png')), 'Agregar Vertice', self.toolbar_h)
            self.vertices_2 = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_quitar_vertice.png')), 'Borrar Vertice', self.toolbar_h)
            self.vertices_1.triggered.connect(self.h_agregar_vertice)
            self.vertices_2.triggered.connect(self.h_quitar_vertice)
            menu_boton.addAction(self.vertices_1)
            menu_boton.addAction(self.vertices_2)
            self.tool_button.setMenu(menu_boton)
            self.tool_button.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
            self.toolbar_h.addWidget(self.tool_button)
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_conectar.png'), 'Conectar', self.h_conectar, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_poste.png'), 'Poste', self.h_poste, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_area.png'), 'Area', self.h_area, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_parcela.png'), 'Parcela', self.h_parcela, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_anotacion.png'), 'Anotacion', self.h_anotacion, True, False, True, True, None, None, self.iface.mainWindow())
            #self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_girar.png'), 'Girar', self.h_girar, True, False, True, True, None, None, self.iface.mainWindow())
            self.toolbar_h.addSeparator()
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_mover.png'), 'Mover', self.h_mover, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_rotar.png'), 'Rotar', self.h_rotar, True, False, True, True, None, None, self.iface.mainWindow())
            self.toolbar_h.addSeparator()
            self.agregar_herramienta(self.toolbar_h, os.path.join(basepath,"icons", 'img_borrar.png'), 'Borrar', self.h_borrar, True, False, True, True, None, None, self.iface.mainWindow())
            #--------------------------------------------------
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_zoom.png'), 'Zoom', self.h_zoom, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_pan.png'), 'Pan', self.h_Pan, True, False, True, True, None, None, self.iface.mainWindow())
            self.toolbar_v.addSeparator()
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_buscar.png'), 'Buscar', self.h_buscar, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_buscar_direccion.png'), 'Buscar Direccion', self.h_buscar_direccion, True, False, True, True, None, None, self.iface.mainWindow())
            self.toolbar_v.addSeparator()
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_nav_fuente.png'), 'Navegar a la Fuente', self.h_navegar_a_la_fuente, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_nav_extremos.png'), 'Navegar a los Extremos', self.h_navegar_extremos, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_desconectados.png'), 'Desconectados', self.h_desconectados, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_aislados.png'), 'Aislados', self.h_aislados, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_loops.png'), 'Loops', self.h_loops, True, False, True, True, None, None, self.iface.mainWindow())
            self.toolbar_v.addSeparator()
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_reclamos.png'), 'Reclamos', self.h_reclamos, True, True, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_contingencias.png'), 'Contingencias', self.carga_contingencias, True, False, True, True, None, None, self.iface.mainWindow())
            self.toolbar_v.addSeparator()
            if self.modulo_calculos==1:
                #boton desplegable
                self.tool_button = QtWidgets.QToolButton()
                self.tool_button.setText("Vertices")
                self.tool_button.setIcon(QtGui.QIcon(os.path.join(basepath,"icons", 'img_calculadora.png')))
                menu_boton = QtWidgets.QMenu()
                self.flujo = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_caida_tension.png')), 'Flujo de Cargas', self.toolbar_v)
                #self.flujo_3f = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_flujo3f.png')), 'Flujo Desequilibrado', self.toolbar_v)
                self.corto = QtGui.QAction(QtGui.QIcon(os.path.join(basepath,"icons", 'img_corto.png')), 'Cortocircuito', self.toolbar_v)
                self.flujo.triggered.connect(self.h_flujo)
                #self.flujo_3f.triggered.connect(self.h_flujo_desequilibrado)
                self.corto.triggered.connect(self.h_cortocircuito)
                menu_boton.addAction(self.flujo)
                #menu_boton.addAction(self.flujo_3f)
                menu_boton.addAction(self.corto)
                self.tool_button.setMenu(menu_boton)
                self.tool_button.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
                self.toolbar_v.addWidget(self.tool_button)
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_usuario.png'), 'Usuarios Nuevos', self.h_usuarios_nuevos, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_electrodependientes.png'), 'Usuarios Electrodependientes', self.h_electrodependientes, True, True, True, True, None, None, self.iface.mainWindow())
            self.toolbar_v.addSeparator()
            self.agregar_herramienta(self.toolbar_v, os.path.join(basepath,"icons", 'img_resultado_seleccion.png'), 'Datos de la Selección', self.h_datos_seleccion, True, False, True, True, None, None, self.iface.mainWindow())
            #--------------------------------------------------
            self.cmbProyecto = QtWidgets.QComboBox(self.iface.mainWindow())
            #--------------------------------------------------
            cursor = self.conn.cursor()
            cursor.execute("SELECT Nombre FROM Proyectos")
            #convierto el cursor en array
            proyectos = tuple(cursor)
            cursor.close()
            self.cmbProyecto.clear()
            self.cmbProyecto.addItem("<Proyecto>")
            for p in range (0, len(proyectos)):
                self.cmbProyecto.addItem(str(proyectos[p][0]))
            self.agregar_herramienta(self.toolbar_p, os.path.join(basepath,"icons", 'img_nuevo.png'), 'Nuevo Proyecto', self.h_crear_proyecto, True, False, True, True, None, None, self.iface.mainWindow())
            #--------------------------------------------------
            self.cmbProyectoAction = self.toolbar_p.addWidget(self.cmbProyecto)
            self.cmbProyecto.currentIndexChanged.connect(self.elijo_proyecto)
            self.cmbProyecto.setToolTip("Proyecto")
            self.cmbProyecto.setFixedWidth(200)
            #--------------------------------------------------
            self.toolbar_p.addSeparator()
            self.agregar_herramienta(self.toolbar_p, os.path.join(basepath,"icons", 'img_editar.png'), 'Modificar Proyecto', self.h_editar_proyecto, True, True, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_p, os.path.join(basepath,"icons", 'img_incorporar.png'), 'Incorporar Proyecto', self.h_incorporar_proyecto, False, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_p, os.path.join(basepath,"icons", 'img_quitar.png'), 'Borrar Proyecto', self.h_borrar_proyecto, False, False, True, True, None, None, self.iface.mainWindow())
            #--------------------------------------------------
            self.toolbar_p.addSeparator()
            self.agregar_herramienta(self.toolbar_p, os.path.join(basepath,"icons", 'img_cotas.png'), 'Agregar Cota', self.h_cotas, False, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_p, os.path.join(basepath,"icons", 'img_borrar_ultima_cota.png'), 'Borrar última Cota', self.h_borrar_ultima_cota, False, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_p, os.path.join(basepath,"icons", 'img_borrar_cotas.png'), 'Borrar Cotas', self.h_borrar_cotas, False, False, True, True, None, None, self.iface.mainWindow())
            for action in self.actions:
                if str(action.text())=='Modificar Proyecto':
                    action.setEnabled(False)
            #Esta etiqueta va ultima
            #--------------------------------------------------
            #self.lblTension = QLabel(self.iface.mainWindow())
            #--------------------------------------------------
            #self.lblTension.setText('0')
            #self.agregar_herramienta(self.toolbar_p, os.path.join(basepath,"icons", 'img_nuevo.png'), 'Tension', self.h_crear_proyecto, True, False, True, True, None, None, self.iface.mainWindow())
            #--------------------------------------------------
            #self.lblTensionAction = self.toolbar_p.addWidget(self.lblTension)
            #self.lblTension.setToolTip("Proyecto")
            self.agregar_herramienta(self.toolbar_e, os.path.join(basepath,"icons", 'img_seleccion_ejes.png'), 'Seleccionar Eje', self.h_seleccionar_ejes, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_e, os.path.join(basepath,"icons", 'img_eje.png'), 'Eje de Calle', self.h_eje, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_e, os.path.join(basepath,"icons", 'img_editar_ejes.png'), 'Cargar Datos', self.h_datos_eje, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_e, os.path.join(basepath,"icons", 'img_mover.png'), 'Mover Ejes', self.h_mover_ejes, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_e, os.path.join(basepath,"icons", 'img_rotar.png'), 'Rotar Ejes', self.h_rotar_ejes, True, False, True, True, None, None, self.iface.mainWindow())
            self.agregar_herramienta(self.toolbar_e, os.path.join(basepath,"icons", 'img_borrar.png'), 'Borrar Eje de Calle', self.h_borrar_ejes, True, False, True, True, None, None, self.iface.mainWindow())
            self.actualizar_db()
            self.h_login()
            self.iface.mapCanvas().setMapTool(None)
        else:
            try:
                main_window = self.iface.mainWindow()
                self.toolbar_h.deleteLater()
                self.toolbar_p.deleteLater()
                self.toolbar_e.deleteLater()
                self.toolbar_v.deleteLater()
                self.dock_widget.deleteLater()
                self.dock_widget2.deleteLater()
            except:
                pass
        self.descargo_red()
        self.h_seleccion()

    def actualizar_base_datos(self):
        self.tipo_navegacion=0
        self.modulo_calculos=0
        try:
            import clr
            clr.AddReference("mscorlib")
            clr.AddReference("System")
            clr.AddReference(os.path.join(basepath, 'NavRed6.dll'))
            from EnerGis6.NavRed6 import NavRed
            from System import Int64
            prueba = Int64(self.tipo_navegacion)
            self.tipo_navegacion=1
        except:
            pass
        #pandas pandapower sqlalchemy numba numpy
        try:
            import pandas as pd
            import pandapower as pp
            prueba = pd.DataFrame()
            self.modulo_calculos=1
        except:
            pass

        self.conectar_db()
        conn = self.conn
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM lineas WHERE desde=0 OR hasta=0 OR desde=hasta")
            conn.commit()
        except:
            conn.rollback()

    def actualizar_a_net(self):
        qgis_path = QgsApplication.applicationDirPath()
        try:
            """
            f = open('c:/gis/energis6/install_pip.bat','w')
            f.writelines("cd " + qgis_path + "/..\n")
            f.writelines("OSGeo4W.bat python3.exe -m pip install --upgrade pip\n")
            f.writelines("exit\n")
            f.close()
            subprocess.run('c:/gis/energis6/install_pip.bat')

            sqlalchemy

            #--------------------------------------------------
            f = open('c:/gis/energis6/install_pyodbc.bat','w')
            f.writelines("cd " + qgis_path + "/..\n")
            f.writelines("OSGeo4W.bat pip install pyodbc\n")
            f.writelines("exit\n")
            f.close()
            subprocess.run('c:/gis/energis6/install_pyodbc.bat')
            #--------------------------------------------------
            f = open('c:/gis/energis6/install_matplotlib.bat','w')
            f.writelines("cd " + qgis_path + "/..\n")
            f.writelines("OSGeo4W.bat pip install matplotlib\n")
            f.writelines("exit\n")
            f.close()
            subprocess.run('c:/gis/energis6/install_matplotlib.bat')
            #--------------------------------------------------
            f = open('c:/gis/energis6/install_pythonnet.bat','w')
            f.writelines("cd " + qgis_path + "/..\n")
            f.writelines("OSGeo4W.bat pip install pythonnet\n")
            f.writelines("exit\n")
            f.close()
            subprocess.run('c:/gis/energis6/install_pythonnet.bat')
            #--------------------------------------------------
            f = open('c:/gis/energis6/install_xlwt.bat','w')
            f.writelines("cd " + qgis_path + "/..\n")
            f.writelines("OSGeo4W.bat pip install xlwt\n")
            f.writelines("exit\n")
            f.close()
            subprocess.run('c:/gis/energis6/install_xlwt.bat')
            """
            #--------------------------------------------------
            subprocess.run('winget install Microsoft.DotNet.DesktopRuntime.9')
            #--------------------------------------------------
            QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ Actualizado !")
        except:
            QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo instalar el entorno !")

            self.tipo_navegacion=0
            try:
                import clr
            except:
                QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo importar clr !")
            try:
                clr.AddReference("mscorlib")
            except:
                QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo agregar mscorlib !")
            try:
                clr.AddReference("System")
            except:
                QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo agregar el System !")
            try:
                clr.AddReference(os.path.join(basepath, 'NavRed6.dll'))
            except:
                QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo agregar " + os.path.join(basepath, 'NavRed6.dll') + " !")

            try:
                dll = os.path.join(basepath, "NavRed6.dll")
                QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "Cargando:" + dll)
                clr.AddReference(dll)
                from EnerGis6.NavRed6 import NavRed
            except Exception as e:
                QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ Error:" + str(e))

            asm = clr.AddReference(dll)
            for t in asm.GetTypes():
                QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ " + t.FullName)

            try:
                from System import Int64
            except:
                QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo importar Int64 !")
            try:
                prueba = Int64(self.tipo_navegacion)
            except:
                QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo cargar la prueba !")
                self.tipo_navegacion=1
            try:
                import System
            except:
                QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo importar System !")
                QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ Ver en: " + str(System._path_))

    def agregar_herramienta(self, toolbar, icon_path, text, callback, enabled_flag, checkable_flag, add_to_menu, add_to_toolbar, status_tip, whats_this, parent):
        try:
            icon = QtGui.QIcon(icon_path)
            action = QtGui.QAction(icon, text, parent)
            action.triggered.connect(callback)
            action.setEnabled(enabled_flag)
            action.setCheckable(checkable_flag)
            if status_tip is not None:
                action.setStatusTip(status_tip)
            if whats_this is not None:
                action.setWhatsThis(whats_this)
            if add_to_toolbar:
                toolbar.addAction(action)
            if add_to_menu:
                #self.iface.addPluginToVectorMenu(self.menu, action)
                pass
            self.actions.append(action)
            return action
        except:
            return None

    def unload(self):
        self.iface.removeToolBarIcon(self.energis_action)
        try:
            self.toolbar_h.deleteLater()
            main_window = self.iface.mainWindow()
            main_window.removeToolBar(self.toolbar_p)
            main_window.removeToolBar(self.toolbar_v)
            self.toolbar_p.deleteLater()
            self.toolbar_v.deleteLater()
            self.iface.mapCanvas().setMapTool(None)
        except:
            pass

    def elijo_tension(self):
        self.tension = self.cmbTension.currentText()
        #Si cambio de tension despues de elegir la herramienta, queda seteada en la herramienta la tension anterior
        # Obtener la herramienta actual del canvas del mapa
        current_map_tool = str(self.iface.mapCanvas().mapTool())
        indice = current_map_tool.find('herrNodo')
        if indice != -1:
            self.h_nodo()
        indice = current_map_tool.find('herrLinea')
        if indice != -1:
            self.h_linea()
        indice = current_map_tool.find('herrPoste')
        if indice != -1:
            self.h_poste()

    def usuarios(self):
        from .frm_datos_usuarios import frmDatosUsuarios
        self.dialogo = frmDatosUsuarios(self.conn, 0)
        self.dialogo.show()

    def carga_contingencias(self):
        if self.red_verificada==False:
            self.h_verificar_red()
        if self.red_verificada==False:
            QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ Podrá cargar contingencias pero no registrarlas")
        if self.tipo_usuario==4:
            return
        if self.tipo_navegacion==0:
            from .mod_navegacion_ant import nodos_por_transformador
            nodos_por_transformador(self, self.conn)
            from .frm_contingencias_ant import frmContingencias
            self.dialogo = frmContingencias(self.conn, self.iface.mapCanvas(), self.tipo_usuario, self.red_verificada)
            self.dialogo.show()
        else:
            from .frm_contingencias import frmContingencias
            self.dialogo = frmContingencias(self.conn, self.iface.mapCanvas(), self.tipo_usuario, self.mnodos, self.mlineas, self.red_verificada)
            self.dialogo.show()

    def listado_lineas(self):
        from .frm_listado_lineas import frmListadoLineas
        self.dialogo = frmListadoLineas(self.conn)
        self.dialogo.show()

    def listado_seccionadores(self):
        str_sql = "SELECT Nodos.Geoname As id_nodo, Nodos.Nombre As secc, Nodos.Val1 As tipo, Nodos.Val2 As subtipo, Nodos.Val3 As fusible, Nodos.Val4 As marca, Nodos.Val5 As modelo, Nodos.Nivel As nivel, Nodos.Tension As tension, Nodos.Zona As zona, Nodos.Alimentador As alimentador, Nodos.XCoord As x, Nodos.YCoord As y FROM Nodos WHERE Nodos.Tension>0 AND Nodos.Elmt = 2 Or Nodos.Elmt = 3"
        from .frm_listados import frmListados
        self.dialogo = frmListados(self.conn, str_sql)
        self.dialogo.setWindowTitle("Listado de Seccionadores")
        self.dialogo.show()

    def listado_postes(self):
        str_sql = "SELECT Postes.Geoname AS id_poste, Elementos_Postes.Descripcion AS material, Estructuras.Descripcion AS estructura, Postes.Altura, Riendas.Descripcion AS rienda, Lineas.Zona AS zona, Lineas.Alimentador AS alimentador, Lineas.Tension AS tension, Postes.XCoord AS x, Postes.YCoord AS y FROM (Lineas_Postes INNER JOIN (Riendas RIGHT JOIN ((Postes LEFT JOIN Elementos_Postes ON Postes.Elmt = Elementos_Postes.Id) LEFT JOIN Estructuras ON Postes.Estructura = Estructuras.Id) ON Riendas.Id = Postes.Rienda) ON Lineas_Postes.id_poste = Postes.Geoname) INNER JOIN Lineas ON Lineas_Postes.id_linea = Lineas.Geoname"
        from .frm_listados import frmListados
        self.dialogo = frmListados(self.conn, str_sql)
        self.dialogo.setWindowTitle("Listado de Postes")
        self.dialogo.show()

    def listado_cts(self):
        str_sql = "SELECT Transformadores.Id_trafo AS id_trafo, Nodos.Geoname AS id_nodo, Ct.id_ct, Ct.Ubicacion AS ubicacion, Transformadores.Potencia AS potencia, Transformadores.Tension_1 AS v1, Transformadores.Tension_2 AS v2, Tipo_Trafo.Tipo AS tipo_trafo, Transformadores.Conexionado AS conexionado, Transformadores.Marca AS marca, Transformadores.N_chapa AS nro_chapa, Transformadores.Obs AS Observaciones, Transformadores.Anio_fabricacion AS año, Ct.Mat_plataf AS plataforma, Ct.Tipo_ct AS tipo_ct, Nodos.Nivel AS nivel, Nodos.Tension AS tension_nodo, Nodos.Zona AS zona, Nodos.Alimentador AS alimentador_mt, Nodos.XCoord AS x, Nodos.YCoord AS y, Transformadores.Kit AS kit, Transformadores.Cromatografia AS cromatografia, Transformadores.Anomalia AS anomalia, Transformadores.Fecha_norm AS fecha_norm, Transformadores.Obs_pcb AS observaciones_pcb FROM Tipo_Trafo INNER JOIN Transformadores ON Tipo_Trafo.Numero = Transformadores.Tipo RIGHT OUTER JOIN Nodos RIGHT OUTER JOIN Ct ON Nodos.Nombre = Ct.Id_ct ON Transformadores.Id_ct = Ct.Id_ct WHERE Nodos.Elmt = 4 ORDER BY Ct.Id_ct"
        from .frm_listados import frmListados
        self.dialogo = frmListados(self.conn, str_sql)
        self.dialogo.setWindowTitle("Listado de CTs")
        self.dialogo.show()

    def listado_transformadores(self):
        str_sql = "SELECT Transformadores.Id_trafo AS id_trafo, Transformadores.id_ct AS id_ct, Ubicaciones.Descripcion AS [ubicado en], Ct.Ubicacion AS ubicacion, Transformadores.Potencia AS potencia, Transformadores.Tension_1 AS v1, Transformadores.Tension_2 AS v2, Tipo_Trafo.Tipo AS tipo_trafo, Transformadores.Conexionado AS conexionado, Transformadores.Marca AS marca, Transformadores.N_chapa AS nro_chapa, Transformadores.Anio_fabricacion AS año, Ct.Mat_plataf AS plataforma, Ct.Tipo_Ct AS tipo_ct, Transformadores.Kit AS kit, Transformadores.Cromatografia AS cromatografia, Transformadores.Anomalia AS anomalia, Transformadores.Fecha_norm AS fecha_norm, Transformadores.Obs_pcb AS observaciones_pcb FROM ((Tipo_Trafo INNER JOIN Transformadores ON Tipo_Trafo.Numero = Transformadores.Tipo) LEFT JOIN Ct ON Transformadores.id_ct = Ct.id_ct) LEFT JOIN Ubicaciones ON Transformadores.Usado = Ubicaciones.Id_Ubicacion"
        from .frm_listados import frmListados
        self.dialogo = frmListados(self.conn, str_sql)
        self.dialogo.setWindowTitle("Listado de Transformadores")
        self.dialogo.show()

    def listado_transformadores_red(self):
        str_sql = "SELECT Transformadores.Id_trafo AS id_trafo, Nodos.Geoname AS id_nodo, Nodos.Nombre AS id_ct, Ct.Ubicacion AS ubicacion, Transformadores.Potencia AS potencia, Transformadores.Tension_1 AS v1, Transformadores.Tension_2 AS v2, Tipo_Trafo.Tipo AS tipo_trafo, Transformadores.Conexionado AS conexionado, Transformadores.Marca AS marca, Transformadores.N_chapa AS nro_chapa, Transformadores.Obs AS Observaciones, Transformadores.Anio_fabricacion AS año, Ct.Mat_plataf AS plataforma, Ct.Tipo_ct AS tipo_ct, Nodos.Nivel AS nivel, Nodos.Tension AS tensión_nodo, Nodos.Zona AS zona, Nodos.Alimentador AS alimentador_mt, Nodos.XCoord AS x, Nodos.YCoord AS y, Transformadores.Kit AS kit, Transformadores.Cromatografia AS cromatografia, Transformadores.Anomalia AS anomalia,  Transformadores.Fecha_norm AS fecha_norm, Transformadores.Obs_pcb AS observaciones_pcb, COUNT(Usuarios.id_usuario) AS cant_usuarios FROM Transformadores INNER JOIN Nodos INNER JOIN Ct ON Nodos.Nombre = Ct.Id_ct ON Transformadores.Id_ct = Ct.Id_ct INNER JOIN Tipo_Trafo ON Transformadores.Tipo = Tipo_Trafo.Numero LEFT OUTER JOIN Suministros_Trafos LEFT OUTER JOIN Usuarios RIGHT OUTER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro ON Suministros_Trafos.Geoname_s = Suministros.id_nodo ON Nodos.Geoname = Suministros_Trafos.Geoname_t WHERE Usuarios.ES = 1 GROUP BY Transformadores.Id_trafo, Nodos.Geoname, Nodos.Nombre, Ct.Ubicacion, Transformadores.Potencia, Transformadores.Tension_1, Transformadores.Tension_2, Tipo_Trafo.Tipo, Transformadores.Conexionado, Transformadores.Marca, Transformadores.N_chapa, Transformadores.Obs, Transformadores.Anio_fabricacion, Ct.Mat_plataf, Ct.Tipo_ct, Nodos.Nivel, Nodos.Tension, Nodos.Zona, Nodos.Alimentador, Nodos.XCoord, Nodos.YCoord, Transformadores.Kit, Transformadores.Cromatografia, Transformadores.Anomalia, Transformadores.Fecha_norm, Transformadores.Obs_pcb"
        from .frm_listados import frmListados
        self.dialogo = frmListados(self.conn, str_sql)
        self.dialogo.setWindowTitle("Listado de Transformadores en la Red")
        self.dialogo.show()

    def importar_usuarios_oceba(self):
        import re
        a=0
        n=0
        fecha_baja=''
        cursor = self.conn.cursor()
        cursor.execute("SELECT Codigo FROM Empresa")
        #convierto el cursor en array
        empresa = tuple(cursor)
        cursor.close()
        codigo_empresa = empresa[0][0]
        dialog = QtWidgets.QFileDialog()
        oFileName = dialog.getOpenFileName(None, "Archivo de Usuarios", "", "TXT files (*.txt)")
        fileName=oFileName[0]
        if fileName:
            f = open(fileName,'r')
            txt_usuarios_oceba = f.readlines()
            f.close()
            ilinea=0
            reply = QtWidgets.QMessageBox.question(None, 'EnerGis', "El archivo tiene " + str(len(txt_usuarios_oceba)) + " lineas. Desea importar ❓", QtWidgets.QMessageBox.StandardButton.Yes, QtWidgets.QMessageBox.StandardButton.No)
            if reply == QtWidgets.QMessageBox.StandardButton.No:
                return
            #----------------------------------------------------------------------------
            progress = QtWidgets.QProgressDialog("Procesando...", "Cancelar", 0, 100)
            progress.setWindowTitle("Progreso")
            progress.setWindowModality(Qt.WindowModality.ApplicationModal)  # Hace que la ventana de progreso sea modal
            progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
            progress.setValue(0)  # Inicia el progreso en 0
            QtWidgets.QApplication.processEvents()
            #----------------------------------------------------------------------------
            for linea in range (1, len(txt_usuarios_oceba)):
                #----------------------------------------------------------------------------
                progress.setValue(int(40*linea/len(txt_usuarios_oceba)))
                if progress.wasCanceled():
                    return
                QtWidgets.QApplication.processEvents()
                #----------------------------------------------------------------------------
                registro_usuario = txt_usuarios_oceba[linea].split(';')
                ilinea=ilinea+1
                if registro_usuario[0].strip()!=codigo_empresa:
                    QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ El archivo no es válido, corresponde a otra empresa:" + registro_usuario[0].strip())
                    return
                if len(registro_usuario)<28:
                    QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ El archivo no es válido, contiene " + str(len(registro_usuario)) + " campos en línea " + str(ilinea))
                    return
            reply = QtWidgets.QMessageBox.question(None, 'EnerGis', "Desea borrar los datos en la base antes de importar ❓", QtWidgets.Yes, QtWidgets.QMessageBox.StandardButton.No)
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                cursor = self.conn.cursor()
                try:
                    cursor.execute("DELETE FROM VW_CCDATOSCOMERCIALES")
                    self.conn.commit()
                except:
                    self.conn.rollback()
            #----------------------------------------------------------------------------
            progress.setValue(40)
            QtWidgets.QApplication.processEvents()
            #----------------------------------------------------------------------------
            for linea in range (1, len(txt_usuarios_oceba)):
                #----------------------------------------------------------------------------
                progress.setValue(40 + int(50*linea/len(txt_usuarios_oceba)))
                if progress.wasCanceled():
                    return
                QtWidgets.QApplication.processEvents()
                #----------------------------------------------------------------------------
                registro_usuario = txt_usuarios_oceba[linea].split(';')
                str_campos = "Id_Usuario,Nro_Medidor,Apellido,Nombre,DNI,CUIT,Direccion_Postal,Calle,Numero,Piso,Dto,Entre, Localidad,Partido,Codigo_Postal,Telefono,E_Mail,Tarifa,Tarifa_Especial,Ruta,Tension_Suministro,Potencia_Declarada,Nomenclatura_Catastral,Fecha_Alta"
                str_valores = ""
                for i in range (2, 28):
                    str_valor = registro_usuario[i].strip()
                    str_valor = str_valor.replace("'", "")
                    if i==8 or i==9:
                        str_valor = re.sub(r"\s+", " ", str_valor)
                    if i==17 or i==23:
                        str_valor = str_valor.lstrip('0')
                    if i==28:
                        if str_valor!="":
                            str_campos = str_campos + ",Fecha_Baja"
                    if i>26: #fechas
                        if i==28: #fecha baja
                            if str_valor=="":
                                pass
                            else:
                                str_valor = datetime.strptime(str_valor, "%d/%m/%Y").strftime("%Y%m%d")
                                fecha_baja = str_valor
                                str_valores = str_valores + "'" + str_valor + "',"
                        elif i==27: #fecha alta
                            if str_valor=="":
                                fecha_alta = "1980-01-01"
                                str_valores = str_valores + "'1980-01-01',"
                            else:
                                str_valor = datetime.strptime(str_valor, "%d/%m/%Y").strftime("%Y%m%d")
                                fecha_alta = str_valor
                                str_valores = str_valores + "'" + str_valor + "',"
                    else:
                        if i!=25 and i!=26: #salteo lat y long
                            str_valores = str_valores + "'" + str_valor + "',"
                #saco la última coma
                str_valores = str_valores[:-1]
                cursor = self.conn.cursor()
                cursor.execute("SELECT * FROM VW_CCDATOSCOMERCIALES WHERE id_usuario='" + str(registro_usuario[2]) + "'")
                #convierto el cursor en array
                usuario = tuple(cursor)
                cursor.close()
                if len(usuario)==0:
                    try:
                        cursor = self.conn.cursor()
                        cursor.execute("INSERT INTO VW_CCDATOSCOMERCIALES (" + str_campos + ") VALUES (" + str_valores + ")")
                        self.conn.commit()
                        n = n + 1
                    except:
                        QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ Fallo al insertar en fila " + str(n+1))
                        self.conn.rollback()
                        return
                else:
                    str_sql = "UPDATE VW_CCDATOSCOMERCIALES SET "
                    str_sql = str_sql + "Nro_Medidor='" + registro_usuario[3].strip() + "',"
                    str_sql = str_sql + "Apellido='" + registro_usuario[4].strip() + "',"
                    str_sql = str_sql + "Nombre='" + registro_usuario[5].strip() + "',"
                    str_sql = str_sql + "DNI='" + registro_usuario[6].strip() + "',"
                    str_sql = str_sql + "CUIT='" + registro_usuario[7].strip() + "',"
                    str_sql = str_sql + "Direccion_Postal='" + re.sub(r"\s+", " ", registro_usuario[8].strip()) + "',"
                    str_sql = str_sql + "Calle='" + re.sub(r"\s+", " ", registro_usuario[9].strip()) + "',"
                    str_sql = str_sql + "Numero='" + registro_usuario[10].strip() + "',"
                    str_sql = str_sql + "Piso='" + registro_usuario[11].strip() + "',"
                    str_sql = str_sql + "Dto='" + registro_usuario[12].strip() + "',"
                    str_sql = str_sql + "Entre='" + registro_usuario[13].strip() + "',"
                    str_sql = str_sql + "Localidad='" + registro_usuario[14].strip() + "',"
                    str_sql = str_sql + "Partido='" + registro_usuario[15].strip() + "',"
                    str_sql = str_sql + "Codigo_Postal='" + registro_usuario[16].strip() + "',"
                    str_sql = str_sql + "Telefono='" + registro_usuario[17].strip().lstrip('0') + "',"
                    str_sql = str_sql + "E_Mail='" + registro_usuario[18].strip() + "',"
                    str_sql = str_sql + "Tarifa='" + registro_usuario[19].strip() + "',"
                    str_sql = str_sql + "Tarifa_Especial='" + registro_usuario[20].strip() + "',"
                    str_sql = str_sql + "Ruta='" + registro_usuario[21].strip() + "',"
                    str_sql = str_sql + "Tension_Suministro='" + registro_usuario[22].strip() + "',"
                    str_sql = str_sql + "Potencia_Declarada='" + registro_usuario[23].strip().lstrip('0') + "',"
                    str_sql = str_sql + "Nomenclatura_Catastral='" + registro_usuario[24].strip() + "',"
                    str_sql = str_sql + "Fecha_Alta='" + fecha_alta + "',"
                    if fecha_baja=='':
                        str_sql = str_sql + "Fecha_Baja=NULL,"
                    else:
                        str_sql = str_sql + "Fecha_Baja='" + fecha_baja + "',"
                    #saco la última coma
                    str_sql = str_sql[:-1]
                    str_sql = str_sql + " WHERE id_usuario='" + str(registro_usuario[2].strip()) + "'"
                    try:
                        cursor = self.conn.cursor()
                        cursor.execute(str_sql)
                        self.conn.commit()
                        a = a + 1
                    except:
                        QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ Fallo al actualizar en fila " + str(a+1))
                        self.conn.rollback()
                        return
            QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ Fin. " + str(n) + " registros nuevos, y " + str(a) + " registros actualizados")
            #----------------------------------------------------------------------------
            progress.setValue(90)
            QtWidgets.QApplication.processEvents()
            #----------------------------------------------------------------------------
        cursor = self.conn.cursor()
        try:
            cursor.execute("UPDATE A SET d=o FROM (SELECT VW_CCDATOSCOMERCIALES.[Apellido] + ' ' + VW_CCDATOSCOMERCIALES.[nombre] AS o, Usuarios.nombre AS d FROM VW_CCDATOSCOMERCIALES INNER JOIN Usuarios ON VW_CCDATOSCOMERCIALES.Id_Usuario = Usuarios.id_usuario WHERE VW_CCDATOSCOMERCIALES.[Apellido] + ' ' + VW_CCDATOSCOMERCIALES.[nombre] <> Usuarios.nombre AND VW_CCDATOSCOMERCIALES.[Apellido] <> VW_CCDATOSCOMERCIALES.[nombre]) AS A ")
            cursor.execute("UPDATE A SET d=o FROM (SELECT VW_CCDATOSCOMERCIALES.[Tarifa] AS o, Usuarios.Tarifa AS d FROM VW_CCDATOSCOMERCIALES INNER JOIN Usuarios ON VW_CCDATOSCOMERCIALES.Id_Usuario = Usuarios.id_usuario WHERE VW_CCDATOSCOMERCIALES.[Tarifa] <> Usuarios.Tarifa) AS A")
            cursor.execute("UPDATE A SET d=o FROM (SELECT VW_CCDATOSCOMERCIALES.[Calle] AS o, Usuarios.Calle AS d FROM VW_CCDATOSCOMERCIALES INNER JOIN Usuarios ON VW_CCDATOSCOMERCIALES.Id_Usuario = Usuarios.id_usuario WHERE VW_CCDATOSCOMERCIALES.[Calle] <> Usuarios.Calle) AS A")
            cursor.execute("UPDATE A SET d=o FROM (SELECT VW_CCDATOSCOMERCIALES.[Numero] AS o, Usuarios.Altura AS d FROM VW_CCDATOSCOMERCIALES INNER JOIN Usuarios ON VW_CCDATOSCOMERCIALES.Id_Usuario = Usuarios.id_usuario WHERE VW_CCDATOSCOMERCIALES.[Numero] <> Usuarios.Altura) AS A")
            cursor.execute("UPDATE Usuarios SET Electrodependiente='N' WHERE Electrodependiente<>'N'")
            cursor.execute("UPDATE Usuarios SET Electrodependiente='S' WHERE Electrodependiente<>'S' AND id_usuario IN (SELECT id_usuario FROM VW_CCDATOSCOMERCIALES WHERE tarifa_especial ='TE')")
            cursor.execute("UPDATE A SET ES = 1 FROM (SELECT Usuarios.[ES] FROM VW_CCDATOSCOMERCIALES INNER JOIN Usuarios ON VW_CCDATOSCOMERCIALES.Id_Usuario = Usuarios.id_usuario WHERE (((VW_CCDATOSCOMERCIALES.Fecha_Baja) IS NULL) AND ((Usuarios.[ES])=0))) AS A")
            cursor.execute("UPDATE A SET ES = 0 FROM (SELECT Usuarios.[ES] FROM VW_CCDATOSCOMERCIALES INNER JOIN Usuarios ON VW_CCDATOSCOMERCIALES.Id_Usuario = Usuarios.id_usuario WHERE (((Usuarios.[ES])=1) AND ((VW_CCDATOSCOMERCIALES.Fecha_Baja) IS NOT NULL))) AS A")
            cursor.execute("INSERT INTO Usuarios SELECT VW_CCDATOSCOMERCIALES.Id_Usuario AS Id_Usuario,0 AS Tipo,VW_CCDATOSCOMERCIALES.Apellido AS Nombre,VW_CCDATOSCOMERCIALES.Calle AS Calle,VW_CCDATOSCOMERCIALES.Numero AS Altura,VW_CCDATOSCOMERCIALES.Piso + ' ' + VW_CCDATOSCOMERCIALES.Dto AS Altura_Ex,VW_CCDATOSCOMERCIALES.Codigo_Postal AS Zona,VW_CCDATOSCOMERCIALES.Id_Usuario AS Id_Suministro,VW_CCDATOSCOMERCIALES.Tarifa AS Tarifa,123 AS Fase,1 AS ES,VW_CCDATOSCOMERCIALES.Localidad AS SubZona,CASE WHEN [Tarifa_Especial]='TE' THEN 'S' ELSE 'N' END AS Electrodependiente,'N' AS Fae,'' AS Prosumidor FROM VW_CCDATOSCOMERCIALES LEFT JOIN Usuarios ON VW_CCDATOSCOMERCIALES.Id_Usuario = Usuarios.id_usuario WHERE VW_CCDATOSCOMERCIALES.Fecha_Baja IS NULL AND Usuarios.id_usuario IS NULL")
            cursor.execute("UPDATE Usuarios SET ES = 1 WHERE Es=0 AND id_usuario IN (SELECT id_usuario FROM VW_CCDATOSCOMERCIALES WHERE Fecha_Baja IS NULL)")
            cursor.execute("UPDATE Usuarios SET ES = 0 WHERE Es=1 AND id_usuario IN (SELECT id_usuario FROM VW_CCDATOSCOMERCIALES WHERE not Fecha_Baja IS NULL)")
            cursor.execute("UPDATE Usuarios SET ES = 0 WHERE Es=1 AND id_usuario NOT IN (SELECT id_usuario from VW_CCDATOSCOMERCIALES)")
            cursor.execute("INSERT INTO medidores SELECT '0' AS nro_medidor, id_usuario, '' AS marca, '' AS modelo, 1980 AS anio, '' AS relacion, '' AS fases, '' AS tipo FROM Usuarios WHERE id_usuario NOT IN (SELECT id_usuario FROM medidores)")
            cursor.execute("UPDATE A SET d=o FROM (SELECT VW_CCDATOSCOMERCIALES.nro_medidor AS o, Medidores.Nro_Medidor AS d FROM VW_CCDATOSCOMERCIALES INNER JOIN Medidores ON VW_CCDATOSCOMERCIALES.Id_Usuario = medidores.id_usuario WHERE VW_CCDATOSCOMERCIALES.Nro_Medidor <> medidores.Nro_Medidor AND VW_CCDATOSCOMERCIALES.nro_medidor<>'') AS A")
            self.conn.commit()
        except:
            self.conn.rollback()
        #----------------------------------------------------------------------------
        progress.setValue(100)
        QtWidgets.QApplication.processEvents()
        #----------------------------------------------------------------------------

    def importar_energias_dpe(self):
        a=0
        n=0
        dialog = QtWidgets.QFileDialog()
        oFileName = dialog.getOpenFileName(None, "Archivo de Consumos", "", "TXT files (*.txt)")
        fileName=oFileName[0]
        if fileName:
            #----------------------------------------------------------------------------
            progress = QtWidgets.QProgressDialog("Procesando...", "Cancelar", 0, 100)
            progress.setWindowTitle("Progreso")
            progress.setWindowModality(Qt.WindowModality.ApplicationModal)  # Hace que la ventana de progreso sea modal
            progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
            progress.setValue(0)  # Inicia el progreso en 0
            QtWidgets.QApplication.processEvents()
            #----------------------------------------------------------------------------
            f = open(fileName,'r')
            txt_consumos_dpe = f.readlines()
            f.close()
            ilinea=0
            reply = QtWidgets.QMessageBox.question(None, 'EnerGis', "El archivo tiene " + str(len(txt_consumos_dpe)) + " lineas. Desea importar ❓", QtWidgets.QMessageBox.StandardButton.Yes, QtWidgets.QMessageBox.StandardButton.No)
            if reply == QtWidgets.QMessageBox.StandardButton.No:
                return
            for linea in range (0, len(txt_consumos_dpe)):
                registro_energia = txt_consumos_dpe[linea].split(',')
                ilinea=ilinea+1
                if len(registro_energia)!=14:
                    QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ El archivo no es válido, contiene " + str(len(registro_energia)) + " campos en línea " + str(ilinea))
                    return
            for linea in range (0, len(txt_consumos_dpe)):
                #----------------------------------------------------------------------------
                # Actualiza el progreso
                progress.setValue(int(100*linea/len(txt_consumos_dpe)))
                if progress.wasCanceled():
                    break
                # Permitir que la GUI se actualice (similar a DoEvents)
                QtWidgets.QApplication.processEvents()
                #----------------------------------------------------------------------------
                registro_energia = txt_consumos_dpe[linea].split(',')
                str_campos = "Id_Usuario,Periodo,Tipo_Periodo,Tarifa,Contrato_Especial,E,Ep,EFp,Er,Ev,Pp,Pfp,Pcp,Pcfp"
                str_valores = ""
                for i in range (0, len(registro_energia)):
                    str_valor = registro_energia[i].strip()
                    str_valor = str_valor.replace("'", "")
                    str_valores = str_valores + "'" + str_valor + "',"
                #saco la última coma
                str_valores = str_valores[:-1]
                cursor = self.conn.cursor()
                try:
                    cursor.execute("SELECT * FROM Energias_DPE WHERE id_usuario='" + str(registro_energia[0]) + "' AND periodo='" + str(registro_energia[1]) + "'")
                    #convierto el cursor en array
                    usuario = tuple(cursor)
                    cursor.close()
                except:
                    QtWidgets.QMessageBox.critical(None, 'EnerGis 6', "❌ Error en " + "SELECT * FROM Energias_DPE WHERE id_usuario='" + str(registro_energia[0]) + "' AND periodo='" + str(registro_energia[1]) + "'")
                    return
                try:
                    if len(usuario)==1:
                        cursor = self.conn.cursor()
                        cursor.execute("DELETE FROM Energias_DPE WHERE id_usuario='" + str(registro_energia[0]) + "' AND periodo='" + str(registro_energia[1]) + "'")
                        #cursor.execute("DELETE FROM Energia_Facturada WHERE id_usuario='" + str(registro_energia[0]) + "' AND periodo='" + str(registro_energia[1])[:4] + "/" + str(registro_energia[1])[-2:] + "'")
                        a = a + 1
                    cursor = self.conn.cursor()
                    cursor.execute("INSERT INTO Energias_DPE (" + str_campos + ") VALUES (" + str_valores + ")")
                    #cursor.execute("INSERT INTO Energia_Facturada SELECT LEFT(Periodo,4)+'/'+RIGHT(Periodo,2) AS Periodo,CAST(LEFT(Periodo,4)+RIGHT(Periodo,2)+'01' AS date) AS Desde,CASE WHEN Tipo_Periodo='M' THEN DATEADD(d,-1,DATEADD(M,1,CAST(LEFT(Periodo,4)+RIGHT(Periodo,2)+'01' AS date))) ELSE DATEADD(d,-1,DATEADD(M,2,CAST(LEFT(Periodo,4)+RIGHT(Periodo,2)+'01' AS date))) END AS Hasta,Id_Usuario,E+Ep+Efp+Er+Ev AS EtF FROM Energias_DPE WHERE id_usuario='" + str(registro_energia[0]) + "' AND periodo='" + str(registro_energia[1]) + "'")
                    self.conn.commit()
                    n = n + 1
                except:
                    QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ Fallo al insertar en fila " + str(n+1))
                    self.conn.rollback()
                    return
            QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ Fin. " + str(n) + " registros nuevos, y " + str(a) + " registros actualizados")

    def listado_movimiento_transformadores(self):
        str_sql = "SELECT Movimiento_Transformadores.id_mov AS id_movimiento, Movimiento_Transformadores.Fecha AS fecha_movimiento, Ubicaciones.Descripcion AS ubicacion_desde, Ubicaciones_1.Descripcion AS ubicacion_hasta, Movimiento_Transformadores.observaciones, Transformadores.Id_Trafo AS id_trafo, Transformadores.Potencia AS potencia, Transformadores.Conexionado AS conexionado, Transformadores.Marca AS marca, Transformadores.N_Chapa AS nro_chapa, Transformadores.Anio_fabricacion AS año FROM Ct, ((Movimiento_Transformadores INNER JOIN Transformadores ON Movimiento_Transformadores.id_trafo = Transformadores.Id_Trafo) INNER JOIN Ubicaciones ON Movimiento_Transformadores.mov_desde = Ubicaciones.Id_Ubicacion) INNER JOIN Ubicaciones AS Ubicaciones_1 ON Movimiento_Transformadores.mov_hasta = Ubicaciones_1.Id_Ubicacion GROUP BY Movimiento_Transformadores.id_mov, Movimiento_Transformadores.Fecha, Ubicaciones.Descripcion, Ubicaciones_1.Descripcion, Movimiento_Transformadores.observaciones, Transformadores.Id_Trafo, Transformadores.Potencia, Transformadores.Conexionado, Transformadores.Marca, Transformadores.N_Chapa, Transformadores.Anio_fabricacion ORDER BY Movimiento_Transformadctores.Fecha"
        from .frm_listados import frmListados
        self.dialogo = frmListados(self.conn, str_sql)
        self.dialogo.setWindowTitle("Movimiento de Transformadores")
        self.dialogo.show()

    def listado_movimientos_trafo(self):
        id_trafo=''
        str_sql = "SELECT Movimiento_Transformadores.id_mov AS id_movimiento, Movimiento_Transformadores.Fecha AS fecha_movimiento, Ubicaciones.Descripcion AS ubicacion_desde, Ubicaciones_1.Descripcion AS ubicacion_hasta, Movimiento_Transformadores.observaciones, Transformadores.Id_Trafo AS id_trafo, Transformadores.Potencia AS potencia, Transformadores.Conexionado AS conexionado, Transformadores.Marca AS marca, Transformadores.N_Chapa AS nro_chapa, Transformadores.Anio_fabricacion AS año FROM Ct, ((Movimiento_Transformadores INNER JOIN Transformadores ON Movimiento_Transformadores.id_trafo = Transformadores.Id_Trafo) INNER JOIN Ubicaciones ON Movimiento_Transformadores.mov_desde = Ubicaciones.Id_Ubicacion) INNER JOIN Ubicaciones AS Ubicaciones_1 ON Movimiento_Transformadores.mov_hasta = Ubicaciones_1.Id_Ubicacion GROUP BY Movimiento_Transformadores.id_mov, Movimiento_Transformadores.Fecha, Ubicaciones.Descripcion, Ubicaciones_1.Descripcion, Movimiento_Transformadores.observaciones, Transformadores.Id_Trafo, Transformadores.Potencia, Transformadores.Conexionado, Transformadores.Marca, Transformadores.N_Chapa, Transformadores.Anio_fabricacion HAVING Transformadores.id_trafo=" + id_trafo + " ORDER BY Movimiento_Transformadores.Fecha"
        from .frm_listados import frmListados
        self.dialogo = frmListados(self.conn, str_sql)
        self.dialogo.setWindowTitle("Movimiento de Transformadores")
        self.dialogo.show()

    def listado_movimientos_ct(self):
        id_ct=''
        str_sql = "SELECT Movimiento_Transformadores.id_mov AS id_movimiento, Movimiento_Transformadores.Fecha AS fecha_movimiento, Ubicaciones.Descripcion AS ubicacion_desde, Ubicaciones_1.Descripcion AS ubicacion_hasta, Movimiento_Transformadores.observaciones, Transformadores.Id_Trafo AS id_trafo, Transformadores.Potencia AS potencia, Transformadores.Conexionado AS conexionado, Transformadores.Marca AS marca, Transformadores.N_Chapa AS nro_chapa, Transformadores.Anio_fabricacion AS año FROM Ct, ((Movimiento_Transformadores INNER JOIN Transformadores ON Movimiento_Transformadores.id_trafo = Transformadores.Id_Trafo) INNER JOIN Ubicaciones ON Movimiento_Transformadores.mov_desde = Ubicaciones.Id_Ubicacion) INNER JOIN Ubicaciones AS Ubicaciones_1 ON Movimiento_Transformadores.mov_hasta = Ubicaciones_1.Id_Ubicacion GROUP BY Movimiento_Transformadores.id_mov, Movimiento_Transformadores.Fecha, Ubicaciones.Descripcion, Ubicaciones_1.Descripcion, Movimiento_Transformadores.observaciones, Transformadores.Id_Trafo, Transformadores.Potencia, Transformadores.Conexionado, Transformadores.Marca, Transformadores.N_Chapa, Transformadores.Anio_fabricacion HAVING Movimiento_Transformadores.observaciones LIKE '%CT " + id_ct + "%' OR Movimiento_Transformadores.observaciones LIKE '%SET " + id_ct + "%' ORDER BY Movimiento_Transformadores.Fecha"
        from .frm_listados import frmListados
        self.dialogo = frmListados(self.conn, str_sql)
        self.dialogo.setWindowTitle("Movimientos")
        self.dialogo.show()

    def listado_usuarios(self):
        str_sql = "SELECT Usuarios.id_usuario, Medidores.nro_medidor, Usuarios.nombre, Usuarios.calle, Usuarios.altura, Usuarios.altura_ex, Usuarios.zona, Usuarios.subzona, Usuarios.id_suministro, Usuarios.tarifa, Usuarios.fase, Usuarios.ES AS En_Servicio, Usuarios.electrodependiente, Ct.Id_ct AS codigoct, Nodos_1.XCoord AS xct, Nodos_1.YCoord AS yct, Nodos_1.Nivel AS nivelct, Nodos_1.Tension AS tensionct, Nodos_1.Zona AS zonact, Nodos_1.Alimentador AS alimct, Ct.Ubicacion AS ubicct, Ct.Mat_plataf AS matct, Ct.Tipo_ct AS tipoct, Ct.Obs AS obsct FROM Medidores RIGHT OUTER JOIN Suministros LEFT OUTER JOIN Ct RIGHT OUTER JOIN Nodos AS Nodos_1 ON Ct.Id_ct = Nodos_1.Nombre RIGHT OUTER JOIN Suministros_Trafos ON Nodos_1.Geoname = Suministros_Trafos.Geoname_t ON Suministros.id_nodo = Suministros_Trafos.Geoname_s RIGHT OUTER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro ON Medidores.id_usuario = Usuarios.id_usuario"
        from .frm_listados import frmListados
        self.dialogo = frmListados(self.conn, str_sql)
        self.dialogo.setWindowTitle("Listado de Usuarios")
        self.dialogo.show()

    def listado_usuarios_red(self):
        str_sql = "SELECT Usuarios.id_usuario, Medidores.nro_medidor, Usuarios.nombre, Usuarios.calle, Usuarios.altura, Usuarios.altura_ex, Usuarios.zona, Usuarios.Subzona, Usuarios.id_suministro, Usuarios.tarifa, Usuarios.fase, Usuarios.ES AS En_Servicio, Usuarios.electrodependiente, Ct.Id_ct AS codigoct, Nodos_1.XCoord AS xct, Nodos_1.YCoord AS yct, Nodos_1.Nivel AS nivelct, Nodos_1.Tension AS tensionct, Nodos_1.Zona AS zonact, Nodos_1.Alimentador AS alimct, Ct.Ubicacion AS ubicct, Ct.Mat_plataf AS matct, Ct.Tipo_ct AS tipoct, Ct.Obs AS obsct FROM (Ct INNER JOIN Nodos AS Nodos_1 ON Ct.Id_ct = Nodos_1.Nombre) INNER JOIN ((Medidores RIGHT JOIN (Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) ON Medidores.id_usuario = Usuarios.id_usuario) INNER JOIN Suministros_Trafos ON Suministros.id_nodo = Suministros_Trafos.Geoname_s) ON Nodos_1.Geoname = Suministros_Trafos.Geoname_t"
        from .frm_listados import frmListados
        self.dialogo = frmListados(self.conn, str_sql)
        self.dialogo.setWindowTitle("Listado de Usuarios en la Red")
        self.dialogo.show()

    def h_login(self):
        import winreg
        nombre_usuario=''
        try:
            # Definir la ruta de la clave del registro que quieres leer
            ruta_clave = r"SOFTWARE\EnerGis"
            # Abrir la clave del registro en modo de solo lectura
            clave_registro = winreg.OpenKey(winreg.HKEY_CURRENT_USER, ruta_clave, 0, winreg.KEY_READ)
            # Leer el valor de una entrada en la clave del registro
            valor, tipo = winreg.QueryValueEx(clave_registro, "Usuario") #el tipo no lo usamos
            if valor!=None:
                nombre_usuario=valor
            # Cerrar la clave del registro
            winreg.CloseKey(clave_registro)
        except:
            pass

        seleccion_px = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_seleccion.png'))
        seleccion_px.setMask(seleccion_px.mask())
        seleccion_cursor = QtGui.QCursor(seleccion_px)
        self.iface.mapCanvas().setCursor(seleccion_cursor)

        from .frm_login import frmLogin
        dialogo = frmLogin(self.version, self.str_conexion_seguridad, nombre_usuario)
        dialogo.exec()
        nombre_usuario = dialogo.nombre_usuario
        self.id_usuario_sistema = dialogo.id_usuario_sistema
        self.tipo_usuario = dialogo.tipo_usuario

        self.iface.mainWindow().setWindowTitle('EnerGis (Versión: ' + self.version + ') - ' + self.nombre_modelo + ' - Usuario: ' + nombre_usuario)

        dialogo.close()
        if str(self.tipo_usuario)=='4':
            #deshabilito los botones
            self.toolbar_e.setEnabled(False)
            self.toolbar_p.setEnabled(False)
            for action in self.actions:
                if str(action.text())=='Verificar Red':
                    action.setEnabled(False)
                if str(action.text())=='Nodo':
                    action.setEnabled(False)
                if str(action.text())=='Linea':
                    action.setEnabled(False)
                if str(action.text())=='Poste':
                    action.setEnabled(False)
                if str(action.text())=='Girar':
                    action.setEnabled(False)
                if str(action.text())=='Mover':
                    action.setEnabled(False)
                if str(action.text())=='Rotar':
                    action.setEnabled(False)
                if str(action.text())=='Anotacion':
                    action.setEnabled(False)
                if str(action.text())=='Conectar':
                    action.setEnabled(False)
                if str(action.text())=='Area':
                    action.setEnabled(False)
                if str(action.text())=='Parcela':
                    action.setEnabled(False)
                if str(action.text())=='Borrar':
                    action.setEnabled(False)
                if str(action.text())=='Contingencias':
                    action.setEnabled(False)
                if str(action.text())=='Usuarios Nuevos':
                    action.setEnabled(False)
            self.tool_button.setEnabled(False)
            self.m_administrador.setEnabled(False)
            self.m_modelo.setEnabled(False)
            self.m_archivos.setEnabled(False)

    def actualizar_db(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM Configuracion")
        #convierto el cursor en array
        configuracion = tuple(cursor)
        cursor.close()
        for c in configuracion:
            if c[0]=='Version':
                version_instalada = c[1]
        versiones_nuevas = self.version.split('.')
        version_nueva1 = int(versiones_nuevas[0])
        version_nueva2 = int(versiones_nuevas[1])
        version_nueva3 = int(versiones_nuevas[2])
        versiones_instaladas = version_instalada.split('.')
        version_instalada1 = int(versiones_instaladas[0])
        version_instalada2 = int(versiones_instaladas[1])
        version_instalada3 = int(versiones_instaladas[2])
        if (version_nueva1<version_instalada1) or (version_nueva1==version_instalada1 and version_nueva2<version_instalada2) or (version_nueva1==version_instalada1 and version_nueva2==version_instalada2 and version_nueva3<version_instalada3) or (version_nueva1==version_instalada1 and version_nueva2==version_instalada2 and version_nueva3==version_instalada3):
            return
        conn = self.conn
        cursor = conn.cursor()
        #Esto se ejecuta siempre
        try:
            cursor.execute("UPDATE lineas SET Longitud=obj.STLength() WHERE Longitud < obj.STLength()")
            cursor.execute("UPDATE Transformadores SET usado=1 WHERE usado IS NULL AND id_ct=''")
            cursor.execute("UPDATE Transformadores SET usado=3 WHERE id_ct<>''")            
            cursor.execute("UPDATE Usuarios SET prosumidor='' WHERE prosumidor<>'' AND LEN(prosumidor)<20")
            cursor.execute("UPDATE Nodos SET Val1='Seccionador' WHERE elmt IN (2,3) AND (Val1='' OR Val1 IS NULL)")
            conn.commit()
        except:
            conn.rollback()
        #-------------------------------------------------------------------------------------------------
        #------------------------------------------ actualizar -------------------------------------------
        #-------------------------------------------------------------------------------------------------

        if version_instalada1<=6 and version_instalada2<=0 and version_instalada3<=0:
            try:
                cursor.execute("CREATE TABLE Nodos_Transformador (geoname int NOT NULL, Id int NOT NULL, CONSTRAINT [PK_Nodos_Transformador] PRIMARY KEY CLUSTERED ([geoname] ASC) ON [PRIMARY]) ON [PRIMARY]")
                conn.commit()
            except:
                conn.rollback()
        try:
            cursor.execute("UPDATE Configuracion SET Valor='" + self.version + "' WHERE Variable='Version'")
            conn.commit()
            QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ Se actualizó la DB a la versión " + self.version)
        except:
            conn.rollback()
        #-------------------------------------------------------------------------------------------------

    def resumen_sistema(self):
        from .frm_resumen_sistema import frmResumenSistema
        self.dialogo = frmResumenSistema(self.conn)
        self.dialogo.show()

    def crear_red(self):
        conn = self.conn
        cursor = conn.cursor()
        try:
            cursor.execute("crear_red")
            conn.commit()
        except:
            conn.rollback()
            QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo crear la Red !")

    def red_a_estado_normal(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute("UPDATE nodos SET estado=elmt WHERE (elmt=2 OR elmt=3) AND estado<>elmt")
            self.conn.commit()
        except:
            self.conn.rollback()
        self.crear_red
        QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ Red en Estado Normal")

    def establecer_estado_normal(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute("UPDATE nodos SET elmt=estado WHERE (elmt=2 OR elmt=3) AND estado<>elmt")
            self.conn.commit()
        except:
            self.conn.rollback()
        QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ Se estableció la Configuración de Red como Estado Normal")

    def ver_elementos_estado_anormal(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT 'Nodos' AS Elemento, 'El elemento no está en estado Normal' AS Dedcripcion, Geoname, Nombre FROM nodos WHERE elmt IN (2,3) AND elmt<>estado")
        #convierto el cursor en array
        elementos = tuple(cursor)
        encabezado = [column[0] for column in cursor.description]
        cursor.close()
        if len(elementos)==0:
            QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ Todos los Elementos de Maniobra están en Posición Normal")
            return
        from .frm_lista import frmLista
        self.dialogo = frmLista(self.iface.mapCanvas(), encabezado, elementos)
        self.dialogo.setWindowTitle('Resultados de la Verificación : ' + str(len(elementos)) + ' elementos')
        self.dialogo.show()

    def actualizar_zonas(self):
        #----------------------------------------------------------------------------
        progress = QtWidgets.QProgressDialog("Procesando...", "Cancelar", 0, 100)
        progress.setWindowTitle("Progreso")
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)  # Hace que la ventana de progreso sea modal
        progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
        progress.setValue(0)  # Inicia el progreso en 0
        QtWidgets.QApplication.processEvents()
        #----------------------------------------------------------------------------
        cursor = self.conn.cursor()
        try:
            cursor.execute("UPDATE A SET d1=o1, d2=o2, d3=o3 FROM (SELECT Areas.nombre AS o1, Areas.descripcion AS o2, Areas.Localidad AS o3, Nodos.Zona AS d1, Nodos.subzona AS d2, Nodos.localidad AS d3 FROM Nodos INNER JOIN Areas ON Areas.obj.STContains(Nodos.obj) = 1) A")
            self.conn.commit()
        except:
            self.conn.rollback()
        #----------------------------------------------------------------------------
        progress.setValue(50)
        QtWidgets.QApplication.processEvents()
        #----------------------------------------------------------------------------
        cursor = self.conn.cursor()
        try:
            cursor.execute("UPDATE A SET d=o FROM (SELECT Areas.nombre AS o, Lineas.Zona AS d FROM Lineas INNER JOIN Areas ON Areas.obj.STIntersects(Lineas.obj.STBuffer(0.001)) = 1) A")
            self.conn.commit()
        except:
            self.conn.rollback()
        #----------------------------------------------------------------------------
        progress.setValue(100)
        QtWidgets.QApplication.processEvents()
        #----------------------------------------------------------------------------
        QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ Zonas Asignadas")

    def actualizar_postes_lineas(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute("EXEC Normalizar_Postes")
            self.conn.commit()
        except:
            self.conn.rollback()

    def actualizar_alimentadores(self):
        import clr
        from System import Int64
        reply = QtWidgets.QMessageBox.question(None, 'EnerGis', "Desea actualizar alimentadores ❓", QtWidgets.QMessageBox.StandardButton.Yes, QtWidgets.QMessageBox.StandardButton.No)
        if reply == QtWidgets.QMessageBox.StandardButton.No:
            return
        if self.red_verificada==False:
            self.h_verificar_red()
        if self.red_verificada==False:
            return
        #----------------------------------------------------------------------------
        progress = QtWidgets.QProgressDialog("Procesando...", "Cancelar", 0, 100)
        progress.setWindowTitle("Progreso")
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)  # Hace que la ventana de progreso sea modal
        progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
        progress.setValue(0)  # Inicia el progreso en 0
        QtWidgets.QApplication.processEvents()
        #----------------------------------------------------------------------------
        cursor = self.conn.cursor()
        try:
            cursor.execute("UPDATE mLineas SET alim=0 WHERE alim IS NULL")
            self.conn.commit()
        except:
            self.conn.rollback()
        #----------------------------------------------------------------------------
        progress.setValue(10)
        QtWidgets.QApplication.processEvents()
        #----------------------------------------------------------------------------
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM Alimentadores WHERE Id_Alim NOT IN (SELECT Val1 FROM Nodos WHERE Nodos.Tension>0 AND elmt=8)")
            cursor.execute("INSERT INTO Alimentadores (Id, Id_Alim,Tension,Cd,SSEE,fc,fu,fp) SELECT DISTINCT Aux AS Id, LEFT(Val1, 15) AS Id_Alim, Tension, Descripcion as cd, Val4 as SSEE, 0 AS fc, 0 AS fu, 1 AS fp FROM Nodos WHERE Tension > 1000 AND Elmt = 8 AND (LEFT(Val1, 15) NOT IN (SELECT Id_Alim FROM Alimentadores))")
            cursor.execute("INSERT INTO Alimentadores (Id, Id_Alim,Tension,Cd,SSEE,fc,fu,fp) SELECT DISTINCT Nodos.Aux AS Id, LEFT(Nodos.Val1, 15) AS Id_Alim, Nodos.Tension, Nodos_2.Val4 AS cd, Nodos_2.Descripcion AS SSEE, 0 as fc, 0 as fu, 1 as fp FROM Nodos INNER JOIN Nodos_Transformador ON Nodos.Geoname = Nodos_Transformador.Geoname INNER JOIN Nodos AS Nodos_1 ON Nodos_Transformador.Id = Nodos_1.Geoname INNER JOIN Nodos AS Nodos_2 ON Nodos_1.Alimentador = Nodos_2.Val1 WHERE Nodos.Tension > 0 AND Nodos.Tension < 1000 AND Nodos.Elmt = 8 AND Nodos_2.Elmt = 8 AND LEFT(Nodos.Val1,15) NOT IN (SELECT Id_Alim FROM Alimentadores)")
            cursor.execute("INSERT INTO Alimentadores (Id, Id_Alim,Tension,Cd,SSEE,fc,fu,fp) SELECT DISTINCT Aux, LEFT(Val1,15) AS Id_Alim, Tension,'CD' AS Cd,'SSEE' AS SSEE, 0 AS fc, 0 AS fu, 1 AS fp FROM Nodos WHERE Nodos.Tension>0 AND elmt=8 AND LEFT(Val1,15) NOT IN (SELECT Id_Alim FROM Alimentadores)")
            cursor.execute("UPDATE Alimentadores SET SSEE='SSEE' WHERE SSEE IS NULL")
            cursor.execute("UPDATE Alimentadores SET cd='CD' WHERE cd IS NULL")
            cursor.commit()
        except:
            cursor.rollback()
            QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudieron actualizar Alimentadores !")
        #----------------------------------------------------------------------------
        progress.setValue(20)
        QtWidgets.QApplication.processEvents()
        #----------------------------------------------------------------------------
        cursor = self.conn.cursor()
        cursor.execute("SELECT aux, geoname FROM mNodos WHERE estado=1")
        fuentes = cursor.fetchall()
        cursor.close()
        #----------------------------------------------------------------------------
        # Cargar el ensamblado
        clr.AddReference(os.path.join(basepath, 'NavRed6.dll'))
        from EnerGis6.NavRed6 import NavRed
        #----------------------------------------------------------------------------
        progress.setValue(30)
        QtWidgets.QApplication.processEvents()
        #----------------------------------------------------------------------------
        # Instanciar la clase NavRed
        navred_instance = NavRed()
        for fuente in fuentes:
            #----------------------------------------------------------------------------
            progress.setValue(30 + int(50/len(fuentes)))
            QtWidgets.QApplication.processEvents()
            #----------------------------------------------------------------------------
            # Preparar los valores de entrada
            fuentenavegada = Int64(fuente[0])
            # Llamar a la función
            resultado = navred_instance.Navegar_a_los_extremos(self.amnodos,self.amlineas,fuentenavegada)
            if resultado[0]!="Ok":
                QtWidgets.QMessageBox.critical(None, 'EnerGis 6', "❌ " + resultado[0])
                return
        #----------------------------------------------------------------------------
        progress.setValue(80)
        QtWidgets.QApplication.processEvents()
        #----------------------------------------------------------------------------
        cursor = self.conn.cursor()
        cursor.execute("SELECT Id, Id_Alim,Tension FROM Alimentadores")
        alimentadores = cursor.fetchall()
        cursor.close()
        str_nodos="-1"
        alimentadores_nodos = [list(fila) for fila in alimentadores]
        for fila in alimentadores_nodos:
            fila.append('-1')
        for n in range(self.amnodos.GetLength(0)):
            #----------------------------------------------------------------------------
            progress.setValue(80 + int(5/self.amnodos.GetLength(0)))
            if progress.wasCanceled():
                return
            QtWidgets.QApplication.processEvents()
            #----------------------------------------------------------------------------
            if self.amnodos.GetValue(n,46)==0:
                str_nodos=str_nodos + "," + str(self.amnodos.GetValue(n,1))
            elif self.amnodos.GetValue(n,40) != self.amnodos.GetValue(n,46):
                #en la posicion a de alimentadores pongo el nodo
                for i in range(len(alimentadores_nodos)):
                    if alimentadores_nodos[i][0] == self.amnodos.GetValue(n,46):
                        alimentadores_nodos[i][3] = alimentadores_nodos[i][3] + ',' + str(self.amnodos.GetValue(n,1))
                        break
        str_lineas="-1"
        alimentadores_lineas = [list(fila) for fila in alimentadores]
        for fila in alimentadores_lineas:
            fila.append('-1')
        for l in range(self.amlineas.GetLength(0)):
            #----------------------------------------------------------------------------
            progress.setValue(85 + int(5/self.amlineas.GetLength(0)))
            if progress.wasCanceled():
                return
            QtWidgets.QApplication.processEvents()
            #----------------------------------------------------------------------------
            if self.amlineas.GetValue(l,13)==0:
                str_lineas=str_lineas + "," + str(self.amlineas.GetValue(l,1))
            elif self.amlineas.GetValue(l,8) != self.amlineas.GetValue(l,13):
                #en la posicion a de alimentadores pongo el nodo
                for i in range(len(alimentadores_lineas)):
                    if alimentadores[i][0] == self.amlineas.GetValue(l,13):
                        alimentadores_lineas[i][3] = alimentadores_lineas[i][3] + ',' + str(self.amlineas.GetValue(l,1))
                        break
        #----------------------------------------------------------------------------
        progress.setValue(90)
        QtWidgets.QApplication.processEvents()
        #----------------------------------------------------------------------------
        for i in range(len(alimentadores_nodos)):
            id_alimentador=alimentadores_nodos[i][0]
            alimentador=alimentadores_nodos[i][1]
            tension=alimentadores_nodos[i][2]
            cursor = self.conn.cursor()
            try:
                cursor.execute("UPDATE mNodos SET alim=" + str(id_alimentador) + " WHERE tension=" + str(tension) + " AND geoname IN (" + alimentadores_nodos[i][3] + ")")
                cursor.execute("UPDATE Nodos SET Alimentador='" + alimentador + "' WHERE tension=" + str(tension) + " AND geoname IN (" + alimentadores_nodos[i][3] + ")")
                self.conn.commit()
            except:
                self.conn.rollback()
        for i in range(len(alimentadores_lineas)):
            id_alimentador=alimentadores_nodos[i][0]
            alimentador=alimentadores_nodos[i][1]
            tension=alimentadores_nodos[i][2]
            cursor = self.conn.cursor()
            try:
                cursor.execute("UPDATE mLineas SET alim=" + str(id_alimentador) + " WHERE tension=" + str(tension) + " AND geoname IN (" + alimentadores_lineas[i][3] + ")")
                cursor.execute("UPDATE Lineas SET Alimentador='" + alimentador + "' WHERE tension=" + str(tension) + " AND geoname IN (" + alimentadores_lineas[i][3] + ")")
                self.conn.commit()
            except:
                self.conn.rollback()
        cursor = self.conn.cursor()
        try:
            cursor.execute("UPDATE Nodos SET Alimentador='#NA' WHERE geoname IN (" + str_nodos + ")")
            cursor.execute("UPDATE Lineas SET Alimentador='#NA' WHERE geoname IN (" + str_lineas + ")")
            cursor.execute("UPDATE Nodos SET Alimentador='#NA' WHERE Alimentador IS NULL")
            cursor.execute("UPDATE Lineas SET Alimentador='#NA' WHERE Alimentador IS NULL")
            self.conn.commit()
        except:
            self.conn.rollback()
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:6] == 'Lineas':
                lyr.triggerRepaint()
        #----------------------------------------------------------------------------
        progress.setValue(100)
        QtWidgets.QApplication.processEvents()
        #----------------------------------------------------------------------------
        QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ Alimentadores Actualizados")

    def transformadores_almacen(self):
        from .frm_trafos_almacen import frmTrafosAlmacen
        self.dialogo = frmTrafosAlmacen(self.tipo_usuario, self.conn)
        self.dialogo.show()

    def centros_transformacion(self):
        from .frm_trafos_almacen import frmTrafosAlmacen
        self.dialogo = frmTrafosAlmacen(self.tipo_usuario, self.conn)
        self.dialogo.show()

    def importar_access(self):
        dialog = QtWidgets.QFileDialog()
        oFileName = dialog.getOpenFileName(None, "Archivo de EnerGis 4", "", "EnerGis files (*.uen)")
        database_path=oFileName[0]
        # Ruta a tu archivo de base de datos Access
        if not database_path:
            return
        reply = QtWidgets.QMessageBox.question(None, 'EnerGis', "Se borrarán todos los datos del modelo actual, desea continuar ❓", QtWidgets.QMessageBox.StandardButton.Yes, QtWidgets.QMessageBox.StandardButton.No)
        if reply == QtWidgets.QMessageBox.StandardButton.No:
            return
        from .mod_importacion import importar_access
        importar_access(self, self.conn, database_path)

    def res_811(self):
        from .mod_exportacion import exportar_811
        exportar_811(self, self.conn, self.srid)

    def exportar_usuarios_oceba(self):
        from .mod_exportacion import exportar_usuarios
        exportar_usuarios(self, self.conn, self.srid)

    def cts_oceba(self):
        from .mod_exportacion import exportar_cts
        exportar_cts(self, self.conn, self.srid)

    def cadena1(self):
        if self.red_verificada==False:
            self.h_verificar_red()
        if self.red_verificada==False:
            return
        from .mod_exportacion import exportar_cadena1
        exportar_cadena1(self, self.conn, self.tipo_navegacion)

    def cadena2(self):
        if self.red_verificada==False:
            self.h_verificar_red()
        if self.red_verificada==False:
            return
        from .mod_exportacion import exportar_cadena2
        exportar_cadena2(self, self.conn, self.tipo_navegacion)

    def exportar_qfield(self):
        if os.path.isdir('c:/gis/energis6/QField/')==False:
            os.mkdir('c:/gis/energis6/QField/')
        #project = QgsProject.instance()
        #project.write("c:/gis/energis6/QField/" + self.nombre_modelo + ".gpkg")
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            #lyr.crs()
            if lyr.name()[:5] == 'Nodos' and lyr.name()!='Nodos Proyectos':
                filtro_original = lyr.subsetString()
                new_filter = filtro_original + ' and "estado"!=\'0\' and "estado"!=\'6\''
                lyr.setSubsetString(new_filter)
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis6/QField/" + lyr.name() + ".gpkg", "utf-8", QgsCoordinateReferenceSystem(4326), "GPKG")
                lyr.setSubsetString(filtro_original)
                #Creo la capa Suministros
                duplicate_layer = QgsVectorLayer(lyr.source(), lyr.name().replace("Nodos","Suministros"), lyr.providerType())
                # Obtener los parámetros del proveedor de datos
                provider_params = duplicate_layer.dataProvider().dataSourceUri()
                provider_params = provider_params.replace('mapNodos','mapSuministros')
                duplicate_layer.setDataSource(provider_params, duplicate_layer.name(), "mssql")
                provider_params = duplicate_layer.dataProvider().dataSourceUri()
                #QgsProject.instance().addMapLayer(duplicate_layer)
                QgsVectorFileWriter.writeAsVectorFormat(duplicate_layer, "c:/gis/energis6/QField/" + duplicate_layer.name() + ".gpkg", "utf-8", QgsCoordinateReferenceSystem(4326), "GPKG")
                #QgsProject.instance().removeMapLayer(duplicate_layer.id())
            if lyr.name()[:6] == 'Lineas' and lyr.name()!='Lineas Proyectos':
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis6/QField/" + lyr.name() + ".gpkg", "utf-8", QgsCoordinateReferenceSystem(4326), "GPKG")
            if lyr.name()[:6] == 'Postes' and lyr.name()!='Postes Proyectos':
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis6/QField/" + lyr.name() + ".gpkg", "utf-8", QgsCoordinateReferenceSystem(4326), "GPKG")
        QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ Exportado")

    def exportar_mapinfo(self):
        if os.path.isdir('c:/gis/energis6/MapInfo/')==False:
            os.mkdir('c:/gis/energis6/MapInfo/')

        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos' and lyr.name()!='Nodos Proyectos':
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis6/MapInfo/" + lyr.name() + ".tab", "utf-8", QgsCoordinateReferenceSystem(4326), "MapInfo File")
            if lyr.name()[:6] == 'Lineas' and lyr.name()!='Lineas Proyectos':
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis6/MapInfo/" + lyr.name() + ".tab", "utf-8", QgsCoordinateReferenceSystem(4326), "MapInfo File")
            if lyr.name()[:6] == 'Postes' and lyr.name()!='Postes Proyectos':
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis6/MapInfo/" + lyr.name() + ".tab", "utf-8", QgsCoordinateReferenceSystem(4326), "MapInfo File")
        QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ Exportado")

    def exportar_esri(self):
        if os.path.isdir('c:/gis/energis6/ESRI/')==False:
            os.mkdir('c:/gis/energis6/ESRI/')
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos' and lyr.name()!='Nodos Proyectos':
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis6/ESRI/" + lyr.name() + ".shp", "utf-8", QgsCoordinateReferenceSystem(4326), "ESRI Shapefile")
            if lyr.name()[:6] == 'Lineas' and lyr.name()!='Lineas Proyectos':
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis6/ESRI/" + lyr.name() + ".shp", "utf-8", QgsCoordinateReferenceSystem(4326), "ESRI Shapefile")
            if lyr.name()[:6] == 'Postes' and lyr.name()!='Postes Proyectos':
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis6/ESRI/" + lyr.name() + ".shp", "utf-8", QgsCoordinateReferenceSystem(4326), "ESRI Shapefile")
        QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ Exportado")

    def exportar_kml(self):
        str_nodos = '0'
        str_lineas = '0'
        str_postes = '0'
        ftrs_nodos=[]
        ftrs_lineas=[]
        ftrs_postes=[]
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos' and lyr.name() != 'Nodos_Proyecto':
                for ftr in lyr.selectedFeatures():
                    ftrs_nodos.append(ftr)
                    str_nodos = str_nodos + ',' + str(ftr.id())
            if lyr.name()[:6] == 'Lineas' and lyr.name() != 'Lineas_Proyecto':
                for ftr in lyr.selectedFeatures():
                    ftrs_lineas.append(ftr)
                    str_lineas = str_lineas + ',' + str(ftr.id())
            if lyr.name()[:6] == 'Postes' and lyr.name() != 'Postes_Proyecto':
                for ftr in lyr.selectedFeatures():
                    ftrs_postes.append(ftr)
                    str_postes = str_postes + ',' + str(ftr.id())
        from .frm_exportar_kml import frmExportarKml
        self.dialogo = frmExportarKml(self.conn, self.srid, str_nodos, str_lineas, str_postes, ftrs_nodos, ftrs_lineas, ftrs_postes)
        self.dialogo.show()

    def exportar_demitec(self):
        from .mod_exportacion import exportar_demitec
        exportar_demitec(self, self.conn, self.srid, self.nombre_modelo)

    def exportar_dpe(self):
        if self.red_verificada==False:
            self.h_verificar_red()
        if self.red_verificada==False:
            return
        from .mod_exportacion import exportar_gis_dpe
        exportar_gis_dpe(self, self.conn, self.srid)

    def exportar_google(self):
        from .mod_exportacion import exportar_google
        exportar_google(self, self.mapCanvas, self.conn, self.srid, self.nombre_modelo)

    def exportar_txt(self):
        from .mod_exportacion import exportar_txt
        exportar_txt(self, self.mapCanvas, self.conn, self.srid, self.nombre_modelo)

    def exportar_tab(self):
        if os.path.isdir('c:/gis/energis6/MapInfo/')==False:
            os.mkdir('c:/gis/energis6/MapInfo/')
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                #QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis6/MapInfo/" + self.nombre_modelo.lower() + lyr.name().replace('Nodos ','_no_') + ".tab", "", lyr.crs(), "MapInfo File", symbologyExport=QgsVectorFileWriter.FeatureSymbology)
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis6/MapInfo/" + self.nombre_modelo + ' ' + lyr.name() + ".tab", "", lyr.crs(), "MapInfo File")
            if lyr.name()[:6] == 'Lineas':
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis6/MapInfo/" + self.nombre_modelo + ' ' + lyr.name() + ".tab", "", lyr.crs(), "MapInfo File")
            if lyr.name()[:6] == 'Postes':
                QgsVectorFileWriter.writeAsVectorFormat(lyr, "c:/gis/energis6/MapInfo/" + self.nombre_modelo + ' ' + lyr.name() + ".tab", "", lyr.crs(), "MapInfo File")
        QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ Exportado")

    def h_verificar_red(self):
        if self.tipo_navegacion==0:
            from .mod_navegacion_ant import nodos_por_salida
            from .mod_navegacion_ant import nodos_por_transformador
        else:
            import clr
            from System import Int64
        self.conectar_db()
        self.red_verificada=False
        #----------------------------------------------------------------------------
        progress = QtWidgets.QProgressDialog("Procesando...", "Cancelar", 0, 100)
        progress.setWindowTitle("Progreso")
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)  # Hace que la ventana de progreso sea modal
        progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
        progress.setValue(0)  # Inicia el progreso en 0
        QtWidgets.QApplication.processEvents()
        #----------------------------------------------------------------------------
        cursor = self.conn.cursor()
        try:
            cursor.execute("UPDATE A SET d1=o1, d2=o2 FROM (SELECT Nodos.Val1 AS d1, CTs.potencia AS o1, Nodos.Val2 AS d2, CTs.conexionado AS o2 FROM Nodos INNER JOIN (SELECT Ct.Id_ct, SUM(Transformadores.Potencia) AS potencia, MIN(Transformadores.Conexionado) AS conexionado FROM Ct INNER JOIN Transformadores ON Ct.Id_ct = Transformadores.Id_ct GROUP BY Ct.Id_ct) AS CTs ON Nodos.Nombre = CTs.Id_ct WHERE (Nodos.Elmt = 4))A WHERE d1<>o1 OR d2=o2")
            self.conn.commit()
        except:
            self.conn.rollback()
        #Verificar Red
        str_sql= "SELECT DISTINCT 'Lineas' AS Elemento,'lineas con iguales nodo desde/hasta' AS Problema,Max(A.Geoname) AS Geoname,'Linea' AS Nombre FROM (SELECT Geoname,Desde,Hasta FROM Lineas WHERE Lineas.Tension>0 UNION SELECT Geoname,Hasta,Desde FROM Lineas WHERE Lineas.Tension>0) AS A GROUP BY A.Desde, A.Hasta HAVING Count(A.Geoname)>1"
        str_sql= str_sql + " UNION SELECT 'Lineas' AS Elemento,'lineas con longitud menor a cero' AS Problema,Geoname,'Linea' AS Nombre FROM Lineas WHERE Lineas.Tension>0 AND Lineas.Tension>0 AND Longitud<=0"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'seccionadores sin nombre' AS Problema,Geoname, Nombre FROM Nodos WHERE Nodos.Tension>0 AND (Elmt = 2 OR Elmt = 3) AND ((Nombre) Is null OR Nombre = '')"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'seccionadores con nombre repetido' AS Problema, MIN(Geoname) AS Geoname, Nombre FROM Nodos WHERE Nodos.Tension>0 AND Nodos.Tension>0 AND (Elmt = 2 OR Elmt = 3) GROUP BY Nombre HAVING Count(Nodos.Nombre)>1"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'CTs con nombre repetido' AS Problema, MIN(Geoname) AS Geoname, Nombre FROM Nodos WHERE Nodos.Tension>0 AND Elmt = 4 GROUP BY Nombre HAVING Count(Nodos.Geoname)>1"
        #str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'salida de alimentador con nombre repetido' AS Problema, MIN(Geoname) AS Geoname, Val1 FROM Nodos WHERE Nodos.Tension>0 AND Nodos.Tension>0 AND Elmt = 8 GROUP BY Val1 HAVING Count(Nodos.Geoname)>1"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'salidas de alimentador sin código de alimentador' AS Problema,Geoname, Nombre FROM Nodos WHERE Nodos.Tension>0 AND Elmt = 8 AND ((Val1) Is null OR Val1 = '')"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'fuentes con errores de tensión' AS Problema,Geoname, Nombre FROM Nodos WHERE Nodos.Tension>0 AND Elmt = 1 AND Val1 IS NULL"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'fuentes con mas de una línea' AS Problema,Nodos.Geoname, Nodos.Nombre FROM mNodos INNER JOIN Nodos ON mNodos.Geoname=Nodos.Geoname WHERE Nodos.Tension>0 AND Nodos.estado=1 AND cant_lineas>1"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'seccionadores con mas de dos líneas' AS Problema,Nodos.Geoname, Nodos.Nombre FROM mNodos INNER JOIN Nodos ON mNodos.Geoname=Nodos.Geoname WHERE Nodos.Tension>0 AND (Nodos.estado=2 OR Nodos.estado=3) AND cant_lineas>2"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'CTs con mas de dos líneas' AS Problema,Nodos.Geoname, Nodos.Nombre as Nombre FROM mNodos INNER JOIN Nodos ON mNodos.Geoname=Nodos.Geoname WHERE Nodos.Tension>0 AND Nodos.estado=4 AND cant_lineas>2"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'CTs con usuarios y sin máquina' AS Problema,Nodos.Geoname, Nodos.Nombre FROM (Nodos INNER JOIN ((Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) INNER JOIN Suministros_Trafos ON Suministros.id_nodo = Suministros_Trafos.Geoname_s) ON Nodos.Geoname = Suministros_Trafos.Geoname_t) LEFT JOIN Transformadores ON Nodos.Nombre = Transformadores.Id_ct WHERE Nodos.Tension>0 AND Nodos.elmt = 4 AND Usuarios.[ES] = 1 AND Transformadores.Id_trafo IS NULL GROUP BY Nodos.Geoname, Nodos.Nombre HAVING Count(Usuarios.id_usuario)>0"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'transformadores con error de fases' AS Problema,nodos.Geoname, nodos.Nombre FROM Transformadores INNER JOIN Nodos ON Transformadores.Id_ct = Nodos.Nombre INNER JOIN mNodos ON Nodos.Geoname = mNodos.Geoname WHERE ((mNodos.fases IN (1,2,3) AND Transformadores.Conexionado <> 'M') OR (mNodos.fases IN ('12','23','13') AND Transformadores.Conexionado NOT IN ('M','B'))) AND Nodos.Elmt=4 GROUP BY nodos.Geoname, nodos.Nombre"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'usuarios con error de fases' AS Problema,nodos.Geoname, nodos.Nombre FROM Nodos INNER JOIN (Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) ON Nodos.Geoname = Suministros.id_nodo WHERE Nodos.Tension>0 AND Usuarios.fase='123' GROUP BY nodos.Geoname, nodos.Nombre HAVING MIN(fase) IN ('1','2','3','12','23','13')"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'nodos con inconsistencias de tarifas' AS Problema,A.Geoname, A.Nombre FROM (SELECT Nodos.Geoname, Nodos.Nombre, Tarifas.Nivel_Tension FROM (Usuarios INNER JOIN Tarifas ON Usuarios.tarifa = Tarifas.Tarifa) INNER JOIN (Nodos INNER JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo) ON Usuarios.id_suministro = Suministros.id_suministro GROUP BY Nodos.Geoname, Nodos.Nombre, Tarifas.Nivel_Tension) AS A GROUP BY A.Geoname, A.Nombre HAVING Count(A.Nivel_Tension)>1"
        str_sql= str_sql + " UNION SELECT DISTINCT 'Nodos' AS Elemento,'nodos con inconsistencias de tarifas' AS Problema,Nodos.Geoname, Usuarios.tarifa AS Nombre FROM (Usuarios INNER JOIN Tarifas ON Usuarios.tarifa = Tarifas.Tarifa) INNER JOIN (Nodos INNER JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo) ON Usuarios.id_suministro = Suministros.id_suministro WHERE (((Nodos.Tension)>1000) AND ((Tarifas.Nivel_Tension)='BT')) OR (((Nodos.Tension)<1000) AND ((Tarifas.Nivel_Tension)='MT'))"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'usuarios con tarifas erroneas' AS Problema,Nodos.Geoname, CAST(Usuarios.id_usuario AS varchar) + '->'+ Usuarios.Tarifa AS Nombre FROM Nodos INNER JOIN (Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) ON Nodos.Geoname = Suministros.id_nodo WHERE Nodos.Tension>0 AND (((Usuarios.[ES])=1) AND ((Usuarios.tarifa) IS NULL)) OR (((Usuarios.tarifa) Not In (SELECT tarifa FROM tarifas)))"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'alimentadores sin nombre' AS Problema,nodos.Geoname, nodos.Nombre FROM Nodos WHERE Nodos.Tension>0 AND Elmt = 8 AND (Val1='' OR Val1 IS NULL)"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'cambios de tension sin trafos' AS Problema,nodos.Geoname, nodos.Nombre FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Hasta WHERE (Nodos.Tension>0 AND Nodos.Elmt<>4 AND Lineas.Tension<>0 AND Lineas.Tension<>Nodos.Tension) OR (Nodos.Tension>0 AND Nodos.Elmt=5 AND Lineas.Tension>0)"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'cambios de tension sin trafos' AS Problema,nodos.Geoname, nodos.Nombre FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Desde WHERE (Nodos.Tension>0 AND Nodos.Elmt<>4 AND Lineas.Tension<>0 AND Lineas.Tension<>Nodos.Tension) OR (Nodos.Tension>0 AND Nodos.Elmt=5 AND Lineas.Tension>0)"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'nodos con inconsistencia de fases' AS Problema,nodos.geoname, Nodos.Nombre FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Hasta INNER JOIN mNodos ON Nodos.Geoname = mNodos.geoname WHERE Nodos.Tension>0 AND (LEN(mNodos.fases)<>LEN(Lineas.Fase) AND mNodos.fases<>Lineas.Fase AND mNodos.fases<>123 AND Lineas.Fase<>123) AND (LEN(mNodos.fases)=2 AND CHARINDEX(Lineas.Fase, mNodos.fases, 0)=0 OR LEN(Lineas.Fase)=2 AND CHARINDEX(CONVERT(VARCHAR,mNodos.Fases), Lineas.fase, 0)=0)"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'nodos con inconsistencia de fases' AS Problema,nodos.geoname, Nodos.Nombre FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Hasta INNER JOIN mNodos ON Nodos.Geoname = mNodos.geoname WHERE Nodos.Tension>0 AND (LEN(mNodos.fases)<>LEN(Lineas.Fase) AND mNodos.fases<>Lineas.Fase AND mNodos.fases<>123 AND Lineas.Fase<>123) AND (LEN(mNodos.fases)=2 AND CHARINDEX(Lineas.Fase, mNodos.fases, 0)=0 OR LEN(Lineas.Fase)=2 AND CHARINDEX(CONVERT(VARCHAR,mNodos.Fases), Lineas.fase, 0)=0)"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'seccionadores sin tipo' AS Problema, Nodos.geoname, Nodos.Nombre FROM Nodos WHERE Tension>0 AND (elmt=2 OR elmt=3) AND (Val1='' OR Val1 IS NULL)"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'seccionadores con varias fases' AS Problema, A.geoname, A.Nombre  FROM (SELECT Nodos.Geoname, Nodos.Nombre, Lineas.Fase FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Desde WHERE Nodos.elmt IN (2,3) UNION SELECT Nodos.Geoname, Nodos.Nombre, Lineas.Fase FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Hasta WHERE Nodos.elmt IN (2,3)) AS A GROUP BY A.Geoname, A.Nombre HAVING (((Count(A.Fase))>1))"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'transformadores con error de tensión' AS Problema, Nodos.geoname, Nodos.Nombre FROM Transformadores INNER JOIN Nodos ON Transformadores.Id_ct = Nodos.Nombre WHERE (((Transformadores.[Tension_1]) Not In (132000,66000,33000,19000,13200,7620,6600,400,231)) AND ((Nodos.Elmt)=4)) OR (((Transformadores.[Tension_2]) Not In (132000,66000,33000,19000,13200,7620,6600,400,231)) AND ((Nodos.Elmt)=4))"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'transformadores con error de conexionado' AS Problema, Nodos.geoname, Nodos.Nombre FROM Nodos INNER JOIN Transformadores ON Nodos.Nombre = Transformadores.Id_ct WHERE (Transformadores.Conexionado IN ('Yy0', 'Yd5', 'Yd11', 'Dy5', 'Dy11')) AND (Transformadores.Tipo <> 3) AND (Nodos.Elmt = 4) AND (Nodos.Tension > 0) OR (Transformadores.Conexionado = 'B') AND (Transformadores.Tipo <> 2) AND (Nodos.Elmt = 4) AND (Nodos.Tension > 0) OR (Transformadores.Conexionado = 'M') AND (Transformadores.Tipo <> 1) AND (Nodos.Elmt = 4) AND (Nodos.Tension > 0)"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'transformadores con error de fases' AS Problema, Nodos.geoname, Nodos.Nombre FROM (SELECT ct.id_ct, count(id) as cant FROM ct inner join transformadores on ct.id_ct=transformadores.id_ct group by ct.id_ct)  AS C INNER JOIN (((SELECT Nodos.Geoname, Lineas.Fase FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Desde WHERE Nodos.elmt=4 UNION SELECT Nodos.Geoname, Lineas.Fase FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Hasta WHERE Nodos.elmt =4)  AS A INNER JOIN Nodos ON A.Geoname = Nodos.Geoname) INNER JOIN Transformadores ON Nodos.Nombre = Transformadores.Id_ct) ON C.id_ct = Transformadores.Id_ct WHERE (((A.Fase)<>'123') AND ((Transformadores.Tipo)=3)) OR (((A.Fase)='123') AND ((Transformadores.Tipo)=2)) OR (((A.Fase) Not In ('1','2','3')) AND ((Transformadores.Tipo)=1) AND ((C.cant)=1))"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'fecha de alta de ct faltante' AS Problema, Nodos.geoname, Nodos.Nombre FROM Nodos INNER JOIN Ct ON Nodos.Nombre=Ct.id_ct WHERE elmt=4 AND Fecha_Alta IS NULL"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'estado de ct inconsistente' AS Problema, Nodos.geoname, Nodos.Nombre FROM Nodos INNER JOIN Ct ON Nodos.Nombre=Ct.id_ct WHERE elmt=4 AND Conservacion IS NULL"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'cts sin salidas' AS Problema, Nodos.geoname, Nodos.Nombre FROM Suministros_Trafos INNER JOIN (Nodos INNER JOIN Ct ON Nodos.Nombre = Ct.id_ct) ON Suministros_Trafos.Geoname_t = Nodos.Geoname WHERE (((Nodos.[elmt])=4) AND (([casis]+[casies]+[cases]+[casees])=0))"
        str_sql= str_sql + " UNION SELECT 'Lineas' AS Elemento,'estados de lineas' AS Problema, Lineas.geoname, '' AS Nombre FROM Lineas WHERE Tension>0 AND Conservacion IS NULL"
        str_sql= str_sql + " UNION SELECT 'Lineas' AS Elemento,'longitud de lineas' AS Problema, Lineas.geoname, '' AS Nombre FROM Lineas WHERE Tension>0 AND Longitud=0 OR Longitud IS NULL"
        str_sql= str_sql + " UNION SELECT 'Lineas' AS Elemento,'linea sin unidad constructiva' AS Problema, Lineas.geoname, '' AS Nombre FROM Lineas WHERE Tension>0 AND (UUCC IS NULL OR UUCC='' OR UUCC='SD')"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'nodo sin unidad constructiva' AS Problema, Nodos.geoname, Nodos.Nombre FROM Nodos WHERE Tension>0 AND elmt IN (2, 3, 4, 7, 9) AND (UUCC IS NULL OR UUCC='' OR UUCC='SD')"
        str_sql= str_sql + " UNION SELECT 'Nodos' AS Elemento,'usuario prosumidor sin datos' AS Problema, Suministros.id_nodo AS geoname, Usuarios.nombre FROM Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro WHERE LEN(Prosumidor)<21 AND LEN(Prosumidor)>1"
        cursor = self.conn.cursor()
        cursor.execute(str_sql)
        elementos = tuple(cursor)
        encabezado = [column[0] for column in cursor.description]
        cursor.close()
        if len(elementos)!=0:
            from .frm_lista import frmLista
            self.dialogo = frmLista(self.iface.mapCanvas(), encabezado, elementos)
            self.dialogo.setWindowTitle('Resultados Verificación : ' + str(len(elementos)) + ' errores')
            self.dialogo.show()
            return
        #----------------------------------------------------------------------------
        progress.setValue(20)
        QtWidgets.QApplication.processEvents()
        #----------------------------------------------------------------------------
        self.descargo_red()
        #----------------------------------------------------------------------------
        progress.setValue(30)
        QtWidgets.QApplication.processEvents()
        #----------------------------------------------------------------------------
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM Alimentadores WHERE Id_Alim NOT IN (SELECT Val1 FROM Nodos WHERE Nodos.Tension>0 AND elmt=8)")
            cursor.execute("INSERT INTO Alimentadores (Id, Id_Alim,Tension,Cd,SSEE) SELECT DISTINCT Aux, LEFT(Val1,15) AS Id_Alim, Tension,'0' AS Cd,'0' AS SSEE FROM Nodos WHERE Nodos.Tension>0 AND elmt=8 AND LEFT(Val1,15) NOT IN (SELECT Id_Alim FROM Alimentadores)")
            cursor.execute("UPDATE Alimentadores SET ssee='0' WHERE ssee IS NULL")
            cursor.execute("UPDATE Alimentadores SET cd='0' WHERE cd IS NULL")
            cursor.commit()
        except:
            cursor.rollback()
            QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudieron crear Alimentadores !")
        #----------------------------------------------------------------------------
        progress.setValue(40)
        QtWidgets.QApplication.processEvents()
        #----------------------------------------------------------------------------
        if self.tipo_navegacion==0:
            nodos_por_transformador(self, self.conn)
            nodos_por_salida(self, self.conn)
            self.red_verificada=True
        else:
            cursor = self.conn.cursor()
            cursor.execute("SELECT aux, geoname FROM mNodos WHERE estado=1")
            fuentes = cursor.fetchall()
            cursor.close()
            #----------------------------------------------------------------------------
            # Cargar el ensamblado
            clr.AddReference(os.path.join(basepath, 'NavRed6.dll'))
            from EnerGis6.NavRed6 import NavRed

            # Instanciar la clase NavRed
            navred_instance = NavRed()
            for fuente in fuentes:
                #----------------------------------------------------------------------------
                progress.setValue(40 + int(59/len(fuentes)))
                QtWidgets.QApplication.processEvents()
                if progress.wasCanceled():
                    return
                #----------------------------------------------------------------------------
                # Preparar los valores de entrada
                fuentenavegada = Int64(fuente[0])
                # Llamar a la función
                resultado = navred_instance.Navegar_compilar_red(self.monodos,self.amnodos,self.amlineas,fuentenavegada)
                if resultado[0]!="Ok":
                    QtWidgets.QMessageBox.critical(None, 'EnerGis 6', "❌ " + resultado[0])
                    #----------------------------------------------------------------------------
                    progress.setValue(100)
                    #----------------------------------------------------------------------------
                    return
            self.red_verificada=True
            trafos_nodos=['-1']*self.amnodos.GetLength(0)
            trafos_lineas=['-1']*self.amlineas.GetLength(0)
            trafos_suministros=['-1']*self.amnodos.GetLength(0)
            for n in range(self.amnodos.GetLength(0)):
                if self.amnodos.GetValue(n,44)!=0:
                    trafos_nodos[self.amnodos.GetValue(n,44)]=trafos_nodos[self.amnodos.GetValue(n,44)] + ',' + str(self.amnodos.GetValue(n,1))
                    if self.amnodos.GetValue(n,2)==6:
                        trafos_suministros[self.amnodos.GetValue(n,44)]=trafos_suministros[self.amnodos.GetValue(n,44)] + ',' + str(self.amnodos.GetValue(n,1))
            for n in range(self.amlineas.GetLength(0)):
                if self.amlineas.GetValue(n,11)!=0:
                    try:
                        trafos_lineas[self.amlineas.GetValue(n,11)]=trafos_lineas[self.amlineas.GetValue(n,11)] + ',' + str(self.amlineas.GetValue(n,1))
                    except:
                        pass
            try:
                cursor = self.conn.cursor()
                cursor.execute("TRUNCATE TABLE Suministros_Trafos")
                cursor.execute("TRUNCATE TABLE Nodos_Transformador")
                cursor.execute("TRUNCATE TABLE Lineas_Transformador")
                self.conn.commit()
            except:
                QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pueden borrar las tablas de elementos de Trafos")
                self.conn.rollback()
            cursor = self.conn.cursor()
            cursor.fast_executemany = True
            datos_s = []
            for t in range(len(trafos_suministros)):
                # Separamos por coma y limpiamos espacios
                ids_separados = trafos_suministros[t].split(',')
                for id_individual in ids_separados:
                    # Filtramos los '-1' o valores vacíos
                    if id_individual != '-1' and id_individual != '':
                        try:
                            # Ahora sí, convertimos cada uno a entero
                            val_s = int(id_individual)
                            val_t = int(self.amnodos.GetValue(t, 1))
                            datos_s.append((val_s, val_t))
                        except:
                            pass
            datos_n = []
            for t in range(len(trafos_nodos)):
                # Separamos por coma y limpiamos espacios
                ids_separados = trafos_nodos[t].split(',')
                for id_individual in ids_separados:
                    # Filtramos los '-1' o valores vacíos
                    if id_individual != '-1' and id_individual != '':
                        try:
                            # Ahora sí, convertimos cada uno a entero
                            val_n = int(id_individual)
                            val_id = int(self.amnodos.GetValue(t, 1))
                            datos_n.append((val_n, val_id))
                        except:
                            pass
            datos_l = []
            for t in range(len(trafos_lineas)):
                # Separamos por coma y limpiamos espacios
                ids_separados = trafos_lineas[t].split(',')
                for id_individual in ids_separados:
                    # Filtramos los '-1' o valores vacíos
                    if id_individual != '-1' and id_individual != '':
                        try:
                            # Ahora sí, convertimos cada uno a entero
                            val_l = int(id_individual)
                            val_id = int(self.amnodos.GetValue(t, 1))
                            datos_l.append((val_l, val_id))
                        except:
                            pass
            #Definición de tareas para iterar y no repetir código
            tareas = [
                ("INSERT INTO Suministros_Trafos (geoname_s, geoname_t) VALUES (?, ?)", datos_s, "Suministros"),
                ("INSERT INTO Nodos_Transformador (geoname, id) VALUES (?, ?)", datos_n, "Nodos"),
                ("INSERT INTO Lineas_Transformador (geoname, id) VALUES (?, ?)", datos_l, "Lineas")
            ]
            # Ejecución controlada
            for query, datos, nombre in tareas:
                if datos: # Solo ejecutamos si hay datos
                    try:
                        cursor.executemany(query, datos)
                        self.conn.commit()
                    except Exception as e:
                        self.conn.rollback()
                        QtWidgets.QMessageBox.critical(None, 'EnerGis 6', "❌ " + f"Error cargando {nombre}: {str(e)}")

            """for n in range(len(trafos_suministros)):
                if trafos_suministros[n]!='-1':
                    try:
                        cursor = self.conn.cursor()
                        cursor.execute("INSERT INTO Suministros_Trafos SELECT geoname, " + str(self.amnodos.GetValue(n,1)) + " FROM Nodos WHERE Tension>0 AND geoname IN (" + str(trafos_suministros[n]) + ")")
                        self.conn.commit()
                    except:
                        QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se puede insertar en la tabla Suministros_Trafos")
                        self.conn.rollback()
            for n in range(len(trafos_nodos)):
                if trafos_nodos[n]!='-1':
                    try:
                        cursor = self.conn.cursor()
                        cursor.execute("INSERT INTO Nodos_Transformador SELECT geoname, " + str(self.amnodos.GetValue(n,1)) + " FROM Nodos WHERE Tension>0 AND geoname IN (" + str(trafos_nodos[n]) + ")")
                        self.conn.commit()
                    except:
                        QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se puede insertar en la tabla Nodos_Transformador")
                        self.conn.rollback()
            for n in range(len(trafos_lineas)):
                if trafos_lineas[n]!='-1':
                    try:
                        cursor = self.conn.cursor()
                        cursor.execute("INSERT INTO Lineas_Transformador SELECT geoname, " + str(self.amlineas.GetValue(n,1)) + " FROM Lineas WHERE Tension>0 AND geoname IN (" + str(trafos_lineas[n]) + ")")
                        self.conn.commit()
                    except:
                        QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se puede insertar en la tabla Lineas_Transformador")
                        self.conn.rollback()
            """

        #----------------------------------------------------------------------------
        progress.setValue(100)
        #----------------------------------------------------------------------------
        QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ Red Verificada !")

    def descargo_red(self):
        if self.conn==None:
            return
        if self.tipo_navegacion==0:
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
        else:
            import clr
            clr.AddReference("mscorlib")
            clr.AddReference("System")
            from System import Int64, Array
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM mNodos ORDER BY Aux")
            #convierto el cursor en array
            self.mnodos = tuple(cursor)
            cursor.close()
            listanodos = [list(nodo) for nodo in self.mnodos]
            jnodos = json.dumps(listanodos)
            with open(os.path.join(tempfile.gettempdir(), "jnodos"), "w") as a:
                a.write(jnodos)
            #----------------------------------------------------------------------------
            cursor = self.conn.cursor()
            try:
                cursor.execute("UPDATE mLineas SET alim=0 WHERE alim IS NULL")
                self.conn.commit()
            except:
                self.conn.rollback()
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM mLineas ORDER BY Aux")
            #convierto el cursor en array
            self.mlineas = tuple(cursor)
            cursor.close()
            listalineas = [list(linea) for linea in self.mlineas]
            jlineas = json.dumps(listalineas)
            with open(os.path.join(tempfile.gettempdir(), "jlineas"), "w") as a:
                a.write(jlineas)
            #----------------------------------------------------------------------------
            # Crear arreglos
            self.monodos = Array.CreateInstance(Int64, len(self.mnodos))
            if len(self.mnodos)>0:
                self.amnodos = Array.CreateInstance(Int64, len(self.mnodos), len(self.mnodos[0]))
            else:
                self.amnodos = Array.CreateInstance(Int64, 0, 44)
            if len(self.mlineas)>0:
                self.amlineas = Array.CreateInstance(Int64, len(self.mlineas), len(self.mlineas[0]))
            else:
                self.amlineas = Array.CreateInstance(Int64, 0, 12)
            # Copiar valores a mnodos
            for i in range(len(self.mnodos)):
                for j in range(len(self.mnodos[0])):
                    self.amnodos[i, j] = self.mnodos[i][j]
            # Copiar valores a mlineas
            for i in range(len(self.mlineas)):
                for j in range(len(self.mlineas[0])):
                    self.amlineas[i, j] = self.mlineas[i][j]

    def h_elementos_seleccionados(self):
        from .frm_seleccion import frmSeleccion
        self.dialogo = frmSeleccion(self.iface.mapCanvas())
        self.dialogo.show()

    def h_navegar_a_la_fuente(self):
        ftrs = []
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                for ftr in lyr.selectedFeatures():
                    ftrs.append(ftr)
        if len(ftrs) != 1:
            QtWidgets.QMessageBox.critical(None, 'EnerGis 6', "❌ Debe seleccionar un nodo")
            return
        id = ftrs[0].id()
        if self.tipo_navegacion==0:
            from .herr_navegar_fuente_ant import herrNavegarFuente
            herrNavegarFuente(self.iface.mapCanvas(), self.conn, id)
        else:
            self.descargo_red()
            from .herr_navegar_fuente import herrNavegarFuente
            herrNavegarFuente(self.iface.mapCanvas(), id, self.amnodos, self.amlineas)

    def h_navegar_extremos(self):
        ftrs = []
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                #QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ " + str(lyr.name()))
                for ftr in lyr.selectedFeatures():
                    #QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ " + str(ftr.id()))
                    ftrs.append(ftr)
        if len(ftrs) != 1:
            QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ Debe seleccionar un nodo")
            return
        id=ftrs[0].id()
        if self.tipo_navegacion==0:
            from .herr_navegar_extremos_ant import herrNavegarExtremos
            herrNavegarExtremos(self.iface.mapCanvas(), self.conn, id)
        else:
            self.descargo_red()
            from .herr_navegar_extremos import herrNavegarExtremos
            herrNavegarExtremos(self.iface.mapCanvas(), id, self.amnodos, self.amlineas)

    def h_desconectados(self):
        if self.tipo_navegacion==0:
            from .herr_desconectados import herrDesconectados
            herrDesconectados(self.iface.mapCanvas(), self.conn)
        else:
            self.descargo_red()
            import clr
            from System import Int64
            #----------------------------------------------------------------------------
            progress = QtWidgets.QProgressDialog("Procesando...", "Cancelar", 0, 100)
            progress.setWindowTitle("Progreso")
            progress.setWindowModality(Qt.WindowModality.ApplicationModal)  # Hace que la ventana de progreso sea modal
            progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
            progress.setValue(0)  # Inicia el progreso en 0
            #----------------------------------------------------------------------------
            progress.setValue(10)
            QtWidgets.QApplication.processEvents()
            #----------------------------------------------------------------------------
            cursor = self.conn.cursor()
            cursor.execute("SELECT aux, geoname FROM mNodos WHERE estado=1")
            fuentes = cursor.fetchall()
            cursor.close()
            #----------------------------------------------------------------------------
            # Cargar el ensamblado
            clr.AddReference(os.path.join(basepath, 'NavRed6.dll'))
            from EnerGis6.NavRed6 import NavRed
            #----------------------------------------------------------------------------
            progress.setValue(55)
            QtWidgets.QApplication.processEvents()
            #----------------------------------------------------------------------------
            # Instanciar la clase NavRed
            navred_instance = NavRed()
            for fuente in fuentes:
                #----------------------------------------------------------------------------
                progress.setValue(10 + int(80/len(fuentes)))
                if progress.wasCanceled():
                    return
                QtWidgets.QApplication.processEvents()
                #----------------------------------------------------------------------------
                # Preparar los valores de entrada
                fuentenavegada = Int64(fuente[0])
                # Llamar a la función
                resultado = navred_instance.Navegar_compilar_red(self.monodos,self.amnodos,self.amlineas,fuentenavegada)
                if resultado[0]!="Ok":
                    QtWidgets.QMessageBox.critical(None, 'EnerGis 6', "❌ " + resultado[0])
                    #----------------------------------------------------------------------------
                    progress.setValue(100)
                    #----------------------------------------------------------------------------
                    return
            #----------------------------------------------------------------------------
            progress.setValue(90)
            QtWidgets.QApplication.processEvents()
            #----------------------------------------------------------------------------
            self.seleccion_n = [[]]
            self.seleccion_l = [[]]
            n = self.iface.mapCanvas().layerCount()
            layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
            for lyr in layers:
                if lyr.type() == QgsMapLayerType.VectorLayer:
                    lyr.removeSelection()
            for n in range(self.amnodos.GetLength(0)):
                if self.amnodos.GetValue(n,3) == 0 and self.amnodos.GetValue(n,1) != 0:
                    self.seleccion_n.append([self.amnodos.GetValue(n,1),self.amnodos.GetValue(n,38),self.amnodos.GetValue(n,2)])
            for l in range(self.amlineas.GetLength(0)):
                if self.amlineas.GetValue(l,4) == 0 and self.amlineas.GetValue(l,1) != 0:
                    self.seleccion_l.append([self.amlineas.GetValue(l,1),self.amlineas.GetValue(l,5),self.amlineas.GetValue(l,6)])
            #----------------------------------------------------------------------------
            progress.setValue(100)
            QtWidgets.QApplication.processEvents()
            #----------------------------------------------------------------------------
            from .frm_elementos_navegados import frmElementosNavegados
            self.dialogo = frmElementosNavegados(self.mapCanvas, self.seleccion_n, self.seleccion_l)
            self.dialogo.show()

    def h_aislados(self):
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.type() == QgsMapLayerType.VectorLayer:
                lyr.removeSelection()
        self.descargo_red()
        self.seleccion_n = []
        for n in range (0, len(self.mnodos)):
            if self.mnodos[n][1]!=0 and self.mnodos[n][4] == 0:
                self.seleccion_n.append(self.mnodos[n][1])
        str_mensaje = 'No hay Nodos Aislados'
        if len(self.seleccion_n)!=0:
            str_mensaje = str(len(self.seleccion_n)) + ' Aislados'
        QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ " + str_mensaje)

        if len(self.seleccion_n)==0:
            return
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyr.select(self.seleccion_n)
        self.h_elementos_seleccionados()

    def h_loops(self):
        if self.tipo_navegacion==0:
            from .mod_navegacion_ant import buscar_loops
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
            n = self.iface.mapCanvas().layerCount()
            layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
            for lyr in layers:
                if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                    lyr.removeSelection()
            #--------------------------------------------
            buscar_loops(self, self.mnodos, self.mlineas)
            #--------------------------------------------
        else:
            from .mod_navegacion import buscar_loops
            n = self.iface.mapCanvas().layerCount()
            layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
            for lyr in layers:
                if lyr.type() == QgsMapLayerType.VectorLayer:
                    lyr.removeSelection()
            #--------------------------------------------
            buscar_loops(self, self.mnodos, self.mlineas)
            #--------------------------------------------
        self.seleccion_n = []
        for n in range(0, len(self.mnodos)):
            if self.mnodos[n][45] == 1:
                self.seleccion_n.append(self.mnodos[n][1])
        self.seleccion_l = []
        for n in range (0, len(self.mlineas)):
            if self.mlineas[n][12] == 1:
                self.seleccion_l.append(self.mlineas[n][1])
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setText('Análisis de la Red')
        msg.setInformativeText('Búsqueda de Loops')
        msg.setWindowTitle('EnerGis 6')
        msg.setDetailedText(str(len(self.seleccion_l)) + ' lineas marcadas')
        msg.exec()
        if len(self.seleccion_l)==0:
            return
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyr.select(self.seleccion_n)
            if lyr.name()[:6] == 'Lineas':
                lyr.select(self.seleccion_l)
        self.h_elementos_seleccionados()

    def h_buscar(self):
        from .frm_buscar import frmBuscar
        self.dialogo = frmBuscar(self.iface.mapCanvas(), self.conn)
        self.dialogo.show()

    def h_buscar_direccion(self):
        from .frm_buscar_direccion import frmBuscarDireccion
        self.dialogo = frmBuscarDireccion(self.iface.mapCanvas(), self.conn)
        self.dialogo.show()

    def h_usuarios_nuevos(self):
        self.dock_widget2.setVisible(True)
        self.actualizar_grilla_usuarios()

    def h_electrodependientes(self):
        b_estado=False
        for action in self.actions:
            if str(action.text())=='Usuarios Electrodependientes':
                b_estado = action.isChecked()
        b_existe = False
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyrCRS = lyr.crs().authid()
            if lyr.name() == 'Electrodependientes':
                b_existe = True
                self.electrodependientes = lyr
                if not self.electrodependientes.isEditable():
                    self.electrodependientes.startEditing()
                    for f in lyr.getFeatures():
                        lyr.deleteFeature(f.id())
                    self.electrodependientes.commitChanges()
        if b_estado==True:
            if b_existe == False:
                electrodependientes=[]
                try:
                    cursor = self.conn.cursor()
                    cursor.execute("SELECT Usuarios.id_usuario, Usuarios.Nombre, Usuarios.Calle, Usuarios.Altura, Nodos.XCoord, Nodos.YCoord FROM Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE Usuarios.electrodependiente='S'")
                    #convierto el cursor en array
                    electrodependientes = tuple(cursor)
                    cursor.close()
                except:
                    pass
                self.electrodependientes = QgsVectorLayer("Point?crs=" + lyrCRS, "Electrodependientes", "memory")
                self.electrodependientes.renderer().symbol().setOpacity(1)
                self.electrodependientes.renderer().symbol().symbolLayer(0).setShape(QgsSimpleMarkerSymbolLayerBase.CrossFill)
                self.electrodependientes.renderer().symbol().symbolLayer(0).setSize(4)
                self.electrodependientes.renderer().symbol().symbolLayer(0).setColor(QtGui.QColor("red"))
                prov = self.electrodependientes.dataProvider()
                fields = QgsFields()
                fields.append(QgsField("id_usuario", QVariant.String))
                fields.append(QgsField("nombre", QVariant.String))
                fields.append(QgsField("calle", QVariant.String))
                fields.append(QgsField("altura", QVariant.String))
                prov.addAttributes(fields)
                self.electrodependientes.updateFields()
                features = []
                for eld in electrodependientes:
                    pt =  QgsPoint(eld[4], eld[5])
                    ftr = QgsFeature()
                    ftr.setFields(fields)
                    ftr.setGeometry(pt)
                    ftr.setAttributes([eld[0], eld[1], eld[2], eld[3]])
                    features.append(ftr)
                prov.addFeatures(features)
                self.electrodependientes.updateExtents()
                QgsProject.instance().addMapLayer(self.electrodependientes, False)
                # Obtener el nodo raíz del árbol de capas
                root = QgsProject.instance().layerTreeRoot()
                nodo = QgsLayerTreeLayer(self.electrodependientes)
                nodo.setItemVisibilityChecked(True)
                root.insertChildNode(0, nodo)
                self.electrodependientes.triggerRepaint()
        else:
            try:
                QgsProject.instance().removeMapLayer(self.electrodependientes.id())
            except:
                pass

    def h_reclamos(self):
        b_estado=False
        for action in self.actions:
            if str(action.text())=='Reclamos':
                b_estado = action.isChecked()
        b_existe = False
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyrCRS = lyr.crs().authid()
            if lyr.name() == 'Reclamos':
                b_existe = True
                self.reclamos = lyr
                if not self.reclamos.isEditable():
                    self.reclamos.startEditing()
                    for f in lyr.getFeatures():
                        lyr.deleteFeature(f.id())
                    self.reclamos.commitChanges()
        if b_estado==True:
            if b_existe == False:
                from .frm_elegir_fechas import frmElegirFechas
                dialogo = frmElegirFechas()
                dialogo.exec()
                self.fecha_desde = dialogo.fecha_desde
                self.fecha_hasta = dialogo.fecha_hasta
                dialogo.close()
                str_sql=''
                if self.fecha_desde!=None:
                    str_sql = str_sql + " AND fecha>='" + str(self.fecha_desde)[:19].replace('-','') + "'"
                if self.fecha_hasta!=None:
                    str_sql = str_sql + " AND fecha<='" + str(self.fecha_hasta)[:19].replace('-','') + "'"
                reclamos=[]
                try:
                    cursor = self.conn.cursor()
                    cursor.execute("SELECT TOP 2000 id AS Reclamo, CAST(fecha AS DATE) AS Fecha, id_usuario, Usuarios.Nombre, Direccion, XCoord, YCoord FROM Usuarios INNER JOIN VW_GISRECLAMOS ON Usuarios.id_usuario = VW_GISRECLAMOS.usuario INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro INNER JOIN Nodos ON Suministros.id_nodo = Nodos.Geoname WHERE XCoord>0 AND YCoord>0" + str_sql )
                    #convierto el cursor en array
                    reclamos = tuple(cursor)
                    cursor.close()
                except:
                    pass
                self.reclamos = QgsVectorLayer("Point?crs=" + lyrCRS, "Reclamos", "memory")
                self.reclamos.renderer().symbol().setOpacity(1)
                self.reclamos.renderer().symbol().symbolLayer(0).setShape(QgsSimpleMarkerSymbolLayerBase.Star)
                self.reclamos.renderer().symbol().symbolLayer(0).setSize(4)
                self.reclamos.renderer().symbol().symbolLayer(0).setColor(QtGui.QColor("red"))
                prov = self.reclamos.dataProvider()
                fields = QgsFields()
                fields.append(QgsField("id_reclamo", QVariant.Int))
                fields.append(QgsField("fecha", QVariant.Date))
                fields.append(QgsField("id_usuario", QVariant.String))
                fields.append(QgsField("nombre", QVariant.String))
                fields.append(QgsField("direccion", QVariant.String))
                prov.addAttributes(fields)
                self.reclamos.updateFields()
                features = []
                for reclamo in reclamos:
                    pt =  QgsPoint(reclamo[5], reclamo[6])
                    ftr = QgsFeature()
                    ftr.setFields(fields)
                    ftr.setGeometry(pt)
                    ftr.setAttributes([reclamo[0], reclamo[1], reclamo[2], reclamo[3], reclamo[4]])
                    features.append(ftr)
                prov.addFeatures(features)
                self.reclamos.updateExtents()
                QgsProject.instance().addMapLayer(self.reclamos, False)
                # Obtener el nodo raíz del árbol de capas
                root = QgsProject.instance().layerTreeRoot()
                nodo = QgsLayerTreeLayer(self.reclamos)
                nodo.setItemVisibilityChecked(True)
                root.insertChildNode(0, nodo)
                self.reclamos.triggerRepaint()
        else:
            try:
                QgsProject.instance().removeMapLayer(self.reclamos.id())
            except:
                pass

    def h_datos_seleccion(self):
        from .frm_datos_seleccion import frmDatosSeleccion
        self.dialogo = frmDatosSeleccion(self.id_usuario_sistema, self.tipo_usuario, self.iface.mapCanvas(), self.conn)
        self.dialogo.show()

    def h_seleccion(self):
        self.conectar_db()
        if self.tipo_navegacion==0:
            from .herr_seleccion_ant import herrSeleccion
            tool = herrSeleccion(self.proyecto, self.tipo_usuario, self.iface.mapCanvas(), self.iface, self.conn, self.mnodos, self.mlineas, self.tension, self.red_verificada)
        else:
            from .herr_seleccion import herrSeleccion
            tool = herrSeleccion(self.proyecto, self.id_usuario_sistema, self.tipo_usuario, self.iface.mapCanvas(), self.iface, self.conn, self.amnodos, self.amlineas, self.monodos, self.tension, self.red_verificada)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        seleccion_px = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_seleccion.png'))
        seleccion_px.setMask(seleccion_px.mask())
        seleccion_cursor = QtGui.QCursor(seleccion_px)
        self.iface.mapCanvas().setCursor(seleccion_cursor)

    def h_seleccionar_ejes(self):
        from .herr_seleccion_ejes import herrSeleccionEjes
        tool = herrSeleccionEjes(self.tipo_usuario, self.iface.mapCanvas(), self.iface, self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        seleccion_px = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_seleccion_ejes.png'))
        seleccion_px.setMask(seleccion_px.mask())
        seleccion_cursor = QtGui.QCursor(seleccion_px)
        self.iface.mapCanvas().setCursor(seleccion_cursor)

    def h_seleccion_aleatoria(self):
        from .herr_seleccion_aleatoria import herrSeleccionAleatoria
        tool = herrSeleccionAleatoria(self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        seleccion_px = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_seleccion_aleatoria.png'))
        seleccion_px.setMask(seleccion_px.mask())
        seleccion_cursor = QtGui.QCursor(seleccion_px)
        self.iface.mapCanvas().setCursor(seleccion_cursor)

    def h_seleccion_circular(self):
        from .herr_seleccion_circular import herrSeleccionCircular
        tool = herrSeleccionCircular(self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        seleccion_px = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_seleccion_circular.png'))
        seleccion_px.setMask(seleccion_px.mask())
        seleccion_cursor = QtGui.QCursor(seleccion_px)
        self.iface.mapCanvas().setCursor(seleccion_cursor)

    def h_seleccionar_elementos(self):
        from .frm_seleccionar_elementos import frmSeleccionarElementos
        self.dialogo = frmSeleccionarElementos(self.iface.mapCanvas(), self.conn)
        self.dialogo.setWindowFlags(self.dialogo.windowFlags() & Qt.WindowType.CustomizeWindowHint)
        self.dialogo.setWindowFlags(self.dialogo.windowFlags() & ~Qt.WindowType.WindowMinMaxButtonsHint)
        self.dialogo.show()

    def h_nodo(self):
        from .herr_nodo import herrNodo
        self.tension = self.cmbTension.currentText()
        tool = herrNodo(self.proyecto, self.tipo_usuario, self.iface.mapCanvas(), self.conn, self.tension)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punNodo = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_nodo.png'))
        punNodo.setMask(punNodo.mask())
        curNodo = QtGui.QCursor(punNodo)
        self.iface.mapCanvas().setCursor(curNodo)

    def h_anotacion(self):
        from .herr_anotacion import herrAnotacion
        tool = herrAnotacion(self.proyecto, self.tipo_usuario, self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punNodo = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_nodo.png'))
        punNodo.setMask(punNodo.mask())
        curNodo = QtGui.QCursor(punNodo)
        self.iface.mapCanvas().setCursor(curNodo)

    def h_girar(self):
        self.ftrs_nodos = []
        self.ftrs_postes = []
        self.angulo = 0
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                for ftr in lyr.selectedFeatures():
                    self.ftrs_nodos.append(ftr.id())
            if lyr.name()[:6] == 'Postes':
                for ftr in lyr.selectedFeatures():
                    self.ftrs_postes.append(ftr.id())
        if len(self.ftrs_nodos) > 0 or len(self.ftrs_postes) > 0:
            from .frm_girar import frmGirar
            self.dialogo = frmGirar(self.mapCanvas, self.conn, self.ftrs_nodos, self.ftrs_postes)
            self.dialogo.setWindowFlags(self.dialogo.windowFlags() & Qt.WindowType.CustomizeWindowHint)
            self.dialogo.setWindowFlags(self.dialogo.windowFlags() & ~Qt.WindowType.WindowMinMaxButtonsHint)
            self.dialogo.show()

    def h_linea(self):
        from .herr_linea import herrLinea
        self.tension = self.cmbTension.currentText()
        tool = herrLinea(self.proyecto, self.tipo_usuario, self.iface.mapCanvas(), self.conn, self.tension)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punLinea = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_linea.png'))
        punLinea.setMask(punLinea.mask())
        curLinea = QtGui.QCursor(punLinea)
        self.iface.mapCanvas().setCursor(curLinea)

    def h_eje(self):
        from .herr_eje import herrEje
        tool = herrEje(self.tipo_usuario, self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punEje = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_linea.png'))
        punEje.setMask(punEje.mask())
        curEje = QtGui.QCursor(punEje)
        self.iface.mapCanvas().setCursor(curEje)

    def h_agregar_vertice(self):
        from .herr_agregar_vertice import herrAgregarVertice
        tool = herrAgregarVertice(self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punNodo = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_nodo.png'))
        punNodo.setMask(punNodo.mask())
        curNodo = QtGui.QCursor(punNodo)
        self.iface.mapCanvas().setCursor(curNodo)

    def h_quitar_vertice(self):
        from .herr_quitar_vertice import herrQuitarVertice
        tool = herrQuitarVertice(self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punNodo = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_nodo.png'))
        punNodo.setMask(punNodo.mask())
        curNodo = QtGui.QCursor(punNodo)
        self.iface.mapCanvas().setCursor(curNodo)

    def h_poste(self):
        from .herr_poste import herrPoste
        self.tension = self.cmbTension.currentText()
        tool = herrPoste(self.proyecto, self.tipo_usuario, self.iface.mapCanvas(), self.conn, self.tension)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punPoste = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_nodo.png'))
        punPoste.setMask(punPoste.mask())
        curPoste = QtGui.QCursor(punPoste)
        self.iface.mapCanvas().setCursor(curPoste)

    def h_mover(self):
        from .herr_mover import herrMover
        tool = herrMover(self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punMover = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_mover.png'))
        punMover.setMask(punMover.mask())
        curMover = QtGui.QCursor(punMover)
        self.iface.mapCanvas().setCursor(curMover)

    def h_rotar(self):
        from .herr_rotar import herrRotar
        tool = herrRotar(self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punRotar = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_rotar.png'))
        punRotar.setMask(punRotar.mask())
        curRotar = QtGui.QCursor(punRotar)
        self.iface.mapCanvas().setCursor(curRotar)

    def h_mover_ejes(self):
        from .herr_mover_ejes import herrMoverEjes
        tool = herrMoverEjes(self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punMover = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_mover.png'))
        punMover.setMask(punMover.mask())
        curMover = QtGui.QCursor(punMover)
        self.iface.mapCanvas().setCursor(curMover)

    def h_rotar_ejes(self):
        from .herr_rotar_ejes import herrRotarEjes
        tool = herrRotarEjes(self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punRotar = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_rotar.png'))
        punRotar.setMask(punRotar.mask())
        curRotar = QtGui.QCursor(punRotar)
        self.iface.mapCanvas().setCursor(curRotar)

    def h_conectar(self):
        from .herr_conectar import herrConectar
        tool = herrConectar(self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punConectar = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_conectar.png'))
        punConectar.setMask(punConectar.mask())
        curConectar = QtGui.QCursor(punConectar)
        self.iface.mapCanvas().setCursor(curConectar)

    def h_area(self):
        from .herr_area import herrArea
        tool = herrArea(self.tipo_usuario, self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punLinea = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_linea.png'))
        punLinea.setMask(punLinea.mask())
        curLinea = QtGui.QCursor(punLinea)
        self.iface.mapCanvas().setCursor(curLinea)

    def h_parcela(self):
        from .herr_parcela import herrParcela
        tool = herrParcela(self.tipo_usuario, self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punLinea = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_linea.png'))
        punLinea.setMask(punLinea.mask())
        curLinea = QtGui.QCursor(punLinea)
        self.iface.mapCanvas().setCursor(curLinea)

    def h_borrar(self):
        if self.tipo_usuario==4:
            return
        ftrs_nodos = []
        ftrs_lineas = []
        ftrs_postes = []
        ftrs_areas = []
        ftrs_parcelas = []
        ftrs_anotaciones = []
        capas = []
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        str_nodos = '0'
        str_lineas = '0'
        str_postes = '0'
        str_areas = '0'
        str_parcelas = '0'
        str_anotaciones = '0'
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                for ftr in lyr.selectedFeatures():
                    ftrs_nodos.append(ftr.id())
                    str_nodos = str_nodos + ',' + str(ftr.id())
                    b_existe=False
                    for capa in capas:
                        if capa==lyr:
                            b_existe=True
                    if b_existe==False:
                        capas.append(lyr)
            if lyr.name()[:6] == 'Lineas':
                for ftr in lyr.selectedFeatures():
                    ftrs_lineas.append(ftr.id())
                    str_lineas = str_lineas + ',' + str(ftr.id())
                    b_existe=False
                    for capa in capas:
                        if capa==lyr:
                            b_existe=True
                    if b_existe==False:
                        capas.append(lyr)
            if lyr.name()[:6] == 'Postes':
                for ftr in lyr.selectedFeatures():
                    ftrs_postes.append(ftr.id())
                    str_postes = str_postes + ',' + str(ftr.id())
                    b_existe=False
                    for capa in capas:
                        if capa==lyr:
                            b_existe=True
                    if b_existe==False:
                        capas.append(lyr)
            if lyr.name() == 'Areas':
                for ftr in lyr.selectedFeatures():
                    ftrs_areas.append(ftr.id())
                    str_areas = str_areas + ',' + str(ftr.id())
                    b_existe=False
                    for capa in capas:
                        if capa==lyr:
                            b_existe=True
                    if b_existe==False:
                        capas.append(lyr)
            if lyr.name() == 'Parcelas':
                for ftr in lyr.selectedFeatures():
                    ftrs_parcelas.append(ftr.id())
                    str_parcelas = str_parcelas + ',' + str(ftr.id())
                    b_existe=False
                    for capa in capas:
                        if capa==lyr:
                            b_existe=True
                    if b_existe==False:
                        capas.append(lyr)
            if lyr.name() == 'Anotaciones':
                for ftr in lyr.selectedFeatures():
                    ftrs_parcelas.append(ftr.id())
                    str_anotaciones = str_anotaciones + ',' + str(ftr.id())
                    b_existe=False
                    for capa in capas:
                        if capa==lyr:
                            b_existe=True
                    if b_existe==False:
                        capas.append(lyr)
        if self.tipo_usuario!=4 and len(ftrs_nodos) + len(ftrs_lineas) + len(ftrs_postes) + len(ftrs_areas) + len(ftrs_parcelas) + len(ftrs_anotaciones) > 0:
            if len(capas)==1:
                reply = QtWidgets.QMessageBox.question(None, 'EnerGis', 'Desea borrar los elementos seleccionados ❓', QtWidgets.QMessageBox.StandardButton.Yes, QtWidgets.QMessageBox.StandardButton.No)
                if reply == QtWidgets.QMessageBox.StandardButton.No:
                    return
                layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
                for lyr in layers:
                    if lyr.name()[:6] == 'Lineas':
                        cursor = self.conn.cursor()
                        try:
                            cursor.execute("DELETE FROM Lineas WHERE Geoname IN (" + str_lineas + ")")
                            self.conn.commit()
                        except:
                            self.conn.rollback()
                            QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudieron borrar Lineas ! - (" + str_lineas + ")")
                        lyr.triggerRepaint()
                    elif lyr.name()[:5] == 'Nodos':
                        cursor = self.conn.cursor()
                        try:
                            cursor.execute("DELETE FROM Nodos WHERE Geoname IN (" + str_nodos + ")")
                            self.conn.commit()
                        except:
                            self.conn.rollback()
                            QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudieron borrar Nodos ! - (" + str_nodos + ")")
                        lyr.triggerRepaint()
                    elif lyr.name()[:6] == 'Postes':
                        cursor = self.conn.cursor()
                        try:
                            cursor.execute("DELETE FROM Postes WHERE Geoname IN (" + str_postes + ")")
                            self.conn.commit()
                        except:
                            self.conn.rollback()
                            QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudieron borrar Postes ! - (" + str_postes + ")")
                        lyr.triggerRepaint()
                    elif lyr.name() == 'Areas':
                        cursor = self.conn.cursor()
                        try:
                            cursor.execute("DELETE FROM Areas WHERE Geoname IN (" + str_areas + ")")
                            self.conn.commit()
                        except:
                            self.conn.rollback()
                            QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudieron borrar Areas !")
                        lyr.triggerRepaint()
                    elif lyr.name() == 'Parcelas':
                        cursor = self.conn.cursor()
                        try:
                            cursor.execute("DELETE FROM Parcelas WHERE Geoname IN (" + str_parcelas + ")")
                            self.conn.commit()
                        except:
                            self.conn.rollback()
                            QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudieron borrar Parcelas !")
                        lyr.triggerRepaint()
                    elif lyr.name() == 'Anotaciones':
                        cursor = self.conn.cursor()
                        try:
                            cursor.execute("DELETE FROM Anotaciones WHERE Geoname IN (" + str_anotaciones + ")")
                            self.conn.commit()
                        except:
                            self.conn.rollback()
                            QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudieron borrar Anotaciones !")
                        lyr.triggerRepaint()
                    else:
                        #lyr.triggerRepaint()
                        pass
            else:
                from .frm_borrar import frmBorrar
                dialogo = frmBorrar(capas)
                dialogo.exec()
                capas=dialogo.capas
                dialogo.close()
                if len(capas)==0:
                    return
                layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
                for lyr in layers:
                    if lyr.name()[:6] == 'Lineas':
                        for capa in capas:
                            if capa==lyr.name():
                                str_tension = lyr.name() [7 - len(lyr.name()):]
                                if str_tension.strip() == 'Proyectos':
                                    str_tension='0'
                                cursor = self.conn.cursor()
                                try:
                                    cursor.execute("DELETE FROM Lineas WHERE Tension=" + str_tension + " AND Geoname IN (" + str_lineas + ")")
                                    self.conn.commit()
                                except:
                                    self.conn.rollback()
                                    QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudieron borrar Lineas !")
                                lyr.triggerRepaint()
                    elif lyr.name()[:5] == 'Nodos':
                        for capa in capas:
                            if capa==lyr.name():
                                str_tension = lyr.name() [6 - len(lyr.name()):]
                                if str_tension.strip() == 'Proyectos':
                                    str_tension='0'
                                cursor = self.conn.cursor()
                                try:
                                    cursor.execute("DELETE FROM Nodos WHERE Tension=" + str_tension + " AND Geoname IN (" + str_nodos + ")")
                                    self.conn.commit()
                                except:
                                    self.conn.rollback()
                                    QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudieron borrar Nodos !")
                                lyr.triggerRepaint()
                    elif lyr.name()[:6] == 'Postes':
                        for capa in capas:
                            if capa==lyr.name():
                                str_tension = lyr.name() [7 - len(lyr.name()):]
                                if str_tension.strip() == 'Proyectos':
                                    str_tension='0'
                                cursor = self.conn.cursor()
                                try:
                                    cursor.execute("DELETE FROM Postes WHERE Tension=" + str_tension + " AND Geoname IN (" + str_postes + ")")
                                    self.conn.commit()
                                except:
                                    self.conn.rollback()
                                    QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudieron borrar Postes !")
                                lyr.triggerRepaint()
                    elif lyr.name() == 'Areas':
                        for capa in capas:
                            if capa=='Areas':
                                cursor = self.conn.cursor()
                                try:
                                    cursor.execute("DELETE FROM Areas WHERE Geoname IN (" + str_areas + ")")
                                    self.conn.commit()
                                except:
                                    self.conn.rollback()
                                    QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudieron borrar Areas !")
                                lyr.triggerRepaint()
                    elif lyr.name() == 'Parcelas':
                        for capa in capas:
                            if capa=='Parcelas':
                                cursor = self.conn.cursor()
                                try:
                                    cursor.execute("DELETE FROM Parcelas WHERE Geoname IN (" + str_parcelas + ")")
                                    self.conn.commit()
                                except:
                                    self.conn.rollback()
                                    QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudieron borrar Parcelas !")
                                lyr.triggerRepaint()
                    elif lyr.name() == 'Anotaciones':
                        for capa in capas:
                            if capa=='Anotaciones':
                                cursor = self.conn.cursor()
                                try:
                                    cursor.execute("DELETE FROM Anotaciones WHERE Geoname IN (" + str_anotaciones + ")")
                                    self.conn.commit()
                                except:
                                    self.conn.rollback()
                                    QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudieron borrar Anotaciones !")
                                lyr.triggerRepaint()
                    else:
                        #lyr.triggerRepaint()
                        pass
            return

    def ejecutar_sql(self):
        from .frm_sql import frmSql
        self.dialogo = frmSql(self.iface.mapCanvas, self.conn)
        self.dialogo.show()

    def seguridad(self):
        from .frm_seguridad import frmSeguridad
        self.dialogo = frmSeguridad(self.str_conexion_seguridad)
        self.dialogo.show()

    def h_datos_eje(self):
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        ftrs_ejes = []
        for lyr in layers:
            if lyr.name() == 'Ejes de Calle':
                for ftr in lyr.selectedFeatures():
                    ftrs_ejes.append(ftr)
        if len(ftrs_ejes) > 0:
            from .frm_datos_ejes import frmDatosEjes
            self.dialogo = frmDatosEjes(self.tipo_usuario, self.conn, ftrs_ejes)
            self.dialogo.show()

    def h_borrar_ejes(self):
        ftrs_ejes = []
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        str_ejes = '0'
        for lyr in layers:
            if lyr.name() == 'Ejes de Calle':
                for ftr in lyr.selectedFeatures():
                    ftrs_ejes.append(ftr.id())
                    str_ejes = str_ejes + ',' + str(ftr.id())
        if len(ftrs_ejes) > 0:
            reply = QtWidgets.QMessageBox.question(None, 'EnerGis', 'Desea borrar los ejes seleccionados ❓', QtWidgets.QMessageBox.StandardButton.Yes, QtWidgets.QMessageBox.StandardButton.No)
            if reply == QtWidgets.QMessageBox.StandardButton.No:
                return
            layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
            for lyr in layers:
                if lyr.name() == 'Ejes de Calle':
                    cursor = self.conn.cursor()
                    try:
                        cursor.execute("DELETE FROM Ejes WHERE Geoname IN (" + str_ejes + ")")
                        self.conn.commit()
                    except:
                        self.conn.rollback()
                        QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudieron borrar Ejes !")
                    lyr.triggerRepaint()

    def h_zoom(self):
        from .herr_zoom import herrZoom
        tool = herrZoom(self.iface.mapCanvas(), 'Zoom')
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punZoom = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_zoom.png'))
        punZoom.setMask(punZoom.mask())
        curZoom = QtGui.QCursor(punZoom)
        self.iface.mapCanvas().setCursor(curZoom)

    def h_Pan(self):
        from .herr_zoom import herrZoom
        tool = herrZoom(self.iface.mapCanvas(), 'Pan')
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punZoom = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_pan.png'))
        punZoom.setMask(punZoom.mask())
        curZoom = QtGui.QCursor(punZoom)
        self.iface.mapCanvas().setCursor(curZoom)

    def h_crear_proyecto(self):
        text, ok = QtWidgets.QInputDialog.getText(None, 'Ingreso de Datos', 'Nombre del Proyecto:')
        if ok:
            nuevo_proyecto = str(text)
        else:
            return
        if nuevo_proyecto=='':
            return
        for i in range (0, self.cmbProyecto.count()):
            if self.cmbProyecto.itemText(i) == nuevo_proyecto:
                QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ Ya existe un proyecto con ese nombre")
                return
        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT INTO Proyectos (nombre, descripcion, fecha) VALUES ('" + nuevo_proyecto + "', '', GETDATE())")
            self.conn.commit()
        except:
            self.conn.rollback()
            QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo agregar el Proyecto !")
        QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ Proyecto Creado")
        self.cmbProyecto.addItem(nuevo_proyecto)
        self.cmbProyecto.setCurrentIndex(self.cmbProyecto.count() - 1)
        self.proyecto = ''

    def elijo_proyecto(self):
        if self.cmbProyecto.currentText()=='<Proyecto>':
            for action in self.actions:
                if str(action.text())=='Modificar Proyecto':
                    action.setEnabled(False)
        else:
            for action in self.actions:
                if str(action.text())=='Modificar Proyecto':
                    action.setEnabled(True)

    def h_borrar_proyecto(self):
        reply = QtWidgets.QMessageBox.question(None, 'EnerGis', 'Desea eliminar definitivamente el proyecto ❓', QtWidgets.QMessageBox.StandardButton.Yes, QtWidgets.QMessageBox.StandardButton.No)
        if reply == QtWidgets.QMessageBox.StandardButton.No:
            return
        self.borro_proyecto()

    def borro_proyecto(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM proyectos WHERE nombre='" + self.cmbProyecto.currentText() + "'")
            cursor.execute("DELETE FROM Nodos WHERE Tension=0 AND Alimentador='" + self.cmbProyecto.currentText() + "'")
            cursor.execute("DELETE FROM Lineas WHERE Tension=0 AND Alimentador='" + self.cmbProyecto.currentText() + "'")
            cursor.execute("DELETE FROM Postes WHERE Tension=0 AND Descripcion = '" + self.cmbProyecto.currentText() + "'")
            cursor.execute("DELETE FROM Anotaciones WHERE Proyecto = '" + self.cmbProyecto.currentText() + "'")
            self.conn.commit()
        except:
            self.conn.rollback()
        self.cmbProyecto.removeItem(self.cmbProyecto.currentIndex())
        QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ Proyecto Borrado !")
        self.proyecto = ''
        self.cmbProyecto.setCurrentIndex(0)
        for action in self.actions:
            if str(action.text())=='Modificar Proyecto':
                action.setChecked(True)
            if str(action.text())=='Nuevo Proyecto':
                action.setEnabled(True)
            if str(action.text())=='Incorporar Proyecto':
                action.setEnabled(False)
            if str(action.text())=='Borrar Proyecto':
                action.setEnabled(False)
            if str(action.text())=='Agregar Cota':
                action.setEnabled(False)
            if str(action.text())=='Borrar última Cota':
                action.setEnabled(False)
            if str(action.text())=='Borrar Cotas':
                action.setEnabled(False)
        self.cmbProyecto.setEnabled(True)
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            lyr.triggerRepaint()

    def h_editar_proyecto(self):
        b_estado=False
        self.h_seleccion()
        if self.cmbProyecto.currentText()=='<Proyecto>':
            for action in self.actions:
                if str(action.text())=='Modificar Proyecto':
                    QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ Debe elegir un proyecto")
                    action.setChecked(False)
                if str(action.text())=='Nuevo Proyecto':
                    action.setEnabled(True)
                if str(action.text())=='Incorporar Proyecto':
                    action.setEnabled(False)
                if str(action.text())=='Borrar Proyecto':
                    action.setEnabled(False)
                if str(action.text())=='Agregar Cota':
                    action.setEnabled(False)
                if str(action.text())=='Borrar última Cota':
                    action.setEnabled(False)
                if str(action.text())=='Borrar Cotas':
                    action.setEnabled(False)
            return
        for action in self.actions:
            if str(action.text())=='Modificar Proyecto':
                b_estado = action.isChecked()
        self.cmbProyecto.setEnabled(True)
        if b_estado==True:
            self.proyecto = self.cmbProyecto.currentText()
            self.h_seleccion()
            for action in self.actions:
                if str(action.text())=='Nuevo Proyecto':
                    action.setEnabled(False)
                if str(action.text())=='Incorporar Proyecto':
                    action.setEnabled(True)
                if str(action.text())=='Borrar Proyecto':
                    action.setEnabled(True)
                if str(action.text())=='Agregar Cota':
                    action.setEnabled(True)
                if str(action.text())=='Borrar última Cota':
                    action.setEnabled(True)
                if str(action.text())=='Borrar Cotas':
                    action.setEnabled(True)
            self.cmbProyecto.setEnabled(False)
            n = self.iface.mapCanvas().layerCount()
            layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
            for lyr in layers:
                if lyr.name() == 'Postes Proyectos':
                    lyr.setSubsetString('"Alimentador" = ' + "'" + self.proyecto + "'")
                    lyr.triggerRepaint()
                    try:
                        geom = next(lyr.getFeatures()).geometry()
                        box = geom.buffer(25,1).boundingBox()
                        self.mapCanvas.setExtent(box)
                        self.mapCanvas.refresh()
                    except:
                        pass
                if lyr.name() == 'Lineas Proyectos':
                    lyr.setSubsetString('"Alimentador" = ' + "'" + self.proyecto + "'")
                    lyr.triggerRepaint()
                if lyr.name() == 'Anotaciones':
                    lyr.setSubsetString('"Proyecto" = ' + "'" + self.proyecto + "'")
                    lyr.triggerRepaint()
                if lyr.name() == 'Nodos Proyectos':
                    lyr.setSubsetString('"Alimentador" = ' + "'" + self.proyecto + "'")
                    lyr.triggerRepaint()
                    try:
                        geom = next(lyr.getFeatures()).geometry()
                        box = geom.buffer(25,1).boundingBox()
                        self.mapCanvas.setExtent(box)
                        self.mapCanvas.refresh()
                    except:
                        pass
                if lyr.name() == 'Cotas':
                    lyr.setSubsetString('"proyecto" = ' + "'" + self.proyecto + "'")
                    lyr.triggerRepaint()
        else:
            self.proyecto = ''
            self.h_seleccion()
            for action in self.actions:
                if str(action.text())=='Nuevo Proyecto':
                    action.setEnabled(True)
                if str(action.text())=='Incorporar Proyecto':
                    action.setEnabled(False)
                if str(action.text())=='Borrar Proyecto':
                    action.setEnabled(False)
                if str(action.text())=='Agregar Cota':
                    action.setEnabled(False)
                if str(action.text())=='Borrar última Cota':
                    action.setEnabled(False)
                if str(action.text())=='Borrar Cotas':
                    action.setEnabled(False)
            n = self.iface.mapCanvas().layerCount()
            layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
            for lyr in layers:
                if lyr.name() == 'Nodos Proyectos' or lyr.name() == 'Lineas Proyectos' or lyr.name() == 'Postes Proyectos':
                    lyr.setSubsetString('"Alimentador" = ' + "'@@'")
                    lyr.triggerRepaint()
                if lyr.name() == 'Anotaciones':
                    lyr.setSubsetString('"proyecto" = ' + "''")
                if lyr.name() == 'Cotas':
                    lyr.setSubsetString('"proyecto" = ' + "'@@'")
                    lyr.triggerRepaint()
            self.cmbProyecto.setCurrentIndex(0)

    def h_incorporar_proyecto(self):
        reply = QtWidgets.QMessageBox.question(None, 'EnerGis', 'Desea incorporar el proyecto al modelo ❓', QtWidgets.QMessageBox.StandardButton.Yes, QtWidgets.QMessageBox.StandardButton.No)
        if reply == QtWidgets.QMessageBox.StandardButton.No:
            return
        try:
            str_expediente='1111/2001'
            texto, ok = QtWidgets.QInputDialog.getText(
                None,
                "Ingresar expediente",
                "Número de Expediente:",
                text=str_expediente
            )
            if ok:  # Usuario apretó Aceptar
                str_expediente = texto
            cursor = self.conn.cursor()
            cursor.execute("UPDATE Nodos SET Tension=CAST(subzona AS INT),subzona='' WHERE Tension=0 AND Alimentador='" + self.proyecto + "'")
            cursor.execute("UPDATE Lineas SET Tension=CAST(exp AS INT),Exp='" + str_expediente + "' WHERE Tension=0 AND Alimentador='" + self.proyecto + "'")
            cursor.execute("UPDATE Postes SET Tension=CAST(profundidad AS INT) WHERE Tension=0 AND Descripcion='" + self.proyecto + "'")
            #reply = QtWidgets.QMessageBox.question(None, 'EnerGis', 'Desea copiar las Anotaciones del proyecto al Modelo ❓', QtWidgets.QMessageBox.StandardButton.Yes, QtWidgets.QMessageBox.StandardButton.No)
            #if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            #    cursor.execute("UPDATE Anotacione<s SET Proyecto='' WHERE Proyecto='" + self.proyecto + "'")
            #    for lyr in layers:
            #        if lyr.name() == 'Anotaciones':
            #            lyr.setSubsetString('"Proyecto" = ' + "''")
            self.conn.commit()
            QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ Proyecto Incorporado !")
            self.borro_proyecto()
            self.crear_red
        except:
            self.conn.rollback()
            QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo incorporar el Proyecto !")

    def h_cotas(self):
        from .herr_cota import herrCota
        tool = herrCota(self.proyecto, self.iface.mapCanvas(), self.conn)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punCota = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_linea.png'))
        punCota.setMask(punCota.mask())
        curCota = QtGui.QCursor(punCota)
        self.iface.mapCanvas().setCursor(curCota)

    def h_borrar_ultima_cota(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM Cotas WHERE proyecto='" + self.proyecto + "' AND id IN (SELECT TOP 1 id FROM Cotas WHERE proyecto='" + self.proyecto + "' ORDER BY id DESC)")
            self.conn.commit()
        except:
            self.conn.rollback()
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name() == 'Cotas':
                lyr.triggerRepaint()

    def h_borrar_cotas(self):
        reply = QtWidgets.QMessageBox.question(None, 'EnerGis 6', 'Desea borrar todas las cotas ❓', QtWidgets.QMessageBox.StandardButton.Yes, QtWidgets.QMessageBox.StandardButton.No)
        if reply == QtWidgets.QMessageBox.StandardButton.No:
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM Cotas WHERE proyecto='" + self.proyecto + "'")
            self.conn.commit()
        except:
            self.conn.rollback()
            QtWidgets.QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo Borrar !")
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name() == 'Cotas':
                lyr.triggerRepaint()

    def analisis_carga(self):
        if self.red_verificada==False:
            self.h_verificar_red()
        if self.red_verificada==False:
            return
        #Hay que hacer una SQL y listar en excel los trafos con sus potencias y demandas por los usuarios

    def calculo_cargas(self):
        if self.red_verificada==False:
            self.h_verificar_red()
        if self.red_verificada==False:
            return
        if self.tipo_usuario==4:
            return
        if self.tipo_navegacion==0:
            from .frm_calculo_cargas_ant import frmCalculoCargas
            self.dialogo = frmCalculoCargas(self.conn, 2)
            self.dialogo.show()
        else:
            from .frm_calculo_cargas import frmCalculoCargas
            self.dialogo = frmCalculoCargas(self.conn, 2)
            self.dialogo.show()

    def momentos_electricos(self):
        if self.red_verificada==False:
            self.h_verificar_red()
        if self.red_verificada==False:
            return
        ftrs = []
        n = self.iface.mapCanvas().layerCount()
        layers = [self.iface.mapCanvas().layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                for ftr in lyr.selectedFeatures():
                    ftrs.append(ftr)
        if len(ftrs) != 1:
            QtWidgets.QMessageBox.critical(None, 'EnerGis 6', "❌ Debe seleccionar un nodo")
            return
        id = ftrs[0].id()
        from .frm_momentos_electricos import frmMomentosElectricos
        dialogo = frmMomentosElectricos(self.conn, id)
        dialogo.exec()
        dialogo.close()

    def h_flujo(self):
        if self.red_verificada==False:
            self.h_verificar_red()
        if self.red_verificada==False:
            return
        if self.tipo_usuario==4:
            return

        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE Transformadores SET Potencia=5 WHERE Potencia IS NULL")
            cursor.execute("UPDATE A SET d1=o1, d2=o2, d3=o3, d4=o4 FROM (SELECT * FROM (SELECT Nombre, Val1 AS d1, Val2 AS d2, Val3 AS d3, Val4 AS d4 FROM Nodos WHERE (Elmt = 4)) AS D INNER JOIN (SELECT Id_ct, MAX(Potencia) AS o1, MAX(Conexionado) AS o2, MAX(Tension_1) AS o3, MAX(Tension_2) AS o4 FROM Transformadores GROUP BY Id_ct) AS O ON D.Nombre = O.Id_ct) A")
            cursor.execute("UPDATE Transformadores_Parametros SET P01=18.276*[Potencia]^0.689 WHERE P01 IS NULL")
            cursor.execute("UPDATE Transformadores_Parametros SET P01=18.276*[Potencia]^0.689 WHERE P01 = 0")
            #creo los transformadores_parametros que falten
            cursor.execute("INSERT INTO Transformadores_Parametros SELECT Transformadores.Id_trafo, 0.01 AS R1, 0.05 AS X1, POWER (18.276 * [Potencia], 0.689) AS P01, 100 AS Tap1 FROM Transformadores WHERE Id_Trafo NOT IN (SELECT Id_Trafo FROM Transformadores_Parametros)")
            self.conn.commit()
        except:
            self.conn.rollback()

        if self.tipo_navegacion==0:
            QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ Para utilizar el flujo de cargas faltan instalar componentes.\n Verifique en Menú > Administrador > Actualizar a .NET")
            return

        from .frm_flujo_potencias import frmFlujoPotencias
        dialogo = frmFlujoPotencias(self.id_usuario_sistema, self.conn, -1, self.amnodos, self.amlineas, self.monodos)
        dialogo.exec()
        dialogo.close()

    def h_flujo_desequilibrado(self):
        if self.red_verificada==False:
            self.h_verificar_red()
        if self.red_verificada==False:
            return
        if self.tipo_usuario==4:
            return

        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE Transformadores SET Potencia=5 WHERE Potencia IS NULL")
            cursor.execute("UPDATE A SET d1=o1, d2=o2, d3=o3, d4=o4 FROM (SELECT * FROM (SELECT Nombre, Val1 AS d1, Val2 AS d2, Val3 AS d3, Val4 AS d4 FROM Nodos WHERE (Elmt = 4)) AS D INNER JOIN (SELECT Id_ct, MAX(Potencia) AS o1, MAX(Conexionado) AS o2, MAX(Tension_1) AS o3, MAX(Tension_2) AS o4 FROM Transformadores GROUP BY Id_ct) AS O ON D.Nombre = O.Id_ct) A")
            cursor.execute("UPDATE Transformadores_Parametros SET P01=18.276*[Potencia]^0.689 WHERE P01 IS NULL")
            cursor.execute("UPDATE Transformadores_Parametros SET P01=18.276*[Potencia]^0.689 WHERE P01 = 0")
            #creo los transformadores_parametros que falten
            cursor.execute("INSERT INTO Transformadores_Parametros SELECT Transformadores.Id_trafo, 0.01 AS R1, 0.05 AS X1, POWER (18.276 * [Potencia], 0.689) AS P01, 100 AS Tap1 FROM Transformadores WHERE Id_Trafo NOT IN (SELECT Id_Trafo FROM Transformadores_Parametros)")
            self.conn.commit()
        except:
            self.conn.rollback()

        if self.tipo_navegacion==0:
            QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ Para utilizar el flujo de cargas faltan instalar componentes.\n Verifique en Menú > Administrador > Actualizar a .NET")
            return

        from .frm_flujo_potencias_trifasico import frmFlujoPotencias
        dialogo = frmFlujoPotencias(self.id_usuario_sistema, self.conn, -1, self.amnodos, self.amlineas, self.monodos)
        dialogo.exec()
        dialogo.close()

    def h_cortocircuito(self):
        if self.red_verificada==False:
            self.h_verificar_red()
        if self.red_verificada==False:
            return
        if self.tipo_usuario==4:
            return

        if self.tipo_navegacion==0:
            QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ Para utilizar el cálculo de cortocircuito faltan instalar componentes.\n Verifique en Menú > Administrador > Actualizar a .NET")
            return

        from .frm_cortocircuito import frmCortocircuito
        dialogo = frmCortocircuito(self.id_usuario_sistema, self.conn, -1, self.amnodos, self.amlineas, self.monodos)
        dialogo.exec()
        dialogo.close()

    def actualizar_usuarios(self):
        self.conn.autocommit = False
        cursor = self.conn.cursor()
        try:
            cursor.execute("TRUNCATE TABLE Suministros_Nuevos")
            cursor.execute("INSERT INTO Suministros_Nuevos (id_suministro) SELECT usuarios.id_suministro FROM suministros RIGHT JOIN usuarios ON suministros.id_suministro = usuarios.id_suministro WHERE usuarios.ES=1 AND suministros.id_suministro IS NULL GROUP BY usuarios.id_suministro HAVING usuarios.id_suministro IS NOT NULL")
            self.conn.commit()
        except:
            self.conn.rollback()
        self.actualizar_grilla_usuarios()

    def aproximar_usuarios(self):
        seleccion=''
        self.sql="SELECT Min(Nodos.Geoname) AS geoname, Usuarios.calle + ' ' + Usuarios.altura AS direccion, VW_CCDATOSCOMERCIALES.Ruta AS Ruta FROM (Nodos INNER JOIN (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) ON Nodos.Geoname = Suministros.id_nodo) LEFT JOIN VW_CCDATOSCOMERCIALES ON Usuarios.id_usuario = VW_CCDATOSCOMERCIALES.Id_Usuario WHERE Usuarios.calle LIKE '%" + self.txtCalle.text() + "%' GROUP BY VW_CCDATOSCOMERCIALES.Ruta, Usuarios.calle, Usuarios.altura ORDER BY VW_CCDATOSCOMERCIALES.Ruta, Usuarios.calle, Usuarios.altura"
        from .frm_elegir import frmElegir
        dialogo = frmElegir(self.mapCanvas, self.conn, self.sql)
        dialogo.exec()
        if dialogo.seleccionado != '':
            seleccion = dialogo.seleccionado
            #QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ " + self.suministro)
            #QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ " + seleccion)
            if self.suministro!='':
                cursor = self.conn.cursor()
                try:
                    cursor.execute("DELETE FROM Suministros WHERE id_suministro='" + self.suministro + "'")
                    cursor.execute("INSERT INTO Suministros (id_nodo,id_suministro) VALUES ( " + seleccion + ",'" + self.suministro + "')")
                    self.conn.commit()
                except:
                    self.conn.rollback()
                self.actualizar_usuarios()
        dialogo.close()

    def actualizar_grilla_usuarios(self):
        self.conn.autocommit = True
        cursor = self.conn.cursor()
        cursor.execute("SELECT Usuarios.Calle, Usuarios.Altura, VW_CCDATOSCOMERCIALES.Ruta, Suministros_Nuevos.id_suministro FROM (Suministros_Nuevos INNER JOIN Usuarios ON Suministros_Nuevos.id_suministro = Usuarios.id_suministro) LEFT JOIN VW_CCDATOSCOMERCIALES ON Usuarios.id_usuario = VW_CCDATOSCOMERCIALES.Id_Usuario ORDER BY VW_CCDATOSCOMERCIALES.Ruta, Usuarios.Calle, Usuarios.Altura")
        #convierto el cursor en array
        recordset = tuple(cursor)
        self.tblUsuariosNuevos.setRowCount(len(recordset))
        self.dock_widget2.setWindowTitle(str(len(recordset)) +" Usuarios Nuevos")
        self.tblUsuariosNuevos.setColumnCount(4)
        self.tblUsuariosNuevos.setHorizontalHeaderLabels(["calle", "numero", "ruta", "suministro"])
        self.tblUsuariosNuevos.setColumnWidth(0, 120)
        self.tblUsuariosNuevos.setColumnWidth(1, 60)
        self.tblUsuariosNuevos.setColumnWidth(2, 50)
        self.tblUsuariosNuevos.setColumnWidth(3, 60)
        self.tblUsuariosNuevos.setRowCount(len(recordset))
        for i in range (0, len(recordset)):
            self.tblUsuariosNuevos.setItem(i, 0, QtWidgets.QTableWidgetItem(recordset[i][0]))
            self.tblUsuariosNuevos.setItem(i, 1, QtWidgets.QTableWidgetItem(recordset[i][1]))
            self.tblUsuariosNuevos.setItem(i, 2, QtWidgets.QTableWidgetItem(str(recordset[i][2])))
            self.tblUsuariosNuevos.setItem(i, 3, QtWidgets.QTableWidgetItem(recordset[i][3]))

    def elijo_suministro(self):
        self.suministro = self.tblUsuariosNuevos.item(self.tblUsuariosNuevos.currentRow(),3).text()
        tension = int(self.cmbTension.currentText())
        self.conn.autocommit = True
        cursor = self.conn.cursor()
        cursor.execute("SELECT Usuarios.id_usuario, Usuarios.nombre, Usuarios.calle, Usuarios.altura, Usuarios.altura_ex, Tarifas.Nivel_Tension FROM Usuarios INNER JOIN Suministros_Nuevos ON Usuarios.id_suministro = Suministros_Nuevos.id_suministro LEFT OUTER JOIN Tarifas ON Usuarios.tarifa = Tarifas.Tarifa WHERE Suministros_Nuevos.id_suministro ='" + self.suministro + "'")
        #convierto el cursor en array
        recordset = tuple(cursor)
        if len(recordset)==0:
            return
        self.txtUsuario.setText(str(recordset[0][0]))
        self.txtNombre.setText(str(recordset[0][1]).strip())
        self.txtCalle.setText(str(recordset[0][2]).strip())
        self.txtNumero.setText(str(recordset[0][3].strip()) + ' - ' + str(recordset[0][4]).strip())
        nivel_tension='BT'
        if recordset[0][4]!=None:
            nivel_tension = recordset[0][4]
        if nivel_tension=='MT' and tension < 1000:
            QtWidgets.QMessageBox.exclamation(None, 'EnerGis 6', "❌ La tarifa es de un Nivel de Tensión distinto al seleccionado (" + self.cmbTension.currentText() + ")")
        if nivel_tension=='BT' and tension >= 1000:
            QtWidgets.QMessageBox.exclamation(None, 'EnerGis 6', "❌ La tarifa es de un Nivel de Tensión distinto al seleccionado (" + self.cmbTension.currentText() + ")")
        #activo la herramienta para pegarlo en el mapa
        if self.tipo_usuario==4:
            return
        from .herr_suministro import herrSuministro
        tool = herrSuministro(self, self.iface.mapCanvas(), self.conn, tension, self.suministro)
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punNodo = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_suministro.png'))
        punNodo.setMask(punNodo.mask())
        curNodo = QtGui.QCursor(punNodo)
        self.iface.mapCanvas().setCursor(curNodo)

    def elijo_item(self):
        #QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ " + self.tblResultado.selectedItems()[0].text())
        #QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ " + self.tblResultado.selectedItems()[3].text())
        geom = QgsGeometry.fromWkt(self.tblResultado.selectedItems()[3].text())
        box = geom.buffer(25,1).boundingBox()
        self.mapCanvas.setExtent(box)
        self.mapCanvas.refresh()

    def m_separar_suministros(self):
        if self.suministro==None:
            QtWidgets.QMessageBox.information(None, 'EnerGis 6', "ℹ️ Elija un suministro para separar")
            return
        reply = QtWidgets.QMessageBox.question(None, 'EnerGis 6', 'Desea separar a los usuarios del suministro ' + self.suministro +  '❓', QtWidgets.QMessageBox.StandardButton.Yes, QtWidgets.QMessageBox.StandardButton.No)
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.conn.autocommit = False
            cursor = self.conn.cursor()
            try:
                cursor.execute("UPDATE Usuarios SET id_suministro=id_usuario WHERE id_suministro='" + self.suministro + "'")
                self.conn.commit()
            except:
                self.conn.rollback()

    def m_suministros_sin_usuarios(self):
        cursor = self.conn.cursor()
        self.conn.autocommit = True
        cursor.execute("SELECT Nodos.Geoname, Nodos.Tension FROM ((Nodos LEFT JOIN Lineas AS Lineas_1 ON Nodos.Geoname = Lineas_1.Hasta) LEFT JOIN (Suministros LEFT JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) ON Nodos.Geoname = Suministros.id_nodo) LEFT JOIN Lineas ON Nodos.Geoname = Lineas.Desde WHERE Nodos.Elmt = 6 GROUP BY Nodos.Geoname, Nodos.Tension, Nodos.Elmt HAVING (COUNT(Lineas_1.Geoname) + COUNT(Lineas.Geoname) = 1) AND (COUNT(Usuarios.id_usuario) = 0) OR (COUNT(Lineas_1.Geoname) + COUNT(Lineas.Geoname) = 0) AND (COUNT(Usuarios.id_usuario) = 0)")
        #convierto el cursor en array
        recordset = tuple(cursor)
        cursor.close()
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.type() == QgsMapLayerType.VectorLayer:
                lyr.removeSelection()
        seleccion_n = []
        for n in range(0, len(recordset)):
            seleccion_n.append(recordset[n][0])
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyr.select(seleccion_n)
        from .frm_seleccion import frmSeleccion
        dialogo = frmSeleccion(self.mapCanvas)
        for m in range (0, len(seleccion_n)):
            dialogo.liwNodos.addItem(QtWidgets.QListWidgetItem(str(seleccion_n[m])))
        dialogo.show()

    def m_suministros_con_coordenadas_externas(self):
        from .mod_usuarios_nuevos import suministros_con_coordenadas_externas
        suministros_con_coordenadas_externas(self.mapCanvas, self.conn, self.srid)

    def m_suministros_con_ejes_de_calle(self):
        from .mod_usuarios_nuevos import suministros_con_ejes_de_calle
        suministros_con_ejes_de_calle(self.mapCanvas, self.conn, self.srid)

    def m_suministros_por_catastro(self):
        from .mod_usuarios_nuevos import suministros_por_catastro
        suministros_por_catastro(self.mapCanvas, self.conn, self.srid)

    def m_conectar_suministros_aislados(self):
        from .mod_usuarios_nuevos import conectar_suministros_aislados
        conectar_suministros_aislados(self.mapCanvas, self.conn, self.srid)
