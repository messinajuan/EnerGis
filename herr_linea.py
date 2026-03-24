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

from qgis.core import QgsGeometry, QgsProject, QgsWkbTypes, QgsSnappingUtils
from qgis.gui import QgsVertexMarker
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt, QDate
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import QgsPoint, QgsPointXY, QgsRectangle, QgsFeatureRequest, QgsFeature, QgsSnappingConfig
from math import sqrt, pow, atan, cos, sin
import os

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrLinea(QgsMapTool):
    def __init__(self, proyecto, tipo_usuario, mapCanvas, conn, tension):
        QgsMapTool.__init__(self, mapCanvas)
        self.proyecto = proyecto
        self.tipo_usuario = tipo_usuario
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.tension = tension
        self.tension_original = tension
        self.tecla=''
        self.nodo_desde = 0
        self.nodo_hasta = 0
        self.puntos = []
        self.rubber_band = None

        #snapping
        self.useSnapped = True
        self.snapper = None
        self.markerSnapped = None
        self.prj = QgsProject.instance()
        self.snapConfig = self.prj.snappingConfig()
        self.prj.snappingConfigChanged.connect(self.setSnapping)
        self.setSnapping(self.prj.snappingConfig())

    def setSnapping(self, config):
        self.snapConfig = config
        self.snapConfig.setType(QgsSnappingConfig.Vertex)
        self.snapper = QgsSnappingUtils(self.mapCanvas)
        self.snapper.setConfig(self.snapConfig)
        self.snapper.setMapSettings(self.mapCanvas.mapSettings())

    def deactivate(self):
        self.resetMarker()

    def isSnapped(self):
        self.resetMarker()
        matchres = self.snapper.snapToMap(self.point)
        if matchres.isValid():
            self.markerSnapped = QgsVertexMarker(self.mapCanvas)
            self.markerSnapped.setColor(Qt.GlobalColor.red)
            self.markerSnapped.setIconSize(10)
            self.markerSnapped.setIconType(QgsVertexMarker.ICON_BOX)
            self.markerSnapped.setPenWidth(2)
            self.markerSnapped.setCenter(matchres.point())
            self.point = matchres.point()

    def resetMarker(self):
        self.mapCanvas.scene().removeItem(self.markerSnapped)

    def canvasMoveEvent(self, event):
        x = event.pos().x()
        y = event.pos().y()
        self.point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
        if self.snapConfig.enabled() and self.useSnapped:
            self.isSnapped()
        if len(self.puntos)>0:
            if self.rubber_band:
                self.rubber_band.reset(QgsWkbTypes.LineGeometry)
                self.rubber_band = None
            self.rubber_band = QgsRubberBand(self.mapCanvas, QgsWkbTypes.LineGeometry)
            self.rubber_band.setColor(Qt.GlobalColor.red)
            self.rubber_band.setWidth(2)
            self.puntos.append(QgsPoint(self.point.x(),self.point.y()))
            pts = QgsGeometry.fromPolyline(self.puntos)
            self.ftrLinea = QgsFeature()
            self.ftrLinea.setGeometry(pts)
            for punto in self.puntos:
                self.rubber_band.addPoint(QgsPointXY(punto.x(), punto.y()), True)
            self.rubber_band.show()
            self.puntos.pop()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self.rubber_band:
                self.rubber_band.reset(QgsWkbTypes.LineGeometry)
                self.rubber_band = None
                self.puntos = []
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.termino_linea(event)

    def canvasPressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.snapConfig.enabled() and self.useSnapped:
                self.isSnapped()
            if len(self.puntos) == 0:
                n = self.mapCanvas.layerCount()
                layers = [self.mapCanvas.layer(i) for i in range(n)]
                for lyr in layers:
                    if lyr.name()[:5] == 'Nodos':
                        width = 5 * self.mapCanvas.mapUnitsPerPixel()
                        rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                        int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                        ftrs = lyr.getFeatures(int)
                        i = 0
                        for ftr in ftrs:
                            i = i + 1
                        if i > 0:
                            geom = ftr.geometry()
                            if geom.asPoint().x() > 0:
                                self.puntos.append(QgsPoint(geom.asPoint().x(),geom.asPoint().y()))
                                self.nodo_desde = ftr.id()
                                self.tension = lyr.name() [6 - len(lyr.name()):]
                                if self.tension.strip() == 'Proyectos':
                                    self.tension='0'
                                if self.rubber_band is None:
                                    self.rubber_band = QgsRubberBand(self.mapCanvas, QgsWkbTypes.LineGeometry)
                                    self.rubber_band.setColor(Qt.GlobalColor.red)
                                    self.rubber_band.setWidth(2)
                                self.rubber_band.addPoint(geom.asPoint(), True)
                                self.rubber_band.show()
                                return
            else:
                n = self.mapCanvas.layerCount()
                layers = [self.mapCanvas.layer(i) for i in range(n)]
                for lyr in layers:
                    if lyr.name()[:5] == 'Nodos':
                        width = 5 * self.mapCanvas.mapUnitsPerPixel() #me alejo 5 de los nodos !
                        rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                        int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                        ftrs = lyr.getFeatures(int)
                        i = 0
                        for ftr in ftrs:
                            i = i + 1
                        if i > 0:
                            #No tengo que hacer nada para permitir el doble click
                            return
                if self.point.x() > 0:
                    self.puntos.append(QgsPoint(self.point.x(),self.point.y()))
                    self.rubber_band.addPoint(self.point, True)
                    self.rubber_band.show()
                    return
        elif event.button() == Qt.MouseButton.RightButton:
            self.termino_linea(event)

    def canvasDoubleClickEvent(self, event):
        self.termino_linea(event)

    def termino_linea(self, event):
        self.longitud = 0
        if len(self.puntos) != 0:
            n = self.mapCanvas.layerCount()
            layers = [self.mapCanvas.layer(i) for i in range(n)]
            for lyr in layers:
                if lyr.name()[:5] == 'Nodos':
                    width = 5 * self.mapCanvas.mapUnitsPerPixel()
                    rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                    int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                    ftrs = lyr.getFeatures(int)
                    for ftr in ftrs:
                        geom = ftr.geometry()
                        if geom.asPoint().x() > 0:
                            self.puntos.append(QgsPoint(geom.asPoint().x(),geom.asPoint().y()))
                            self.nodo_hasta = ftr.id()
                            t = lyr.name() [6 - len(lyr.name()):]
                            if t.strip() == 'Proyectos':
                                t = '0'
                            if t != self.tension:
                                if t=='0' or self.tension=='0':
                                    QMessageBox.warning(None, 'EnerGis 6', '❌ Conectar luego de incorporar el proyecto')
                                    if self.rubber_band:
                                        self.rubber_band.reset(QgsWkbTypes.LineGeometry)
                                        self.rubber_band = None
                                    self.resetMarker()
                                    return
                                else:
                                    QMessageBox.warning(None, 'EnerGis 6', '❌ Línea entre dos niveles de Tensión')
                                    if self.rubber_band:
                                        self.rubber_band.reset(QgsWkbTypes.LineGeometry)
                                        self.rubber_band = None
                                    self.resetMarker()
                            #dibujo linea
                            #self.puntos.append(QgsPoint(self.point.x(),self.point.y()))
                            pts = QgsGeometry.fromPolyline(self.puntos)
                            self.ftrLinea = QgsFeature()
                            self.ftrLinea.setGeometry(pts)
                            self.longitud = self.ftrLinea.geometry().length()
                            self.puntos = []
                            self.crearLinea()
                            return
        if len(self.puntos)==0:
            return
        pa = self.puntos[-1]
        xa = pa.x()
        ya = pa.y()
        a = sqrt(pow((self.point.x() - xa), 2) + pow((self.point.y() - ya), 2))
        if a==0:
            return





        from .frm_elegir_longitud import frmElegirLongitud
        dialogo = frmElegirLongitud(a)
        dialogo.exec()
        if dialogo.txtDistancia.text()=='0':
            if self.rubber_band:
                self.rubber_band.reset(QgsWkbTypes.LineGeometry)
                self.rubber_band = None
                self.puntos = []
            return
        d = float(dialogo.txtDistancia.text())
        x,y = self.calcular_extension(self.point.x(), self.point.y(), xa, ya, d)
        self.point = QgsPointXY(x, y)
        #con la longitud = XXX, cambio el valor de self.point
        #---------------------------------------------------------------
        #copiado textual de herr_nodo
        #---------------------------------------------------------------
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        self.zona = 0
        for lyr in layers:
            if lyr.name() == 'Areas':
                width = 5 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                #rect = self.mapCanvas.mapRenderer().mapToLayerCoordinates(lyr, rect)
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    self.zona = ftr.id()
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                width = 2 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                #rect = self.mapCanvas.mapRenderer().mapToLayerCoordinates(lyr, rect)
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    QMessageBox.warning(None, 'EnerGis 6', '❌ Ya hay un nodo en esa posición')
                    return
        #---------------------------------------------------------------
        cnn = self.conn
        cnn.autocommit = False
        cursor = cnn.cursor()
        cursor.execute("SELECT iid FROM iid")
        iid = tuple(cursor)
        self.nodo_hasta = iid[0][0] + 1
        cursor.execute("UPDATE iid SET iid =" + str(self.nodo_hasta))
        cnn.commit()
        cursor = cnn.cursor()
        cursor.execute("SELECT MAX(Aux) FROM Nodos")
        auxnodos = tuple(cursor)
        cursor.close()
        if auxnodos[0][0]==None:
            aux = 1
        else:
            aux = auxnodos[0][0] + 1
        cursor = cnn.cursor()
        cursor.execute("SELECT Valor FROM Configuracion WHERE Variable='SRID'")
        rows = cursor.fetchall()
        cursor.close()
        srid = rows[0][0]
        obj = "geometry::Point(" + str(self.point.x()) + ',' + str(self.point.y()) + ',' + srid + ")"
        str_zona='Rural'
        if self.zona!=0:
            cursor = cnn.cursor()
            cursor.execute("SELECT nombre FROM Areas WHERE Geoname=" + str(self.zona))
            #convierto el cursor en array
            datos_zona = tuple(cursor)
            cursor.close()
            str_zona=datos_zona[0][0]
        cursor = cnn.cursor()
        cursor.execute("SELECT Alimentador FROM Nodos WHERE Geoname=" + str(self.nodo_desde))
        #convierto el cursor en array
        datos_nodo = tuple(cursor)
        cursor.close()
        str_alimentador=datos_nodo[0][0]
        str_subzona=''
        if self.tension=='0':
            str_subzona=str(self.tension_original)
            aux=0
        str_valores = str(self.nodo_hasta) + ", "
        str_valores = str_valores + "'', "
        str_valores = str_valores + "'', "
        str_valores = str_valores + "0, "
        str_valores = str_valores + str(self.point.x()) + ", "
        str_valores = str_valores + str(self.point.y()) + ", "
        str_valores = str_valores + "'35-EnerGIS-16777215-0-2-0', "
        str_valores = str_valores + "'', "
        str_valores = str_valores + "'', "
        str_valores = str_valores + "'', "
        str_valores = str_valores + "'', "
        str_valores = str_valores + "'', "
        str_valores = str_valores + "0, "
        str_valores = str_valores + self.tension + ", "
        str_valores = str_valores + "'" + str_zona + "', "
        str_valores = str_valores + "'" + str_alimentador + "', "
        str_valores = str_valores + str(aux) + ", "
        str_valores = str_valores + "'" + str(QDate.currentDate().toPyDate()).replace('-','') + "', "
        str_valores = str_valores + "'" + str_subzona + "', "
        str_valores = str_valores + "0, "
        str_valores = str_valores + "1, "
        str_valores = str_valores + "'', "
        str_valores = str_valores + obj
        try:
            cursor = cnn.cursor()
            cursor.execute("INSERT INTO Nodos (Geoname, Nombre, Descripcion, Elmt, XCoord, YCoord, Estilo, Val1, Val2, Val3, Val4, Val5, Nivel, Tension, Zona, Alimentador, Aux, Modificacion, Subzona, Estado, Localidad, UUCC, obj) VALUES (" + str_valores + ")")
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.critical(None, 'EnerGis 6', '❌ No se pudo actualizar la Base de Datos')

            if self.rubber_band:
                self.rubber_band.reset(QgsWkbTypes.LineGeometry)
                self.rubber_band = None
            self.resetMarker()
            return
        #---------------------------------------------------------------
        #dibujo linea
        self.puntos.append(QgsPoint(self.point.x(),self.point.y()))
        pts = QgsGeometry.fromPolyline(self.puntos)
        self.ftrLinea = QgsFeature()
        self.ftrLinea.setGeometry(pts)
        self.longitud = self.ftrLinea.geometry().length()
        self.puntos = []
        self.crearLinea()

    def crearLinea(self):
        if self.tension=='0':
            from .frm_lineas_proyecto import frmLineasProyecto
            dialogo = frmLineasProyecto(self.proyecto, self.tipo_usuario, self.mapCanvas, self.conn, self.tension_original, self.nodo_desde, self.nodo_hasta, self.longitud, self.ftrLinea, 0)
            dialogo.exec()
        else:
            from .frm_lineas import frmLineas
            dialogo = frmLineas(self.tipo_usuario, self.mapCanvas, self.conn, self.tension, self.nodo_desde, self.nodo_hasta, self.longitud, self.ftrLinea, 0)
            dialogo.exec()

        if self.rubber_band:
            self.rubber_band.reset(QgsWkbTypes.LineGeometry)
            self.rubber_band = None
            self.resetMarker()
            dialogo.close()

        #snapping
        self.setSnapping(self.prj.snappingConfig())

        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:6] == 'Lineas':
                lyr.triggerRepaint()


    def calcular_extension(self, xp, yp, xa, ya, d):
        if xa - xp < 0:
            if ya - yp < 0:
                i_cuadrante = 1
            if ya - yp > 0:
                i_cuadrante = 4
            if yp==ya:
                i_cuadrante = 1
        elif xa - xp > 0:
            if ya - yp < 0:
                i_cuadrante = 2
            if ya - yp > 0:
                i_cuadrante = 3
            if yp==ya:
                i_cuadrante = 2
        else:
            if ya - yp < 0:
                i_cuadrante = 1
            if ya - yp > 0:
                i_cuadrante = 4
            if yp==ya:
                i_cuadrante = 1
        #Calculo el angulo al que se encuentra el origen del centro
        alfa = abs(atan((yp - ya) / (xp - xa)))
        if i_cuadrante==1:
            x = xa + d * abs(cos(alfa))
            y = ya + d * abs(sin(alfa))
            return (x, y)
        if i_cuadrante==2:
            x = xa - d * abs(cos(alfa))
            y = ya + d * abs(sin(alfa))
            return (x, y)
        if i_cuadrante==3:
            x = xa - d * abs(cos(alfa))
            y = ya - d * abs(sin(alfa))
            return (x, y)
        if i_cuadrante==4:
            x = xa + d * abs(cos(alfa))
            y = ya - d * abs(sin(alfa))
            return (x, y)
        return (0, 0)
