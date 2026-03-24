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

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_areas.ui'))

class frmAreas(DialogType, DialogBase):

    def __init__(self, tipo_usuario, mapCanvas, conn, obj, geoname):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.tipo_usuario = tipo_usuario
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.obj = obj
        self.geoname = geoname
        self.localidad=0

        cnn = self.conn
        cursor = cnn.cursor()
        self.ciudades=[]
        cursor.execute("SELECT Ciudad, Descripcion FROM Ciudades")
        #convierto el cursor en array
        self.ciudades = tuple(cursor)
        cursor.close()
        for i in range (0, len(self.ciudades)):
            self.cmbLocalidad.addItem(self.ciudades[i][1])

        self.cmbZona.addItem('Rural')
        self.cmbZona.addItem('SubUrbana')
        self.cmbZona.addItem('Urbana')

        if self.geoname != 0:
            self.lblArea.setText(str(self.geoname))
            cursor = cnn.cursor()
            cursor.execute("SELECT Ciudades.Descripcion, Areas.Nombre, Areas.Descripcion, Areas.Localidad FROM Areas LEFT JOIN Ciudades ON Areas.Localidad=Ciudades.ciudad WHERE Geoname=" + str(self.geoname))
            #convierto el cursor en array
            datos_area = tuple(cursor)
            cursor.close()

            if datos_area[0][0]!=None:
                #self.cmbLocalidad.setCurrentIndex(0)
                for i in range (0, self.cmbLocalidad.count()):
                    if self.cmbLocalidad.itemText(i) == str(datos_area[0][0]):
                        self.cmbLocalidad.setCurrentIndex(i)

            for i in range (0, self.cmbZona.count()):
                if self.cmbZona.itemText(i) == str(datos_area[0][1]):
                    self.cmbZona.setCurrentIndex(i)

            self.txtBarrio.setText(str(datos_area[0][2]))
            self.localidad = datos_area[0][3]

        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)

    def aceptar(self):
        obj = ''
        
        if self.geoname == 0: #Si es area nueva -> INSERT
            cnn = self.conn
            cnn.autocommit = False
            cursor = cnn.cursor()
            cursor.execute("SELECT iid FROM iid")
            iid = tuple(cursor)
            id = iid[0][0] + 1
            cursor.execute("UPDATE iid SET iid =" + str(id))
            cnn.commit()

            cursor = cnn.cursor()
            cursor.execute("SELECT Valor FROM Configuracion WHERE Variable='SRID'")
            rows = cursor.fetchall()
            cursor.close()
            srid = rows[0][0]

            obj = "geometry::STGeomFromText(" + "'" + self.obj.geometry().asWkt() + "'," + srid + ")"
            str_valores = str(id) + ", "

            for i in range (0, len(self.ciudades)):
                if self.cmbLocalidad.itemText(i) == str(self.ciudades[i][1]):
                    self.localidad = self.ciudades[i][0]

            str_valores = str_valores + "'" + str(self.localidad) + "', "
            str_valores = str_valores + "'" + self.cmbZona.currentText() + "', "
            str_valores = str_valores + "'" + self.txtBarrio.text() + "', "
            str_valores = str_valores + obj

            cursor = cnn.cursor()
            try:
                cursor.execute("INSERT INTO Areas (Geoname, Localidad, Nombre, Descripcion, obj) VALUES (" + str_valores + ")")
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudieron insertar Areas !")
            pass

        else: #Si cambio algo -> UPDATE
            cnn = self.conn
            cnn.autocommit = False
            cursor = cnn.cursor()

            for i in range (0, len(self.ciudades)):
                if self.cmbLocalidad.itemText(i) == str(self.ciudades[i][1]):
                    self.localidad = self.ciudades[i][0]

            str_set = "Localidad='" + str(self.localidad) + "', "
            str_set = str_set + "Nombre='" + self.cmbZona.currentText() + "', "
            str_set = str_set + "Descripcion='" + self.txtBarrio.text() + "'"

            try:
                cursor.execute("UPDATE Areas SET " + str_set + " WHERE Geoname=" + str(self.geoname))
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
