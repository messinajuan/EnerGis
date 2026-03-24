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

class herrAgregarVertice(QgsMapTool):
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

        self.snapConfig.setType(QgsSnappingConfig.Segment)

        self.snapper = QgsSnappingUtils(self.mapCanvas)
        self.snapper.setConfig(self.snapConfig)
        self.snapper.setMapSettings(self.mapCanvas.mapSettings())

    def deactivate(self):
        self.resetMarker()
        #self.mapCanvas.scene().removeItem(self.rb)

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
                width = 1 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(point.x() - width, point.y() - width, point.x() + width, point.y() + width)
                #rect = self.mapCanvas.mapRenderer().mapToLayerCoordinates(lyr, rect)                
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    geom = ftr.geometry()
                    g = self.agregar_vertice(geom, point, 1)
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
                        QMessageBox.information(None, 'Energis 5', 'ℹ️ Vertice Agregado')
                        lyr.triggerRepaint()
                    except:
                        cnn.rollback()
                        QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudo actualizar')
                    return

            if lyr.name() == 'Areas':
                width = 1 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(point.x() - width, point.y() - width, point.x() + width, point.y() + width)
                #rect = self.mapCanvas.mapRenderer().mapToLayerCoordinates(lyr, rect)
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    geom = ftr.geometry()
                    g = self.agregar_vertice(geom, point, 1)
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
                        QMessageBox.information(None, 'Energis 5', 'ℹ️ Vertice Agregado')
                        lyr.triggerRepaint()
                    except:
                        cnn.rollback()
                        QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudo actualizar')
                    return

            if lyr.name() == 'Parcelas':
                width = 1 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(point.x() - width, point.y() - width, point.x() + width, point.y() + width)
                #rect = self.mapCanvas.mapRenderer().mapToLayerCoordinates(lyr, rect)
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    geom = ftr.geometry()
                    g = self.agregar_vertice(geom, point, 1)
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
                        QMessageBox.information(None, 'Energis 5', 'ℹ️ Vertice Agregado')
                        lyr.triggerRepaint()
                    except:
                        cnn.rollback()
                        QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudo actualizar')
                    return

    def agregar_vertice(self, geom, point, tolerancia):
        p1, at, b1, after, d1 = geom.closestVertex(point)
        dist, p2, segmento, s = geom.closestSegmentWithContext(point)
        if at == 0:
            if dist < tolerancia:
                # insert into first segment
                geom.insertVertex(point.x(), point.y(), after)
            else:
                # insert before first vertex
                geom.insertVertex(point.x(), point.y(), 0)
        elif after == -1:
            if dist < tolerancia:
                # insert after last vertex
                geom.insertVertex(point.x(), point.y(), at)
            else:
                # insert into last segment
                last = geom.vertexAt(at)
                geom.moveVertex(point.x(), point.y(), at)
                geom.insertVertex(last.x(), last.y(), at)
        else:
            # insert into any other segment
            geom.insertVertex(point.x(), point.y(), segmento)
        return geom
