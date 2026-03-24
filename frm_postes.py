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
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QDoubleValidator, QIntValidator
from PyQt6.QtWidgets import QMessageBox
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_postes.ui'))

class frmPostes(DialogType, DialogBase):
        
    def __init__(self, tipo_usuario, mapCanvas, conn, tension, geoname, elemento_asociado, geoname_asociado, zona, punto):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.tipo_usuario = tipo_usuario
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.tension = tension
        self.geoname = geoname
        self.zona = zona
        self.elemento_asociado = elemento_asociado
        self.geoname_asociado = geoname_asociado
        self.nodo=0
        self.elmt=0
        self.arrEstructura = []
        self.arrPoste = []
        self.arrRienda = []
        vfloat = QDoubleValidator()
        self.txtCota.setValidator(vfloat)
        self.txtAltura.setValidator(vfloat)
        vint = QIntValidator()
        self.txtDescargadores.setValidator(vint)
        self.punto = punto

        if self.tipo_usuario==4:
            self.cmdNuevo.setEnabled(False)
            self.cmdAceptar.setEnabled(False)

        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT id, descripcion FROM Estructuras")
        #convierto el cursor en array
        rows = tuple(cursor)
        cursor.close()
        for row in rows:
            self.arrEstructura.append(row)
            self.cmbEstructura.addItem(str(row[1]))

        cursor = cnn.cursor()
        cursor.execute("SELECT id, descripcion, estilo FROM Elementos_Postes")
        #convierto el cursor en array
        rows = tuple(cursor)
        cursor.close()
        for row in rows:
            self.arrPoste.append(row)
            self.cmbPoste.addItem(str(row[1]))

        self.cmbTipo.addItem('Monoposte')
        self.cmbTipo.addItem('Biposte')
        self.cmbTipo.addItem('Triposte')
        self.cmbTipo.addItem('Disposición A')
        self.cmbTipo.addItem('Contraposte')
        self.cmbTipo.addItem('Rienda')

        self.cmbAislacion.addItem('Suspensión')
        self.cmbAislacion.addItem('Suspensión con Morsa')
        self.cmbAislacion.addItem('Perno Rígido')
        self.cmbAislacion.addItem('Line Post')
        self.cmbAislacion.addItem('Percha')

        cursor = cnn.cursor()
        cursor.execute("SELECT id, descripcion FROM Riendas")
        #convierto el cursor en array
        rows = tuple(cursor)
        cursor.close()
        b_existe=False
        for row in rows:
            self.arrRienda.append(row)
            self.cmbRienda.addItem(str(row[1]))
            if str(row[1])=="Sin Rienda":
                b_existe=True
        if b_existe==False:
            self.cmbRienda.addItem("Sin Rienda")

        self.cmbComparte.addItem('No')
        self.cmbComparte.addItem('Telefonía')
        self.cmbComparte.addItem('VideoCable')
        self.cmbComparte.addItem('Otro')

        self.cmbTernas.addItem('Simple Terna')
        self.cmbTernas.addItem('2 Ternas')
        self.cmbTernas.addItem('3 Ternas')
        self.cmbTernas.addItem('4 Ternas')
        self.cmbTernas.addItem('Alumbrado')

        cursor = cnn.cursor()
        cursor.execute("SELECT Tension FROM Niveles_Tension WHERE Tension>=50")
        #convierto el cursor en array
        tensiones = tuple(cursor)
        cursor.close()

        n = self.mapCanvas.layerCount()
        j = 0
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:6] == 'Postes':
                str_tension = lyr.name() [7 - len(lyr.name()):]
                for tension in tensiones:
                    if str(tension[0])==str_tension:
                        self.cmbCapa.addItem(str_tension)
                        if str_tension == self.tension:
                            j = self.cmbCapa.count() - 1

        if self.cmbCapa.count()==0:
            QMessageBox.exclamation(None, 'EnerGis 6', '❌ Verifique que la capa de postes se encuentre visible !')
            self.close()

        self.cmbCapa.setCurrentIndex(j)
        if self.geoname != 0:
            self.lblPoste.setText(str(self.geoname))
            cursor = cnn.cursor()
            cursor.execute("SELECT Estructura,CASE WHEN Riendas.id IS NULL THEN 'Sin Rienda' ELSE Riendas.descripcion END AS Rienda,Altura,Nivel,Tension,Zona,Modificacion,tipo,Aislacion,Fundacion,Comparte,Ternas,PAT,ISNULL(Descargadores,0) AS descargadores,elmt FROM Postes LEFT JOIN Elementos_Postes ON Postes.Elmt=Elementos_Postes.id LEFT JOIN Riendas ON Postes.rienda=Riendas.id WHERE Geoname=" + str(self.geoname))
            #convierto el cursor en array
            datos_poste = tuple(cursor)
            cursor.close()
            for i in range (0, len(self.arrEstructura)):
                if datos_poste[0][0]==self.arrEstructura[i][0]:
                    self.cmbEstructura.setCurrentIndex(i)

            for i in range (0, self.cmbRienda.count()):
                if self.cmbRienda.itemText(i) == str(datos_poste[0][1]):
                    self.cmbRienda.setCurrentIndex(i)
            self.txtAltura.setText(str(datos_poste[0][2]))
            self.txtCota.setText(str(datos_poste[0][3]))
            for i in range (0, self.cmbCapa.count()):
                if self.cmbCapa.itemText(i) == str(datos_poste[0][4]):
                    self.cmbCapa.setCurrentIndex(i)
            self.lblZona.setText(str(datos_poste[0][5]))
            self.datInstalacion.setDate(datos_poste[0][6])
            for i in range (0, self.cmbTipo.count()):
                if self.cmbTipo.itemText(i) == str(datos_poste[0][7]):
                    self.cmbTipo.setCurrentIndex(i)
            for i in range (0, self.cmbAislacion.count()):
                if self.cmbAislacion.itemText(i) == str(datos_poste[0][8]):
                    self.cmbAislacion.setCurrentIndex(i)
            if datos_poste[0][9]==1:
                self.chkFundacion.setChecked(True)
            for i in range (0, self.cmbComparte.count()):
                if self.cmbComparte.itemText(i) == str(datos_poste[0][10]):
                    self.cmbComparte.setCurrentIndex(i)
            for i in range (0, self.cmbTernas.count()):
                if self.cmbTernas.itemText(i) == str(datos_poste[0][11]):
                    self.cmbTernas.setCurrentIndex(i)
            if datos_poste[0][12]==1:
                self.chkPat.setChecked(True)
            self.txtDescargadores.setText(str(datos_poste[0][13]))
            for i in range (0, len(self.arrPoste)):
                if datos_poste[0][14]==self.arrPoste[i][0]:
                    self.cmbPoste.setCurrentIndex(i)

        else: #Poste nuevo
            if self.zona!=0:
                cnn = self.conn
                cursor = cnn.cursor()
                cursor.execute("SELECT Nombre FROM Areas WHERE geoname=" + str(self.zona))
                #convierto el cursor en array
                self.rs = tuple(cursor)
                cursor.close()
                self.lblZona.setText(self.rs[0][0])
            else:
                self.lblZona.setText('Rural')

            self.datInstalacion.setDate(QDate.currentDate())

        self.cmdNuevo.clicked.connect(self.agregar)
        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)

    def closeEvent(self, event):
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:6] == 'Postes':
                lyr.triggerRepaint()
                
    def agregar(self):
        from .frm_abm_postes import frmAbmPostes

        for i in range (0, len(self.arrPoste)):
            if self.cmbPoste.currentText()==self.arrPoste[i][1]:
                apoyo=self.arrPoste[i][0]

        for i in range (0, len(self.arrEstructura)):
            if self.cmbEstructura.currentText()==self.arrEstructura[i][1]:
                estructura=self.arrEstructura[i][0]

        for i in range (0, len(self.arrRienda)):
            if self.cmbRienda.currentText()==self.arrRienda[i][1]:
                rienda=self.arrRienda[i][0]

        dialogo = frmAbmPostes(self.conn, self.tipo_usuario, apoyo, estructura, rienda)
        dialogo.exec()

    def aceptar(self):
        x_coord=0
        y_coord=0
        obj = ''
        self.elmt=0
        estilo = '39-MapInfo Oil&Gas-0-8421504-12-0'
        estructura=0
        rienda=0
        id=0

        if self.geoname == 0: #Si es nuevo -> INSERT
            x_coord = self.punto.x()
            y_coord = self.punto.y()

            cnn = self.conn
            cursor = cnn.cursor()
            cursor.execute("SELECT Valor FROM Configuracion WHERE Variable='SRID'")
            rows = cursor.fetchall()
            cursor.close()
            srid = rows[0][0]
            obj = "geometry::Point(" + str(x_coord) + ',' + str(y_coord) + ',' + srid + ")"

            for i in range (0, len(self.arrPoste)):
                if self.cmbPoste.currentText()==self.arrPoste[i][1]:
                    self.elmt=self.arrPoste[i][0]
                    estilo=self.arrPoste[i][2]

            for i in range (0, len(self.arrEstructura)):
                if self.cmbEstructura.currentText()==self.arrEstructura[i][1]:
                    estructura=self.arrEstructura[i][0]

            for i in range (0, len(self.arrRienda)):
                if self.cmbRienda.currentText()==self.arrRienda[i][1]:
                    rienda=self.arrRienda[i][0]

            cnn = self.conn
            cnn.autocommit = False
            cursor = cnn.cursor()
            cursor.execute("SELECT iid FROM iid")
            iid = tuple(cursor)
            id = iid[0][0] + 1
            cursor.execute("UPDATE iid SET iid =" + str(id))
            cnn.commit()
            
            cursor = cnn.cursor()
            str_valores = str(id) + ", "
            str_valores = str_valores + str(self.nodo) + ", "
            str_valores = str_valores + str(x_coord) + ", "
            str_valores = str_valores + str(y_coord) + ", "
            str_valores = str_valores + str(self.elmt) + ", "
            str_valores = str_valores + "'" + estilo + "', "
            str_valores = str_valores + str(estructura) + ", "
            str_valores = str_valores + str(rienda) + ", "
            str_valores = str_valores + self.txtAltura.text() + ", "
            str_valores = str_valores + self.txtCota.text() + ", "
            str_valores = str_valores + "'" + self.lblZona.text() + "', "
            str_valores = str_valores + self.cmbCapa.currentText() + ", "
            str_valores = str_valores + "'" + self.cmbTipo.currentText() + "', "
            str_valores = str_valores + "'" + self.cmbAislacion.currentText() + "', "
            if self.chkFundacion.isChecked() == True:
                str_valores = str_valores + "'1', "
            else:
                str_valores = str_valores + "'0', "
            str_valores = str_valores + "'" + self.cmbComparte.currentText() + "', "
            str_valores = str_valores + "'" + self.cmbTernas.currentText() + "', "
            str_valores = str_valores + "'" + str(self.datInstalacion.date().toPyDate()).replace('-','') + "', "
            if self.chkPat.isChecked() == True:
                str_valores = str_valores + "'1', "
            else:
                str_valores = str_valores + "'0', "
            str_valores = str_valores + self.txtDescargadores.text() + ", "
            str_valores = str_valores + obj
            try:
                cursor.execute("INSERT INTO Postes (Geoname,id_nodo,XCoord,YCoord,elmt,estilo,estructura,rienda,altura,nivel,zona,tension,tipo,aislacion,fundacion,comparte,ternas,modificacion,pat,descargadores,obj) VALUES (" + str_valores + ")")
                cnn.commit()
                if self.elemento_asociado=='1':
                    cursor.execute('UPDATE Postes SET id_nodo=' +  str(self.geoname_asociado) + ' WHERE Geoname=' + str(id))
                    cnn.commit()
                    self.salir()
                elif self.elemento_asociado=='2':
                    cursor.execute('INSERT INTO Lineas_Postes(id_linea, id_poste) VALUES (' + str(self.geoname_asociado) + ', ' + str(str(id)) + ')')
                    cnn.commit()
                    self.salir()
            except:
                cnn.rollback()
                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudo insertar en la Base de Datos')

        else: #Si cambio algo -> UPDATE

            cnn = self.conn
            cursor = cnn.cursor()
            for i in range (0, len(self.arrPoste)):
                if self.cmbPoste.currentText()==self.arrPoste[i][1]:
                    self.elmt=self.arrPoste[i][0]
                    estilo=self.arrPoste[i][2]

            for i in range (0, len(self.arrEstructura)):
                if self.cmbEstructura.currentText()==self.arrEstructura[i][1]:
                    estructura=self.arrEstructura[i][0]

            for i in range (0, len(self.arrRienda)):
                if self.cmbRienda.currentText()==self.arrRienda[i][1]:
                    rienda=self.arrRienda[i][0]

            str_set = "id_nodo=" + str(self.nodo) + ", "
            str_set = str_set + "elmt=" + str(self.elmt) + ", "
            str_set = str_set + "estilo='" + estilo + "', "
            str_set = str_set + "estructura=" + str(estructura) + ", "
            str_set = str_set + "rienda=" + str(rienda) + ", "
            str_set = str_set + "altura=" + self.txtAltura.text() + ", "
            str_set = str_set + "nivel=" + self.txtCota.text() + ", "
            str_set = str_set + "zona='" + self.lblZona.text() + "', "
            str_set = str_set + "tension=" + self.cmbCapa.currentText() + ", "
            str_set = str_set + "tipo='" + self.cmbTipo.currentText() + "', "
            str_set = str_set + "aislacion='" +  self.cmbAislacion.currentText() + "', "
            if self.chkFundacion.isChecked() == True:
                str_set = str_set + "fundacion=1, "
            else:
                str_set = str_set + "fundacion=0, "
            str_set = str_set + "comparte='" +  self.cmbComparte.currentText() + "', "
            str_set = str_set + "ternas='" +  self.cmbTernas.currentText() + "', "
            str_set = str_set + "modificacion='" + str(self.datInstalacion.date().toPyDate()).replace('-','') + "', "
            if self.chkPat.isChecked() == True:
                str_set = str_set + "pat=1, "
            else:
                str_set = str_set + "pat=0, "
            str_set = str_set + "descargadores=" + self.txtDescargadores.text()
            try:
                cursor.execute("UPDATE Postes SET " + str_set + " WHERE Geoname=" + str(self.geoname))
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudo actualizar la Base de Datos')
        self.close()

    def salir(self):
        self.close()
