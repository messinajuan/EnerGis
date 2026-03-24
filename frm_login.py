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
from PyQt6 import QtCore
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QPixmap
from PyQt6 import uic

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_login.ui'))

class frmLogin(DialogType, DialogBase):

    def __init__(self, version, str_conexion_seguridad, nombre_usuario):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(QtCore.Qt.WindowType.WindowSystemMenuHint)
        self.id_usuario_sistema = 0
        self.tipo_usuario = 4
        self.pixmap = QPixmap(os.path.join(basepath,"icons", 'splash.jpg'))
        self.img.setPixmap(self.pixmap)
        # Optional, resize label to image size
        self.img.resize(self.pixmap.width(),self.pixmap.height())
        self.str_conexion_seguridad = str_conexion_seguridad
        self.nombre_usuario = nombre_usuario
        self.lblVersion.setText("Versión " + version)
        self.lblWeb.setOpenExternalLinks(True)
        self.txtUsuario.setText(self.nombre_usuario)
        self.txtPassword.setText('')
        self.txtPassword.setFocus()
        self.buttonBox.accepted.connect(self.aceptar)
        self.buttonBox.rejected.connect(self.salir)
    
    def aceptar(self):
        import winreg
        self.tipo_usuario = 4
        try:
            mensaje = 'No hay acceso a la base de datos ' + self.str_conexion_seguridad
            self.conn_seguridad = pyodbc.connect(self.str_conexion_seguridad)
            mensaje = 'Error buscando usuario'
            cursor = self.conn_seguridad.cursor()
            cursor.execute("SELECT id_usuario_sistema,us_nombre,us_contraseña,us_aplicacion,us_tipo_usuario FROM usuarios_sistema WHERE us_aplicacion='energis' AND us_nombre_usuario='" + self.txtUsuario.text() + "'")
            rows = cursor.fetchall()
            cursor.close()
            if len(rows)==0:
                QMessageBox.critical(None, 'EnerGis 6', '❌ Usuario incorrecto !')
                return
            mensaje = 'Error recorriendo tabla usuarios'
            for row in rows:
                if str(self.txtPassword.text()) == str(row[2]):
                    self.id_usuario_sistema = str(row[0])
                    self.tipo_usuario = str(row[4])
                    #me agrego a la lista de sesiones
                    cursor = self.conn_seguridad.cursor()
                    cursor.execute("UPDATE usuarios_sistema SET us_logged=1 WHERE us_aplicacion='energis' AND id_usuario_sistema=" + self.id_usuario_sistema)
                    cursor.close()
                    self.close()
                    #guardo el usuario
                    # Definir la ruta de la clave del registro en la que quieres escribir
                    ruta_clave = r"SOFTWARE\EnerGis"
                    try:
                        # Abrir la clave del registro en modo de escritura
                        clave_registro = winreg.OpenKey(winreg.HKEY_CURRENT_USER, ruta_clave, 0, winreg.KEY_WRITE)
                        #guardo el usuario
                        # Definir la ruta de la clave del registro en la que quieres escribir
                        ruta_clave = r"SOFTWARE\EnerGis"
                        try:
                            # Abrir la clave del registro en modo de escritura
                            clave_registro = winreg.OpenKey(winreg.HKEY_CURRENT_USER, ruta_clave, 0, winreg.KEY_WRITE)
                            # Escribir un valor en la clave del registro
                            nombre_valor = "Usuario"
                            valor = self.txtUsuario.text()
                            winreg.SetValueEx(clave_registro, nombre_valor, 0, winreg.REG_SZ, valor)
                            # Cerrar la clave del registro
                            winreg.CloseKey(clave_registro)
                        except:
                            # Crear la clave en el registro
                            try:
                                # Intentar crear la nueva clave del registro
                                winreg.CreateKey(winreg.HKEY_CURRENT_USER, ruta_clave)
                            except:
                                pass
                            #guardo el usuario
                            # Definir la ruta de la clave del registro en la que quieres escribir
                            ruta_clave = r"SOFTWARE\EnerGis"
                            try:
                                # Abrir la clave del registro en modo de escritura
                                clave_registro = winreg.OpenKey(winreg.HKEY_CURRENT_USER, ruta_clave, 0, winreg.KEY_WRITE)
                                # Escribir un valor en la clave del registro
                                nombre_valor = "Usuario"
                                valor = self.txtUsuario.text()
                                winreg.SetValueEx(clave_registro, nombre_valor, 0, winreg.REG_SZ, valor)
                                # Cerrar la clave del registro
                                winreg.CloseKey(clave_registro)
                            except:
                                # Crear la clave en el registro
                                try:
                                    # Intentar crear la nueva clave del registro
                                    winreg.CreateKey(winreg.HKEY_CURRENT_USER, ruta_clave)
                                except:
                                    pass
                                #guardo el usuario
                                # Definir la ruta de la clave del registro en la que quieres escribir
                                ruta_clave = r"SOFTWARE\EnerGis"
                                try:
                                    # Abrir la clave del registro en modo de escritura
                                    clave_registro = winreg.OpenKey(winreg.HKEY_CURRENT_USER, ruta_clave, 0, winreg.KEY_WRITE)
                                    # Escribir un valor en la clave del registro
                                    nombre_valor = "Usuario"
                                    valor = self.txtUsuario.text()
                                    winreg.SetValueEx(clave_registro, nombre_valor, 0, winreg.REG_SZ, valor)
                                    # Cerrar la clave del registro
                                    winreg.CloseKey(clave_registro)
                                except:
                                    # Crear la clave en el registro
                                    try:
                                        # Intentar crear la nueva clave del registro
                                        winreg.CreateKey(winreg.HKEY_CURRENT_USER, ruta_clave)
                                    except:
                                        pass

                        # Escribir un valor en la clave del registro
                        nombre_valor = "Usuario"
                        valor = self.txtUsuario.text()
                        winreg.SetValueEx(clave_registro, nombre_valor, 0, winreg.REG_SZ, valor)
                        # Cerrar la clave del registro
                        winreg.CloseKey(clave_registro)
                    except:
                        # Crear la clave en el registro
                        try:
                            # Intentar crear la nueva clave del registro
                            winreg.CreateKey(winreg.HKEY_CURRENT_USER, ruta_clave)
                        except:
                            pass
                else:
                    QMessageBox.critical(None, 'EnerGis 6', '❌ Contraseña incorrecta !')
                    self.txtPassword.setText('')
            #guardo el usuario
            self.nombre_usuario = self.txtUsuario.text()
        except:
            QMessageBox.information(None, 'EnerGis 6', "ℹ️ " + mensaje)

    def salir(self):
        self.tipo_usuario = 4
        self.close()
