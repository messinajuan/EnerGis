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
from PyQt6.QtWidgets import QMessageBox, QInputDialog
from qgis.core import QgsProject
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_seguridad.ui'))

class frmSeguridad(DialogType, DialogBase):

    def __init__(self, str_conexion_seguridad):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.cmbTipoUsuario.addItem("Administrador")
        self.cmbTipoUsuario.addItem("Editor de Red")
        self.cmbTipoUsuario.addItem("Calidad")
        self.cmbTipoUsuario.addItem("Consulta")
        try:
            self.conn_seguridad = pyodbc.connect(str_conexion_seguridad)
        except:
            QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo conectar a la Base de Datos de Seguridad !")
            return

        self.cargar_usuarios()

        self.liwUsuarios.currentRowChanged.connect(self.elijo_usuario)
        self.cmdNuevo.clicked.connect(self.agregar)
        self.cmdBorrar.clicked.connect(self.borrar)
        self.cmdGuardar.clicked.connect(self.guardar)
        self.cmdSalir.clicked.connect(self.salir)

    def cargar_usuarios(self):
        self.liwUsuarios.clear()
        cursor = self.conn_seguridad.cursor()
        cursor.execute("SELECT us_nombre,us_nombre_usuario,us_contraseña,us_tipo_usuario FROM usuarios_sistema WHERE us_aplicacion='energis'")
        self.usuarios = cursor.fetchall()
        for usuario in self.usuarios:
            self.liwUsuarios.addItem(usuario[1])

    def elijo_usuario(self):
        if self.liwUsuarios.currentItem()==None:
            return
        for i in range (0, len(self.usuarios)):
            if self.liwUsuarios.currentItem().text()==self.usuarios[i][1]:
                self.txtNombre.setText(self.usuarios[i][0])
                for j in range (0, self.cmbTipoUsuario.count()):
                    if self.usuarios[i][3]==j+1:
                        self.cmbTipoUsuario.setCurrentIndex(j)
                self.txtUsuario.setText(self.usuarios[i][1])
                self.txtPassword.setText(self.usuarios[i][2])

    def guardar(self):
        reply = QMessageBox.question(None, 'EnerGis 6', 'Desea guardar los cambios ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        try:
            cursor = self.conn_seguridad.cursor()
            cursor.execute("UPDATE usuarios_sistema SET us_nombre='" + self.txtNombre.text() + "', us_contraseña='" + self.txtPassword.text() + "', us_tipo_usuario=" + str(self.cmbTipoUsuario.currentIndex()+1) + " WHERE us_nombre_usuario='" + self.txtUsuario.text() + "'")
            self.conn_seguridad.commit()
        except:
            self.conn_seguridad.rollback()
            QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo guardar !")
            return
        self.cargar_usuarios()

    def borrar(self):
        reply = QMessageBox.question(None, 'EnerGis 6', 'Desea borrar el usuario ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        try:
            cursor = self.conn_seguridad.cursor()
            cursor.execute("DELETE FROM usuarios_sistema WHERE us_nombre='" + self.txtNombre.text() + "'")
            self.conn_seguridad.commit()
        except:
            self.conn_seguridad.rollback()
            QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo borrar el usuario !")
            return
        self.txtNombre.setText("")
        self.txtUsuario.setText("")
        self.txtPassword.setText("")
        self.cargar_usuarios()

    def agregar(self):
        text, ok = QInputDialog.getText(None, 'Ingreso de Datos', 'Nombre del Usuario')
        if ok:
            nuevo_usuario = str(text)
        else:
            return
        if nuevo_usuario=='':
            return
        self.txtNombre.setText("Nombre completo")
        self.txtUsuario.setText(nuevo_usuario)
        self.txtPassword.setText("pwd")
        cursor = self.conn_seguridad.cursor()
        cursor.execute("SELECT MAX(id_usuario_sistema) FROM usuarios_sistema")
        rows = cursor.fetchall()
        cursor.close()
        id = rows[0][0] + 1
        reply = QMessageBox.question(None, 'EnerGis 6', 'Desea agregar un nuevo usuario ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        try:
            cursor = self.conn_seguridad.cursor()
            cursor.execute("INSERT INTO usuarios_sistema (id_usuario_sistema, us_nombre, us_nombre_usuario, us_contraseña, us_aplicacion,us_tipo_usuario) VALUES (" + str(id) + ",'" + self.txtNombre.text() + "','" + self.txtUsuario.text() + "','" + self.txtPassword.text() + "','energis'," + str(self.cmbTipoUsuario.currentIndex()+1) + ")")
            self.conn_seguridad.commit()
        except:
            self.conn_seguridad.rollback()
            QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo agregar el usuario !")
            return
        self.cargar_usuarios()

    def salir(self):
        self.close()
