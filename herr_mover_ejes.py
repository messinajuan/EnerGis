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
from qgis.core import QgsRectangle, QgsFeatureRequest, QgsFeature, QgsMapLayerType
from qgis.core import QgsPoint
import os

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrMoverEjes(QgsMapTool):

    def __init__(self, mapCanvas, conn):
        QgsMapTool.__init__(self, mapCanvas)
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.p1 = QgsPoint()
        self.p2 = QgsPoint()
        self.ftrs_nodos = []
        self.ftrs_lineas = []
        self.ftrs_postes = []
        self.ftrs_areas = []
        self.ftrs_parcelas = []
        self.ftrs_ejes = []
        self.ftrs_cotas = []
        self.ftrs_anotaciones = []
        #snapping
        self.useSnapped = True
        self.snapper = None
        self.markerSnapped = None
        self.prj = QgsProject.instance()
        self.snapConfig = self.prj.snappingConfig()
        self.prj.snappingConfigChanged.connect(self.setSnapping)
        self.setSnapping(self.prj.snappingConfig())
        #armo las colecciones de objetos a mover en grupo
        n = mapCanvas.layerCount()
        layers = [mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name() == 'Ejes de Calle':
                for ftr in lyr.selectedFeatures():
                    self.ftrs_ejes.append(ftr.id())

        if len(self.ftrs_ejes) > 0:
            self.tipo_herramienta='muchos'
            from .frm_mover import frmMover
            self.dialogo = frmMover(self.mapCanvas, self.conn, self.ftrs_nodos, self.ftrs_lineas, self.ftrs_postes, self.ftrs_areas, self.ftrs_parcelas, self.ftrs_ejes, self.ftrs_cotas, self.ftrs_anotaciones)
            self.dialogo.setWindowFlags(self.dialogo.windowFlags() & Qt.CustomizeWindowHint)
            self.dialogo.setWindowFlags(self.dialogo.windowFlags() & -Qt.WindowMinMaxButtonsHint)
            self.dialogo.show()
        else:
            self.tipo_herramienta='uno'
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
        if self.tipo_herramienta=='muchos':
            return

    def canvasPressEvent(self, event):
        if self.tipo_herramienta=='muchos':
            return
        if event.button() == Qt.MouseButton.RightButton:
            return
        self.elmt = ''
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                if lyr.name() == 'Ejes de Calle':
                    width = 5 * self.mapCanvas.mapUnitsPerPixel()
                    rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                    int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                    ftrs = lyr.getFeatures(int)
                    for ftr in ftrs:
                        geom = ftr.geometry()
                        self.ftr = ftr
                        vertices  = geom.asPolyline()
                        for i in range(len(vertices)):
                            vertice=QgsPoint(vertices [i][0],vertices [i][1])
                            if abs(self.point.x()-vertices [i][0])<width and abs(self.point.y()-vertices [i][1])<width:
                                v = QgsFeature()
                                v.setGeometry(vertice)
                                self.p1 = QgsPoint(vertice.x(), vertice.y())
                                self.elmt = 'Vertice ' + str(i + 1)
                                return

    def canvasReleaseEvent(self, event):
        if self.tipo_herramienta=='muchos':
            return
        if self.elmt=='':
            return
        self.p2 = QgsPoint(self.point.x(), self.point.y())
        self.dx = self.p2.x() - self.p1.x()
        self.dy = self.p2.y() - self.p1.y()
        self.setSnapping(self.prj.snappingConfig())
        if self.elmt[:7]=='Vertice':
            str_vertice = self.elmt[8:]
            cnn = self.conn
            cursor = cnn.cursor()
            try:
                cursor.execute('mover_eje ' + str(self.ftr.id()) + ', ' + str_vertice + ', ' + str(self.dx) + ', ' + str(self.dy))
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudieron mover Ejes')
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            lyr.triggerRepaint()
        self.ftr = None
        self.p1 = None
        self.p2 = None
