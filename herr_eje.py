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
from PyQt6.QtCore import Qt
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import QgsPoint, QgsPointXY, QgsRectangle, QgsFeatureRequest, QgsFeature
import os

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrEje(QgsMapTool):
    def __init__(self, tipo_usuario, mapCanvas, conn):
        QgsMapTool.__init__(self, mapCanvas)
        self.tipo_usuario = tipo_usuario
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.tecla=''
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
                if lyr.name() == 'Ejes de Calle':
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
                if lyr.name() == 'Ejes de Calle':
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

                    self.crearEje()
                    self.puntos = []
                    return

    def crearEje(self):
        X1 = self.puntos[0].x()
        Y1 = self.puntos[0].y()
        X2 = self.puntos[1].x()
        Y2 = self.puntos[1].y()
        from .frm_ejes import frmEjes
        dialogo = frmEjes(self.tipo_usuario, self.mapCanvas, self.conn, X1, Y1, X2, Y2, 0)
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
            if lyr.name() == 'Ejes de Calle':
                lyr.triggerRepaint()


