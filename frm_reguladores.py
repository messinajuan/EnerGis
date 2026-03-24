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
from PyQt6.QtGui import QDoubleValidator, QIntValidator
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_reguladores.ui'))

class frmReguladores(DialogType, DialogBase):
        
    def __init__(self, tipo_usuario, conn, geoname):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.tipo_usuario = tipo_usuario
        self.conn = conn
        self.geoname = geoname
        vfloat = QDoubleValidator()
        self.txtPotencia.setValidator(vfloat)
        self.txtPrioridad.setValidator(vfloat)
        self.txtMaxTap.setValidator(vfloat)
        self.txtPasoTap.setValidator(vfloat)
        vint = QIntValidator()
        self.txtDescargadores.setValidator(vint)

        if self.tipo_usuario==4:
            self.cmdAceptar.setEnabled(False)

        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT ISNULL(Val1,''), ISNULL(Val2,''), ISNULL(Val3,''), ISNULL(Val4,''), ISNULL(Val5,'0') FROM Nodos WHERE geoname=" + str(self.geoname))
        #convierto el cursor en array
        rs = tuple(cursor)
        cursor.close()

        self.txtPotencia.setText(rs[0][0])
        self.txtPrioridad.setText(rs[0][1])
        self.txtMaxTap.setText(rs[0][2])
        self.txtPasoTap.setText(rs[0][3])
        self.txtDescargadores.setText(rs[0][4])

        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)
        pass
        
    def aceptar(self):
        cnn = self.conn
        cursor = cnn.cursor()
        str_set = "Val1='" + self.txtPotencia.text() + "'"
        str_set = str_set + ", Val2='" + self.txtPrioridad.text() + "'"
        str_set = str_set + ", Val3='" + self.txtMaxTap.text() + "'"
        str_set = str_set + ", Val4='" + self.txtPasoTap.text() + "'"
        str_set = str_set + ", Val5='" + self.txtDescargadores.text() + "'"
        try:
            cursor.execute("UPDATE Nodos SET " + str_set + " WHERE Geoname=" + str(self.geoname))
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudo actualizar la Base de Datos')
        self.close()

    def salir(self):
        self.close()
