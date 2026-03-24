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
from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QDoubleValidator
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_nodos.ui'))

class frmNodos(DialogType, DialogBase):
        
    def __init__(self, tipo_usuario, mapCanvas, conn, tension, geoname, zona, punto):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.tipo_usuario = tipo_usuario
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.tension = tension
        self.geoname = geoname
        self.zona = zona
        self.arrNodo = []
        self.localidad = 0
        self.elmt=0
        self.uucc=""
        self.where=''
        self.cmdDatosCt.setVisible(False)
        self.cmdCargas.setVisible(False)
        self.cmdMediciones.setVisible(False)
        vfloat = QDoubleValidator()
        self.txtCota.setValidator(vfloat)
        self.punto = punto
        self.nombre_anterior=""
        self.nombre=""
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
            if elemento[0]==1:
                self.cmbElemento.addItem(QtGui.QIcon(os.path.join(basepath,"icons", 'img_fuente.png')), elemento[1], elemento[0])
            if elemento[0]==8:
                self.cmbElemento.addItem(QtGui.QIcon(os.path.join(basepath,"icons", 'img_salida_alimentador.png')), elemento[1], elemento[0])
            if elemento[0]==2:
                self.cmbElemento.addItem(QtGui.QIcon(os.path.join(basepath,"icons", 'img_seccionador_cerrado.png')), elemento[1], elemento[0])
            if elemento[0]==3:
                self.cmbElemento.addItem(QtGui.QIcon(os.path.join(basepath,"icons", 'img_seccionador_abierto.png')), elemento[1], elemento[0])
            if elemento[0]==4:
                self.cmbElemento.addItem(QtGui.QIcon(os.path.join(basepath,"icons", 'img_transformador.png')), elemento[1], elemento[0])
            if elemento[0]==9:
                self.cmbElemento.addItem(QtGui.QIcon(os.path.join(basepath,"icons", 'img_regulador_tension.png')), elemento[1], elemento[0])
            if elemento[0]==7:
                self.cmbElemento.addItem(QtGui.QIcon(os.path.join(basepath,"icons", 'img_capacitor.png')), elemento[1], elemento[0])
            if elemento[0]==6:
                self.cmbElemento.addItem(QtGui.QIcon(os.path.join(basepath,"icons", 'img_suministro.png')), elemento[1], elemento[0])
            if elemento[0]==5:
                self.cmbElemento.addItem(QtGui.QIcon(os.path.join(basepath,"icons", 'img_luminaria.png')), elemento[1], elemento[0])
            if elemento[0]==11:
                self.cmbElemento.addItem(QtGui.QIcon(os.path.join(basepath,"icons", 'img_generador.png')), elemento[1], elemento[0])
            if elemento[0]==10:
                self.cmbElemento.addItem(QtGui.QIcon(os.path.join(basepath,"icons", 'img_fin_linea.png')), elemento[1], elemento[0])
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
                        if str_tension == self.tension:
                            j = self.cmbCapa.count() - 1
        self.cmbCapa.setCurrentIndex(j)
        if self.geoname != 0:
            self.lblNodo.setText(str(self.geoname))
            cursor = cnn.cursor()
            cursor.execute("SELECT Nombre, Nodos.Descripcion, ISNULL(Elementos_Nodos.Descripcion, 0) AS Elemento, Nivel, Zona, Subzona, ISNULL(Localidad, 0) AS Localidad, Alimentador, Modificacion, Tension, UUCC, Elmt FROM Nodos LEFT JOIN Elementos_Nodos ON Nodos.Elmt=Elementos_Nodos.id WHERE Geoname=" + str(self.geoname))
            #convierto el cursor en array
            datos_nodo = tuple(cursor)
            cursor.close()
            self.nombre_anterior = str(datos_nodo[0][0])
            self.txtNombre.setText(self.nombre_anterior)
            self.txtDescripcion.setPlainText(str(datos_nodo[0][1]))
            self.cmbElemento.setCurrentIndex(0)
            for i in range (0, self.cmbElemento.count()):
                if self.cmbElemento.itemText(i) == str(datos_nodo[0][2]):
                    self.cmbElemento.setCurrentIndex(i)

            for i in range (0, self.cmbCapa.count()):
                if self.cmbCapa.itemText(i) == str(datos_nodo[0][9]):
                    self.cmbCapa.setCurrentIndex(i)
            self.txtCota.setText(str(datos_nodo[0][3]))
            self.lblZona.setText(str(datos_nodo[0][4]))
            self.lblSubzona.setText(str(datos_nodo[0][5]))
            self.localidad = datos_nodo[0][6]
            self.lblAlimentador.setText(str(datos_nodo[0][7]))
            if datos_nodo[0][10] != None:
                self.txtUUCC.setText(str(datos_nodo[0][10]))
            self.elmt = datos_nodo[0][11]
            if self.elmt == 4:
                self.cmdDatosCt.setVisible(True)
                self.cmdCargas.setVisible(True)
                self.cmdMediciones.setVisible(True)
            if self.elmt == 6:
                self.cmdCargas.setVisible(True)
            #setCurrentDate(QDate::currentDate())
            #self.datInstalacion.setDisplayFormat('dd MM yyyy')
            self.datInstalacion.setDate(datos_nodo[0][8])
            cursor = cnn.cursor()
            cursor.execute("SELECT Aux FROM mNodos WHERE Geoname=" + str(self.geoname))
            #convierto el cursor en array
            datos_nodo = tuple(cursor)
            cursor.close()
            self.lblAux.setText('(' + str(datos_nodo[0][0])  + ')')
        else: #Nodo nuevo
            if self.zona!=0:
                cnn = self.conn
                cursor = cnn.cursor()
                cursor.execute("SELECT Nombre, Localidad, Descripcion FROM Areas WHERE geoname=" + str(self.zona))
                #convierto el cursor en array
                self.rs = tuple(cursor)
                cursor.close()
                self.lblZona.setText(self.rs[0][0])
                self.localidad = self.rs[0][1]
                self.lblSubzona.setText(self.rs[0][2])
            else:
                self.lblZona.setText('Rural')
                self.localidad = 1
            self.datInstalacion.setDate(QDate.currentDate())
        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdValores.clicked.connect(self.valores)
        #self.cmdCoordenadas.clicked.connect(self.coordenadas)
        self.cmdDatosCt.clicked.connect(self.datos_ct)
        self.cmdUUCC.clicked.connect(self.elegir_uucc)
        self.cmbCapa.activated.connect(self.elijo_tension)
        self.cmdCargas.clicked.connect(self.cargas)
        self.cmdFotos.clicked.connect(self.fotos)
        self.cmdMediciones.clicked.connect(self.mediciones)
        self.cmbElemento.activated.connect(self.elijo_elemento)
        self.cmdSalir.clicked.connect(self.salir)

    def elijo_tension(self):
        self.tension = int(self.cmbCapa.currentText())

    def closeEvent(self, event):
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyr.triggerRepaint()
        
    def elijo_elemento(self): #Evento de elegir
        #busco en la base el id del elemento seleccionado
        for i in range (0, len(self.elementos_nodos)):
            if self.cmbElemento.currentText()==self.elementos_nodos[i][1]:
                self.elmt = self.elementos_nodos[i][0]
                if self.elmt == 4:
                    self.cmdDatosCt.setVisible(True)

    def coordenadas(self):
        from .mod_coordenadas import convertir_coordenadas
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT Valor FROM Configuracion WHERE Variable='SRID'")
        coordenadas_nodo = tuple(cursor)
        cursor.close()
        srid = coordenadas_nodo[0][0]
        if self.geoname == 0: #Si es nodo nuevo
            x = self.punto.x()
            y = self.punto.y()
        else:
            cnn = self.conn
            cursor = cnn.cursor()
            cursor.execute("SELECT xcoord, ycoord FROM Nodos WHERE geoname=" + str(self.geoname))
            coordenadas_nodo = tuple(cursor)
            cursor.close()
            x = coordenadas_nodo[0][0]
            y = coordenadas_nodo[0][1]
            resultado = str(convertir_coordenadas(self, x, y, srid, 4326))
        QMessageBox.information(None, 'EnerGis 6', 'ℹ️ ' + resultado.replace('[','').replace(']',''))

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

        if self.elmt==2 or self.elmt==3:
            cnn = self.conn
            cursor = cnn.cursor()
            cursor.execute("SELECT Val1 FROM Nodos WHERE geoname=" + str(self.geoname))
            #convierto el cursor en array
            rst = tuple(cursor)
            cursor.close()
            if len(rst)==0:
                self.valores()
                return
            elif rst[0][0]=='' or rst[0][0]==None:
                cursor = cnn.cursor()
                cursor.execute("UPDATE Nodos SET Val1='Seccionador' WHERE geoname=" + str(self.geoname))
                cnn.commit()
                self.valores()
                return

        if self.elmt==2 or self.elmt==3 or self.elmt==4 or self.elmt==7 or self.elmt==9:
            if self.txtUUCC.text()=='':
                self.elegir_uucc()
            if self.txtUUCC.text()=='':
                return

        if self.geoname == 0: #Si es nodo nuevo -> INSERT
            x_coord = self.punto.x()
            y_coord = self.punto.y()
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
            cursor.execute("SELECT MAX(Aux) FROM Nodos")
            auxnodos = tuple(cursor)
            cursor.close()
            if auxnodos[0][0]==None:
                aux = 1
            else:
                aux = auxnodos[0][0] + 1
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
            str_valores = str_valores + self.txtCota.text() + ", "
            str_valores = str_valores + self.cmbCapa.currentText() + ", "
            str_valores = str_valores + "'" + self.lblZona.text() + "', "
            str_valores = str_valores + "'" + self.lblAlimentador.text() + "', "
            str_valores = str_valores + str(aux) + ", "
            str_valores = str_valores + "'" + str(self.datInstalacion.date().toPyDate()).replace('-','') + "', "
            str_valores = str_valores + "'" + self.lblSubzona.text() + "', "
            str_valores = str_valores + str(self.elmt) + ", "
            str_valores = str_valores + str(self.localidad) + ", "
            str_valores = str_valores + "'" + self.txtUUCC.text() + "', "
            str_valores = str_valores + obj
            try:
                cursor.execute("INSERT INTO Nodos (Geoname, Nombre, Descripcion, Elmt, XCoord, YCoord, Estilo, Val1, Val2, Val3, Val4, Val5, Nivel, Tension, Zona, Alimentador, Aux, Modificacion, Subzona, Estado, Localidad, UUCC, obj) VALUES (" + str_valores + ")")
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.critical(None, 'EnerGis 6', '❌ No se pudo insertar en la Base de Datos')
        else: #Si cambio algo -> UPDATE
            self.nombre = self.txtNombre.text().replace("'","")
            cnn = self.conn
            cursor = cnn.cursor()
            str_set = "Nombre='" + self.nombre + "', "
            str_set = str_set + "Descripcion='" + self.txtDescripcion.toPlainText().replace("'","") + "', "
            str_set = str_set + "Elmt=" + str(self.elmt) + ", "
            str_set = str_set + "Estilo='" + estilo + "', "
            str_set = str_set + "Nivel=" + self.txtCota.text() + ", "
            str_set = str_set + "Tension=" + self.cmbCapa.currentText() + ", "
            str_set = str_set + "Modificacion='" + str(self.datInstalacion.date().toPyDate()).replace('-','') + "', "
            str_set = str_set + "Estado=" + str(self.elmt) + ", "
            str_set = str_set + "UUCC='" + self.txtUUCC.text() + "'"
            try:
                cursor.execute("UPDATE Nodos SET " + str_set + " WHERE Geoname=" + str(self.geoname))
                cnn.commit()
                if self.elmt==4 and self.nombre_anterior != self.nombre:
                    cnn = self.conn
                    cursor = cnn.cursor()
                    cursor.execute("UPDATE Ct SET id_ct='" + self.nombre + "' WHERE id_ct='" + self.nombre_anterior + "'")
                    if self.nombre_anterior!="":
                        cursor.execute("UPDATE Transformadores SET id_ct='" + self.nombre + "' WHERE usado=3 AND id_ct='" + self.nombre_anterior + "'")
                    cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudo actualizar la Base de Datos')
        self.close()

    def valores(self):
        if self.geoname==0:
            x_coord = 0
            y_coord = 0
            obj = ''
            self.elmt=0
            estilo = '35-EnerGIS-16777215-0-2-0'
            x_coord = self.punto.x()
            y_coord = self.punto.y()
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
            cursor.execute("SELECT MAX(Aux) FROM Nodos")
            auxnodos = tuple(cursor)
            cursor.close()
            if auxnodos[0][0]==None:
                aux = 1
            else:
                aux = auxnodos[0][0] + 1
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
            str_valores = str_valores + self.txtCota.text() + ", "
            str_valores = str_valores + self.cmbCapa.currentText() + ", "
            str_valores = str_valores + "'" + self.lblZona.text() + "', "
            str_valores = str_valores + "'" + self.lblAlimentador.text() + "', "
            str_valores = str_valores + str(aux) + ", "
            str_valores = str_valores + "'" + str(self.datInstalacion.date().toPyDate()).replace('-','') + "', "
            str_valores = str_valores + "'" + self.lblSubzona.text() + "', "
            str_valores = str_valores + str(self.elmt) + ", "
            str_valores = str_valores + str(self.localidad) + ", "
            str_valores = str_valores + "'" + self.txtUUCC.text() + "', "
            str_valores = str_valores + obj
            try:
                cursor.execute("INSERT INTO Nodos (Geoname, Nombre, Descripcion, Elmt, XCoord, YCoord, Estilo, Val1, Val2, Val3, Val4, Val5, Nivel, Tension, Zona, Alimentador, Aux, Modificacion, Subzona, Estado, Localidad, UUCC, obj) VALUES (" + str_valores + ")")
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.critical(None, 'EnerGis 6', '❌ No se pudo insertar en la Base de Datos')
            self.geoname = id
        if self.cmbElemento.currentText() != "Nodo Simple":
            cnn = self.conn
            cursor = cnn.cursor()
            cursor.execute("SELECT id FROM Elementos_Nodos WHERE Descripcion='" + self.cmbElemento.currentText() + "'")
            rows = cursor.fetchall()
            cursor.close()
            for row in rows:
                self.elmt = row[0]
        if self.elmt==1 or self.elmt==11:
            from .frm_fuentes import frmFuentes
            dialogo = frmFuentes(self.tipo_usuario, self.conn, self.geoname, self.elmt)
            dialogo.exec()
            self.txtDescripcion.setText(dialogo.txtSSEE.text())
            if dialogo.elmt==1:
                for i in range (0, self.cmbElemento.count()):
                    if self.cmbElemento.itemText(i) == 'Fuente':
                        self.cmbElemento.setCurrentIndex(i)
            if dialogo.elmt==11:
                for i in range (0, self.cmbElemento.count()):
                    if self.cmbElemento.itemText(i) == 'Generador':
                        self.cmbElemento.setCurrentIndex(i)
            dialogo.close()
        if self.elmt==2 or self.elmt==3:
            from .frm_seccionadores import frmSeccionadores
            self.dialogo = frmSeccionadores(self.tipo_usuario, self.conn, self.tension, self.geoname)
            self.dialogo.show()
        if self.elmt==4:
            if self.txtNombre.text()=='':
                return
            from .frm_transformadores import frmTransformadores
            self.dialogo = frmTransformadores(self.tipo_usuario, self.conn, self.tension, self.geoname, self.txtNombre.text())
            self.dialogo.show()
        if self.elmt==6:
            from .frm_suministros import frmSuministros
            self.dialogo = frmSuministros(self.tipo_usuario, self.conn, self.geoname)
            self.dialogo.show()
        if self.elmt==8:
            from .frm_salidas import frmSalidas
            self.dialogo = frmSalidas(self.tipo_usuario, self.conn, self.geoname, self.txtDescripcion.toPlainText())
            self.dialogo.show()
        if self.elmt==9:
            from .frm_reguladores import frmReguladores
            self.dialogo = frmReguladores(self.tipo_usuario, self.conn, self.geoname)
            self.dialogo.show()

    def fotos(self):
        from .frm_fotos import frmFotos
        self.dialogo = frmFotos(self.tipo_usuario, self.conn, self.geoname)
        self.dialogo.show()

    def mediciones(self):
        from .frm_calidad_producto import frmCalidadProducto
        self.dialogo = frmCalidadProducto(self.conn, self.txtNombre.text())
        self.dialogo.show()

    def cargas(self):


        if self.elmt==4:
            from .frm_cargas import frmCargas
            self.dialogo = frmCargas(self.conn, self.geoname, 4)
            self.dialogo.show()
        if self.elmt==6:
            from .frm_cargas import frmCargas
            self.dialogo = frmCargas(self.conn, self.geoname, 6)
            self.dialogo.show()

    def datos_ct(self):
        if self.elmt==4:
            if self.txtNombre.text()=='':
                #return
                self.sql="SELECT Ct.Id_ct FROM Nodos RIGHT OUTER JOIN Ct ON Nodos.Nombre = Ct.Id_ct WHERE Nodos.Geoname IS NULL"
                from .frm_elegir import frmElegir
                dialogo = frmElegir(self.mapCanvas, self.conn, self.sql)
                dialogo.tblListado.setColumnWidth(0, 400)
                dialogo.exec()
                if dialogo.seleccionado != '':
                    self.txtNombre.setText(dialogo.seleccionado)
            from .frm_ct import frmCT
            self.dialogo = frmCT(self.tipo_usuario, self.conn, self.tension, self.geoname, self.txtNombre.text())
            self.dialogo.show()

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

            if len(self.recordset)==0:
                self.txtUUCC.setText("SIN TRAFO")
                return

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

    def salir(self):
        self.close()
