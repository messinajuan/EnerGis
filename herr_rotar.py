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

from PyQt6 import QtCore
#from PyQt6.QtWidgets import QMessageBox
from qgis.gui import QgsMapTool
from qgis.core import QgsPoint
import os

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrRotar(QgsMapTool):

    def __init__(self, mapCanvas, conn):
        QgsMapTool.__init__(self, mapCanvas)
        self.mapCanvas = mapCanvas    
        self.conn = conn
        self.p1 = QgsPoint()
        self.ftrs_nodos = []
        self.ftrs_lineas = []
        self.ftrs_postes = []
        self.ftrs_areas = []
        self.ftrs_parcelas = []
        self.ftrs_ejes = []
        self.ftrs_cotas = []
        self.ftrs_anotaciones = []
        self.angulo = 0

        n = mapCanvas.layerCount()
        layers = [mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                for ftr in lyr.selectedFeatures():
                    self.ftrs_nodos.append(ftr.id())
            if lyr.name()[:6] == 'Lineas':
                for ftr in lyr.selectedFeatures():
                    self.ftrs_lineas.append(ftr.id())
            if lyr.name()[:6] == 'Postes':
                for ftr in lyr.selectedFeatures():
                    self.ftrs_postes.append(ftr.id())
            if lyr.name() == 'Areas':
                for ftr in lyr.selectedFeatures():
                    self.ftrs_areas.append(ftr.id())
            if lyr.name() == 'Parcelas':
                for ftr in lyr.selectedFeatures():
                    self.ftrs_parcelas.append(ftr.id())
            if lyr.name() == 'Cotas':
                for ftr in lyr.selectedFeatures():
                    self.ftrs_cotas.append(ftr.id())
            if lyr.name() == 'Anotaciones':
                for ftr in lyr.selectedFeatures():
                    self.ftrs_anotaciones.append(ftr.id())

    def canvasPressEvent(self, event):
        #Get the click
        x = event.pos().x()
        y = event.pos().y()
        point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
        
        self.pc = QgsPoint(point.x(), point.y())

        if len(self.ftrs_nodos) + len(self.ftrs_lineas) + len(self.ftrs_areas) + len(self.ftrs_parcelas) + len(self.ftrs_cotas) + len(self.ftrs_anotaciones) > 0:
            from .frm_rotar import frmRotar
            self.dialogo = frmRotar(self.mapCanvas, self.conn, self.ftrs_nodos, self.ftrs_lineas, self.ftrs_postes, self.ftrs_areas, self.ftrs_parcelas, self.ftrs_ejes, self.ftrs_cotas, self.ftrs_anotaciones, self.pc)
            self.dialogo.setWindowFlags(self.dialogo.windowFlags() & QtCore.Qt.CustomizeWindowHint)
            self.dialogo.setWindowFlags(self.dialogo.windowFlags() & ~QtCore.Qt.WindowMinMaxButtonsHint)
            self.dialogo.show()
