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
from PyQt6 import QtCore
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_trafos_almacen.ui'))

class frmTrafosAlmacen(DialogType, DialogBase):
    def __init__(self, tipo_usuario, conn):
        super().__init__()
        self.setupUi(self)
        #self.setFixedSize(self.size())
        self.conn = conn
        self.tipo_usuario = tipo_usuario
        self.lleno_grilla()
        self.cmdAgregar.clicked.connect(self.agregar)
        self.cmdEditar.clicked.connect(self.editar)
        self.cmdBorrar.clicked.connect(self.borrar)
        self.cmdSalir.clicked.connect(self.salir)

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key.Key_Escape:
            self.seleccionado = ""
            self.close()

    def lleno_grilla(self):
        self.tblListado.setRowCount(0)
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT id_trafo, potencia, marca, n_chapa, tension_1, tension_2, conexionado FROM Transformadores WHERE usado<>0 AND id_ct='' OR id_ct IS NULL ORDER BY MARCA, N_CHAPA")
        elementos = tuple(cursor)
        encabezado = [column[0] for column in cursor.description]
        cursor.close()
        self.tblListado.setRowCount(0)
        if len(elementos) > 0:
            self.tblListado.setRowCount(len(elementos))
            self.tblListado.setColumnCount(len(elementos[0]))
        for i in range (0, len(elementos)):
            for j in range (len(elementos[0])):
                item = QTableWidgetItem(str(elementos[i][j]))
                self.tblListado.setItem(i,j,item)
        self.tblListado.setHorizontalHeaderLabels(encabezado)

    def agregar(self):
        from .frm_abm_transformadores import frmAbmTransformadores
        self.dialogo = frmAbmTransformadores(self.tipo_usuario, self.conn, 0)
        self.dialogo.show()

    def editar(self):
        if self.tblListado.currentRow()==None:
            return
        id = self.tblListado.item(self.tblListado.currentRow(),0).text()
        if id=='':
            return
        from .frm_abm_transformadores import frmAbmTransformadores
        self.dialogo = frmAbmTransformadores(self.tipo_usuario, self.conn, id)
        self.dialogo.exec()
        self.dialogo.close()
        self.lleno_grilla()

    def borrar(self):
        #se puede borrar el registro o dar de baja con un movimiento
        if self.tblListado.currentRow()==None:
            return
        id = self.tblListado.item(self.tblListado.currentRow(),0).text()
        if id=='':
            return
        # Crear el mensaje
        msg = QMessageBox()
        msg.setWindowTitle("EnerGis")
        msg.setText(f"Desea quitar el transformador seleccionado (id={id})?")
        msg.setIcon(QMessageBox.Question)
        # Crear botones personalizados
        btn_borrar = msg.addButton("Borrar registro", QMessageBox.AcceptRole)
        btn_baja = msg.addButton("Dar de baja", QMessageBox.DestructiveRole)
        btn_cancelar = msg.addButton("Cancelar", QMessageBox.RejectRole)
        # Mostrar el diálogo
        msg.exec_()
        # Evaluar la opción elegida
        if msg.clickedButton() == btn_borrar:
            cnn = self.conn
            cursor = cnn.cursor()
            try:
                cursor.execute("DELETE FROM Transformadores WHERE id_trafo=" + str(id))
                cnn.commit()
            except:
                cnn.rollback()
        elif msg.clickedButton() == btn_baja:
            from .frm_mover_trafo import frmMoverTrafo
            self.dialogo = frmMoverTrafo(self.conn, id, '', 0)
            self.dialogo.exec()
            self.dialogo.close()
        else:
            return
        self.lleno_grilla()

    def salir(self):
        self.close()
