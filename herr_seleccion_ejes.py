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

from PyQt6 import QtGui
from PyQt6.QtWidgets import QMessageBox, QMenu
from PyQt6.QtCore import Qt, QPoint
from qgis.gui import QgsMapTool
from qgis.core import QgsRectangle, QgsFeatureRequest, QgsMapLayerType
from qgis.core import QgsProject

import os

#from .herr_eje import herrEje
from .herr_zoom import herrZoom

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrSeleccionEjes(QgsMapTool):
    def __init__(self, tipo_usuario, mapCanvas, iface, conn):
        QgsMapTool.__init__(self, mapCanvas)
        self.tipo_usuario = tipo_usuario
        self.mapCanvas = mapCanvas
        self.iface = iface
        self.conn = conn
        self.clipboard=[]
        self.tecla=''

    def keyPressEvent(self, event):
        if str(event.key()) == '16777249':
            self.tecla = 'Ctrl'

    def keyReleaseEvent(self, event):
        self.tecla=''
        if str(event.key()) == '16777223':
            self.h_borrar_ejes() #copiado textualmente de energis6.py

    def h_borrar_ejes(self): #copiado textualmente de energis6.py
        ftrs_ejes = []
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        str_ejes = '0'
        for lyr in layers:
            if lyr.name() == 'Ejes de Calle':
                for ftr in lyr.selectedFeatures():
                    ftrs_ejes.append(ftr.id())
                    str_ejes = str_ejes + ',' + str(ftr.id())
        if len(ftrs_ejes) > 0:
            reply = QMessageBox.question(None, 'EnerGis', 'Desea borrar los ejes seleccionados ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return
            layers = [self.mapCanvas.layer(i) for i in range(n)]
            for lyr in layers:
                if lyr.name() == 'Ejes de Calle':
                    cursor = self.conn.cursor()
                    try:
                        cursor.execute("DELETE FROM Ejes WHERE Geoname IN (" + str_ejes + ")")
                        self.conn.commit()
                    except:
                        self.conn.rollback()
                        QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudieron borrar Ejes !")
                    lyr.triggerRepaint()

    def lyr_visible(self, layer):
        layer_tree_root = QgsProject.instance().layerTreeRoot()
        layer_tree_layer = layer_tree_root.findLayer(layer)
        return layer_tree_layer.isVisible()

    def canvasPressEvent(self, event):
        #Get the click
        x = event.pos().x()
        y = event.pos().y()
        self.point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
        #primero right click
        if event.button() == Qt.MouseButton.RightButton:
            if self.tipo_usuario==4:
                return
            contextMenu = QMenu()
            n = self.mapCanvas.layerCount()
            layers = [self.mapCanvas.layer(i) for i in range(n)]
            setCurrentAction = contextMenu.addAction(QtGui.QIcon(os.path.join(basepath,"icons","img_zoom_in.png")),"Zoom In")
            setCurrentAction.triggered.connect(self.zoomIn)
            setCurrentAction = contextMenu.addAction(QtGui.QIcon(os.path.join(basepath,"icons","img_zoom_out.png")),"Zoom Out")
            setCurrentAction.triggered.connect(self.zoomOut)
            setCurrentAction = contextMenu.addAction(QtGui.QIcon(os.path.join(basepath,"icons","img_pan.png")),"Pan")
            setCurrentAction.triggered.connect(self.pan)
            for lyr in layers:
                if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                    if self.lyr_visible(lyr) is True:
                        lyr.removeSelection()
                        if lyr.name() == 'Ejes de Calle':
                            width = 5 * self.mapCanvas.mapUnitsPerPixel()
                            rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                            int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                            ftrs = lyr.getFeatures(int)
                            for ftr in ftrs:
                                lyr.select(ftr.id())
                                #geom = ftr.geometry()
                                self.capa = lyr
                                self.ftr = ftr
                                contextMenu = QMenu()
                                setCurrentAction = contextMenu.addAction(QtGui.QIcon(os.path.join(basepath,"icons","img_editar.png")),"Editar")
                                setCurrentAction.triggered.connect(self.editar)
                                setCurrentAction = contextMenu.addAction(QtGui.QIcon(os.path.join(basepath,"icons","img_borrar.png")),"Borrar")
                                setCurrentAction.triggered.connect(self.borrar)
                                contextMenu.addSeparator()
                                x = event.pos().x() + 5
                                y = event.pos().y()
                                self.point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
                                action = contextMenu.exec_(self.mapCanvas.mapToGlobal(QPoint(event.pos().x()+5, event.pos().y())))
                                return
            x = event.pos().x() + 5
            y = event.pos().y()
            self.point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
            action = contextMenu.exec_(self.mapCanvas.mapToGlobal(QPoint(event.pos().x()+5, event.pos().y())))
            return
        else:
            #si no tengo apretada Ctrl borro la seleccion anterior
            if self.tecla != 'Ctrl':
                n = self.mapCanvas.layerCount()
                layers = [self.mapCanvas.layer(i) for i in range(n)]
                for lyr in layers:
                    if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                        lyr.removeSelection()
            n = self.mapCanvas.layerCount()
            layers = [self.mapCanvas.layer(i) for i in range(n)]
            #hacemos que se busque en las capas que queremos !!!
            for lyr in layers:
                if self.lyr_visible(lyr) is True:
                    if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                        if lyr.name() == 'Ejes de Calle':
                            width = 5 * self.mapCanvas.mapUnitsPerPixel()
                            rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                            #rect = self.mapCanvas.mapRenderer().mapToLayerCoordinates(lyr, rect)
                            int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                            ftrs = lyr.getFeatures(int)
                            for ftr in ftrs:
                                b_seleccionado = False
                                for i in lyr.selectedFeatures():
                                    if i.id() == ftr.id():
                                        b_seleccionado = True
                                if b_seleccionado == True:
                                    seleccion = []
                                    for i in lyr.selectedFeatures():
                                        seleccion.append(i.id())
                                    seleccion.remove(ftr.id())
                                    lyr.removeSelection()
                                    lyr.select(seleccion)
                                    return
                                else:
                                    lyr.select(ftr.id())
                                    return

    def canvasDoubleClickEvent(self, event):
        #Get the click
        x = event.pos().x()
        y = event.pos().y()
        self.point = self.mapCanvas.getCoordinateTransform().toMapCoordinates(x, y)
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        #hacemos que se busque en las capas que queremos !!!
        for lyr in layers:
            if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                if self.lyr_visible(lyr) is True:
                    if lyr.name() == 'Ejes de Calle':
                        width = 6 * self.mapCanvas.mapUnitsPerPixel()
                        rect = QgsRectangle(self.point.x() - width, self.point.y() - width, self.point.x() + width, self.point.y() + width)
                        int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                        ftrs = lyr.getFeatures(int)
                        for ftr in ftrs:
                            lyr.select(ftr.id())
                            if lyr.name() == 'Ejes de Calle':
                                from .frm_ejes import frmEjes
                                self.dialogo = frmEjes(self.tipo_usuario, self.mapCanvas, self.conn, 0, 0, 0, 0, ftr.id())
                                self.dialogo.show()
                                return
                            return

    def editar(self):
        if self.capa.name() == 'Ejes de Calle':
            from .frm_ejes import frmEjes
            self.dialogo = frmEjes(self.tipo_usuario, self.mapCanvas, self.conn, 0, 0, 0, 0, self.ftr.id())
            self.dialogo.show()

    def borrar(self):
        reply = QMessageBox.question(None, 'EnerGis 6', 'Desea borrar de capa Ejes ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return

        if self.capa.name() == 'Ejes de Calle':
            cnn = self.conn
            cursor = cnn.cursor()
            try:
                cursor.execute("DELETE FROM Ejes WHERE geoname=" + str(self.ftr.id()))
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudieron borrar Ejes !")
            self.capa.triggerRepaint()
            return

    def zoomIn(self):
        tool = herrZoom(self.iface, self.iface.mapCanvas(), 'ZoomIn')
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punZoom = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_zoom_in.png'))
        punZoom.setMask(punZoom.mask())
        curZoom = QtGui.QCursor(punZoom)
        self.mapCanvas.setCursor(curZoom)

    def zoomOut(self):
        tool = herrZoom(self.iface, self.iface.mapCanvas(), 'ZoomOut')
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punZoom = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_zoom_out.png'))
        punZoom.setMask(punZoom.mask())
        curZoom = QtGui.QCursor(punZoom)
        self.mapCanvas.setCursor(curZoom)

    def pan(self):
        tool = herrZoom(self.iface, self.iface.mapCanvas(), 'Pan')
        self.iface.mapCanvas().setMapTool(tool)
        #Cambio el cursor
        punZoom = QtGui.QPixmap(os.path.join(basepath,"icons", 'cur_pan.png'))
        punZoom.setMask(punZoom.mask())
        curZoom = QtGui.QCursor(punZoom)
        self.mapCanvas.setCursor(curZoom)
