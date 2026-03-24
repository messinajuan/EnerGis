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
from PyQt6.QtGui import QPixmap
from PyQt6.QtGui import QDoubleValidator

from PyQt6 import uic

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_elegir_longitud.ui'))

class frmElegirLongitud(DialogType, DialogBase):

    def __init__(self, a):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())

        pixmap = QPixmap(os.path.join(basepath,"icons", 'img_pregunta.png'))
        self.lbIcono.setPixmap(pixmap)
        self.txtDistancia.setText(str(round(a)))
        vfloat = QDoubleValidator()
        self.txtDistancia.setValidator(vfloat)

        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)

    def aceptar(self):
        self.close()

    def salir(self):
        self.txtDistancia.setText('0')
        self.close()
