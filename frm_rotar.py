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

import os
from PyQt6.QtWidgets import QMessageBox
from qgis.core import QgsMapLayerType, QgsPoint, QgsFeature
from PyQt6.QtGui import QIcon
from PyQt6.QtGui import QDoubleValidator
from math import sqrt, pow, atan, cos, sin
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_rotar.ui'))
basepath = os.path.dirname(os.path.realpath(__file__))

class frmRotar(DialogType, DialogBase):
        
    def __init__(self, mapCanvas, conn, ftrs_nodos, ftrs_lineas, ftrs_postes, ftrs_areas, ftrs_parcelas, ftrs_ejes, ftrs_cotas, ftrs_anotaciones, pc):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.ftrs_nodos = ftrs_nodos
        self.ftrs_lineas = ftrs_lineas
        self.ftrs_postes = ftrs_postes
        self.ftrs_areas = ftrs_areas
        self.ftrs_parcelas = ftrs_parcelas
        self.ftrs_ejes = ftrs_ejes
        self.ftrs_cotas = ftrs_cotas
        self.ftrs_anotaciones = ftrs_anotaciones
        self.pc = pc
        vfloat = QDoubleValidator()
        self.txtAngulo.setValidator(vfloat)

        #self.setWindowIcon(QIcon(path))

        self.cmdDerecha.setIcon(QIcon(os.path.join(basepath,"icons", 'derecha.png')))
        self.cmdIzquierda.setIcon(QIcon(os.path.join(basepath,"icons", 'izquierda.png')))

        self.cmdDerecha.clicked.connect(self.derecha)
        self.cmdIzquierda.clicked.connect(self.izquierda)
        pass
        
    def derecha(self):
        angulo = float(self.txtAngulo.text())*3.141592653589793/180
        self.rotar(self.pc, angulo, True)
        pass

    def izquierda(self):
        angulo = float(self.txtAngulo.text())*3.141592653589793/180
        self.rotar(self.pc, angulo, False)
        pass

    def rotar(self, pc, angulo, sentido):
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                if lyr.name()[:5] == 'Nodos':
                    ftrs = lyr.getFeatures(self.ftrs_nodos)
                    for ftr in ftrs:
                        mx, my = self.calcular_giro(ftr.geometry().asPoint().x(), ftr.geometry().asPoint().y(), pc.x(), pc.y(), angulo, sentido)
                        if mx!=0 or my!=0:
                            cnn = self.conn
                            cursor = cnn.cursor()
                            try:
                                cursor.execute("mover_nodo " + str(ftr.id()) + ', ' + str(mx) + ', ' + str(my))
                                cnn.commit()
                            except:
                                cnn.rollback()
                                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudieron rotar Nodos')
                            lyr.triggerRepaint()

                if lyr.name()[:6] == 'Lineas':
                    ftrs = lyr.getFeatures(self.ftrs_lineas)
                    for ftr in ftrs:
                        vertices  = ftr.geometry().asPolyline()
                        m = len(vertices)
                        for i in range(m):
                            vertice=QgsPoint(vertices [i][0],vertices [i][1])
                            v = QgsFeature()
                            v.setGeometry(vertice)
                            mx, my = self.calcular_giro(vertice.x(), vertice.y(), pc.x(), pc.y(), angulo, sentido)
                            cnn = self.conn
                            cursor = cnn.cursor()
                            try:
                                cursor.execute("mover_linea " + str(ftr.id()) + ', ' + str(i) + ', ' + str(mx) + ', ' + str(my))
                                cnn.commit()
                            except:
                                cnn.rollback()
                                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudieron rotar Lineas')
                            lyr.triggerRepaint()

                if lyr.name() == 'Ejes de Calle':
                    ftrs = lyr.getFeatures(self.ftrs_ejes)
                    for ftr in ftrs:
                        vertices  = ftr.geometry().asPolyline()
                        m = len(vertices)
                        for i in range(m):
                            vertice=QgsPoint(vertices [i][0],vertices [i][1])
                            v = QgsFeature()
                            v.setGeometry(vertice)
                            mx, my = self.calcular_giro(vertice.x(), vertice.y(), pc.x(), pc.y(), angulo, sentido)
                            cnn = self.conn
                            cursor = cnn.cursor()
                            try:
                                cursor.execute("mover_eje " + str(ftr.id()) + ', ' + str(i + 1) + ', ' + str(mx) + ', ' + str(my))
                                cnn.commit()
                            except:
                                cnn.rollback()
                                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudieron rotar Ejes')
                            lyr.triggerRepaint()


                if lyr.name()[:6] == 'Postes':
                    ftrs = lyr.getFeatures(self.ftrs_postes)
                    for ftr in ftrs:
                        mx, my = self.calcular_giro(ftr.geometry().asPoint().x(), ftr.geometry().asPoint().y(), pc.x(), pc.y(), angulo, sentido)
                        if mx!=0 or my!=0:
                            cnn = self.conn
                            cursor = cnn.cursor()
                            try:
                                cursor.execute("mover_poste " + str(ftr.id()) + ', ' + str(mx) + ', ' + str(my))
                                cnn.commit()
                            except:
                                cnn.rollback()
                                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudieron rotar Postes')
                            lyr.triggerRepaint()

                if lyr.name() == 'Anotaciones':
                    ftrs = lyr.getFeatures(self.ftrs_anotaciones)
                    for ftr in ftrs:
                        mx, my = self.calcular_giro(ftr.geometry().asPoint().x(), ftr.geometry().asPoint().y(), pc.x(), pc.y(), angulo, sentido)
                        if mx!=0 or my!=0:
                            cnn = self.conn
                            cursor = cnn.cursor()
                            try:
                                cursor.execute("mover_anotacion " + str(ftr.id()) + ', ' + str(mx) + ', ' + str(my))
                                cnn.commit()
                            except:
                                cnn.rollback()
                                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudieron rotar Anotaciones')
                            lyr.triggerRepaint()

                if lyr.name() == 'Areas':
                    ftrs = lyr.getFeatures(self.ftrs_areas)
                    for ftr in ftrs:
                        poligono = ftr.geometry().asPolygon()
                        n = len(poligono[0])
                        for i in range(n):
                            vertice=QgsPoint(poligono [0][i])
                            v = QgsFeature()
                            v.setGeometry(vertice)
                            mx, my = self.calcular_giro(vertice.x(), vertice.y(), pc.x(), pc.y(), angulo, sentido)
                            cnn = self.conn
                            cursor = cnn.cursor()
                            try:
                                cursor.execute("mover_area " + str(ftr.id()) + ', ' + str(i) + ', ' + str(mx) + ', ' + str(my))
                                cnn.commit()
                            except:
                                cnn.rollback()
                                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudieron rotar Areas')
                            lyr.triggerRepaint()

                if lyr.name() == 'Parcelas':
                    ftrs = lyr.getFeatures(self.ftrs_parcelas)
                    for ftr in ftrs:
                        poligono = ftr.geometry().asPolygon()
                        n = len(poligono[0])
                        for i in range(n):
                            vertice=QgsPoint(poligono [0][i])
                            v = QgsFeature()
                            v.setGeometry(vertice)
                            mx, my = self.calcular_giro(vertice.x(), vertice.y(), pc.x(), pc.y(), angulo, sentido)
                            cnn = self.conn
                            cursor = cnn.cursor()
                            try:
                                cursor.execute("mover_parcela " + str(ftr.id()) + ', ' + str(i) + ', ' + str(mx) + ', ' + str(my))
                                cnn.commit()
                            except:
                                cnn.rollback()
                                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudieron rotar Parcelas')
                            lyr.triggerRepaint()

                if lyr.name() == 'Cotas':
                    ftrs = lyr.getFeatures(self.ftrs_cotas)
                    for ftr in ftrs:
                        vertices  = ftr.geometry().asPolyline()
                        m = len(vertices)
                        for i in range(m):
                            vertice=QgsPoint(vertices [i][0],vertices [i][1])
                            v = QgsFeature()
                            v.setGeometry(vertice)
                            mx, my = self.calcular_giro(vertice.x(), vertice.y(), pc.x(), pc.y(), angulo, sentido)
                            cnn = self.conn
                            cursor = cnn.cursor()
                            try:
                                cursor.execute("mover_cota " + str(ftr.id()) + ', ' + str(i) + ', ' + str(mx) + ', ' + str(my))
                                cnn.commit()
                            except:
                                cnn.rollback()
                                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudieron rotar Cotas')
                            lyr.triggerRepaint()
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            lyr.triggerRepaint()
        pass

    def calcular_giro(self, xp, yp, xc, yc, angulo, sentido_horario):
        a = sqrt(pow((xp - xc), 2) + pow((yp - yc), 2))
        if a==0:
            return (0, 0)

        if xc - xp < 0:
            if yc - yp < 0:
                i_cuadrante = 1
            if yc - yp > 0:
                i_cuadrante = 4
            if yp==yc:
                i_cuadrante = 1
        elif xc - xp > 0:
            if yc - yp < 0:
                i_cuadrante = 2
            if yc - yp > 0:
                i_cuadrante = 3
            if yp==yc:
                i_cuadrante = 2
        else:
            if yc - yp < 0:
                i_cuadrante = 1
            if yc - yp > 0:
                i_cuadrante = 4
            if yp==yc:
                i_cuadrante = 1

        #Calculo el angulo al que se encuentra el origen del centro
        alfa = abs(atan((yp - yc) / (xp - xc)))
        if i_cuadrante==1:
            if sentido_horario == True:
                beta = alfa - angulo
                mx = a * abs(cos(beta) - cos(alfa))
                my = -a * abs(sin(beta) - sin(alfa))
                return (mx, my)
            else:
                beta = alfa + angulo
                mx = -a * abs(cos(beta) - cos(alfa))
                my = a * abs(sin(beta) - sin(alfa))
                return (mx, my)
        if i_cuadrante==2:
            if sentido_horario == True:
                beta = alfa + angulo
                mx = a * abs(cos(beta) - cos(alfa))
                my = a * abs(sin(beta) - sin(alfa))
                return (mx, my)
            else:
                beta = alfa - angulo
                mx = -a * abs(cos(beta) - cos(alfa))
                my = -a * abs(sin(beta) - sin(alfa))
                return (mx, my)
        if i_cuadrante==3:
            if sentido_horario == True:
                beta = alfa - angulo
                mx = -a * abs(cos(beta) - cos(alfa))
                my = a * abs(sin(beta) - sin(alfa))
                return (mx, my)
            else:
                beta = alfa + angulo
                mx = a * abs(cos(beta) - cos(alfa))
                my = -a * abs(sin(beta) - sin(alfa))
                return (mx, my)
        if i_cuadrante==4:
            if sentido_horario == True:
                beta = alfa + angulo
                mx = -a * abs(cos(beta) - cos(alfa))
                my = -a * abs(sin(beta) - sin(alfa))
                return (mx, my)
            else:
                beta = alfa - angulo
                mx = a * abs(cos(beta) - cos(alfa))
                my = a * abs(sin(beta) - sin(alfa))
                return (mx, my)
        return (0, 0)
