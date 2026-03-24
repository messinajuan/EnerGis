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

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_seleccionar_elementos.ui'))
basepath = os.path.dirname(os.path.realpath(__file__))

class frmSeleccionarElementos(DialogType, DialogBase):
        
    def __init__(self, mapCanvas, conn):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.cmbCapa.addItem('Ninguna')
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT Tension FROM Niveles_Tension WHERE Tension>=50")
        #convierto el cursor en array
        tensiones = tuple(cursor)
        cursor.close()
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                str_tension = lyr.name() [6 - len(lyr.name()):]
                for tension in tensiones:
                    if str(tension[0])==str_tension:
                        self.cmbCapa.addItem(str_tension)
        self.cmbCapa.addItem('Todas')
        self.cmbAlimentador.addItem('Todos')
        self.cmbZona.addItem('Todas')
        self.cmbZona.addItem('Rural')
        self.cmbZona.addItem('Urbana')
        self.lista_nodos = []
        self.lista_lineas = []
        self.lista_postes = []
        self.cmbCapa.activated.connect(self.elijo)
        self.cmbZona.activated.connect(self.elijo)
        self.cmbAlimentador.activated.connect(self.elijo_alimentador)
        self.liwNodos.itemSelectionChanged.connect(self.modificar)
        self.liwLineas.itemSelectionChanged.connect(self.modificar)
        self.liwPostes.itemSelectionChanged.connect(self.modificar)
        self.tabWidget.currentChanged.connect(self.elijo)
        self.cmdSeleccionNodos.clicked.connect(self.seleccionar_nodos)
        self.cmdSeleccionLineas.clicked.connect(self.seleccionar_lineas)
        self.cmdSeleccionPostes.clicked.connect(self.seleccionar_postes)
        self.cmdSalir.clicked.connect(self.salir)

    def elijo(self):
        self.sqlNodos.setPlainText('')
        self.sqlLineas.setPlainText('')
        self.sqlPostes.setPlainText('')
        self.liwLineas.clear()
        self.liwNodos.clear()
        self.liwPostes.clear()

        str_where = ""
        if self.cmbZona.currentText()!="Todas":
            str_where = str_where + " AND Zona='" + self.cmbZona.currentText() + "'"
        if self.cmbCapa.currentText()!="Todas":
            str_where = str_where + " AND Tension=" + self.cmbCapa.currentText()
        if self.cmbCapa.currentText()=="Ninguna":
            return
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT DISTINCT elmt FROM Nodos WHERE Tension > 0" + str_where + " ORDER BY elmt")
        #convierto el cursor en array
        rst = tuple(cursor)
        cursor.close()
        self.lista_nodos = []
        for i in range (0, len(rst)):
            if rst[i][0]==1:
                self.liwNodos.addItem("Fuentes")
                self.lista_nodos.append(("Fuentes", "1"))
            if rst[i][0]==2:
                self.liwNodos.addItem("Seccionadores Cerrados")
                self.lista_nodos.append(("Seccionadores Cerrados", "2"))
            if rst[i][0]==3:
                self.liwNodos.addItem("Seccionadores Abiertos")
                self.lista_nodos.append(("Seccionadores Abiertos", "3"))
            if rst[i][0]==4:
                self.liwNodos.addItem("Centros Transformación")
                self.lista_nodos.append(("Centros Transformación", "4"))
            if rst[i][0]==5:
                self.liwNodos.addItem("Luminarias")
                self.lista_nodos.append(("Luminarias", "5"))
            if rst[i][0]==6:
                self.liwNodos.addItem("Suministros")
                self.lista_nodos.append(("Suministros", "6"))
            if rst[i][0]==7:
                self.liwNodos.addItem("Capacitores")
                self.lista_nodos.append(("Capacitores", "7"))
            if rst[i][0]==8:
                self.liwNodos.addItem("Salidas de Alimentador")
                self.lista_nodos.append(("Salidas de Alimentador", "8"))
            if rst[i][0]==9:
                self.liwNodos.addItem("Reguladores de Tensión")
                self.lista_nodos.append(("Reguladores de Tensión", "9"))
            if rst[i][0]==11:
                self.liwNodos.addItem("Generadores")
                self.lista_nodos.append(("Generadores", "11"))
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT DISTINCT id, descripcion FROM Elementos_Lineas INNER JOIN Lineas ON Elementos_Lineas.id=Lineas.elmt WHERE Tension > 0 " + str_where + " ORDER BY Descripcion")
        #convierto el cursor en array
        rst = tuple(cursor)
        cursor.close()
        self.lista_lineas = []
        for i in range (0, len(rst)):
            self.liwLineas.addItem(rst[i][1])
            self.lista_lineas.append((str(rst[i][0]), str(rst[i][1])))
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT DISTINCT Elementos_Postes.Id AS elmt, Estructuras.Id AS estructura, Estructuras.Descripcion + ' | ' + Elementos_Postes.Descripcion AS descripcion FROM Postes INNER JOIN Elementos_Postes ON Postes.Elmt = Elementos_Postes.Id INNER JOIN Estructuras ON Postes.Estructura = Estructuras.Id WHERE Tension > 0 " + str_where + " ORDER BY Descripcion")
        #convierto el cursor en array
        rst = tuple(cursor)
        cursor.close()
        self.lista_postes = []
        for i in range (0, len(rst)):
            self.liwPostes.addItem(rst[i][2])
            self.lista_postes.append((str(rst[i][0]), str(rst[i][1]), str(rst[i][2])))
        self.cmbAlimentador.clear()
        self.cmbAlimentador.addItem('Todos')
        if self.cmbCapa.currentText()!="Todas":
            cnn = self.conn
            cursor = cnn.cursor()
            cursor.execute("SELECT DISTINCT Alimentador FROM Nodos WHERE Tension=" + self.cmbCapa.currentText())
            #convierto el cursor en array
            rst = tuple(cursor)
            cursor.close()
            for i in range (0, len(rst)):
                self.cmbAlimentador.addItem(rst[i][0])

    def elijo_alimentador(self):
        self.sqlNodos.setPlainText('')
        self.sqlLineas.setPlainText('')
        self.sqlPostes.setPlainText('')

    def modificar(self):
        str_where = ""
        if self.cmbCapa.currentText()=="Ninguna":
            return
        self.sqlNodos.setPlainText('')
        self.sqlLineas.setPlainText('')
        self.sqlPostes.setPlainText('')
        elementos_nodos = "-1"
        elementos_lineas = "-1"
        str_where_postes = ""
        nodos_seleccionados = self.liwNodos.selectedItems()
        for nodo in nodos_seleccionados:
            for i in range (0, len(self.lista_nodos)):
                if nodo.text()==self.lista_nodos[i][0]:
                    elementos_nodos = elementos_nodos + ',' + self.lista_nodos[i][1]
        lineas_seleccionadas = self.liwLineas.selectedItems()
        for linea in lineas_seleccionadas:
            for i in range (0, len(self.lista_lineas)):
                if linea.text()==self.lista_lineas[i][1]:
                    elementos_lineas = elementos_lineas + ',' + self.lista_lineas[i][0]
        postes_seleccionados = self.liwPostes.selectedItems()
        for poste in postes_seleccionados:
            for i in range (0, len(self.lista_postes)):
                if poste.text()==self.lista_postes[i][2]:
                    str_where_postes = str_where_postes + ' OR (Postes.elmt=' + self.lista_postes[i][0] + ' AND Postes.estructura=' + self.lista_postes[i][1] + ')'
        if self.cmbCapa.currentText()!="Todas":
            str_where = str_where + " AND Tension=" + self.cmbCapa.currentText()
        if self.cmbZona.currentText()!="Todas":
            str_where = str_where + " AND Zona='" + self.cmbZona.currentText() + "'"
        if self.cmbAlimentador.currentText()!="Todos":
            str_where = str_where + " AND Alimentador='" + self.cmbAlimentador.currentText() + "'"
        if elementos_nodos != "-1":
            self.sqlNodos.setPlainText("SELECT geoname FROM Nodos WHERE Tension > 0 AND elmt IN (" + elementos_nodos.replace("-1,","") + ")" + str_where)
        if elementos_lineas != "-1":
            self.sqlLineas.setPlainText("SELECT geoname FROM Lineas WHERE Tension > 0 AND elmt IN (" + elementos_lineas.replace("-1,","") + ")" + str_where)
        if str_where_postes!="":
            self.sqlPostes.setPlainText("SELECT geoname FROM Postes WHERE Tension > 0 AND (elmt < 0" + str_where_postes + ")" + str_where)
            if self.cmbAlimentador.currentText()!="Todos" or self.cmbZona.currentText()!="Todas":
                str_where = str_where.replace(" AND Tension", " AND Postes.Tension")
                if self.cmbAlimentador.currentText()!="Todos":
                    str_where = str_where.replace(" AND Alimentador", " AND Lineas.Alimentador")
                    #str_where = str_where + " AND Lineas.Alimentador='" + self.cmbAlimentador.currentText() + "'"
                if self.cmbZona.currentText()!="Todas":
                    str_where = str_where.replace(" AND Zona", " AND Postes.Zona")
                    #str_where = str_where + " AND Postes.Zona='" + self.cmbZona.currentText() + "'"
                self.sqlPostes.setPlainText("SELECT Postes.geoname FROM Lineas INNER JOIN Lineas_Postes ON Lineas.Geoname = Lineas_Postes.id_linea INNER JOIN Postes ON Lineas_Postes.id_poste = Postes.Geoname WHERE Postes.Tension > 0 AND (Postes.elmt < 0" + str_where_postes + ")" + str_where)

    def seleccionar_nodos(self):
        if self.sqlNodos.toPlainText()=="":
            return
        cursor = self.conn.cursor()
        cursor.execute(self.sqlNodos.toPlainText())
        #convierto el cursor en array
        selnodos = tuple(cursor)
        cursor.close()
        self.seleccion_n = []
        #b_existe=False
        for n in range(0, len(selnodos)):
            #if self.seleccion_n[n]==selnodos[n][0]:
            #    b_existe=True
            #if b_existe==False:
            self.seleccion_n.append(selnodos[n][0])
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyr.select(self.seleccion_n)
        QMessageBox.information(None, 'EnerGis 6', 'ℹ️ ' + str(len(self.seleccion_n)) + " nodos seleccionados")

    def seleccionar_lineas(self):
        if self.sqlLineas.toPlainText()=="":
            return
        cursor = self.conn.cursor()
        cursor.execute(self.sqlLineas.toPlainText())
        #convierto el cursor en array
        sellineas = tuple(cursor)
        cursor.close()
        self.seleccion_l = []
        #b_existe=False
        for n in range(0, len(sellineas)):
            #if self.seleccion_l[n]==sellineas[n][0]:
            #    b_existe=True
            #if b_existe==False:
            self.seleccion_l.append(sellineas[n][0])
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:6] == 'Lineas':
                lyr.select(self.seleccion_l)
        QMessageBox.information(None, 'EnerGis 6', 'ℹ️ ' + str(len(self.seleccion_l)) + " líneas seleccionadas")

    def seleccionar_postes(self):
        if self.sqlPostes.toPlainText()=="":
            return
        cursor = self.conn.cursor()
        cursor.execute(self.sqlPostes.toPlainText())
        #convierto el cursor en array
        selpostes = tuple(cursor)
        cursor.close()
        self.seleccion_p = []
        #b_existe=False
        for n in range(0, len(selpostes)):
            #if self.seleccion_p[n]==selpostes[n][0]:
            #    b_existe=True
            #if b_existe==False:
            self.seleccion_p.append(selpostes[n][0])
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:6] == 'Postes':
                lyr.select(self.seleccion_p)
        QMessageBox.information(None, 'EnerGis 6', 'ℹ️ ' + str(len(self.seleccion_p)) + " postes seleccionados")

    def salir(self):
        self.close()
