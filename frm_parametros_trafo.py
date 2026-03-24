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
from PyQt6.QtGui import QDoubleValidator
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_parametros_trafo.ui'))

class frmParametrosTrafo(DialogType, DialogBase):

    def __init__(self, tipo_usuario, conn, id, potencia):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        #basepath = os.path.dirname(os.path.realpath(__file__))
        self.tipo_usuario = tipo_usuario
        self.conn = conn
        self.id = id
        self.potencia = potencia
        vfloat = QDoubleValidator()
        self.txtRpu.setValidator(vfloat)
        self.txtXpu.setValidator(vfloat)
        self.txtPo.setValidator(vfloat)

        if self.tipo_usuario==4:
            self.txtRpu.setEnabled(False)
            self.txtXpu.setEnabled(False)
            self.txtPo.setEnabled(False)

        cnn = self.conn
        self.dial.valueChanged.connect(self.tap)
        cursor = cnn.cursor()
        cursor.execute("SELECT R1, X1, P01, Tap1 FROM Transformadores_Parametros WHERE Id_Trafo=" + str(self.id))
        #convierto el cursor en array
        rs = tuple(cursor)
        cursor.close()

        if len(rs)==0:
            self.txtRpu.setText('0.05')
            self.txtXpu.setText('0.01')
            self.txtPo.setText(str(18.276 * self.potencia ** 0.689))
            self.dial.setValue(3)
            cursor = cnn.cursor()
            cursor.execute('INSERT INTO Transformadores_Parametros (Id_Trafo, R1, X1, P01, Tap1) VALUES (' + str(self.id) + ',0.05,0.01,' + self.txtPo.text() + ',100)')
            cursor.close()
        else:
            self.txtRpu.setText(str(rs[0][0]))
            self.txtXpu.setText(str(rs[0][1]))
            self.txtPo.setText(str(rs[0][2]))
            self.dial.setValue(3)
            if rs[0][3] <= 95:
                self.dial.setValue(1)
            if rs[0][3] > 95 and rs[0][3] <= 97.5:
                self.dial.setValue(2)
            if rs[0][3] >= 102.5 and rs[0][3] < 105:
                self.dial.setValue(4)
            if rs[0][3] >= 105:
                self.dial.setValue(5)

        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)
        pass

    def tap(self):
        if self.dial.value()==1:
            self.lbl_tap.setText('Posición Tap: 95')
        if self.dial.value()==2:
            self.lbl_tap.setText('Posición Tap: 97.5')
        if self.dial.value()==3:
            self.lbl_tap.setText('Posición Tap: 100')
        if self.dial.value()==4:
            self.lbl_tap.setText('Posición Tap: 102.5')
        if self.dial.value()==5:
            self.lbl_tap.setText('Posición Tap: 105')

    def aceptar(self):
        cnn = self.conn
        str_set = "R1=" + self.txtRpu.text() + ", "
        str_set = str_set + "X1=" + self.txtXpu.text() + ", "
        str_set = str_set + "P01=" + self.txtPo.text() + ", "
        if self.dial.value()==1:
            str_set = str_set + "Tap1=95"
        if self.dial.value()==2:
            str_set = str_set + "Tap1=97.5"
        if self.dial.value()==3:
            str_set = str_set + "Tap1=100"
        if self.dial.value()==4:
            str_set = str_set + "Tap1=102.5"
        if self.dial.value()==5:
            str_set = str_set + "Tap1=105"

        #reply = QMessageBox.question(None, 'EnerGis 6', 'Desea guardar los cambios ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        #if reply == QMessageBox.StandardButton.Yes:
        try:
            cursor = cnn.cursor()
            cursor.execute("UPDATE Transformadores_Parametros SET " + str_set + " WHERE id_trafo=" + str(self.id))
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo grabar !")
            return
        self.close()
        pass

    def salir(self):
        self.close()
        pass
