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
from PyQt6 import QtGui
from PyQt6.QtWidgets import QMessageBox
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_nodos_proyecto.ui'))

class frmNodosProyecto(DialogType, DialogBase):
        
    def __init__(self, proyecto, tipo_usuario, mapCanvas, conn, tension, geoname, zona, punto):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.proyecto = proyecto
        self.tipo_usuario = tipo_usuario
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.tension = tension
        self.geoname = geoname
        self.zona = zona
        self.str_zona = 'Rural'
        self.arrNodo = []
        self.localidad = 0
        self.elmt=0
        self.uucc=""
        self.where=''
        self.punto = punto

        if self.tipo_usuario==4:
            self.cmdAceptar.setEnabled(False)

        basepath = os.path.dirname(os.path.realpath(__file__))

        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT id, Descripcion, Estilo FROM Elementos_Nodos")
        #convierto el cursor en array
        self.elementos_nodos = tuple(cursor)
        cursor.close()

        self.cmbElemento.addItem(QtGui.QIcon(os.path.join(basepath,"icons", 'img_nodo_simple.png')), 'Nodo Simple')
        for elemento in self.elementos_nodos:
            self.arrNodo.append(elemento)
            if elemento[0]==2:
                self.cmbElemento.addItem(QtGui.QIcon(os.path.join(basepath,"icons", 'img_seccionador_cerrado.png')), elemento[1], elemento[0])
            if elemento[0]==3:
                self.cmbElemento.addItem(QtGui.QIcon(os.path.join(basepath,"icons", 'img_seccionador_abierto.png')), elemento[1], elemento[0])
            if elemento[0]==4:
                self.cmbElemento.addItem(QtGui.QIcon(os.path.join(basepath,"icons", 'img_transformador.png')), elemento[1], elemento[0])
            if elemento[0]==6:
                self.cmbElemento.addItem(QtGui.QIcon(os.path.join(basepath,"icons", 'img_suministro.png')), elemento[1], elemento[0])
            if elemento[0]==9:
                self.cmbElemento.addItem(QtGui.QIcon(os.path.join(basepath,"icons", 'img_regulador_tension.png')), elemento[1], elemento[0])
            if elemento[0]==11:
                self.cmbElemento.addItem(QtGui.QIcon(os.path.join(basepath,"icons", 'img_generador.png')), elemento[1], elemento[0])

        if self.geoname!=0:
            cursor = cnn.cursor()
            cursor.execute("SELECT subzona AS Tension FROM Nodos WHERE geoname=" + str(self.geoname))
            tensiones = tuple(cursor)
            cursor.close()
            self.tension = tensiones[0][0]

        cursor = cnn.cursor()
        cursor.execute("SELECT Tension FROM Niveles_Tension WHERE Tension>=50")
        #convierto el cursor en array
        tensiones = tuple(cursor)
        cursor.close()

        n = self.mapCanvas.layerCount()
        j = 0
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                str_tension = lyr.name() [6 - len(lyr.name()):]
                for tension in tensiones:
                    if str(tension[0])==str_tension:
                        self.cmbCapa.addItem(str_tension)
                        if str_tension == str(self.tension):
                            j = self.cmbCapa.count() - 1

        self.cmbCapa.setCurrentIndex(j)
        if self.geoname != 0:
            self.lblNodo.setText(str(self.geoname))
            cursor = cnn.cursor()
            cursor.execute("SELECT Nombre, Nodos.Descripcion, ISNULL(Elementos_Nodos.Descripcion, 0) AS Elemento, Nivel, Zona, Subzona, ISNULL(Localidad, 0) AS Localidad, Alimentador, Modificacion, subzona AS Tension, UUCC, Elmt FROM Nodos LEFT JOIN Elementos_Nodos ON Nodos.Elmt=Elementos_Nodos.id WHERE Geoname=" + str(self.geoname))
            #convierto el cursor en array
            datos_nodo = tuple(cursor)
            cursor.close()
            self.txtNombre.setText(str(datos_nodo[0][0]))
            self.txtDescripcion.setPlainText(str(datos_nodo[0][1]))
            self.cmbElemento.setCurrentIndex(0)
            for i in range (0, self.cmbElemento.count()):
                if self.cmbElemento.itemText(i) == str(datos_nodo[0][2]):
                    self.cmbElemento.setCurrentIndex(i)
            for i in range (0, self.cmbCapa.count()):
                if self.cmbCapa.itemText(i) == str(datos_nodo[0][9]):
                    self.cmbCapa.setCurrentIndex(i)
            self.str_zona = str(datos_nodo[0][4])
            self.localidad = datos_nodo[0][6]
            if datos_nodo[0][10] != None:
                self.txtUUCC.setText(str(datos_nodo[0][10]))
            self.elmt = datos_nodo[0][11]

        else: #Nodo nuevo
            if self.zona!=0:
                cnn = self.conn
                cursor = cnn.cursor()
                cursor.execute("SELECT Nombre, Localidad, Descripcion FROM Areas WHERE geoname=" + str(self.zona))
                #convierto el cursor en array
                rs = tuple(cursor)
                cursor.close()
                self.str_zona.setText(self.rs[0][0])
                self.localidad = rs[0][1]
            else:
                self.str_zona = "Rural"
                self.localidad = 1

        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdUUCC.clicked.connect(self.elegir_uucc)
        self.cmdFotos.clicked.connect(self.fotos)
        self.cmbElemento.activated.connect(self.elijo_elemento)
        self.cmdSalir.clicked.connect(self.salir)
        pass

    def closeEvent(self, event):
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name() == 'Nodos Proyectos':
                lyr.triggerRepaint()

    def elijo_elemento(self): #Evento de elegir
        for i in range (0, len(self.elementos_nodos)):
            if self.cmbElemento.currentText()==self.elementos_nodos[i][1]:
                self.elmt = self.elementos_nodos[i][0]
                #if self.elmt == 4:
                #    self.cmdDatosCt.setVisible(True)

    def aceptar(self):
        x_coord = 0
        y_coord = 0
        obj = ''
        self.elmt=0
        estilo = '35-EnerGIS-16777215-0-2-0'

        if self.cmbElemento.currentText() != "Nodo Simple":
            for i in range (0, len(self.arrNodo)):
                if self.cmbElemento.currentText()==self.arrNodo[i][1]:
                    self.elmt=self.arrNodo[i][0]
                    estilo=self.arrNodo[i][2]

        if self.geoname == 0: #Si es nodo nuevo -> INSERT
            x_coord = self.punto.x()
            y_coord = self.punto.y()
            #---------------------------
            cnn = self.conn
            cursor = cnn.cursor()
            cursor.execute("SELECT Valor FROM Configuracion WHERE Variable='SRID'")
            rows = cursor.fetchall()
            cursor.close()
            srid = rows[0][0]
            obj = "geometry::Point(" + str(x_coord) + ',' + str(y_coord) + ',' + srid + ")"
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
            str_valores = str_valores + "'" + self.txtNombre.text() + "', "
            str_valores = str_valores + "'" + self.txtDescripcion.toPlainText() + "', "
            str_valores = str_valores + str(self.elmt) + ", "
            str_valores = str_valores + str(x_coord) + ", "
            str_valores = str_valores + str(y_coord) + ", "
            str_valores = str_valores + "'" + estilo + "', "
            str_valores = str_valores + "'', "
            str_valores = str_valores + "'', "
            str_valores = str_valores + "'', "
            str_valores = str_valores + "'', "
            str_valores = str_valores + "'', "
            str_valores = str_valores + "0, " #cota
            str_valores = str_valores + "0, " #tension
            str_valores = str_valores + "'" + self.str_zona + "', "
            str_valores = str_valores + "'" + self.proyecto + "', " #alimentador
            str_valores = str_valores + "0, "
            str_valores = str_valores + "'', " #fecha
            str_valores = str_valores + "'" + self.cmbCapa.currentText() + "', " #subzona (tension)
            str_valores = str_valores + str(self.elmt) + ", "
            str_valores = str_valores + str(self.localidad) + ", "
            str_valores = str_valores + "'" + self.txtUUCC.text() + "', "
            str_valores = str_valores + obj
            try:
                cursor.execute("INSERT INTO Nodos (Geoname, Nombre, Descripcion, Elmt, XCoord, YCoord, Estilo, Val1, Val2, Val3, Val4, Val5, Nivel, Tension, Zona, Alimentador, Aux, Modificacion, Subzona, Estado, Localidad, UUCC, obj) VALUES (" + str_valores + ")")
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudo insertar en la Base de Datos - INSERT INTO Nodos (Geoname, Nombre, Descripcion, Elmt, XCoord, YCoord, Estilo, Val1, Val2, Val3, Val4, Val5, Nivel, Tension, Zona, Alimentador, Aux, Modificacion, Subzona, Estado, Localidad, UUCC, obj) VALUES (' + str_valores + ')')

        else: #Si cambio algo -> UPDATE

            cnn = self.conn
            cursor = cnn.cursor()
            str_set = "Nombre='" + self.txtNombre.text().replace("'","") + "', "
            str_set = str_set + "Descripcion='" + self.txtDescripcion.toPlainText().replace("'","") + "', "
            str_set = str_set + "Elmt=" + str(self.elmt) + ", "
            #str_set = str_set + "XCoord=" + valor + ", "
            #str_set = str_set + "YCoord=" + valor + ", "
            str_set = str_set + "Estilo='" + estilo + "', "
            #str_set = str_set + "Val1='" + self.valor1 + "', "
            #str_set = str_set + "Val2='" + self.valor2 + "', "
            #str_set = str_set + "Val3='" + self.valor3 + "', "
            #str_set = str_set + "Val4='" + self.valor4 + "', "
            #str_set = str_set + "Val5='" + self.valor5 + "', "
            str_set = str_set + "Nivel=0, "
            str_set = str_set + "Tension=0, "
            #str_set = str_set + "Zona='" + self.zona + "', "
            #str_set = str_set + "Alimentador='" + self.proyecto + "', "
            #str_set = str_set + "Aux=" + valor + ", "
            str_set = str_set + "Modificacion='', "
            str_set = str_set + "Subzona='" + self.cmbCapa.currentText() + "', "
            str_set = str_set + "Estado=" + str(self.elmt) + ", "
            #str_set = str_set + "Localidad=" + str(self.localidad) + ", "
            str_set = str_set + "UUCC='" + self.txtUUCC.text() + "'"
            try:
                cursor.execute("UPDATE Nodos SET " + str_set + " WHERE Geoname=" + str(self.geoname))
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudo actualizar la Base de Datos')
        self.close()
        pass

    def fotos(self):
        from .frm_fotos import frmFotos
        self.dialogo = frmFotos(self.tipo_usuario, self.conn, self.geoname)
        self.dialogo.show()
        pass

    def elegir_uucc(self):
        if self.elmt==0:
            return
        if self.elmt==1:
            self.where = "Tipo IN ('SALIDA')"
        if self.elmt==2:
            self.where = "Tipo IN ('INTERRUPTOR', 'RECONECTADOR', 'SECCIONADOR', 'SECCIONALIZADOR')"
        if self.elmt==3:
            self.where = "Tipo IN ('INTERRUPTOR', 'RECONECTADOR', 'SECCIONADOR', 'SECCIONALIZADOR')"
        if self.elmt==4:
            self.where = "Tipo = 'TRANSFORMACION'"
            cnn = self.conn
            cursor = cnn.cursor()
            cursor.execute("SELECT conexionado, SUM(potencia) FROM Transformadores WHERE Id_ct='" + self.txtNombre.text() + "' GROUP BY conexionado")
            #convierto el cursor en array
            self.recordset = tuple(cursor)
            cursor.close()

            if self.recordset[0][0] == "M" or self.recordset[0][0] == "B":
                self.where = self.where + " AND Fases<3"
                #CInt(Round(CDbl(Combo2.Text) / Sqr(3), 0) / 100) * 100    esto da 7600
            else:
                self.where = self.where + " AND Fases=3"

        if self.elmt==6:
            self.where = "Tipo = 'MEDICION'"
        if self.elmt==7:
            self.where = "Tipo = 'CAPACITOR'"
        if self.elmt==8:
            self.where = "Tipo = 'SALIDA'"
        if self.elmt==9:
            self.where = "Tipo = 'REGULADOR'"

        #if self.where != '':
        self.uucc = self.txtUUCC.text()

        from .frm_elegir_uucc import frmElegirUUCC
        dialogo = frmElegirUUCC(self.conn, self.tension, self.where, self.uucc)
        dialogo.exec()
        if dialogo.uucc != '':
            self.txtUUCC.setText(dialogo.uucc)
        dialogo.close()
        pass

    def salir(self):
        self.close()
        pass
