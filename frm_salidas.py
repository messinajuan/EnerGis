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
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QIntValidator, QDoubleValidator
from PyQt6.QtGui import QColor
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_salidas.ui'))

class frmSalidas(DialogType, DialogBase):
        
    def __init__(self, tipo_usuario, conn, geoname, ssee):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.tipo_usuario = tipo_usuario
        self.conn = conn
        self.geoname = geoname
        vint = QIntValidator()
        vfloat = QDoubleValidator()
        self.txtPrioridad.setValidator(vint)
        self.txtDemanda.setValidator(vfloat)
        self.qcolor= QColor("#00000")
        self.linea.setStyleSheet("color:" + self.qcolor.name() + ";")
        if self.tipo_usuario==4:
            self.cmdAceptar.setEnabled(False)

        self.txtSSEE.setText(ssee)

        cnn = self.conn
        cursor = cnn.cursor()
        cursor = cnn.cursor()
        cursor.execute("SELECT ISNULL(Val1, ''), ISNULL(Val5, ''), ISNULL(descripcion, ''), ISNULL(Val2, ''), ISNULL(Val3, '0'), ISNULL(Val4, '') FROM Nodos WHERE Geoname=" + str(self.geoname))
        #convierto el cursor en array
        datos_nodo = tuple(cursor)
        cursor.close()
        self.txtNombre.setText(str(datos_nodo[0][0]))
        self.txtPrioridad.setText(str(datos_nodo[0][1]))
        self.txtCD.setText(str(datos_nodo[0][5]))
        self.txtDemanda.setText(str(datos_nodo[0][4]))

        try:
            str_color = str(hex(int(datos_nodo[0][3]))).replace('0x','')
            str_color = '000000' + str_color
            str_color = str_color[-6:]
            str_color = self.invertir_cadena(str_color)
            self.linea.setStyleSheet("color: #" + str_color + ";")
            self.qcolor = QColor("#" + str_color)
        except:
             pass

        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdColor.clicked.connect(self.cambiar_color)
        self.cmdSalir.clicked.connect(self.salir)

    def invertir_cadena(self, cadena):
        cadena_invertida = ""
        for letra in cadena:
            cadena_invertida = letra + cadena_invertida
        return cadena_invertida

    def cambiar_color(self):
        if self.qcolor==None:
           self.qcolor = QtWidgets.QColorDialog.getColor()
        else:
            self.qcolor = QtWidgets.QColorDialog.getColor(self.qcolor)
        self.linea.setStyleSheet("color:" + self.qcolor.name() + ";")

    def aceptar(self):
        cnn = self.conn
        cursor = cnn.cursor()
        str_set = "descripcion='" + self.txtCD.text() + "', "
        str_set = str_set + "Val1='" + self.txtNombre.text() + "', "
        c = self.linea.styleSheet().replace('color:','').replace('#','').replace(' ','').replace(';','')
        c=self.invertir_cadena(c)
        c = str(int(c, 16))
        str_set = str_set + "Val2='" + c + "', "
        str_set = str_set + "Val3='" + self.txtDemanda.text() + "', "
        str_set = str_set + "Val4='" + self.txtCD.text() + "', "
        str_set = str_set + "Val5='" + self.txtPrioridad.text() + "'"
        try:
            cursor.execute("UPDATE Nodos SET " + str_set + " WHERE Geoname=" + str(self.geoname))
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudo actualizar')
        self.close()

    def salir(self):
        self.close()
