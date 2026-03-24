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
#from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsFeature, QgsPoint, QgsPointXY
import os

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrSeleccionAleatoria(QgsMapTool):
    def __init__(self, mapCanvas, conn):
        QgsMapTool.__init__(self, mapCanvas)
        self.mapCanvas = mapCanvas    
        self.conn = conn
        self.puntos = []
        self.rubber_band = None
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self.rubber_band:
                self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)
                self.rubber_band = None
                self.puntos = []
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.termino_seleccion(event)

    def canvasPressEvent(self, event):
        x = event.pos().x()
        y = event.pos().y()
        point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
        self.puntos.append(QgsPoint(point.x(),point.y()))
        pts = QgsGeometry.fromPolyline(self.puntos)
        str_pts = pts.asWkt()
        str_pts = str_pts.replace("LineString ","Polygon (") + ")"

        if event.button() == Qt.MouseButton.LeftButton:
            if self.rubber_band is None:
                self.rubber_band = QgsRubberBand(self.mapCanvas, QgsWkbTypes.PolygonGeometry)
                transparent_red = QColor(255, 0, 0, 50)
                self.rubber_band.setColor(transparent_red)
                self.rubber_band.setWidth(2)
            self.rubber_band.addPoint(point, True)
            self.rubber_band.show()

        elif event.button() == Qt.MouseButton.RightButton:
            self.termino_seleccion(event)

    def canvasMoveEvent(self, event):
        x = event.pos().x()
        y = event.pos().y()
        point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)

        if len(self.puntos)>0:
            self.rubber_band.reset(QgsWkbTypes.LineGeometry)
            self.rubber_band = None
            self.rubber_band = QgsRubberBand(self.mapCanvas, QgsWkbTypes.PolygonGeometry)
            transparent_red = QColor(255, 0, 0, 50)
            self.rubber_band.setColor(transparent_red)
            self.rubber_band.setWidth(2)
            self.puntos.append(QgsPoint(point.x(),point.y()))
            for punto in self.puntos:
                self.rubber_band.addPoint(QgsPointXY(punto.x(), punto.y()), True)
            self.rubber_band.show()
            self.puntos.pop()
        
    def canvasDoubleClickEvent(self, event):
        self.termino_seleccion(event)

    def termino_seleccion(self, event):
        #point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
        self.seleccion_n = []
        self.seleccion_l = []
        self.seleccion_p = []
        self.seleccion_a = []
        self.seleccion_c = []
        self.seleccion_e = []

        if len(self.puntos)<2:
            return

        #puntos.append(QgsPoint(point.x(),point.y()))
        self.puntos.append(self.puntos[0])

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

        self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)
        self.rubber_band = None

        #del puntos[:]
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
        return

    def verificar_visibilidad_capa(self, lyr):
        from qgis.core import QgsProject
        proyecto = QgsProject.instance()
        root = proyecto.layerTreeRoot()
        node = root.findLayer(lyr.id())
        if node is not None and node.isVisible():
            return True
        else:
            return False
