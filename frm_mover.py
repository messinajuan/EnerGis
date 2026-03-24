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
from PyQt6.QtGui import QIcon
from PyQt6.QtGui import QDoubleValidator
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_mover.ui'))
basepath = os.path.dirname(os.path.realpath(__file__))

class frmMover(DialogType, DialogBase):
        
    def __init__(self, mapCanvas, conn, ftrs_nodos, ftrs_lineas, ftrs_postes, ftrs_areas, ftrs_parcelas, ftrs_ejes, ftrs_cotas, ftrs_anotaciones):
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
        vfloat = QDoubleValidator()
        self.txtDistancia.setValidator(vfloat)

        self.cmdN.setIcon(QIcon(os.path.join(basepath,"icons", 'arriba.png')))
        self.cmdS.setIcon(QIcon(os.path.join(basepath,"icons", 'abajo.png')))
        self.cmdE.setIcon(QIcon(os.path.join(basepath,"icons", 'derecha.png')))
        self.cmdO.setIcon(QIcon(os.path.join(basepath,"icons", 'izquierda.png')))
        self.cmdNE.setIcon(QIcon(os.path.join(basepath,"icons", 'arriba_derecha.png')))
        self.cmdNO.setIcon(QIcon(os.path.join(basepath,"icons", 'arriba_izquierda.png')))
        self.cmdSE.setIcon(QIcon(os.path.join(basepath,"icons", 'abajo_derecha.png')))
        self.cmdSO.setIcon(QIcon(os.path.join(basepath,"icons", 'abajo_izquierda.png')))

        self.cmdN.clicked.connect(self.n)
        self.cmdS.clicked.connect(self.s)
        self.cmdE.clicked.connect(self.e)
        self.cmdO.clicked.connect(self.o)
        self.cmdNE.clicked.connect(self.ne)
        self.cmdNO.clicked.connect(self.no)
        self.cmdSE.clicked.connect(self.se)
        self.cmdSO.clicked.connect(self.so)
        
    def n(self):
        mx = 0
        my = float(self.txtDistancia.text())
        self.mover(mx, my)

    def s(self):
        mx = 0
        my = -1 * float(self.txtDistancia.text())
        self.mover(mx, my)

    def e(self):
        mx = float(self.txtDistancia.text())
        my = 0
        self.mover(mx, my)

    def o(self):
        mx = -1 * float(self.txtDistancia.text())
        my = 0
        self.mover(mx, my)

    def ne(self):
        mx = float(self.txtDistancia.text()) * 0.707
        my = float(self.txtDistancia.text()) * 0.707
        self.mover(mx, my)

    def no(self):
        mx = -1 * float(self.txtDistancia.text()) * 0.707
        my = float(self.txtDistancia.text()) * 0.707
        self.mover(mx, my)

    def se(self):
        mx = float(self.txtDistancia.text()) * 0.707
        my = -1 * float(self.txtDistancia.text()) * 0.707
        self.mover(mx, my)

    def so(self):
        mx = -1 * float(self.txtDistancia.text()) * 0.707
        my = -1 * float(self.txtDistancia.text()) * 0.707
        self.mover(mx, my)

    def mover(self, mx, my):
        for i in range (0, len(self.ftrs_nodos)):
            cnn = self.conn
            cnn.autocommit = False
            cursor = cnn.cursor()
            try:
                cursor.execute("mover_nodo " + str(self.ftrs_nodos[i]) + ', ' + str(mx) + ', ' + str(my))
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudieron mover Nodos')

        for i in range (0, len(self.ftrs_lineas)):
            cnn = self.conn
            cnn.autocommit = False
            cursor = cnn.cursor()
            try:
                cursor.execute("mover_linea " + str(self.ftrs_lineas[i]) + ',0 , ' + str(mx) + ', ' + str(my))
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudieron mover Lineas')

        for i in range (0, len(self.ftrs_ejes)):
            cnn = self.conn
            cnn.autocommit = False
            cursor = cnn.cursor()
            try:
                cursor.execute("mover_eje " + str(self.ftrs_ejes[i]) + ',0 , ' + str(mx) + ', ' + str(my))
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudieron mover Ejes')

        for i in range (0, len(self.ftrs_postes)):
            cnn = self.conn
            cnn.autocommit = False
            cursor = cnn.cursor()
            try:
                cursor.execute("mover_poste " + str(self.ftrs_postes[i]) + ', ' + str(mx) + ', ' + str(my))
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudieron mover Postes')

        for i in range (0, len(self.ftrs_areas)):
            cnn = self.conn
            cnn.autocommit = False
            cursor = cnn.cursor()
            try:
                cursor.execute("mover_area " + str(self.ftrs_areas[i]) + ',-1 , ' + str(mx) + ', ' + str(my))
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudieron mover Areas')

        for i in range (0, len(self.ftrs_parcelas)):
            cnn = self.conn
            cnn.autocommit = False
            cursor = cnn.cursor()
            try:
                cursor.execute("mover_parcela " + str(self.ftrs_parcelas[i]) + ',-1 , ' + str(mx) + ', ' + str(my))
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudieron mover Parcelas')

        for i in range (0, len(self.ftrs_cotas)):
            cnn = self.conn
            cnn.autocommit = False
            cursor = cnn.cursor()
            try:
                cursor.execute("mover_cota " + str(self.ftrs_cotas[i]) + ',-1 , ' + str(mx) + ', ' + str(my))
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudieron mover Cotas')

        for i in range (0, len(self.ftrs_anotaciones)):
            cnn = self.conn
            cnn.autocommit = False
            cursor = cnn.cursor()
            try:
                cursor.execute("mover_anotacion " + str(self.ftrs_anotaciones[i]) + ', ' + str(mx) + ', ' + str(my))
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudieron mover Anotaciones')

        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            lyr.triggerRepaint()
