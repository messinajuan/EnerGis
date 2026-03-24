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
from PyQt6.QtGui import QIntValidator
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_medidores.ui'))

class frmMedidores(DialogType, DialogBase):
        
    def __init__(self, tipo_usuario, conn, id):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.tipo_usuario = tipo_usuario
        self.conn = conn
        self.id = id
        vint = QIntValidator()
        self.txtAnio.setValidator(vint)

        if self.tipo_usuario==4:
            self.cmdAceptar.setEnabled(False)

        self.cmbTipo.addItem("Monotarifa")
        self.cmbTipo.addItem("Multitarifa")
        self.cmbTipo.addItem("Multitarifa Bidireccional")
        self.cmbTipo.addItem("Multitarifa Bidireccional con Telemedicion")

        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT Marca, Modelo, Anio, Fases, Relacion, nro_medidor, tipo FROM Medidores WHERE id_usuario=" + str(self.id))
        #convierto el cursor en array
        rs = tuple(cursor)
        cursor.close()

        if len(rs)==0:
            QMessageBox.warning(None, 'EnerGis 6', '❌ No hay medidor en la base de datos')
        else:
            self.txtMarca.setText(rs[0][0])
            self.txtModelo.setText(rs[0][1])
            self.txtAnio.setText(rs[0][2])
            self.txtFases.setText(rs[0][3])
            self.txtRelacion.setText(rs[0][4])
            self.lblMedidor.setText('Id Medidor: ' + str(rs[0][5]))
            for i in range (0, self.cmbTipo.count()):
                if self.cmbTipo.itemText(i) == str(rs[0][6]).strip():
                    self.cmbTipo.setCurrentIndex(i)

            self.cmdElementos.clicked.connect(self.elementos)
            self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)
        pass

    def elementos(self):
        from .frm_bloques import frmBloques
        self.dialogo = frmBloques(self.tipo_usuario, self.conn, self.id)
        self.dialogo.show()
        pass

    def aceptar(self):
        cnn = self.conn
        cursor = cnn.cursor()
        str_set = "Marca='" + self.txtMarca.text() + "'"
        str_set = str_set + ", Modelo='" + self.txtModelo.text() + "'"
        str_set = str_set + ", Anio='" + self.txtAnio.text() + "'"
        str_set = str_set + ", Fases='" + self.txtFases.text() + "'"
        str_set = str_set + ", Relacion='" + self.txtRelacion.text() + "'"
        str_set = str_set + ", Tipo='" + self.cmbTipo.currentText() + "'"

        try:
            cursor.execute("UPDATE Medidores SET " + str_set + " WHERE id_usuario=" + str(self.id))
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudo actualiar')
        self.close()
        pass

    def salir(self):
        self.close()
        pass
