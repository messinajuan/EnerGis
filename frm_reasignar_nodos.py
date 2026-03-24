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
#from qgis.core import *

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_reasignar_nodos.ui'))

class frmReasignarNodos(DialogType, DialogBase):
        
    def __init__(self, mapCanvas, conn, inn):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.inn = inn

        self.cmbCapa.addItem('Todas')
        self.cmbNivelTension.addItem('<No Modificar>')
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT Tension FROM Niveles_Tension WHERE Tension>=50")
        #convierto el cursor en array
        tensiones = tuple(cursor)
        cursor.close()
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        self.lista_tensiones='-1'
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                str_tension = lyr.name() [6 - len(lyr.name()):]
                for tension in tensiones:
                    if str(tension[0])==str_tension:
                        self.cmbCapa.addItem(str_tension)
                        self.cmbNivelTension.addItem(str_tension)
                        self.lista_tensiones=self.lista_tensiones + ',' + str_tension

        self.rbtTodos.toggled.connect(self.rbt_todos)
        self.rbtCt.toggled.connect(self.rbt_ct)
        self.rbtSeccionador.toggled.connect(self.rbt_seccionador)
        self.chkInstalacion.clicked.connect(self.cambiar_fecha)
        self.cmdUUCC.clicked.connect(self.elegir_uucc)
        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)

    def rbt_todos(self):
        self.liwElementos.clear()
        self.liwElementos.addItem("Todos")

    def rbt_ct(self):
        self.liwElementos.clear()
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT DISTINCT Val1, conexionado, tipo_ct FROM (Transformadores INNER JOIN Ct ON Transformadores.Id_ct = Ct.Id_ct) INNER JOIN Nodos ON Ct.Id_ct = Nodos.Nombre WHERE elmt=4 AND geoname IN (" + self.inn + ")")
        #convierto el cursor en array
        rst = tuple(cursor)
        cursor.close()

        for i in range (0, len(rst)):
            self.liwElementos.addItem(rst[i][0] + "kVA | " + str(rst[i][1]) + " | " + rst[i][2])

    def rbt_seccionador(self):
        self.liwElementos.clear()
        self.liwElementos.addItem('<sin dato del tipo de elemento>')

        str_tensiones = ""
        if self.cmbCapa.currentText()!="Todas":
             str_tensiones = " AND Tension=" + self.cmbCapa.currentText()

        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT DISTINCT UPPER(Val1) FROM Nodos WHERE Nodos.Tension>0 AND (elmt=2 OR elmt=3) AND NOT Val1 IS NULL AND NOT Val1='' AND geoname IN (" + self.inn + ")" + str_tensiones)
        #convierto el cursor en array
        rst = tuple(cursor)
        cursor.close()

        for i in range (0, len(rst)):
            self.liwElementos.addItem(rst[i][0])

    def cambiar_fecha(self):
        if self.chkInstalacion.checkState()==2:
            self.datInstalacion.setEnabled(True)
        else:
            self.datInstalacion.setEnabled(False)

    def aceptar(self):
        if self.liwElementos.count() < 1:
            return

        if self.liwElementos.currentRow() == -1:
            return

        str_set = "nivel=nivel"
        str_where = "geoname IN (" + self.inn + ")"

        if self.cmbCapa.currentText()!= 'Todas':
            str_where = str_where + " AND Tension IN (" + self.cmbCapa.currentText() +")"
            self.lista_tensiones = self.cmbCapa.currentText()

        if self.cmbNivelTension.currentText() != '<No Modificar>':
            str_set = str_set + ", Tension = " + self.cmbNivelTension.currentText()

        if self.rbtSeccionador.isChecked() == True:
            if self.liwElementos.currentItem().text() == "<sin dato del tipo de elemento>":
                str_where = str_where + " AND (elmt=2 OR elmt=3) AND (Val1='' OR Val1 IS NULL)"
            else:
                str_where = str_where + " AND (elmt=2 OR elmt=3) AND Val1='" + self.liwElementos.currentItem().text() + "'"

        if self.rbtCt.isChecked() == True:
            str_matriz = self.liwElementos.currentItem().text().split("|")
            #right de 6: str [6 - len(str):]
            #left de l-3: str[:len(str)-3]
            #trim str.strip()
            potencia = str_matriz[0][:len(str_matriz[0])-4]
            conexionado = str_matriz[1].strip()
            tipo_ct = str_matriz[2].strip()

            str_where = str_where + " AND elmt=4 AND Val1='" + potencia + "' AND Val2='" + conexionado + "' AND Tipo_CT='" + tipo_ct + "'"

            if self.txtUUCC.text()!="#":
                str_set = str_set + ", UUCC = '" + self.txtUUCC.text() + "'"

        if self.chkInstalacion.isChecked() == True:
            str_set = str_set + ", modificacion='" + str(self.datInstalacion.date().toPyDate()).replace('-','') + "'"

        reply = QMessageBox.question(None, 'EnerGis 6', 'Desea cambiar los datos de los nodos seleccionados ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        cnn = self.conn
        cursor = cnn.cursor()
        try:
            cursor.execute("UPDATE Nodos SET " + str_set + " FROM Nodos LEFT JOIN Ct ON Nodos.Nombre = Ct.Id_ct WHERE " + str_where)
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudo actualizar la Base de Datos')

    def elegir_uucc(self):

        if self.cmbCapa.currentText() != 'Todas':
             self.lista_tensiones = self.cmbCapa.currentText()

        if self.liwElementos.count() < 1:
            return
        if self.liwElementos.currentRow() == -1:
            return
        if self.rbtSeccionador.isChecked() == True:
            self.where = "Tipo IN ('SECCIONADOR', 'SECCIONALIZADOR', 'RECONECTADOR', 'INTERRUPTOR')"
        if self.rbtCt.isChecked() == True:
            str_matriz = self.liwElementos.currentItem().text().split("|")
            potencia = str_matriz[0][:len(str_matriz[0])-4]
            conexionado = str_matriz[1].strip()
            tipo_ct = str_matriz[2].strip()

            if tipo_ct == "Monoposte":
                ulike = "-MPM-"
            if tipo_ct == "Plataforma":
                ulike = "-BP-"
            if tipo_ct == "Biposte":
                ulike = "-BP-"
            if tipo_ct == "Cámara Subterránea":
                ulike = "-MCS-"
            if tipo_ct == "Cámara Nivel":
                ulike = "-CAN-"
            if tipo_ct == "Centro Compacto":
                ulike = "-CI-"
            if tipo_ct == "A Nivel":
                ulike = "-IN-"

            if conexionado == "M":
                self.where = "Codigo LIKE '%" + ulike + "%' AND Valor_Principal>=" + potencia + " AND fases=1"
            elif conexionado == "B":
                self.where = "Codigo LIKE '%" + ulike + "%' AND Valor_Principal>=" + potencia + " AND fases=2"
            else:
                self.where = "Codigo LIKE '%" + ulike + "%' AND Valor_Principal>=" + potencia + " AND fases=3"

        self.uucc = self.txtUUCC.text
        from .frm_elegir_uucc import frmElegirUUCC
        dialogo = frmElegirUUCC(self.conn, self.lista_tensiones, self.where, self.uucc)
        dialogo.exec()
        if dialogo.uucc != '':
            self.txtUUCC.setText(dialogo.uucc)
        dialogo.close()
        pass

    def salir(self):
        self.close()
        pass
