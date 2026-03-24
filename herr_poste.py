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

from qgis.core import QgsProject, QgsSnappingUtils, QgsWkbTypes
from qgis.gui import QgsVertexMarker
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import QgsRectangle, QgsFeatureRequest, QgsSnappingConfig
import os

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrPoste(QgsMapTool):

    def __init__(self, proyecto, tipo_usuario, mapCanvas, conn, tension):
        QgsMapTool.__init__(self, mapCanvas)
        self.proyecto = proyecto
        self.tipo_usuario = tipo_usuario
        self.mapCanvas = mapCanvas    
        self.conn = conn
        self.tension = tension
        self.zona = 0
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
        self.snapConfig.setType(QgsSnappingConfig.VertexAndSegment)
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
        if self.useSnapped:
            self.isSnapped()
        else:
            self.resetMarker()
        
    def canvasReleaseEvent(self, event):
        if self.rubber_band is None:
            self.rubber_band = QgsRubberBand(self.mapCanvas, QgsWkbTypes.PointGeometry)
            self.rubber_band.setColor(Qt.GlobalColor.red)
            self.rubber_band.setWidth(5)

        self.rubber_band.addPoint(self.point)
        self.rubber_band.show()

        point = self.point
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        self.zona = 0
        for lyr in layers:
            if lyr.name() == 'Areas':
                width = 1 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(point.x() - width, point.y() - width, point.x() + width, point.y() + width)
                #rect = self.mapCanvas.mapRenderer().mapToLayerCoordinates(lyr, rect)
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    self.zona = ftr.id()

        for lyr in layers:
            #primero nos fijamos si hay una linea abajo, a ver si insertamos
            self.elmt_asociado=''
            if lyr.name()[:5] == 'Nodos':
                width = 2 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(point.x() - width, point.y() - width, point.x() + width, point.y() + width)
                #rect = self.mapCanvas.mapRenderer().mapToLayerCoordinates(lyr, rect)                
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    self.crearPoste(point, '1', ftr.id())
                    return

            if lyr.name()[:6] == 'Postes':
                width = 2 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(point.x() - width, point.y() - width, point.x() + width, point.y() + width)
                #rect = self.mapCanvas.mapRenderer().mapToLayerCoordinates(lyr, rect)
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    QMessageBox.warning(None, 'EnerGis 6', '❌ Ya hay un poste en esa posición')
                    return

            if lyr.name()[:6] == 'Lineas':
                width = 4 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(point.x() - width, point.y() - width, point.x() + width, point.y() + width)
                #rect = self.mapCanvas.mapRenderer().mapToLayerCoordinates(lyr, rect)
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    self.crearPoste(point, '2', ftr.id())
                    return

        self.crearPoste(point, '0', 0)
        if self.rubber_band:
            self.rubber_band.reset(QgsWkbTypes.PointGeometry)
            self.rubber_band = None
        self.resetMarker()

    def crearPoste(self, point, elemento_asociado, geoname_asociado):
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:6] == 'Postes':
                lyr.triggerRepaint()

        if self.proyecto!='<Proyecto>' and self.proyecto!='':
            from .frm_postes_proyecto import frmPostesProyecto
            dialogo = frmPostesProyecto(self.proyecto, self.tipo_usuario, self.mapCanvas, self.conn, self.tension, 0, elemento_asociado, geoname_asociado, self.zona, point)
            dialogo.exec()
        else:
            from .frm_postes import frmPostes
            dialogo = frmPostes(self.tipo_usuario, self.mapCanvas, self.conn, self.tension, 0, elemento_asociado, geoname_asociado, self.zona, point)
            dialogo.exec()

        if self.rubber_band:
            self.rubber_band.reset(QgsWkbTypes.PointGeometry)
            self.rubber_band = None
        self.resetMarker()
        dialogo.close()
