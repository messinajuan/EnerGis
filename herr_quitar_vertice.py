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

from qgis.core import QgsProject, QgsSnappingUtils
from qgis.gui import QgsVertexMarker
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt
from qgis.gui import QgsMapTool
from qgis.core import QgsRectangle, QgsFeatureRequest, QgsSnappingConfig
import os

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrQuitarVertice(QgsMapTool):
    def __init__(self, mapCanvas, conn):
        QgsMapTool.__init__(self, mapCanvas)
        self.mapCanvas = mapCanvas    
        self.conn = conn

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

    def canvasPressEvent(self, event):
        point=self.point
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            #primero nos fijamos si hay una linea abajo, a ver si insertamos
            if lyr.name()[:6] == 'Lineas':
                width = 0.01 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(point.x() - width, point.y() - width, point.x() + width, point.y() + width)
                #rect = self.mapCanvas.mapRenderer().mapToLayerCoordinates(lyr, rect)                
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    reply = QMessageBox.question(None, 'EnerGis 6', 'Desea borrar el vértice ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
                    if reply == QMessageBox.StandardButton.No:
                        return
                    geom = ftr.geometry()
                    g = self.quitar_vertice(geom, point, 0.01)
                    cnn = self.conn
                    cursor = cnn.cursor()
                    cursor.execute("SELECT Valor FROM Configuracion WHERE Variable='SRID'")
                    rows = cursor.fetchall()
                    cursor.close()
                    srid = rows[0][0]
                    cursor = cnn.cursor()
                    try:
                        cursor.execute("UPDATE Lineas SET obj = geometry::STGeomFromText(" + "'" + g.asWkt() + "'," + srid + ")  WHERE geoname=" + str(ftr.id()))
                        cnn.commit()
                        lyr.triggerRepaint()
                    except:
                        cnn.rollback()
                        QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo actualizar !")
                    return
            if lyr.name() == 'Areas':
                width = 0.01 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(point.x() - width, point.y() - width, point.x() + width, point.y() + width)
                #rect = self.mapCanvas.mapRenderer().mapToLayerCoordinates(lyr, rect)
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    reply = QMessageBox.question(None, 'EnerGis 6', 'Desea borrar el vértice ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
                    if reply == QMessageBox.StandardButton.No:
                        return
                    geom = ftr.geometry()
                    g = self.quitar_vertice(geom, point, 0.01)
                    cnn = self.conn
                    cursor = cnn.cursor()
                    cursor.execute("SELECT Valor FROM Configuracion WHERE Variable='SRID'")
                    rows = cursor.fetchall()
                    cursor.close()
                    srid = rows[0][0]
                    cursor = cnn.cursor()
                    try:
                        cursor.execute("UPDATE Areas SET obj = geometry::STGeomFromText(" + "'" + g.asWkt() + "'," + srid + ")  WHERE geoname=" + str(ftr.id()))
                        cnn.commit()
                        lyr.triggerRepaint()
                    except:
                        cnn.rollback()
                        QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo actualizar !")
                    return
            if lyr.name() == 'Parcelas':
                width = 0.01 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(point.x() - width, point.y() - width, point.x() + width, point.y() + width)
                #rect = self.mapCanvas.mapRenderer().mapToLayerCoordinates(lyr, rect)
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    reply = QMessageBox.question(None, 'EnerGis 6', 'Desea borrar el vértice ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
                    if reply == QMessageBox.StandardButton.No:
                        return
                    geom = ftr.geometry()
                    g = self.quitar_vertice(geom, point, 0.01)
                    cnn = self.conn
                    cursor = cnn.cursor()
                    cursor.execute("SELECT Valor FROM Configuracion WHERE Variable='SRID'")
                    rows = cursor.fetchall()
                    cursor.close()
                    srid = rows[0][0]
                    cursor = cnn.cursor()
                    try:
                        cursor.execute("UPDATE Parcelas SET obj = geometry::STGeomFromText(" + "'" + g.asWkt() + "'," + srid + ")  WHERE geoname=" + str(ftr.id()))
                        cnn.commit()
                        lyr.triggerRepaint()
                    except:
                        cnn.rollback()
                        QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo actualizar !")
                    return

    def quitar_vertice(self, geom, point, tolerancia):
        punto1, at, b1, after, d1 = geom.closestVertex(point)
        if at==0:
                pass
        elif after==-1:
                pass
        else:
            geom.deleteVertex(at)
        return geom
