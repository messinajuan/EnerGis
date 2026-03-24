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

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_datos_ejes.ui'))

class frmDatosEjes(DialogType, DialogBase):

    def __init__(self, tipo_usuario, conn, ftrs_ejes):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.tipo_usuario = tipo_usuario
        self.conn = conn
        self.ftrs_ejes = ftrs_ejes

        self.str_ejes = "0"
        for i in range (0, len(self.ftrs_ejes)):
            self.str_ejes = self.str_ejes + ',' + str(ftrs_ejes[i].id())

        if self.tipo_usuario==4:
            self.cmdCiudades.setEnabled(False)
            self.cmdCalles.setEnabled(False)
            self.cmdAceptar.setEnabled(False)

        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT ciudad, descripcion FROM Ciudades")
        #convierto el cursor en array
        self.ciudades = tuple(cursor)
        cursor.close()

        self.cmbCiudad.addItem('<Indistinto>')
        for ciudad in self.ciudades:
            self.cmbCiudad.addItem(ciudad[1])
        self.cmbCiudad.setCurrentIndex(0)

        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT ciudad, descripcion FROM Calles WHERE ciudad='0'")
        #convierto el cursor en array
        self.calles = tuple(cursor)
        cursor.close()

        self.cmbCalle.clear()
        for calle in self.calles:
            self.cmbCalle.addItem(calle[1])

        self.txtIzqde.textChanged.connect(self.alturas_desde)
        self.txtIzqa.textChanged.connect(self.alturas_hasta)

        self.txtIzqde.setText('0')

        self.cmdCiudades.clicked.connect(self.abm_ciudades)
        self.cmdCalles.clicked.connect(self.abm_calles)

        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)
        self.cmbCiudad.activated.connect(self.elijo_ciudad)

    def elijo_ciudad(self): #Evento de elegir
        self.ciudad=0
        #busco en la base el id del elemento seleccionado
        for i in range (0, len(self.ciudades)):
            if self.cmbCiudad.currentText()==self.ciudades[i][1]:
                self.ciudad = self.ciudades[i][0]

        if self.cmbCiudad.currentText()=='<indistinto>':
            cnn = self.conn
            cursor = cnn.cursor()
            cursor.execute("SELECT calle, descripcion FROM Calles")
            #convierto el cursor en array
            self.calles = tuple(cursor)
            cursor.close()
        else:
            cnn = self.conn
            cursor = cnn.cursor()
            cursor.execute("SELECT calle, descripcion FROM Calles WHERE ciudad='" + str(self.ciudad) + "'")
            #convierto el cursor en array
            self.calles = tuple(cursor)
            cursor.close()

        self.cmbCalle.clear()
        for calle in self.calles:
            self.cmbCalle.addItem(str(calle[1]))

    def abm_ciudades(self):
        from .frm_abm_ciudades import frmAbmCiudades
        dialogo = frmAbmCiudades(self.conn)
        dialogo.exec()
        dialogo.close()
        pass

    def abm_calles(self):
        from .frm_abm_calles import frmAbmCalles
        self.dialogo = frmAbmCalles(self.conn)
        self.dialogo.show()
        pass

    def aceptar(self):
        if self.toolBox.currentIndex()==2:
            if self.chkInvertir.isChecked()==True:
                cnn = self.conn
                cursor = cnn.cursor()
                cursor.execute("SELECT Valor FROM Configuracion WHERE Variable='SRID'")
                rows = cursor.fetchall()
                cursor.close()
                srid = rows[0][0]

                cnn = self.conn
                cnn.autocommit = False
                cursor = cnn.cursor()
                for i in range (0, len(self.ftrs_ejes)):
                    geom = self.ftrs_ejes[i].geometry()
                    vertices  = geom.asPolyline()
                    X2 = vertices[0].x()
                    Y2 = vertices[0].y()
                    X1 = vertices[1].x()
                    Y1 = vertices[1].y()
                    try:
                        cursor.execute("UPDATE Ejes SET obj=geometry::STGeomFromText(" + "'LINESTRING (" + str(X1) + " " + str(Y1) + "," + str(X2) + " " + str(Y2) + ")', " + srid + ") WHERE Geoname=" + str(self.ftrs_ejes[i].id()))
                        cnn.commit()
                    except:
                        cnn.rollback()
                        QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo actualizar !")
                        return
                QMessageBox.information(None, 'EnerGis 6', "ℹ️ Actualizado !")
            return

        id_ciudad=0
        id_calle=0
        for ciudad in self.ciudades:
            if self.cmbCiudad.currentText()==ciudad[1]:
                id_ciudad=ciudad[0]
        for calle in self.calles:
            if self.cmbCalle.currentText()==calle[1]:
                id_calle=calle[0]
        try:
            cnn = self.conn
            cnn.autocommit = False
            cursor = cnn.cursor()
            if self.toolBox.currentIndex()==0:
                str_set = "Ciudad='" + str(id_ciudad) + "', "
                str_set = str_set + "Calle=" + str(id_calle)
            if self.toolBox.currentIndex()==1:
                str_set = "IzqDe=" + self.txtIzqde.text() + ", "
                str_set = str_set + "IzqA=" + self.txtIzqa.text() + ", "
                str_set = str_set + "DerDe=" + self.txtDerde.text() + ", "
                str_set = str_set + "DerA=" + self.txtDera.text()

            cursor.execute("UPDATE Ejes SET " + str_set + " WHERE Geoname IN (" + self.str_ejes + ")")
            cnn.commit()
            QMessageBox.information(None, 'EnerGis 6', "Actualizado !")
        except:
            cnn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo actualizar !")
        self.close()
        pass

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
        pass
