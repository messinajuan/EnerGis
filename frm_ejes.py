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

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_ejes.ui'))

class frmEjes(DialogType, DialogBase):

    def __init__(self, tipo_usuario, mapCanvas, conn, X1, Y1, X2, Y2, geoname):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.tipo_usuario = tipo_usuario
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.X1 = X1
        self.Y1 = Y1
        self.X2 = X2
        self.Y2 = Y2
        self.geoname = geoname
        if self.tipo_usuario==4:
            self.cmdCiudades.setEnabled(False)
            self.cmdCalles.setEnabled(False)
            self.cmdAceptar.setEnabled(False)
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT RTRIM(ciudad) AS ciudad, descripcion FROM Calles WHERE RTRIM(ciudad)='0' ORDER BY descripcion")
        #convierto el cursor en array
        self.calles = tuple(cursor)
        cursor.close()
        self.cmbCalle.clear()
        for calle in self.calles:
            self.cmbCalle.addItem(calle[1])
        self.id_ciudad='0'
        self.cargar_ciudades()
        if self.geoname != 0:
            self.lblEje.setText(str(self.geoname))
            cnn = self.conn
            cursor = cnn.cursor()
            cursor.execute("SELECT ISNULL(Ciudades.Descripcion,'<Indistinto>'), ISNULL(Calles.descripcion, '<Desc>'), Ejes.IzqDe, Ejes.IzqA, Ejes.DerDe, Ejes.DerA, Ejes.ciudad FROM Ejes LEFT OUTER JOIN Ciudades ON Ejes.Ciudad = Ciudades.Ciudad LEFT OUTER JOIN Calles ON Ejes.Calle = Calles.calle WHERE Geoname=" + str(self.geoname))
            #convierto el cursor en array
            datos_eje = tuple(cursor)
            cursor.close()
            for i in range (0, self.cmbCiudad.count()):
                if self.cmbCiudad.itemText(i) == datos_eje[0][0]:
                    self.cmbCiudad.setCurrentIndex(i)
                    self.id_ciudad = datos_eje[0][6]
            self.cargar_calles()
            #self.cmbCalle.setCurrentIndex(0)
            for i in range (0, self.cmbCalle.count()):
                if self.cmbCalle.itemText(i) == str(datos_eje[0][1]):
                    self.cmbCalle.setCurrentIndex(i)
            self.txtIzqde.setText(str(datos_eje[0][2]))
            self.txtIzqa.setText(str(datos_eje[0][3]))
            self.txtDerde.setText(str(datos_eje[0][4]))
            self.txtDera.setText(str(datos_eje[0][5]))
        self.txtIzqde.textChanged.connect(self.alturas_desde)
        self.txtIzqa.textChanged.connect(self.alturas_hasta)
        self.cmdCiudades.clicked.connect(self.abm_ciudades)
        self.cmdCalles.clicked.connect(self.abm_calles)
        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)
        self.cmbCiudad.activated.connect(self.elijo_ciudad)

    def cargar_ciudades(self):
        self.cmbCiudad.clear()
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT RTRIM(ciudad), descripcion FROM Ciudades ORDER BY descripcion")
        #convierto el cursor en array
        self.ciudades = tuple(cursor)
        cursor.close()
        self.cmbCiudad.addItem('<Indistinto>')
        for ciudad in self.ciudades:
            self.cmbCiudad.addItem(ciudad[1])
        self.cmbCiudad.setCurrentIndex(0)

    def cargar_calles(self):
        self.cmbCalle.clear()
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT calle, descripcion FROM Calles WHERE ciudad='" + str(self.id_ciudad) + "' ORDER BY descripcion")
        #convierto el cursor en array
        self.calles = tuple(cursor)
        cursor.close()
        for calle in self.calles:
            self.cmbCalle.addItem(calle[1])

    def elijo_ciudad(self): #Evento de elegir
        self.id_ciudad='0'
        #busco en la base el id del elemento seleccionado
        for i in range (0, len(self.ciudades)):
            if self.cmbCiudad.currentText()==self.ciudades[i][1]:
                self.id_ciudad = self.ciudades[i][0]
        self.cargar_calles()

    def abm_ciudades(self):
        from .frm_abm_ciudades import frmAbmCiudades
        dialogo = frmAbmCiudades(self.conn)
        dialogo.exec()
        dialogo.close()
        self.cargar_ciudades()

    def abm_calles(self):
        from .frm_abm_calles import frmAbmCalles
        self.dialogo = frmAbmCalles(self.conn)
        self.dialogo.show()
        self.cargar_calles()

    def aceptar(self):
        id_ciudad='0'
        id_calle=0
        for ciudad in self.ciudades:
            if self.cmbCiudad.currentText()==ciudad[1]:
                id_ciudad=ciudad[0]
        for calle in self.calles:
            if self.cmbCalle.currentText()==calle[1]:
                id_calle=calle[0]
        try:
            if self.geoname == 0: #Si es nuevo -> INSERT
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
                obj = "geometry::STGeomFromText(" + "'LINESTRING (" + str(self.X1) + " " + str(self.Y1) + "," + str(self.X2) + " " + str(self.Y2) + ")', " + srid + ")"
                cursor = cnn.cursor()
                str_valores = str(id) + ", "
                str_valores = str_valores + "'" + id_ciudad + "', "
                str_valores = str_valores + str(id_calle) + ", "
                str_valores = str_valores + self.txtIzqde.text() + ", "
                str_valores = str_valores + self.txtIzqa.text() + ", "
                str_valores = str_valores + self.txtDerde.text() + ", "
                str_valores = str_valores + self.txtDera.text() + ", "
                str_valores = str_valores + str(self.X1) + ", "
                str_valores = str_valores + str(self.Y1) + ", "
                str_valores = str_valores + str(self.X2) + ", "
                str_valores = str_valores + str(self.Y2) + ", "
                str_valores = str_valores + obj
                cursor.execute("INSERT INTO Ejes (Geoname, Ciudad, Calle, IzqDe, IzqA, DerDe, DerA, X1, Y1, X2, Y2, obj) VALUES (" + str_valores + ")")
                cnn.commit()
            else: #Si cambio algo -> UPDATE
                cnn = self.conn
                cnn.autocommit = False
                cursor = cnn.cursor()
                str_set = "Ciudad='" + id_ciudad + "', "
                str_set = str_set + "Calle=" + str(id_calle) + ", "
                str_set = str_set + "IzqDe=" + self.txtIzqde.text() + ", "
                str_set = str_set + "IzqA=" + self.txtIzqa.text() + ", "
                str_set = str_set + "DerDe=" + self.txtDerde.text() + ", "
                str_set = str_set + "DerA=" + self.txtDera.text()
                cursor.execute("UPDATE Ejes SET " + str_set + " WHERE Geoname=" + str(self.geoname))
                cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudo grabar en la base de datos')
        self.close()

    def alturas_desde(self):
        try:
            self.txtDerde.setText(str(int(self.txtIzqde.text())+1))
            self.txtIzqa.setText(str(int(self.txtIzqde.text())+98))
        except:
            pass

    def alturas_hasta(self):
        try:
            self.txtDera.setText(str(int(self.txtIzqa.text())+1))
        except:
            pass

    def salir(self):
        self.close()
