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

from qgis.core import QgsGeometry, QgsProject, QgsSnappingUtils
from qgis.gui import QgsVertexMarker
#from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from qgis.gui import QgsMapTool
from qgis.core import QgsPoint, QgsRectangle, QgsFeatureRequest, QgsVectorLayer, QgsFeature
import os

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrCota(QgsMapTool):
    def __init__(self, proyecto, mapCanvas, conn):
        QgsMapTool.__init__(self, mapCanvas)
        self.proyecto = proyecto
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.tecla=''
        self.puntos = []
        self.lineas_temp = QgsVectorLayer()

        #snapping
        self.useSnapped = True
        self.snapper = None
        self.markerSnapped = None
        self.prj = QgsProject.instance()
        self.snapConfig = self.prj.snappingConfig()
        self.prj.snappingConfigChanged.connect(self.setSnapping)
        self.setSnapping(self.prj.snappingConfig())
        n = self.mapCanvas.layerCount()
        b_existe = False
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyrCRS = lyr.crs().authid()
            if lyr.name() == 'Lineas_Temp':
                b_existe = True
                self.lineas_temp = lyr

        if b_existe == False:
            lineas_temp = QgsVectorLayer("LineString?crs=" + lyrCRS, "Lineas_Temp", "memory")
            QgsProject.instance().addMapLayer(lineas_temp)
            self.lineas_temp.renderer().symbol().setWidth(0.4)
            self.lineas_temp.renderer().symbol().setColor(QColor("red"))
        pass

    def setSnapping(self, config):
        self.snapConfig = config
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
            #borra todos los objetos de la capa
            if not self.lineas_temp.isEditable():
                self.lineas_temp.startEditing()
            listOfIds = [feat.id() for feat in self.lineas_temp.getFeatures()]
            self.lineas_temp.deleteFeatures(listOfIds)
            self.lineas_temp.commitChanges()
            #----------------------------------
            self.puntos.append(QgsPoint(self.point.x(),self.point.y()))
            pts = QgsGeometry.fromPolyline(self.puntos)
            self.ftrCota = QgsFeature()
            self.ftrCota.setGeometry(pts)
            lineas_temp_data = self.lineas_temp.dataProvider()
            lineas_temp_data.addFeatures([self.ftrCota])
            self.lineas_temp.triggerRepaint()
            self.puntos.pop()
        pass

    def keyPressEvent(self, event):
        if str(event.key()) == '16777249':
            self.tecla = 'Ctrl'
        if str(event.key()) == '16777240':
            self.tecla = 'Shift'
        if str(event.key()) == '16777216':
            self.tecla = 'Esc'
            self.puntos = []
            #borra todos los objetos de la capa
            if not self.lineas_temp.isEditable():
                self.lineas_temp.startEditing()
            listOfIds = [feat.id() for feat in self.lineas_temp.getFeatures()]
            self.lineas_temp.deleteFeatures(listOfIds)
            self.lineas_temp.commitChanges()
            #----------------------------------

    def keyReleaseEvent(self, event):
        self.tecla = ''
        
    def canvasPressEvent(self, event):
        x = event.pos().x()
        y = event.pos().y()
        self.point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
        if self.snapConfig.enabled() and self.useSnapped:
            self.isSnapped()
        if len(self.puntos) == 0:
            n = self.mapCanvas.layerCount()
            layers = [self.mapCanvas.layer(i) for i in range(n)]
            for lyr in layers:
                if lyr.name() == 'Cotas':
                    width = 5 * self.mapCanvas.mapUnitsPerPixel()
                    rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                    int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                    ftrs = lyr.getFeatures(int)
                    i = 0
                    for ftr in ftrs:
                        i = i + 1
                    if i > 0:
                        geom = ftr.geometry()
                        vertices  = geom.asPolyline()
                        m = len(vertices)
                        for i in range(m):
                            vertice=QgsPoint(vertices [i][0],vertices [i][1])
                            if abs(self.point.x()-vertices [i][0])<width and abs(self.point.y()-vertices [i][1])<width:
                                v = QgsFeature()
                                v.setGeometry(vertice)
                                self.puntos.append(QgsPoint(vertice.x(), vertice.y()))
                    else:
                        self.puntos.append(QgsPoint(self.point.x(), self.point.y()))
                    return

        if len(self.puntos) == 1:
            n = self.mapCanvas.layerCount()
            layers = [self.mapCanvas.layer(i) for i in range(n)]
            for lyr in layers:
                if lyr.name() == 'Cotas':
                    width = 5 * self.mapCanvas.mapUnitsPerPixel()
                    rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                    int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                    ftrs = lyr.getFeatures(int)
                    i = 0
                    for ftr in ftrs:
                        i = i + 1
                    if i > 0:
                        geom = ftr.geometry()
                        vertices  = geom.asPolyline()
                        m = len(vertices)
                        for i in range(m):
                            vertice=QgsPoint(vertices [i][0],vertices [i][1])
                            if abs(self.point.x()-vertices [i][0])<width and abs(self.point.y()-vertices [i][1])<width:
                                v = QgsFeature()
                                v.setGeometry(vertice)
                                self.puntos.append(QgsPoint(vertice.x(), vertice.y()))
                    else:
                        self.puntos.append(QgsPoint(self.point.x(), self.point.y()))
                    #borra todos los objetos de la capa
                    if not self.lineas_temp.isEditable():
                        self.lineas_temp.startEditing()
                    listOfIds = [feat.id() for feat in self.lineas_temp.getFeatures()]
                    self.lineas_temp.deleteFeatures(listOfIds)
                    self.lineas_temp.commitChanges()
                    self.lineas_temp.triggerRepaint()
                    self.crearCota(self.puntos)
                    self.puntos = []
                    return

    def crearCota(self, puntos):
        if len(puntos)==0:
            return
        X1 = puntos[0].x()
        Y1 = puntos[0].y()
        X2 = puntos[1].x()
        Y2 = puntos[1].y()
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT Valor FROM Configuracion WHERE Variable='SRID'")
            rows = cursor.fetchall()
            cursor.close()
            srid = rows[0][0]
            obj = "geometry::STGeomFromText(" + "'LINESTRING (" + str(X1) + " " + str(Y1) + "," + str(X2) + " " + str(Y2) + ")', " + srid + ")"
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO Cotas (proyecto, obj) VALUES ('" + self.proyecto + "'," + obj + ")")
            self.conn.commit()
        except:
            self.conn.rollback()
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name() == 'Cotas':
                lyr.triggerRepaint()
