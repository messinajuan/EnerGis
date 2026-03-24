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
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_configuracion.ui'))

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class frmConfiguracion(DialogType, DialogBase):
        
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())

        self.inicio()
        pass

    def inicio(self):

        f = open('C:\GIS\EnerGis6\conexion.ini','r')
        ini = f.readlines()
        f.close()

        self.txtConexion.setText(ini[0])
        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)
        pass
        
    def aceptar(self):
        f = open('C:\GIS\EnerGis6\conexion.ini','w')
        f.write(self.txtConexion.toPlainText())
        f.close()

        QMessageBox.information(None, 'EnerGis 6', 'ℹ️ Grabado')
        self.close()
        pass

    def salir(self):
        self.close()
        pass
