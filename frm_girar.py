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

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_girar.ui'))
basepath = os.path.dirname(os.path.realpath(__file__))

class frmGirar(DialogType, DialogBase):
        
    def __init__(self, mapCanvas, conn, ftrs_nodos, ftrs_postes):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.ftrs_nodos = ftrs_nodos
        self.ftrs_postes = ftrs_postes
        vfloat = QDoubleValidator()
        self.txtAngulo.setValidator(vfloat)

        #self.setWindowIcon(QIcon(path))
        self.cmdDerecha.setIcon(QIcon(os.path.join(basepath,"icons", 'derecha.png')))
        self.cmdIzquierda.setIcon(QIcon(os.path.join(basepath,"icons", 'izquierda.png')))

        self.cmdDerecha.clicked.connect(self.derecha)
        self.cmdIzquierda.clicked.connect(self.izquierda)
        self.cmdAceptar.clicked.connect(self.aceptar)
        pass
        
    def derecha(self):
        self.txtAngulo.setText(str(int(self.txtAngulo.text())+1))

    def izquierda(self):
        self.txtAngulo.setText(str(int(self.txtAngulo.text())-1))

    def aceptar(self):
        angulo = float(self.txtAngulo.text())
        self.girar(self.ftrs_nodos, self.ftrs_postes, angulo)
        self.close()

    def girar(self, nodos, postes, angulo):
        cnn = self.conn
        cursor = cnn.cursor()
        try:
            if len(nodos)>0:
                cursor.execute("UPDATE Nodos SET giro=giro + " + str(angulo) + " WHERE geoname IN (" + str(nodos).replace('[','').replace(']','') + ")")
                cursor.execute("UPDATE Nodos SET giro=giro-360*CAST(giro/360 AS int) WHERE giro>360")
                cursor.execute("UPDATE Nodos SET giro=360+giro+360*CAST(-giro/360 AS int) WHERE giro<360")
                cursor.execute("UPDATE Nodos SET giro=0 WHERE giro=360")
                cnn.commit()
            if len(postes)>0:
                cursor.execute("UPDATE Postes SET giro = giro + " + str(angulo) + " WHERE geoname IN (" + str(postes).replace('[','').replace(']','') + ")")
                cursor.execute("UPDATE Postes SET giro=giro-360*CAST(giro/360 AS int) WHERE giro>360")
                cursor.execute("UPDATE Postes SET giro=360+giro+360*CAST(-giro/360 AS int) WHERE giro<360")
                cursor.execute("UPDATE Postes SET giro=0 WHERE giro=360")
                cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.critical(None, 'EnerGis 6', '❌ No se pudo grabar en la base de datos')

        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            lyr.triggerRepaint()
