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

from qgis.core import QgsWkbTypes
from PyQt6.QtWidgets import QMessageBox
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import QgsRectangle
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsPoint, QgsPointXY
import os

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrZoom(QgsMapTool):

    def __init__(self, mapCanvas, herramienta):
        QgsMapTool.__init__(self, mapCanvas)
        self.mapCanvas = mapCanvas    
        self.herramienta = herramienta
        self.ancho = 0
        self.alto = 0
        self.pcentro = QgsPointXY()
        self.p1 = QgsPoint()
        self.p2 = QgsPoint()
        self.rubber_band = None

    def canvasPressEvent(self, event):
        if event.button() == 1: #Boton izquierdo
            #Get the click
            x = event.pos().x()
            y = event.pos().y()
            self.p1 = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
            if self.herramienta == 'Pan':
                self.herramienta = 'Pon'
        else:
            self.mapCanvas.zoomOut()
            self.p1 = QgsPoint()
            self.p2 = QgsPoint()

    def canvasMoveEvent(self, event):
        if str(self.p1)=='<QgsPoint: Point EMPTY>':
            return
        #Get the click
        x = event.pos().x()
        y = event.pos().y()
        self.p2 = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)

        if self.herramienta == 'Pon':
            e = self.mapCanvas.extent()
            self.ancho = abs(e.xMaximum() - e.xMinimum())
            self.alto = abs(e.yMaximum() - e.yMinimum())
            xcentro = e.xMinimum() + (e.xMaximum() - e.xMinimum()) / 2
            ycentro = e.yMinimum() + (e.yMaximum() - e.yMinimum()) / 2            
            self.pcentro = QgsPointXY(xcentro, ycentro)

            #p3 es el nuevo centro del mapa, o sea el centro inicial + lo que se desplazó el mouse (p2 - p1)
            x3 = self.pcentro.x() - self.p2.x() + self.p1.x()
            y3 = self.pcentro.y() - self.p2.y() + self.p1.y()
            
            self.p3 = QgsPointXY(x3, y3)
            self.mapCanvas.setCenter(self.p3)
            self.mapCanvas.refresh()
            return

        if self.rubber_band:
            self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)
            self.rubber_band = None

        self.rubber_band = QgsRubberBand(self.mapCanvas, QgsWkbTypes.PolygonGeometry)
        transparent_red = QColor(255, 0, 0, 50)
        self.rubber_band.setColor(transparent_red)
        self.rubber_band.setWidth(2)

        self.rubber_band.addPoint(QgsPointXY(self.p1.x(), self.p1.y()), True)
        self.rubber_band.addPoint(QgsPointXY(self.p1.x(), self.p2.y()), True)
        self.rubber_band.addPoint(QgsPointXY(self.p2.x(), self.p2.y()), True)
        self.rubber_band.addPoint(QgsPointXY(self.p2.x(), self.p1.y()), True)

        self.rubber_band.show()

    def canvasReleaseEvent(self, event):
        if event.button() == 1: #Boton izquierdo
            if self.herramienta == 'Pon':
                self.mapCanvas.refresh()
                self.p1 = QgsPoint()
                self.p2 = QgsPoint()
                self.herramienta = 'Pan'
                return

            #Get the click
            x = event.pos().x()
            y = event.pos().y()
            self.p2 = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
            rect = QgsRectangle(self.p1.x(), self.p1.y(), self.p2.x(), self.p2.y())
            self.mapCanvas.setExtent(rect)
            self.mapCanvas.refresh()
            self.p1 = QgsPoint()
            self.p2 = QgsPoint()
            if self.rubber_band:
                self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)
                self.rubber_band = None
