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
from PyQt6 import QtCore
from qgis.gui import QgsMapTool
from qgis.core import QgsPoint, QgsRectangle, QgsFeatureRequest, QgsFeature, QgsMapLayerType, QgsSnappingConfig
import os

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrMover(QgsMapTool):

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
        self.elmt=''
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
        if len(self.ftrs_nodos) + len(self.ftrs_lineas) + len(self.ftrs_areas) + len(self.ftrs_parcelas) + len(self.ftrs_cotas) + len(self.ftrs_anotaciones) > 0:
            self.tipo_herramienta='muchos'
            from .frm_mover import frmMover
            self.dialogo = frmMover(self.mapCanvas, self.conn, self.ftrs_nodos, self.ftrs_lineas, self.ftrs_postes, self.ftrs_areas, self.ftrs_parcelas, self.ftrs_ejes, self.ftrs_cotas, self.ftrs_anotaciones)
            self.dialogo.setWindowFlags(self.dialogo.windowFlags() & QtCore.Qt.CustomizeWindowHint)
            self.dialogo.setWindowFlags(self.dialogo.windowFlags() & ~QtCore.Qt.WindowMinMaxButtonsHint)
            self.dialogo.show()
        else:
            self.tipo_herramienta='uno'
        import gc
        gc.collect()


    def setSnapping(self, config):
        self.snapConfig = config
        if self.elmt[:7]=='Vertice':
            self.snapConfig.setType(QgsSnappingConfig.VertexAndSegment)
        elif self.elmt=='Poste':
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
            self.markerSnapped.setColor(QtCore.Qt.red)
            self.markerSnapped.setIconSize(10)
            self.markerSnapped.setIconType(QgsVertexMarker.ICON_BOX)
            self.markerSnapped.setPenWidth(5)
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
        if event.button() == QtCore.Qt.MouseButton.RightButton:
            return
        self.elmt = ''
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                if lyr.name()[:5] == 'Nodos':
                    width = 5 * self.mapCanvas.mapUnitsPerPixel()
                    rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                    int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                    ftrs = lyr.getFeatures(int)
                    for ftr in ftrs:
                        geom = ftr.geometry()
                        self.ftr = ftr
                        p = QgsFeature()
                        p.setGeometry(geom)
                        self.p1 = QgsPoint(geom.asPoint().x(), geom.asPoint().y())
                        self.elmt = 'Nodo'
                        self.setSnapping(self.prj.snappingConfig())
                        return
                if lyr.name()[:6] == 'Lineas':
                    width = 5 * self.mapCanvas.mapUnitsPerPixel()
                    rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                    int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                    ftrs = lyr.getFeatures(int)
                    for ftr in ftrs:
                        geom = ftr.geometry()
                        self.ftr = ftr
                        vertices  = geom.asPolyline()
                        m = len(vertices)
                        for i in range(m):
                            vertice=QgsPoint(vertices [i][0],vertices [i][1])
                            if abs(self.point.x()-vertices [i][0])<width and abs(self.point.y()-vertices [i][1])<width:
                                v = QgsFeature()
                                v.setGeometry(vertice)
                                self.p1 = QgsPoint(vertice.x(), vertice.y())
                                self.elmt = 'Vertice ' + str(i)
                                self.setSnapping(self.prj.snappingConfig())
                                return
                if lyr.name()[:6] == 'Postes':
                    width = 5 * self.mapCanvas.mapUnitsPerPixel()
                    rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                    int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                    ftrs = lyr.getFeatures(int)
                    for ftr in ftrs:
                        geom = ftr.geometry()
                        self.ftr = ftr
                        p = QgsFeature()
                        p.setGeometry(geom)
                        self.p1 = QgsPoint(geom.asPoint().x(), geom.asPoint().y())
                        self.elmt = 'Poste'
                        self.setSnapping(self.prj.snappingConfig())
                        return
                if lyr.name() == 'Areas':
                    width = 5 * self.mapCanvas.mapUnitsPerPixel()
                    rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                    int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                    ftrs = lyr.getFeatures(int)
                    for ftr in ftrs:
                        geom = ftr.geometry()
                        self.ftr = ftr
                        poligono = geom.asPolygon()
                        n = len(poligono[0])
                        for i in range(n):
                            vertice=QgsPoint(poligono [0][i])
                            if abs(self.point.x()-vertice.x())<width and abs(self.point.y()-vertice.y())<width:
                                v = QgsFeature()
                                v.setGeometry(vertice)
                                self.p1 = QgsPoint(vertice.x(), vertice.y())
                                self.elmt = 'Oertice ' + str(i)
                                self.setSnapping(self.prj.snappingConfig())
                                return
                if lyr.name() == 'Parcelas':
                    width = 1 * self.mapCanvas.mapUnitsPerPixel()
                    rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                    int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                    ftrs = lyr.getFeatures(int)
                    for ftr in ftrs:
                        geom = ftr.geometry()
                        self.ftr = ftr
                        poligono = geom.asPolygon()
                        n = len(poligono[0])
                        for i in range(n):
                            vertice=QgsPoint(poligono [0][i])
                            if abs(self.point.x()-vertice.x())<width and abs(self.point.y()-vertice.y())<width:
                                v = QgsFeature()
                                v.setGeometry(vertice)
                                self.p1 = QgsPoint(vertice.x(), vertice.y())
                                self.elmt = 'Pertice ' + str(i)
                                self.setSnapping(self.prj.snappingConfig())
                                return
                if lyr.name() == 'Cotas':
                    width = 5 * self.mapCanvas.mapUnitsPerPixel()
                    rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                    int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                    ftrs = lyr.getFeatures(int)
                    for ftr in ftrs:
                        geom = ftr.geometry()
                        self.ftr = ftr
                        vertices  = geom.asPolyline()
                        m = len(vertices)
                        for i in range(m):
                            vertice=QgsPoint(vertices [i][0],vertices [i][1])
                            if abs(self.point.x()-vertices [i][0])<width and abs(self.point.y()-vertices [i][1])<width:
                                v = QgsFeature()
                                v.setGeometry(vertice)
                                self.p1 = QgsPoint(vertice.x(), vertice.y())
                                self.elmt = 'Certice ' + str(i + 1)
                                self.setSnapping(self.prj.snappingConfig())
                                return
                if lyr.name() == 'Anotaciones':
                    width = 5 * self.mapCanvas.mapUnitsPerPixel()
                    rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                    int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                    ftrs = lyr.getFeatures(int)
                    for ftr in ftrs:
                        geom = ftr.geometry()
                        self.ftr = ftr
                        p = QgsFeature()
                        p.setGeometry(geom)
                        self.p1 = QgsPoint(geom.asPoint().x(), geom.asPoint().y())
                        self.elmt = 'Anotacion'
                        self.setSnapping(self.prj.snappingConfig())
                        return

    def canvasReleaseEvent(self, event):
        if self.tipo_herramienta=='muchos':
            return
        if self.elmt=='':
            return
        if self.snapConfig.enabled() and self.useSnapped:
            self.isSnapped()
        self.p2 = QgsPoint(self.point.x(), self.point.y())
        self.dx = self.p2.x() - self.p1.x()
        self.dy = self.p2.y() - self.p1.y()
        self.setSnapping(self.prj.snappingConfig())
        if self.elmt=='Nodo':
            nodo = self.detecto_nodo(self.point)
            if nodo!=0:
                QMessageBox.warning(None, 'EnerGis 6', '❌ Ya hay un nodo en esa posicion')
                return
            #linea = self.detecto_linea(self.point)
            #if linea!=0:
            #    return
            cnn = self.conn
            cursor = cnn.cursor()
            try:
                cursor.execute("mover_nodo " + str(self.ftr.id()) + ', ' + str(self.dx) + ', ' + str(self.dy))
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudieron mover Nodos')
            zona = self.detecto_zona(self.point)
            if zona!=0:
                cnn = self.conn
                cursor = cnn.cursor()
                cursor.execute("SELECT nombre, descripcion, localidad FROM Areas WHERE Geoname=" + str(zona))
                rst = cursor.fetchall()
                cursor.close()
                cursor = cnn.cursor()
                try:
                    cursor.execute("UPDATE Nodos SET Zona='" + rst[0][0] + "', subzona='" + rst[0][1] + "', localidad=" + str(rst[0][2]) + " WHERE Geoname=" + str(self.ftr.id()))
                    cnn.commit()
                except:
                    cnn.rollback()
                    QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudieron actualizar Zonas')
                pass
            poste = self.detecto_poste(self.point)
            if poste!=0:
                cnn = self.conn
                cursor = cnn.cursor()
                try:
                    cursor.execute("UPDATE Postes SET id_nodo=" + str(self.ftr.id()) + " WHERE Geoname=" + str(poste))
                    cnn.commit()
                except:
                    cnn.rollback()
                    QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudieron actualizar Postes')
        if self.elmt=='Poste':
            poste = self.detecto_poste(self.point)
            if poste!=0:
                QMessageBox.warning(None, 'EnerGis 6', '❌ Ya hay un poste en esa posicion')
                return
            cnn = self.conn
            cursor = cnn.cursor()
            try:
                cursor.execute("mover_poste " + str(self.ftr.id()) + ', ' + str(self.dx) + ', ' + str(self.dy))
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudieron mover Postes')
            zona = self.detecto_zona(self.point)
            if zona!=0:
                pass
            nodo = self.detecto_nodo(self.point)
            if nodo!=0:
                cnn = self.conn
                cursor = cnn.cursor()
                try:
                    cursor.execute("UPDATE Postes SET id_nodo=" + str(nodo) + " WHERE Geoname=" + str(poste))
                    cnn.commit()
                except:
                    cnn.rollback()
                    QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudieron actualizar Postes')
            else:
                linea = self.detecto_linea(self.point)
                if linea!=0:
                    cnn = self.conn
                    cursor = cnn.cursor()
                    try:
                        cursor.execute("DELETE FROM Lineas_Postes WHERE id_linea=" + str(linea))
                        cnn.commit()
                    except:
                        cnn.rollback()
                        QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudieron borrar Lineas por Poste')
                    try:
                        cursor.execute("INSERT INTO Lineas_Postes (id_linea, id_poste) VALUES (" + str(linea) + ", " +  str(self.ftr.id()) + ")")
                        cnn.commit()
                    except:
                        cnn.rollback()
                        QMessageBox.warning(None, 'EnerGis 6', '❌ No se insertar Lineas por Poste')
        if self.elmt[:7]=='Vertice':
            nodo = self.detecto_nodo(self.point)
            if nodo!=0:
                QMessageBox.warning(None, 'EnerGis 6', '❌ Ya hay un nodo en esa posicion')
                return
            str_vertice = self.elmt[8:]
            cnn = self.conn
            cursor = cnn.cursor()
            try:
                cursor.execute("mover_linea " + str(self.ftr.id()) + ', ' + str_vertice + ', ' + str(self.dx) + ', ' + str(self.dy))
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudieron mover Lineas')
            poste = self.detecto_poste(self.point)
            if poste!=0:
                cnn = self.conn
                cursor = cnn.cursor()
                try:
                    cursor.execute("DELETE FROM Lineas_Postes WHERE id_linea=" + str(self.ftr.id()))
                    cursor.execute("INSERT INTO Lineas_Postes (id_linea, id_poste) VALUES (" + str(self.ftr.id()) + ", " + str(poste) + ")")
                    cnn.commit()
                except:
                    cnn.rollback()
                    QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudieron actualizar Lineas por Poste')
        if self.elmt[:7]=='Oertice':
            str_vertice = self.elmt[8:]
            cnn = self.conn
            cursor = cnn.cursor()
            try:
                cursor.execute("mover_area " + str(self.ftr.id()) + ', ' + str_vertice + ', ' + str(self.dx) + ', ' + str(self.dy))
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudieron mover Areas')

        if self.elmt[:7]=='Pertice':
            str_vertice = self.elmt[8:]
            cnn = self.conn
            cursor = cnn.cursor()
            try:
                cursor.execute("mover_parcela " + str(self.ftr.id()) + ', ' + str_vertice + ', ' + str(self.dx) + ', ' + str(self.dy))
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudieron mover Parcelas')

        if self.elmt=='Anotacion':
            cnn = self.conn
            cursor = cnn.cursor()
            try:
                cursor.execute("mover_anotacion " + str(self.ftr.id()) + ', ' + str(self.dx) + ', ' + str(self.dy))
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudo mover la Anotación')

        if self.elmt[:7]=='Certice':
            str_vertice = self.elmt[8:]
            cnn = self.conn
            cursor = cnn.cursor()
            try:
                cursor.execute("mover_cota " + str(self.ftr.id()) + ', ' + str_vertice + ', ' + str(self.dx) + ', ' + str(self.dy))
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudo mover la Cota')
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            lyr.triggerRepaint()
        self.elmt = ''
        self.ftr = None
        self.p1 = None
        self.p2 = None

    def detecto_poste(self, point):
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:6] == 'Postes':
                width = 0.1 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    return ftr.id()
        return 0

    def detecto_zona(self, point):
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name() == 'Areas':
                width = 0.1 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(point.x() - width, point.y() - width, point.x() + width, point.y() + width)
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    return ftr.id()
        return 0

    def detecto_linea(self, point):
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:6] == 'Lineas':
                width = 5 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    return ftr.id()
        return 0

    def detecto_nodo(self, point):
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                width = 5 * self.mapCanvas.mapUnitsPerPixel()
                rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                ftrs = lyr.getFeatures(int)
                for ftr in ftrs:
                    return ftr.id()
        return 0
