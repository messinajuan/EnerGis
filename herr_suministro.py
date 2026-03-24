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

from PyQt6.QtWidgets import QMessageBox
from qgis.gui import QgsMapTool
from qgis.core import QgsRectangle, QgsFeatureRequest
import os

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrSuministro(QgsMapTool):

    def __init__(self, energis6, mapCanvas, conn, tension, suministro):
        QgsMapTool.__init__(self, mapCanvas)
        self.energis6 = energis6
        self.mapCanvas = mapCanvas    
        self.conn = conn
        self.tension = tension
        self.suministro = suministro

    def canvasMoveEvent(self, event):
        x = event.pos().x()
        y = event.pos().y()
        self.point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
        
    def canvasReleaseEvent(self, event):
        from datetime import datetime

        x_coord = self.point.x()
        y_coord = self.point.y()

        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        id_zona = 0
        for lyr in layers:
            if lyr.name() == 'Areas':
                width = 5 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                #rect = self.mapCanvas.mapRenderer().mapToLayerCoordinates(lyr, rect)
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    id_zona = ftr.id()

        zona = 'Rural'
        localidad = 1
        subzona =''
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT Nombre, Localidad, Descripcion FROM Areas WHERE geoname=" + str(id_zona))
        #convierto el cursor en array
        rs = tuple(cursor)
        cursor.close()
        if len(rs)>0:
            zona = rs[0][0]
            localidad = rs[0][1]
            subzona = rs[0][2]

        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT Valor FROM Configuracion WHERE Variable='SRID'")
        rows = cursor.fetchall()
        cursor.close()
        srid = rows[0][0]
        obj = "geometry::Point(" + str(x_coord) + ',' + str(y_coord) + ',' + srid + ")"

        cnn = self.conn
        cnn.autocommit = False
        cursor = cnn.cursor()
        cursor.execute("SELECT iid FROM iid")
        iid = tuple(cursor)
        id = iid[0][0] + 1
        cursor.execute("UPDATE iid SET iid =" + str(id))
        cnn.commit()
        cursor = cnn.cursor()
        cursor.execute("SELECT MAX(Aux) FROM Nodos")
        auxnodos = tuple(cursor)
        cursor.close()
        if auxnodos[0][0]==None:
            aux = 1
        else:
            aux = auxnodos[0][0] + 1
        cursor = cnn.cursor()
        str_valores = str(id) + ", "
        str_valores = str_valores + "'','', "
        str_valores = str_valores + "6, "
        str_valores = str_valores + str(x_coord) + ", "
        str_valores = str_valores + str(y_coord) + ", "
        str_valores = str_valores + "'35-Map Symbols-0-33023-3-0', "
        str_valores = str_valores + "'','','','','', "
        str_valores = str_valores + "0, "
        str_valores = str_valores + str(self.tension) + ", "
        str_valores = str_valores + "'" + zona + "', "
        str_valores = str_valores + "'', "
        str_valores = str_valores + str(aux) + ", "
        str_valores = str_valores + "'" + datetime.now().strftime("%Y%m%d") + "', "
        str_valores = str_valores + "'" + subzona + "', "
        str_valores = str_valores + "6, "
        str_valores = str_valores + str(localidad) + ", "
        str_valores = str_valores + "'', "
        str_valores = str_valores + obj
        try:
            cursor.execute("INSERT INTO Nodos (Geoname, Nombre, Descripcion, Elmt, XCoord, YCoord, Estilo, Val1, Val2, Val3, Val4, Val5, Nivel, Tension, Zona, Alimentador, Aux, Modificacion, Subzona, Estado, Localidad, UUCC, obj) VALUES (" + str_valores + ")")
            cursor.execute("INSERT INTO Suministros (id_nodo, id_suministro) VALUES (" + str(id) + ",'" + self.suministro + "')")
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.critical(None, 'EnerGis 6', '❌ No se pudo insertar en la Base de Datos')

        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyr.triggerRepaint()

        self.energis6.h_seleccion()
