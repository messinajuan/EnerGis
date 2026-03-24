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
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_parcelas.ui'))

class frmParcelas(DialogType, DialogBase):

    def __init__(self, tipo_usuario, mapCanvas, conn, obj, geoname):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.tipo_usuario = tipo_usuario
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.obj = obj
        self.geoname = geoname

        if self.geoname != 0:
            cnn = self.conn
            cursor = cnn.cursor()
            cursor.execute("SELECT Parcela, Manzana, Chacra, Quinta, Circunscripcion, Seccion FROM Parcelas WHERE geoname=" + str(self.geoname))
            #convierto el cursor en array
            parcelas = tuple(cursor)
            cursor.close()

            self.lblGeoname.setText(str(self.geoname))
            self.txtParcela.setText(str(parcelas[0][0]))
            self.txtManzana.setText(str(parcelas[0][1]))
            self.txtChacra.setText(str(parcelas[0][2]))
            self.txtQuinta.setText(str(parcelas[0][3]))
            self.txtCircunscripcion.setText(str(parcelas[0][4]))
            self.txtSeccion.setText(str(parcelas[0][5]))

        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)

    def aceptar(self):
        obj = ''
        
        if self.geoname == 0: #Si es nueva -> INSERT
            cnn = self.conn
            cnn.autocommit = False
            cursor = cnn.cursor()
            cursor.execute("SELECT iid FROM iid")
            iid = tuple(cursor)
            id = iid[0][0] + 1
            cursor.execute("UPDATE iid SET iid =" + str(id))
            cnn.commit()

            cursor = cnn.cursor()
            cursor.execute("SELECT VAlor FROM Configuracion WHERE Variable='SRID'")
            rows = cursor.fetchall()
            cursor.close()
            srid = rows[0][0]

            obj = "geometry::STGeomFromText(" + "'" + self.obj.geometry().asWkt() + "'," + srid + ")"

            str_valores = str(id) + ", "
            str_valores = str_valores + "'" + self.txtParcela.text() + "', "
            str_valores = str_valores + "'" + self.txtManzana.text() + "', "
            str_valores = str_valores + "'" + self.txtChacra.text() + "', "
            str_valores = str_valores + "'" + self.txtQuinta.text() + "', "
            str_valores = str_valores + "'" + self.txtCircunscripcion.text() + "', "
            str_valores = str_valores + "'" + self.txtSeccion.text() + "', "
            str_valores = str_valores + obj
            try:
                cursor = cnn.cursor()
                cursor.execute("INSERT INTO Parcelas (Geoname, Parcela, Manzana, Chacra, Quinta, Circunscripcion, Seccion, obj) VALUES (" + str_valores + ")")
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudo insertar en la Base de Datos')

        else: #Si cambio algo -> UPDATE
            cnn = self.conn
            cursor = cnn.cursor()
            str_set = "Parcela='" + self.txtParcela.text() + "', "
            str_set = str_set + "Manzana='" + self.txtManzana.text() + "', "
            str_set = str_set + "Chacra='" + self.txtChacra.text() + "', "
            str_set = str_set + "Quinta='" + self.txtQuinta.text() + "', "
            str_set = str_set + "Circunscripcion='" + self.txtCircunscripcion.text() + "', "
            str_set = str_set + "Seccion='" + self.txtSeccion.text() + "'"
            try:
                cursor.execute("UPDATE Parcelas SET " + str_set + " WHERE Geoname=" + str(self.geoname))
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudo actualizar la Base de Datos')

        self.close()
        pass

    def salir(self):
        self.close()
        pass
