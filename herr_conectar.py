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

from qgis.core import QgsProject, QgsGeometry, QgsMapLayerType, QgsSnappingUtils, QgsWkbTypes
from qgis.gui import QgsVertexMarker, QgsRubberBand
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt
from qgis.gui import QgsMapTool
from qgis.core import QgsPoint, QgsPointXY, QgsRectangle, QgsFeatureRequest, QgsFeature
import os

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrConectar(QgsMapTool):

    def __init__(self, mapCanvas, conn):
        QgsMapTool.__init__(self, mapCanvas)
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.geoname_primer_nodo = 0
        self.tension = '0'
        self.p1 = QgsPoint()
        self.p2 = QgsPoint()
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

    def canvasPressEvent(self, event):
        x = event.pos().x()
        y = event.pos().y()
        self.point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)

        if self.snapConfig.enabled() and self.useSnapped:
            self.isSnapped()

        self.geoname_primer_nodo = 0
        self.tension = '0'
        self.p1 = QgsPoint()
        self.p2 = QgsPoint()
        
        #tengo que detectar si hay nodo en el primer click -> conectar
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                if lyr.name()[:5] == 'Nodos':
                    width = 5 * self.mapCanvas.mapUnitsPerPixel()
                    rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                    int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                    ftrs = lyr.getFeatures(int)
                    i = 0
                    for ftr in ftrs:
                        i = i + 1
                    if i > 0:
                        geom = ftr.geometry()
                        if geom.asPoint().x() > 0:
                            self.p1 = QgsPoint(geom.asPoint().x(),geom.asPoint().y())
                            self.geoname_primer_nodo = ftr.id()
                            self.tension = lyr.name() [6 - len(lyr.name()):]
                            return

        #sino es la herramienta de cortar línea
        self.p1 = QgsPoint(self.point.x(), self.point.y())
        pass

    def canvasMoveEvent(self, event):
        if self.p1.x()==0:
            return
        #Get the pos
        x = event.pos().x()
        y = event.pos().y()
        self.point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
        self.p2 = QgsPoint(self.point.x(), self.point.y())
        if self.snapConfig.enabled() and self.useSnapped:
            self.isSnapped()
        self.puntos = []
        self.puntos.append(self.p1)
        self.puntos.append(self.p2)

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
        
    def canvasReleaseEvent(self, event):
        x = event.pos().x()
        y = event.pos().y()
        self.point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
        self.p2 = QgsPoint(self.point.x(), self.point.y())
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        
        puntos = []
        puntos.append(self.p1)
        puntos.append(self.p2)

        #blanqueo los puntos para que se reinicie la herramienta
        self.p1 = QgsPoint()
        self.p2 = QgsPoint()

        pts = QgsGeometry.fromPolyline(puntos)
        ftrLinea = QgsFeature()
        ftrLinea.setGeometry(pts)

        linea_a_borrar="0"
        for lyr in layers:
            if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                if linea_a_borrar=="0":
                    if self.tension != '0':
                        #creo 3 lineas
                        if lyr.name() == 'Lineas ' + self.tension:
                            #para cada objeto de la capa (luego sera de lo que haya en el entorno de la linea que tracé)
                            for f in lyr.getFeatures():
                                if linea_a_borrar=="0":
                                    #algunas veces intesecta a la linea que toca al nodo desde, entonces paso de largo las lineas donde desde o hasta = p1
                                    pts = f.geometry().asPolyline()
                                    b_existe = False
                                    if round(pts[0][0], 1) == round(puntos[0].x(), 1) and round(pts[0][1], 1) == round(puntos[0].y(), 1):
                                        b_existe = True
                                    n = len(pts)
                                    if round(pts[n - 1][0], 1) == round(puntos[0].x(), 1) and round(pts[n - 1][1], 1) == round(puntos[0].y(), 1):
                                        b_existe = True
                                    #si p1 toca a la linea en alguno de sus extremos la paso de largo !
                                    if b_existe == False:
                                        if ftrLinea.geometry().intersects(f.geometry()):
                                            linea_a_borrar = str(f.id())
                                            #pts contiene los quiebres de la linea intersectada
                                            tramo_cruce = 0
                                            nuevo_nodo = QgsFeature()
                                            for q in range (1, len(pts)):
                                                tramo = []
                                                tramo.append(QgsPoint(pts[q][0],pts[q][1]))
                                                tramo.append(QgsPoint(pts[q - 1][0],pts[q - 1][1]))
                                                pts_tramo = QgsGeometry.fromPolyline(tramo)
                                                t = QgsFeature()
                                                t.setGeometry(pts_tramo)
                                                if ftrLinea.geometry().intersects(t.geometry()):
                                                    intersection = ftrLinea.geometry().intersection(t.geometry())
                                                    tramo_cruce = q
                                                    nuevo_nodo = intersection
                                            if tramo_cruce == 0:
                                                return
                                            #Si hubo cruce entre tramo y linea, creo el nodo
                                            cnn = self.conn
                                            cursor = cnn.cursor()
                                            cursor.execute("SELECT fase, elmt, desde, hasta, estilo, zona, alimentador, exp, disposicion, conservacion, Convert(CHAR(8),modificacion,112) AS modificacion, uucc, ternas FROM Lineas WHERE geoname=" + str(f.id()))
                                            rows = cursor.fetchall()
                                            cursor.close()
                                            for row in rows:
                                                fase = str(row[0])
                                                elmt = str(row[1])
                                                geoname_desde = str(row[2])
                                                geoname_hasta = str(row[3])
                                                estilo = str(row[4])
                                                zona = str(row[5])
                                                alimentador = str(row[6])
                                                expediente = str(row[7])
                                                disposicion = str(row[8])
                                                conservacion = str(row[9])
                                                modificacion = str(row[10])
                                                uucc = str(row[11])
                                                ternas = str(row[12])
                                            cnn = self.conn
                                            cursor = cnn.cursor()
                                            cursor.execute("SELECT subzona, ISNULL(localidad, 0) FROM Nodos WHERE geoname=" + geoname_desde)
                                            rows = cursor.fetchall()
                                            cursor.close()
                                            for row in rows:
                                                subzona = str(row[0])
                                                localidad = str(row[1])
                                            #-----------------------------------------------------------
                                            #-----------------------------------------------------------
                                            #Creacion del nuevo nodo
                                            #-----------------------------------------------------------
                                            #-----------------------------------------------------------
                                            x_coord = nuevo_nodo.asPoint().x()
                                            y_coord = nuevo_nodo.asPoint().y()

                                            cnn = self.conn
                                            cursor = cnn.cursor()
                                            cursor.execute("SELECT TOP 1 obj.STSrid FROM nodos")
                                            rows = cursor.fetchall()
                                            cursor.close()
                                            for row in rows:
                                                srid = str(row[0])
                                            if srid == '':
                                                srid = lyr.crs().authid()
                                                srid = srid [len(srid)-5:] #5: EPSG:
                                            obj = "geometry::Point(" + str(x_coord) + ',' + str(y_coord) + ',' + srid + ")"

                                            cnn = self.conn
                                            cursor = cnn.cursor()
                                            cursor.execute("SELECT iid FROM iid")
                                            iid = tuple(cursor)
                                            id = iid[0][0] + 1
                                            cursor.execute("UPDATE iid SET iid =" + str(id))
                                            cnn.commit()
                                            geoname_nuevo_nodo = id
                                            cnn = self.conn
                                            cnn.autocommit = False
                                            cursor = cnn.cursor()
                                            str_valores = str(id) + ", "
                                            str_valores = str_valores + "'', '', 0, "
                                            str_valores = str_valores + str(x_coord) + ", "
                                            str_valores = str_valores + str(y_coord) + ", "
                                            str_valores = str_valores + "'35-EnerGIS-16777215-0-2-0', "
                                            str_valores = str_valores + "'', "
                                            str_valores = str_valores + "'', "
                                            str_valores = str_valores + "'', "
                                            str_valores = str_valores + "'', "
                                            str_valores = str_valores + "'', "
                                            str_valores = str_valores + "0, "
                                            if self.tension.strip() == 'Proyectos':
                                                str_valores = str_valores + "0, "
                                            else:
                                                str_valores = str_valores + self.tension + ", "
                                            str_valores = str_valores + "'" + zona + "', "
                                            str_valores = str_valores + "'" + alimentador + "', "
                                            str_valores = str_valores + "0, "
                                            str_valores = str_valores + "'" + modificacion + "', "
                                            str_valores = str_valores + "'" + subzona + "', "
                                            str_valores = str_valores + "0, "
                                            str_valores = str_valores + obj + ", "
                                            str_valores = str_valores + localidad + ", "
                                            str_valores = str_valores + "''"
                                            try:
                                                cursor.execute("INSERT INTO Nodos (Geoname, Nombre, Descripcion, Elmt, XCoord, YCoord, Estilo, Val1, Val2, Val3, Val4, Val5, Nivel, Tension, Zona, Alimentador, Aux, Modificacion, Subzona, Estado, obj, Localidad, UUCC) VALUES (" + str_valores + ")")
                                                cnn.commit()
                                            except:
                                                cnn.rollback()
                                                QMessageBox.critical(None, 'EnerGis 6', '❌ No se pudo insertar el Nodo')
                                            #-----------------------------------------------------------
                                            #-----------------------------------------------------------
                                            nueva_linea_1 = []
                                            nueva_linea_2 = []
                                            nueva_linea_3 = []
                                            #una vez creado el nodo podemos crear las lineas
                                            p = QgsPoint(pts[0].x(),pts[0].y())
                                            nueva_linea_1.append(p)
                                            for q in range (1, tramo_cruce):
                                                p = QgsPoint(pts[q].x(),pts[q].y())
                                                nueva_linea_1.append(p)
                                            #a la primer linea le agrego el nuevo nodo
                                            p = QgsPoint(nuevo_nodo.asPoint().x(), nuevo_nodo.asPoint().y())
                                            nueva_linea_1.append(p)
                                            #la tercer linea va del nodo inicial al nuevo nodo
                                            r = QgsPoint(puntos[0].x(),puntos[0].y())
                                            nueva_linea_3.append(r)
                                            nueva_linea_3.append(p)
                                            #arranco la segunda linea con el nuevo nodo
                                            nueva_linea_2.append(p)
                                            for q in range (tramo_cruce, len(pts)):
                                                p = QgsPoint(pts[q].x(),pts[q].y())
                                                nueva_linea_2.append(p)
                                            #-----------------------------------------------------------
                                            #-----------------------------------------------------------
                                            #Creacion de la nueva linea 1
                                            #-----------------------------------------------------------
                                            #-----------------------------------------------------------
                                            pts = QgsGeometry.fromPolyline(nueva_linea_1)
                                            ftrLinea = QgsFeature()
                                            ftrLinea.setGeometry(pts)
                                            longitud = ftrLinea.geometry().length()
                                            geom = ftrLinea.geometry()
                                            obj = "geometry::STGeomFromText('" + geom.asWkt()  + "', " + srid + ")"
                                            cnn = self.conn
                                            cursor = cnn.cursor()
                                            cursor.execute("SELECT iid FROM iid")
                                            iid = tuple(cursor)
                                            id = iid[0][0] + 1
                                            cursor.execute("UPDATE iid SET iid =" + str(id))
                                            cnn.commit()
                                            cnn = self.conn
                                            cnn.autocommit = False
                                            cursor = cnn.cursor()
                                            str_valores = str(id) + ", "
                                            str_valores = str_valores + "'" + fase + "', "
                                            str_valores = str_valores + elmt + ", "
                                            str_valores = str_valores + str(geoname_desde) + ", "
                                            str_valores = str_valores + str(geoname_nuevo_nodo) + ", "
                                            str_valores = str_valores + "'" + "" + "', " #Quiebres
                                            str_valores = str_valores + str(longitud) + ", "
                                            str_valores = str_valores + "'" + estilo + "', "
                                            if self.tension.strip() == 'Proyectos':
                                                str_valores = str_valores + "0, "
                                            else:
                                                str_valores = str_valores + self.tension + ", "
                                            str_valores = str_valores + "'" + zona + "', "
                                            str_valores = str_valores + "'" + alimentador + "', "
                                            str_valores = str_valores + "0, " #Aux
                                            str_valores = str_valores + "'" + modificacion + "', "
                                            str_valores = str_valores + "'" + expediente + "', "
                                            str_valores = str_valores + "'" + disposicion + "', "
                                            str_valores = str_valores + "'" + conservacion + "', "
                                            str_valores = str_valores + "'" + ternas + "', "
                                            str_valores = str_valores + "0, "
                                            str_valores = str_valores + "'" + uucc + "', "
                                            str_valores = str_valores + obj
                                            try:
                                                cursor.execute("INSERT INTO Lineas (Geoname, Fase, Elmt, Desde, Hasta, Quiebres, Longitud, Estilo, Tension, Zona, Alimentador, Aux, Modificacion, Exp, Disposicion, Conservacion, Ternas, Acometida, UUCC, obj) VALUES (" + str_valores + ")")
                                                cnn.commit()
                                            except:
                                                cnn.rollback()
                                                QMessageBox.critical(None, 'EnerGis 6', '❌ No se pudo insertar la Linea 1')
                                            #-----------------------------------------------------------
                                            #-----------------------------------------------------------

                                            #-----------------------------------------------------------
                                            #-----------------------------------------------------------
                                            #Creacion de la nueva linea 2
                                            #-----------------------------------------------------------
                                            #-----------------------------------------------------------
                                            pts = QgsGeometry.fromPolyline(nueva_linea_2)
                                            ftrLinea = QgsFeature()
                                            ftrLinea.setGeometry(pts)
                                            longitud = ftrLinea.geometry().length()
                                            geom = ftrLinea.geometry()
                                            obj = "geometry::STGeomFromText('" + geom.asWkt()  + "', " + srid + ")"
                                            cnn = self.conn
                                            cursor = cnn.cursor()
                                            cursor.execute("SELECT iid FROM iid")
                                            iid = tuple(cursor)
                                            id = iid[0][0] + 1
                                            cursor.execute("UPDATE iid SET iid =" + str(id))
                                            cnn.commit()
                                            cnn = self.conn
                                            cnn.autocommit = False
                                            cursor = cnn.cursor()
                                            str_valores = str(id) + ", "
                                            str_valores = str_valores + "'" + fase + "', "
                                            str_valores = str_valores + elmt + ", "
                                            str_valores = str_valores + str(geoname_nuevo_nodo) + ", "
                                            str_valores = str_valores + str(geoname_hasta) + ", "
                                            str_valores = str_valores + "'" + "" + "', " #Quiebres
                                            str_valores = str_valores + str(longitud) + ", "
                                            str_valores = str_valores + "'" + estilo + "', "
                                            if self.tension.strip() == 'Proyectos':
                                                str_valores = str_valores + "0, "
                                            else:
                                                str_valores = str_valores + self.tension + ", "
                                            str_valores = str_valores + "'" + zona + "', "
                                            str_valores = str_valores + "'" + alimentador + "', "
                                            str_valores = str_valores + "0, " #Aux
                                            str_valores = str_valores + "'" + modificacion + "', "
                                            str_valores = str_valores + "'" + expediente + "', "
                                            str_valores = str_valores + "'" + disposicion + "', "
                                            str_valores = str_valores + "'" + conservacion + "', "
                                            str_valores = str_valores + "'" + ternas + "', "
                                            str_valores = str_valores + "0, "
                                            str_valores = str_valores + "'" + uucc + "', "
                                            str_valores = str_valores + obj
                                            try:
                                                cursor.execute("INSERT INTO Lineas (Geoname, Fase, Elmt, Desde, Hasta, Quiebres, Longitud, Estilo, Tension, Zona, Alimentador, Aux, Modificacion, Exp, Disposicion, Conservacion, Ternas, Acometida, UUCC, obj) VALUES (" + str_valores + ")")
                                                cnn.commit()
                                            except:
                                                cnn.rollback()
                                                QMessageBox.critical(None, 'EnerGis 6', '❌ No se pudo insertar la Linea 2')
                                            #-----------------------------------------------------------
                                            #-----------------------------------------------------------

                                            #-----------------------------------------------------------
                                            #-----------------------------------------------------------
                                            #Creacion de la nueva linea 3, la realmente nueva
                                            #-----------------------------------------------------------
                                            #-----------------------------------------------------------
                                            pts = QgsGeometry.fromPolyline(nueva_linea_3)
                                            ftrLinea = QgsFeature()
                                            ftrLinea.setGeometry(pts)
                                            longitud = ftrLinea.geometry().length()
                                            geom = ftrLinea.geometry()
                                            obj = "geometry::STGeomFromText('" + geom.asWkt()  + "', " + srid + ")"
                                            cnn = self.conn
                                            cursor = cnn.cursor()
                                            cursor.execute("SELECT iid FROM iid")
                                            iid = tuple(cursor)
                                            id = iid[0][0] + 1
                                            cursor.execute("UPDATE iid SET iid =" + str(id))
                                            cnn.commit()
                                            cnn = self.conn
                                            cnn.autocommit = False
                                            cursor = cnn.cursor()
                                            str_valores = str(id) + ", "
                                            str_valores = str_valores + "'" + fase + "', "
                                            str_valores = str_valores + elmt + ", "
                                            str_valores = str_valores + str(self.geoname_primer_nodo) + ", "
                                            str_valores = str_valores + str(geoname_nuevo_nodo) + ", "
                                            str_valores = str_valores + "'" + "" + "', " #Quiebres
                                            str_valores = str_valores + str(longitud) + ", "
                                            str_valores = str_valores + "'" + estilo + "', "
                                            if self.tension.strip() == 'Proyectos':
                                                str_valores = str_valores + "0, "
                                            else:
                                                str_valores = str_valores + self.tension + ", "
                                            str_valores = str_valores + "'" + zona + "', "
                                            str_valores = str_valores + "'" + alimentador + "', "
                                            str_valores = str_valores + "0, " #Aux
                                            str_valores = str_valores + "'" + modificacion + "', "
                                            str_valores = str_valores + "'" + expediente + "', "
                                            str_valores = str_valores + "'" + disposicion + "', "
                                            str_valores = str_valores + "'" + conservacion + "', "
                                            str_valores = str_valores + "'" + ternas + "', "
                                            str_valores = str_valores + "0, "
                                            str_valores = str_valores + "'" + uucc + "', "
                                            str_valores = str_valores + obj
                                            try:
                                                cursor.execute("INSERT INTO Lineas (Geoname, Fase, Elmt, Desde, Hasta, Quiebres, Longitud, Estilo, Tension, Zona, Alimentador, Aux, Modificacion, Exp, Disposicion, Conservacion, Ternas, Acometida, UUCC, obj) VALUES (" + str_valores + ")")
                                                cnn.commit()
                                            except:
                                                cnn.rollback()
                                                QMessageBox.critical(None, 'EnerGis 6', '❌ No se pudo insertar la Linea 3')
                    else:
                        #creo 2 lineas
                        if lyr.name()[:7] == 'Lineas ':
                            for f in lyr.getFeatures():
                                if linea_a_borrar=="0":
                                    #esto se hizo para salvar un error de ftr nulo
                                    try:
                                        pts = f.geometry().asPolyline()
                                    except:
                                        pass
                                    #algunas veces intesecta a la linea que toca al nodo desde, entonces paso de largo las lineas donde: desde ó hasta = p1
                                    if ftrLinea.geometry().intersects(f.geometry()):
                                        self.tension = lyr.name() [6 - len(lyr.name()):]
                                        linea_a_borrar = str(f.id())
                                        #pts contiene los quiebres de la linea intersectada
                                        tramo_cruce = 0
                                        nuevo_nodo = QgsFeature()
                                        for q in range (1, len(pts)):
                                            tramo = []
                                            tramo.append(QgsPoint(pts[q][0],pts[q][1]))
                                            tramo.append(QgsPoint(pts[q - 1][0],pts[q - 1][1]))
                                            pts_tramo = QgsGeometry.fromPolyline(tramo)
                                            t = QgsFeature()
                                            t.setGeometry(pts_tramo)
                                            if ftrLinea.geometry().intersects(t.geometry()):
                                                intersection = ftrLinea.geometry().intersection(t.geometry())
                                                tramo_cruce = q
                                                nuevo_nodo = intersection
                                        if tramo_cruce == 0:
                                            return
                                        #Si hubo cruce entre tramo y linea, creo el nodo
                                        cnn = self.conn
                                        cursor = cnn.cursor()
                                        cursor.execute("SELECT fase, elmt, desde, hasta, estilo, zona, alimentador, exp, disposicion, conservacion, Convert(CHAR(8),modificacion,112) AS modificacion, uucc, ternas FROM Lineas WHERE geoname=" + str(f.id()))
                                        rows = cursor.fetchall()
                                        cursor.close()
                                        for row in rows:
                                            fase = str(row[0])
                                            elmt = str(row[1])
                                            geoname_desde = str(row[2])
                                            geoname_hasta = str(row[3])
                                            estilo = str(row[4])
                                            zona = str(row[5])
                                            alimentador = str(row[6])
                                            expediente = str(row[7])
                                            disposicion = str(row[8])
                                            conservacion = str(row[9])
                                            modificacion = str(row[10])
                                            uucc = str(row[11])
                                            ternas = str(row[12])
                                        cnn = self.conn
                                        cursor = cnn.cursor()
                                        cursor.execute("SELECT subzona, ISNULL(localidad, 0) FROM Nodos WHERE geoname=" + geoname_desde)
                                        rows = cursor.fetchall()
                                        cursor.close()
                                        for row in rows:
                                            subzona = str(row[0])
                                            localidad = str(row[1])
                                        #-----------------------------------------------------------
                                        #-----------------------------------------------------------
                                        #Creacion del nuevo nodo
                                        #-----------------------------------------------------------
                                        #-----------------------------------------------------------
                                        x_coord = nuevo_nodo.asPoint().x()
                                        y_coord = nuevo_nodo.asPoint().y()
                                        cnn = self.conn
                                        cursor = cnn.cursor()
                                        cursor.execute("SELECT TOP 1 obj.STSrid FROM nodos")
                                        rows = cursor.fetchall()
                                        cursor.close()
                                        for row in rows:
                                            srid = str(row[0])
                                        if srid == '':
                                            srid = lyr.crs().authid()
                                            srid = srid [len(srid)-5:] #5: EPSG:
                                        obj = "geometry::Point(" + str(x_coord) + ',' + str(y_coord) + ',' + srid + ")"
                                        cnn = self.conn
                                        cursor = cnn.cursor()
                                        cursor.execute("SELECT iid FROM iid")
                                        iid = tuple(cursor)
                                        id = iid[0][0] + 1
                                        cursor.execute("UPDATE iid SET iid =" + str(id))
                                        cnn.commit()
                                        geoname_nuevo_nodo = id
                                        cnn = self.conn
                                        cnn.autocommit = False
                                        cursor = cnn.cursor()
                                        str_valores = str(id) + ", "
                                        str_valores = str_valores + "'', '', 0, "
                                        str_valores = str_valores + str(x_coord) + ", "
                                        str_valores = str_valores + str(y_coord) + ", "
                                        str_valores = str_valores + "'35-EnerGIS-16777215-0-2-0', "
                                        str_valores = str_valores + "'', "
                                        str_valores = str_valores + "'', "
                                        str_valores = str_valores + "'', "
                                        str_valores = str_valores + "'', "
                                        str_valores = str_valores + "'', "
                                        str_valores = str_valores + "0, "
                                        if self.tension.strip() == 'Proyectos':
                                            str_valores = str_valores + "0, "
                                        else:
                                            str_valores = str_valores + self.tension + ", "
                                        str_valores = str_valores + "'" + zona + "', "
                                        str_valores = str_valores + "'" + alimentador + "', "
                                        str_valores = str_valores + "0, "
                                        str_valores = str_valores + "'" + modificacion + "', "
                                        str_valores = str_valores + "'" + subzona + "', "
                                        str_valores = str_valores + "0, "
                                        str_valores = str_valores + obj + ", "
                                        str_valores = str_valores + localidad + ", "
                                        str_valores = str_valores + "''"
                                        try:
                                            cursor.execute("INSERT INTO Nodos (Geoname, Nombre, Descripcion, Elmt, XCoord, YCoord, Estilo, Val1, Val2, Val3, Val4, Val5, Nivel, Tension, Zona, Alimentador, Aux, Modificacion, Subzona, Estado, obj, Localidad, UUCC) VALUES (" + str_valores + ")")
                                            cnn.commit()
                                        except:
                                            cnn.rollback()
                                            QMessageBox.critical(None, 'EnerGis 6', '❌ No se pudo insertar el Nodo')
                                        #-----------------------------------------------------------
                                        #-----------------------------------------------------------
                                        nueva_linea_1 = []
                                        nueva_linea_2 = []
                                        #una vez creado el nodo podemos crear las lineas
                                        p = QgsPoint(pts[0].x(),pts[0].y())
                                        nueva_linea_1.append(p)
                                        for q in range (1, tramo_cruce):
                                            p = QgsPoint(pts[q].x(),pts[q].y())
                                            nueva_linea_1.append(p)
                                        #a la primer linea le agrego el nuevo nodo
                                        p = QgsPoint(nuevo_nodo.asPoint().x(), nuevo_nodo.asPoint().y())
                                        nueva_linea_1.append(p)
                                        #arranco la segunda linea con el nuevo nodo
                                        nueva_linea_2.append(p)
                                        for q in range (tramo_cruce, len(pts)):
                                            p = QgsPoint(pts[q].x(),pts[q].y())
                                            nueva_linea_2.append(p)
                                        #-----------------------------------------------------------
                                        #-----------------------------------------------------------
                                        #Creacion de la nueva linea 1
                                        #-----------------------------------------------------------
                                        #-----------------------------------------------------------
                                        pts = QgsGeometry.fromPolyline(nueva_linea_1)
                                        ftrLinea = QgsFeature()
                                        ftrLinea.setGeometry(pts)
                                        longitud = ftrLinea.geometry().length()
                                        geom = ftrLinea.geometry()
                                        obj = "geometry::STGeomFromText('" + geom.asWkt()  + "', " + srid + ")"
                                        cnn = self.conn
                                        cursor = cnn.cursor()
                                        cursor.execute("SELECT iid FROM iid")
                                        iid = tuple(cursor)
                                        id = iid[0][0] + 1
                                        cursor.execute("UPDATE iid SET iid =" + str(id))
                                        cnn.commit()
                                        cnn = self.conn
                                        cnn.autocommit = False
                                        cursor = cnn.cursor()
                                        str_valores = str(id) + ", "
                                        str_valores = str_valores + "'" + fase + "', "
                                        str_valores = str_valores + elmt + ", "
                                        str_valores = str_valores + str(geoname_desde) + ", "
                                        str_valores = str_valores + str(geoname_nuevo_nodo) + ", "
                                        str_valores = str_valores + "'" + "" + "', " #Quiebres
                                        str_valores = str_valores + str(longitud) + ", "
                                        str_valores = str_valores + "'" + estilo + "', "
                                        if self.tension.strip() == 'Proyectos':
                                            str_valores = str_valores + "0, "
                                        else:
                                            str_valores = str_valores + self.tension + ", "
                                        str_valores = str_valores + "'" + zona + "', "
                                        str_valores = str_valores + "'" + alimentador + "', "
                                        str_valores = str_valores + "0, " #Aux
                                        str_valores = str_valores + "'" + modificacion + "', "
                                        str_valores = str_valores + "'" + expediente + "', "
                                        str_valores = str_valores + "'" + disposicion + "', "
                                        str_valores = str_valores + "'" + conservacion + "', "
                                        str_valores = str_valores + "'" + ternas + "', "
                                        str_valores = str_valores + "0, "
                                        str_valores = str_valores + "'" + uucc + "', "
                                        str_valores = str_valores + obj
                                        try:
                                            cursor.execute("INSERT INTO Lineas (Geoname, Fase, Elmt, Desde, Hasta, Quiebres, Longitud, Estilo, Tension, Zona, Alimentador, Aux, Modificacion, Exp, Disposicion, Conservacion, Ternas, Acometida, UUCC, obj) VALUES (" + str_valores + ")")
                                            cnn.commit()
                                        except:
                                            cnn.rollback()
                                            QMessageBox.critical(None, 'EnerGis 6', '❌ No se pudo insertar la Linea 1')
                                        #-----------------------------------------------------------
                                        #-----------------------------------------------------------

                                        #-----------------------------------------------------------
                                        #-----------------------------------------------------------
                                        #Creacion de la nueva linea 2
                                        #-----------------------------------------------------------
                                        #-----------------------------------------------------------
                                        pts = QgsGeometry.fromPolyline(nueva_linea_2)
                                        ftrLinea = QgsFeature()
                                        ftrLinea.setGeometry(pts)
                                        longitud = ftrLinea.geometry().length()
                                        geom = ftrLinea.geometry()
                                        obj = "geometry::STGeomFromText('" + geom.asWkt()  + "', " + srid + ")"
                                        cnn = self.conn
                                        cursor = cnn.cursor()
                                        cursor.execute("SELECT iid FROM iid")
                                        iid = tuple(cursor)
                                        id = iid[0][0] + 1
                                        cursor.execute("UPDATE iid SET iid =" + str(id))
                                        cnn.commit()
                                        cnn = self.conn
                                        cnn.autocommit = False
                                        cursor = cnn.cursor()
                                        str_valores = str(id) + ", "
                                        str_valores = str_valores + "'" + fase + "', "
                                        str_valores = str_valores + elmt + ", "
                                        str_valores = str_valores + str(geoname_nuevo_nodo) + ", "
                                        str_valores = str_valores + str(geoname_hasta) + ", "
                                        str_valores = str_valores + "'" + "" + "', " #Quiebres
                                        str_valores = str_valores + str(longitud) + ", "
                                        str_valores = str_valores + "'" + estilo + "', "
                                        if self.tension.strip() == 'Proyectos':
                                            str_valores = str_valores + "0, "
                                        else:
                                            str_valores = str_valores + self.tension + ", "
                                        str_valores = str_valores + "'" + zona + "', "
                                        str_valores = str_valores + "'" + alimentador + "', "
                                        str_valores = str_valores + "0, " #Aux
                                        str_valores = str_valores + "'" + modificacion + "', "
                                        str_valores = str_valores + "'" + expediente + "', "
                                        str_valores = str_valores + "'" + disposicion + "', "
                                        str_valores = str_valores + "'" + conservacion + "', "
                                        str_valores = str_valores + "'" + ternas + "', "
                                        str_valores = str_valores + "0, "
                                        str_valores = str_valores + "'" + uucc + "', "
                                        str_valores = str_valores + obj
                                        try:
                                            cursor.execute("INSERT INTO Lineas (Geoname, Fase, Elmt, Desde, Hasta, Quiebres, Longitud, Estilo, Tension, Zona, Alimentador, Aux, Modificacion, Exp, Disposicion, Conservacion, Ternas, Acometida, UUCC, obj) VALUES (" + str_valores + ")")
                                            cnn.commit()
                                        except:
                                            cnn.rollback()
                                            QMessageBox.critical(None, 'EnerGis 6', '❌ No se pudo insertar la Linea 2')
                                        #-----------------------------------------------------------
                                        #-----------------------------------------------------------

        if linea_a_borrar!="0":
            cnn = self.conn
            cnn.autocommit = False
            cursor = cnn.cursor()
            try:
                cursor.execute("DELETE FROM Lineas WHERE Geoname=" + linea_a_borrar)
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.critical(None, 'EnerGis 6', '❌ No se pudo borrar la Linea')

            for lyr in layers:
                lyr.triggerRepaint()

            if self.rubber_band:
                self.rubber_band.reset(QgsWkbTypes.LineGeometry)
                self.rubber_band = None
                self.resetMarker()
