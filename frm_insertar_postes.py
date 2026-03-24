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
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QDoubleValidator
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_insertar_postes.ui'))

class frmInsertarPostes(DialogType, DialogBase):
        
    def __init__(self, proyecto, mapCanvas, conn, tension, geoname, p1, p2):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.proyecto = proyecto
        if tension == 'Proyectos':
            self.tension = '0'
            cnn = self.conn
            cursor = cnn.cursor()
            cursor.execute("SELECT Exp FROM Lineas WHERE geoname=" + str(geoname))
            #convierto el cursor en array
            rows = tuple(cursor)
            cursor.close()
            self.str_profundidad = rows[0][0]
        else:
            self.tension = tension
            self.str_profundidad = 0
        self.geoname = geoname
        self.p1 = p1
        self.p2 = p2
        self.longitud = 0
        self.elmt = 0
        self.arrEstructura = []
        self.arrPoste = []
        self.arrRienda = []
        vfloat = QDoubleValidator()
        self.txtAltura.setValidator(vfloat)

        #self.longitud = pow((pow((self.p2.x()-self.p1.x()), 2) + pow((self.p2.y()-self.p1.y()), 2)), 0.5)
        self.longitud = self.p1.distance(self.p2)
        self.lblLongitud.setText(str(format(self.longitud, ",.2f")))

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

        self.datInstalacion.setDate(QDate.currentDate())
        self.spbCantidad.setMinimum(0)
        self.spbCantidad.valueChanged.connect(self.cantidad)

        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)
        pass

    def cantidad(self):
        self.txtVano.setText(str(format(self.longitud/(self.spbCantidad.value()+1), ",.2f")))

    def aceptar(self):
        x=0
        y=0
        obj = ''
        self.elmt=0
        estilo = '39-MapInfo Oil&Gas-0-8421504-12-0'
        estructura=0
        rienda=0
        id=0

        if self.spbCantidad.value()=='0':
            return

        #obj = geom.asWkt()
        #obj = obj [:len(obj)-1]
        #obj = obj + ", 22194)"
        #---------------------------
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT Valor FROM Configuracion WHERE Variable='SRID'")
        rows = cursor.fetchall()
        cursor.close()
        srid = rows[0][0]

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

        cant_postes_a_insertar = self.spbCantidad.value()
        for t in range (1, cant_postes_a_insertar + 1):
            if self.p2.x() > self.p1.x():
                x = self.p1.x() + t * ((self.p2.x() - self.p1.x()) / (cant_postes_a_insertar + 1))
            elif self.p1.x() > self.p2.x():
                x = self.p1.x() - t * ((self.p1.x() - self.p2.x()) / (cant_postes_a_insertar + 1))
            else:
                x = self.p1.x()
            if self.p2.y() > self.p1.y():
                y = self.p1.y() + t * ((self.p2.y() - self.p1.y()) / (cant_postes_a_insertar + 1))
            elif self.p1.y() > self.p2.y():
                y = self.p1.y() - t * ((self.p1.y() - self.p2.y()) / (cant_postes_a_insertar + 1))
            else:
                y = self.p1.y()

            obj = "geometry::Point(" + str(x) + ',' + str(y) + ',' + srid + ")"

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
            str_valores = str_valores + "0, "
            str_valores = str_valores + "'" + self.proyecto + "', "
            str_valores = str_valores + str(x) + ", "
            str_valores = str_valores + str(y) + ", "
            str_valores = str_valores + str(self.elmt) + ", "
            str_valores = str_valores + "'" + estilo + "', "
            str_valores = str_valores + str(estructura) + ", "
            str_valores = str_valores + str(rienda) + ", "
            str_valores = str_valores + self.txtAltura.text() + ", "
            str_valores = str_valores + "0, " #cota
            str_valores = str_valores + "'', " #zona, la tomo de la linea que la toma de los nodos
            str_valores = str_valores + str(self.tension) + ", "
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
            str_valores = str_valores + "0, "
            str_valores = str_valores + "'" + str(self.str_profundidad) + "', "
            str_valores = str_valores + obj
            try:
                cursor.execute("INSERT INTO Postes (Geoname,id_nodo,descripcion,XCoord,YCoord,elmt,estilo,estructura,rienda,altura,nivel,zona,tension,tipo,aislacion,fundacion,comparte,ternas,modificacion,pat,descargadores,profundidad,obj) VALUES (" + str_valores + ")")
                cnn.commit()
                cursor.execute('INSERT INTO Lineas_Postes(id_linea, id_poste) VALUES (' + str(self.geoname) + ', ' + str(str(id)) + ')')
                cnn.commit()
                n = self.mapCanvas.layerCount()
                layers = [self.mapCanvas.layer(i) for i in range(n)]
                for lyr in layers:
                    if lyr.name()[:6] == 'Postes':
                            lyr.triggerRepaint()
                self.salir()
            except:
                cnn.rollback()
                QMessageBox.critical(None, 'EnerGis 6', '❌ Error al insertar el poste')
        pass

    def salir(self):
        self.close()
        pass
