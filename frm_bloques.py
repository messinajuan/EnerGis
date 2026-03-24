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

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_bloques.ui'))

class frmBloques(DialogType, DialogBase):
        
    def __init__(self, tipo_usuario, conn, id):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.tipo_usuario = tipo_usuario
        self.conn = conn
        self.id = id
        vfloat = QDoubleValidator()
        self.txtI1.setValidator(vfloat)
        self.txtI2.setValidator(vfloat)
        self.txtV1.setValidator(vfloat)
        self.txtV2.setValidator(vfloat)

        if self.tipo_usuario==4:
            self.cmdAceptar.setEnabled(False)

        self.cmbFuncionI.addItem("Medicion")
        self.cmbFuncionI.addItem("Proteccion")
        self.cmbFuncionI.addItem("Medicion y Proteccion")

        self.cmbTecnologiaI.addItem("Inductivo")
        self.cmbTecnologiaI.addItem("Otro")

        self.cmbFuncionV.addItem("Medición")
        self.cmbFuncionV.addItem("Protección")
        self.cmbFuncionV.addItem("Medicion y Proteccion")

        self.cmbTecnologiaV.addItem("Inductivo")
        self.cmbTecnologiaV.addItem("Otro")

        self.cmbMontaje.addItem("Intemperie")
        self.cmbMontaje.addItem("Interior")
        self.cmbMontaje.addItem("GIS")
        self.cmbMontaje.addItem("Celda")

        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT i1, i2, funcioni, tecnologiai, v1, v2, funcionv, tecnologiav, montaje, combinado FROM Bloques WHERE id_usuario=" + str(self.id))
        #convierto el cursor en array
        rs = tuple(cursor)
        cursor.close()

        if len(rs)==1:
            self.txtI1.setText(str(rs[0][0]))
            self.txtI2.setText(str(rs[0][1]))

            for i in range (0, self.cmbFuncionI.count()):
                if self.cmbFuncionI.itemText(i) == str(rs[0][2]).strip():
                    self.cmbFuncionI.setCurrentIndex(i)

            for i in range (0, self.cmbTecnologiaI.count()):
                if self.cmbTecnologiaI.itemText(i) == str(rs[0][3]).strip():
                    self.cmbTecnologiaI.setCurrentIndex(i)

            self.txtV1.setText(str(rs[0][4]))
            self.txtV2.setText(str(rs[0][5]))

            for i in range (0, self.cmbFuncionV.count()):
                if self.cmbFuncionV.itemText(i) == str(rs[0][6]).strip():
                    self.cmbFuncionV.setCurrentIndex(i)

            for i in range (0, self.cmbTecnologiaV.count()):
                if self.cmbTecnologiaV.itemText(i) == str(rs[0][7]).strip():
                    self.cmbTecnologiaV.setCurrentIndex(i)

            for i in range (0, self.cmbMontaje.count()):
                if self.cmbMontaje.itemText(i) == str(rs[0][8]).strip():
                    self.cmbMontaje.setCurrentIndex(i)

            if rs[0][9]==1:
                self.chkCombinados.setChecked(True)
        else:
            cnn = self.conn
            cursor = cnn.cursor()
            try:
                cursor.execute("INSERT INTO Bloques (id_usuario) VALUES (" + str(self.id) + ")")
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo insertar !")
            pass

        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)
        pass
        
    def aceptar(self):
        if self.txtI1.text().strip()=='':
            self.txtI1.setText('0')
        if self.txtI2.text().strip()=='':
            self.txtI2.setText('0')
        str_set = "i1=" + self.txtI1.text()
        str_set = str_set + ", i2=" + self.txtI2.text()
        str_set = str_set + ", funcioni='" + self.cmbFuncionI.currentText() + "'"
        str_set = str_set + ", tecnologiai='" + self.cmbTecnologiaI.currentText() + "'"
        if self.txtV1.text().strip()=='':
            self.txtV1.setText('0')
        if self.txtV2.text().strip()=='':
            self.txtV2.setText('0')
        str_set = str_set + ", v1=" + self.txtV1.text()
        str_set = str_set + ", v2=" + self.txtV2.text()
        str_set = str_set + ", funcionv='" + self.cmbFuncionV.currentText() + "'"
        str_set = str_set + ", tecnologiav='" + self.cmbTecnologiaV.currentText() + "'"
        str_set = str_set + ", montaje='" + self.cmbMontaje.currentText() + "'"
        if self.chkCombinados.isChecked() == True:
            str_set = str_set + ", combinado=1"
        else:
            str_set = str_set + ", combinado=0"

        cnn = self.conn
        cursor = cnn.cursor()
        try:
            cursor.execute("UPDATE Bloques SET " + str_set + " WHERE id_usuario=" + str(self.id))
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo actualizar !")
        pass
        self.close()
        pass

    def salir(self):
        self.close()
        pass
