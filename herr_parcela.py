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

from qgis.core import QgsGeometry, QgsProject, QgsSnappingUtils, QgsWkbTypes
from qgis.gui import QgsVertexMarker, QgsRubberBand
#from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt
from qgis.gui import QgsMapTool
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsPoint, QgsPointXY, QgsFeature
import os

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrParcela(QgsMapTool):
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
            self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)
            self.rubber_band = None
            self.rubber_band = QgsRubberBand(self.mapCanvas, QgsWkbTypes.PolygonGeometry)
            transparent_red = QColor(255, 0, 0, 50)
            self.rubber_band.setColor(transparent_red)
            self.rubber_band.setWidth(2)
            self.puntos.append(QgsPoint(self.point.x(),self.point.y()))
            for punto in self.puntos:
                self.rubber_band.addPoint(QgsPointXY(punto.x(), punto.y()), True)
            self.rubber_band.show()
            self.puntos.pop()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self.rubber_band:
                self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)
                self.rubber_band = None
                self.puntos = []
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.termino_parcela(event)

    def canvasPressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.puntos.append(QgsPoint(self.point.x(),self.point.y()))
            if len(self.puntos)>0:
                pts = QgsGeometry.fromPolyline(self.puntos)
                str_pts = pts.asWkt()
                str_pts = str_pts.replace("LineString ","Polygon (") + ")"

                if self.rubber_band is None:
                    self.rubber_band = QgsRubberBand(self.mapCanvas, QgsWkbTypes.PolygonGeometry)
                    transparent_red = QColor(255, 0, 0, 50)
                    self.rubber_band.setColor(transparent_red)
                    self.rubber_band.setWidth(2)
                self.rubber_band.addPoint(self.point, True)
                self.rubber_band.show()

        elif event.button() == Qt.MouseButton.RightButton:
            self.termino_parcela(event)

    def canvasDoubleClickEvent(self, event):
        self.termino_parcela(event)

    def termino_parcela(self, event):
        self.puntos.append(QgsPoint(self.point.x(),self.point.y()))
        self.puntos.append(self.puntos[0])
        self.crearParcela()
        self.puntos=[]

    def crearParcela(self):
        pts = QgsGeometry.fromPolyline(self.puntos)
        str_pts = pts.asWkt()
        str_pts = str_pts.replace("LineString ","Polygon (") + ")"
        ftr = QgsFeature()
        ftr.setGeometry(QgsGeometry.fromWkt(str_pts))

        from .frm_parcelas import frmParcelas
        dialogo = frmParcelas(self.tipo_usuario, self.mapCanvas, self.conn, ftr, 0)
        dialogo.exec()

        if self.rubber_band:
            self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)
            self.rubber_band = None
        self.resetMarker()

        dialogo.close()

        #snapping
        self.setSnapping(self.prj.snappingConfig())

        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name() == 'Parcelas':
                lyr.triggerRepaint()

