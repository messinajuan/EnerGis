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

from qgis.core import QgsGeometry, QgsWkbTypes, QgsMapLayerType
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsFeature, QgsPoint, QgsPointXY
import os
import math

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrSeleccionCircular(QgsMapTool):
    def __init__(self, mapCanvas, conn):
        QgsMapTool.__init__(self, mapCanvas)
        self.mapCanvas = mapCanvas    
        self.conn = conn
        self.puntos = []
        self.centro = QgsPointXY()
        self.rubber_band = None
        self.dibujando = False
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self.rubber_band:
                self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)
                self.rubber_band = None
                self.puntos = []
            self.dibujando = False

    def canvasPressEvent(self, event):
        x = event.pos().x()
        y = event.pos().y()
        self.centro = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
        if self.dibujando == False:
            self.dibujando = True

    def canvasMoveEvent(self, event):
        if self.dibujando == False:
            return
        x = event.pos().x()
        y = event.pos().y()
        point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
        if self.rubber_band:
            self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)
            self.rubber_band = None
        self.puntos = []
        radio = point.distance(self.centro)
        # Crear la instancia de QgsRubberBand para una polilínea cerrada (Polygon)
        self.rubber_band = QgsRubberBand(self.mapCanvas, QgsWkbTypes.PolygonGeometry)
        transparent_red = QColor(255, 0, 0, 50)
        self.rubber_band.setColor(transparent_red)
        self.rubber_band.setWidth(2)
        # Generar los puntos que forman el círculo
        num_points = int(radio/1000) + 12  # Número de puntos para aproximar el círculo
        angle_step = 2 * math.pi / num_points
        for i in range(num_points + 1):  # +1 para cerrar el círculo
            angle = i * angle_step
            x = self.centro.x() + radio * math.cos(angle)
            y = self.centro.y() + radio * math.sin(angle)
            point = QgsPointXY(x, y)
            self.rubber_band.addPoint(point, True)
            self.puntos.append(QgsPoint(point.x(),point.y()))
        self.rubber_band.show()
        
    def canvasReleaseEvent(self, event):
        self.dibujando = True
        if len(self.puntos)<3:
            self.puntos=[]
            return
        self.termino_seleccion(event)
        self.dibujando = False

    def termino_seleccion(self, event):
        #point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
        self.seleccion_n = []
        self.seleccion_l = []
        self.seleccion_p = []
        self.seleccion_a = []
        self.seleccion_c = []
        self.seleccion_e = []
        pts = QgsGeometry.fromPolyline(self.puntos)
        str_pts = pts.asWkt()
        str_pts = str_pts.replace("LineString ","Polygon (") + ")"
        ftrArea = QgsFeature()
        ftrArea.setGeometry(QgsGeometry.fromWkt(str_pts))
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                lyr.removeSelection()
                if self.verificar_visibilidad_capa(lyr):
                    if lyr.name()[:5] == 'Nodos':
                        for ftr in lyr.getFeatures():
                            if ftrArea.geometry().intersects(ftr.geometry()):
                                self.seleccion_n.append(ftr.id())
                    if lyr.name()[:6] == 'Lineas':
                        for ftr in lyr.getFeatures():
                            if ftrArea.geometry().intersects(ftr.geometry()):
                                self.seleccion_l.append(ftr.id())
                    if lyr.name()[:6] == 'Postes':
                        for ftr in lyr.getFeatures():
                            if ftrArea.geometry().intersects(ftr.geometry()):
                                self.seleccion_p.append(ftr.id())
                    if lyr.name() == 'Areas':
                        for ftr in lyr.getFeatures():
                            if ftrArea.geometry().intersects(ftr.geometry()):
                                self.seleccion_a.append(ftr.id())
                    if lyr.name() == 'Parcelas':
                        for ftr in lyr.getFeatures():
                            if ftrArea.geometry().intersects(ftr.geometry()):
                                self.seleccion_c.append(ftr.id())
                    if lyr.name() == 'Ejes':
                        for ftr in lyr.getFeatures():
                            if ftrArea.geometry().intersects(ftr.geometry()):
                                self.seleccion_e.append(ftr.id())
        if self.rubber_band:
            self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)
            self.rubber_band = None
        self.puntos=[]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyr.select(self.seleccion_n)
            if lyr.name()[:6] == 'Lineas':
                lyr.select(self.seleccion_l)
            if lyr.name()[:6] == 'Postes':
                lyr.select(self.seleccion_p)
            if lyr.name() == 'Areas':
                lyr.select(self.seleccion_a)
            if lyr.name() == 'Parcelas':
                lyr.select(self.seleccion_c)
            if lyr.name() == 'Ejes':
                lyr.select(self.seleccion_e)

    def verificar_visibilidad_capa(self, lyr):
        from qgis.core import QgsProject
        proyecto = QgsProject.instance()
        root = proyecto.layerTreeRoot()
        node = root.findLayer(lyr.id())
        if node is not None and node.isVisible():
            return True
        else:
            return False
