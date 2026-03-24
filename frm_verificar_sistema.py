# encoding: utf-8
#-----------------------------------------------------------
# Copyright (C) 2025 Juan Messina
#-----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#---------------------------------------------------------------------

import os
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_configuracion.ui'))

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class frmConfiguracion(DialogType, DialogBase):
        
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())


        SELECT geoname, obj FROM Lineas WHERE NOT obj.STIsValid()=1
        SELECT DISTINCT obj.STGeometryType() FROM Lineas
        SELECT DISTINCT obj.STIsValid() FROM Lineas
        SELECT * FROM Lineas WHERE obj IS NULL


        select * from nodos where estado!=elmt and elmt in (2,3)
        select * from lineas where Longitud <= 0 or longitud is null



        f = open('C:\GIS\EnerGis5\conexion.ini','r')
        ini = f.readlines()
        f.close()

        self.txtConexion.setText(ini[0])
        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)
        pass
        
    def aceptar(self):
        f = open('C:\GIS\EnerGis5\conexion.ini','w')
        f.write(self.txtConexion.toPlainText())
        f.close()

        QMessageBox.information(None, 'EnerGis 5', 'Grabado')
        self.close()
        pass

    def salir(self):
        self.close()
        pass
