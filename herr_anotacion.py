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
from PyQt6.QtWidgets import QMessageBox, QInputDialog
from PyQt6.QtCore import Qt
from qgis.gui import QgsMapTool
import os

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrAnotacion(QgsMapTool):

    def __init__(self, proyecto, tipo_usuario, mapCanvas, conn):
        QgsMapTool.__init__(self, mapCanvas)
        self.proyecto = proyecto
        self.tipo_usuario = tipo_usuario
        self.mapCanvas = mapCanvas    
        self.conn = conn

        #selcolor = self.mapCanvas.selectionColor()
        #mycolor = QColor(selcolor.red(), selcolor.green(), selcolor.blue(), 40)
        #self.rb = QgsRubberBand(self.mapCanvas, QgsWkbTypes.PolygonGeometry)
        #self.rb.setStrokeColor(QColor(255, 0, 0, 40))
        #self.rb.setFillColor(mycolor)
        #self.rb.setLineStyle(Qt.PenStyle(Qt.SolidLine))
        #self.rb.setWidth(5)

        #snapping
        self.useSnapped = True
        self.snapper = None
        self.markerSnapped = None
        self.prj = QgsProject.instance()
        self.snapConfig = self.prj.snappingConfig()
        self.prj.snappingConfigChanged.connect(self.setSnapping)
        self.setSnapping(self.prj.snappingConfig())
        pass

    def setSnapping(self, config):
        self.snapConfig = config
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
        #if self.snapConfig.enabled() and self.useSnapped:
        if self.useSnapped:
            self.isSnapped()
        else:
            self.resetMarker()

    def keyPressEvent(self, event):
        if str(event.key()) == '16777249':
            self.tecla = 'Ctrl'
            
    def keyReleaseEvent(self, event):
        self.tecla = ''

    def canvasReleaseEvent(self, event):
        #hacemos que se agregue inicialmente en una capa de memoria !!!
        x_coord = self.point.x()
        y_coord = self.point.y()
        etiqueta = ''
        text, ok = QInputDialog.getText(self.mapCanvas, 'Ingreso de Datos', 'Ingrese Anotación')
        if ok:
            etiqueta=str(text)
        else:
            return
        if etiqueta=='':
            return
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT Valor FROM Configuracion WHERE Variable='SRID'")
        rows = cursor.fetchall()
        cursor.close()
        srid = rows[0][0]
        obj = "geometry::Point(" + str(x_coord) + ',' + str(y_coord) + ',' + srid + ")"
        id = 1
        try:
            cnn = self.conn
            cnn.autocommit = False
            cursor = cnn.cursor()
            cursor.execute("SELECT MAX(geoname) FROM Anotaciones")
            iid = tuple(cursor)
            id = iid[0][0] + 1
        except:
            pass
        cursor = cnn.cursor()
        str_valores = str(id) + ", "
        str_valores = str_valores + "'" + self.proyecto + "', "
        str_valores = str_valores + "'" + etiqueta + "', "
        str_valores = str_valores + obj
        try:
            cursor.execute("INSERT INTO Anotaciones (geoname, proyecto, etiqueta, obj) VALUES (" + str_valores + ")")
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.critical(None, 'EnerGis 6', '❌ No se pudo insertar en la Base de Datos')
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name() == 'Anotaciones':
                lyr.triggerRepaint()
