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
import pyodbc
from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtWidgets import QFileDialog
from PyQt6 import uic
    
DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_fotos.ui'))

class frmFotos(DialogType, DialogBase):

    def __init__(self, tipo_usuario, conn, geoname):
        super().__init__()
        self.setupUi(self)
        #self.setFixedSize(self.size())
        self.tipo_usuario = tipo_usuario
        self.conn = conn
        self.geoname = geoname

        if self.tipo_usuario==4:
            self.cmdAgregar.setEnabled(False)
            self.cmdBorrar.setEnabled(False)

        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT nombre, imagen, id FROM Fotos WHERE Geoname=" + str(self.geoname))
        #convierto el cursor en array
        self.fotos = tuple(cursor)
        cursor.close()
        self.hslFotos.setMaximum(len(self.fotos))

        self.lblFoto.resize(self.size())

        self.angulo_actual=0

        if len(self.fotos)>0:
            self.hslFotos.setMinimum(1)
            self.mostrar()

        self.cmdAgregar.clicked.connect(self.agregar)
        self.cmdBorrar.clicked.connect(self.borrar)
        self.cmdGirar.clicked.connect(self.girar)
        self.hslFotos.valueChanged.connect(self.mostrar)
        self.cmdSalir.clicked.connect(self.salir)

    def agregar(self):
        fname = QFileDialog.getOpenFileName(self, 'Abrir', 'c:\\',"Archivos de Imagen (*.jpg *.jpeg *.gif)")
        if fname[0]=='':
            return
        f = open(fname[0], 'rb')
        bindata = f.read()
        nombre = os.path.basename(f.name)
        f.close

        cnn = self.conn
        try:
            sql = "INSERT INTO Fotos (geoname, nombre, imagen) VALUES (?,?,?)"
            cnn.cursor().execute(sql, (self.geoname, nombre, pyodbc.Binary(bindata)))
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudo insertar')

        pixmap = QtGui.QPixmap(fname[0])
        self.lblFoto.setPixmap(pixmap.scaled(self.lblFoto.size(), QtCore.Qt.KeepAspectRatio))
        self.lblFoto.setVisible(True)

        self.actualizo_fotos()

        QMessageBox.information(None, 'EnerGis 6', 'ℹ️ Grabado !')

        #esto es para varios archivos
        #dlg = QFileDialog()
        #dlg.setFileMode(QFileDialog.AnyFile)
        #dlg.setFilter("Text files (*.txt)")
        #filenames = QStringList()
        #if dlg.exec_():
        #    filenames = dlg.selectedFiles()

    def mostrar(self):
        if len(self.fotos)>0:
            self.pixmap = QtGui.QPixmap()
            self.pixmap.loadFromData(self.fotos[self.hslFotos.value()-1][1])
            self.lblFoto.setPixmap(self.pixmap.scaled(self.lblFoto.size(), QtCore.Qt.KeepAspectRatio))

    def borrar(self):
        if self.hslFotos.value()-1<0:
            return
        reply = QMessageBox.question(None, 'EnerGis 6', 'Desea borrar la foto seleccionada ?', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            cursor = self.conn.cursor()
            try:
                cursor.execute("DELETE FROM Fotos WHERE Id=" + str(self.fotos[self.hslFotos.value()-1][2]))
                self.conn.commit()
            except:
                self.conn.rollback()
                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudo borrar')
            self.lblFoto.clear()
            self.actualizo_fotos()

    def actualizo_fotos(self):
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT nombre, imagen, id FROM Fotos WHERE Geoname=" + str(self.geoname))
        #convierto el cursor en array
        self.fotos = tuple(cursor)
        cursor.close()
        self.hslFotos.setMaximum(len(self.fotos))

    def girar(self):
        if self.pixmap:
            # Incrementar el ángulo de rotación
            self.angulo_actual += 90  # Rotación de 90 grados en sentido horario
            self.angulo_actual %= 360  # Mantener el ángulo dentro del rango [0, 360]

            # Crear un QTransform para rotar la imagen
            transform = QtGui.QTransform()
            transform.rotate(self.angulo_actual)

            # Aplicar la transformación al QPixmap
            pixmap_rotado = self.pixmap.transformed(transform, QtCore.Qt.SmoothTransformation)

            # Mostrar la imagen rotada en el QLabel
            self.lblFoto.setPixmap(pixmap_rotado.scaled(self.lblFoto.size(), QtCore.Qt.KeepAspectRatio))

    def salir(self):
        self.close()
