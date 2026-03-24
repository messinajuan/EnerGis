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
from PyQt6 import uic
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QIntValidator
from PyQt6.QtGui import QDoubleValidator
#from qgis.core import *

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_reasignar_postes.ui'))

class frmReasignarPostes(DialogType, DialogBase):
        
    def __init__(self, mapCanvas, conn, inn):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.inn = inn
        self.arrEstructura = []
        self.arrPoste = []
        self.arrRienda = []
        vint = QIntValidator()
        vfloat = QDoubleValidator()
        self.txtDescargadores.setValidator(vint)
        self.txtAltura.setValidator(vfloat)
        self.txtCota.setValidator(vfloat)

        b_existe=False

        self.cmbCapa.addItem('Todas')
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT Tension FROM Niveles_Tension WHERE Tension>=200")
        #convierto el cursor en array
        tensiones = tuple(cursor)
        cursor.close()
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:6] == 'Postes':
                str_tension = lyr.name() [7 - len(lyr.name()):]
                for tension in tensiones:
                    if str(tension[0])==str_tension:
                        self.cmbCapa.addItem(str_tension)

        self.cmbEstructura.addItem('Todas')
        self.cmbNuevaEstructura.addItem('<No Modificar>')

        cursor = cnn.cursor()
        cursor.execute("SELECT id, descripcion FROM Estructuras")
        #convierto el cursor en array
        rows = tuple(cursor)
        cursor.close()
        for row in rows:
            self.arrEstructura.append(row)
            self.cmbEstructura.addItem(str(row[1]))
            self.cmbNuevaEstructura.addItem(str(row[1]))

        self.cmbPoste.addItem('<No Modificar>')
        cursor = cnn.cursor()
        cursor.execute("SELECT id, descripcion, estilo FROM Elementos_Postes")
        #convierto el cursor en array
        rows = tuple(cursor)
        cursor.close()
        for row in rows:
            self.arrPoste.append(row)
            self.cmbPoste.addItem(str(row[1]))

        self.cmbTipo.addItem('<No Modificar>')
        self.cmbTipo.addItem('Monoposte')
        self.cmbTipo.addItem('Biposte')
        self.cmbTipo.addItem('Triposte')
        self.cmbTipo.addItem('Disposición A')
        self.cmbTipo.addItem('Contraposte')
        self.cmbTipo.addItem('Rienda')

        self.cmbAislacion.addItem('<No Modificar>')
        self.cmbAislacion.addItem('Suspensión')
        self.cmbAislacion.addItem('Perno Rígido')
        self.cmbAislacion.addItem('Line Post')
        self.cmbAislacion.addItem('Percha')

        self.cmbRienda.addItem('<No Modificar>')
        cursor = cnn.cursor()
        cursor.execute("SELECT id, descripcion FROM Riendas")
        #convierto el cursor en array
        rows = tuple(cursor)
        cursor.close()
        for row in rows:
            self.arrRienda.append(row)
            self.cmbRienda.addItem(str(row[1]))
            if str(row[1])=="Sin Rienda":
                b_existe=True
        if b_existe==False:
            self.cmbRienda.addItem("Sin Rienda")

        self.cmbComparte.addItem('<No Modificar>')
        self.cmbComparte.addItem('No')
        self.cmbComparte.addItem('Telefonía')
        self.cmbComparte.addItem('VideoCable')
        self.cmbComparte.addItem('Otro')

        self.cmbTernas.addItem('<No Modificar>')
        self.cmbTernas.addItem('Simple Terna')
        self.cmbTernas.addItem('2 Ternas')
        self.cmbTernas.addItem('3 Ternas')
        self.cmbTernas.addItem('4 Ternas')
        self.cmbTernas.addItem('Alumbrado')

        self.chkFundacion.setCheckState(1)
        self.chkPat.setCheckState(1)

        self.chkInstalacion.clicked.connect(self.cambiar_fecha)
        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)
        
    def cambiar_fecha(self):
        if self.chkInstalacion.checkState()==2:
            self.datInstalacion.setEnabled(True)
        else:
            self.datInstalacion.setEnabled(False)

    def aceptar(self):
        elmt = 0
        estructura = 0
        rienda = 0
        str_where = "geoname IN (" + self.inn + ")"

        if self.cmbCapa.currentText() != 'Todas':
            str_where = str_where + " AND Tension=" + self.cmbCapa.currentText()

        for i in range (0, len(self.arrPoste)):
            if self.cmbPoste.currentText()==self.arrPoste[i][1]:
                elmt=self.arrPoste[i][0]

        for i in range (0, len(self.arrEstructura)):
            if self.cmbNuevaEstructura.currentText()==self.arrEstructura[i][1]:
                estructura=self.arrEstructura[i][0]

        for i in range (0, len(self.arrRienda)):
            if self.cmbRienda.currentText()==self.arrRienda[i][1]:
                rienda=self.arrRienda[i][0]

        if self.cmbEstructura.currentText() != 'Todas':
            str_where = str_where + " AND estructura=" + str(estructura)

        str_set = "nivel=nivel"
        if self.cmbNuevaEstructura.currentText() != '<No Modificar>':
            str_set = str_set + ", estructura=" + str(estructura)
        if self.cmbPoste.currentText() != '<No Modificar>':
            str_set = str_set + ", elmt=" + str(elmt)
        if self.cmbTipo.currentText() != '<No Modificar>':
            str_set = str_set + ", tipo='" + self.cmbTipo.currentText() + "'"
        if self.cmbAislacion.currentText() != '<No Modificar>':
            str_set = str_set + ", aislacion='" + self.cmbAislacion.currentText() + "'"
        if self.cmbRienda.currentText() != '<No Modificar>':
            str_set = str_set + ", rienda=" + str(rienda)
        if self.cmbComparte.currentText() != '<No Modificar>':
            str_set = str_set + ", comparte=" + self.cmbComparte.currentText() + "'"
        if self.cmbTernas.currentText() != '<No Modificar>':
            str_set = str_set + ", ternas='" + self.cmbTernas.currentText() + "'"

        if self.txtDescargadores.text()!= "#":
            str_set = str_set + ", descargadores=" + self.txtDescargadores.text()
        if self.txtAltura.text()!= "#":
            str_set = str_set + ", altura=" + self.txtAltura.text()
        if self.txtCota.text()!= "#":
            str_set = str_set + ", nivel=" + self.txtCota.text()

        if self.chkFundacion.checkState() == 2:
            str_set = str_set + ", fundacion=1"
        if self.chkFundacion.checkState() == 0:
            str_set = str_set + ", fundacion=0"

        if self.chkPat.checkState() == 2:
            str_set = str_set + ", pat=1"
        if self.chkPat.checkState() == 0:
            str_set = str_set + ", pat=0"

        if self.chkInstalacion.isChecked() == True:
            str_set = str_set + ", modificacion='" + str(self.datInstalacion.date().toPyDate()).replace('-','') + "'"

        reply = QMessageBox.question(None, 'EnerGis 6', 'Desea cambiar los datos de los postes seleccionados ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return

        cnn = self.conn
        cursor = cnn.cursor()
        try:
            cursor.execute("UPDATE Postes SET " + str_set + " WHERE " + str_where)
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudo actualizar la Base de Datos')

    def salir(self):
        self.close()
