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

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_reasignar_lineas.ui'))

class frmReasignarLineas(DialogType, DialogBase):

    def __init__(self, mapCanvas, conn, inn):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.inn = inn
        self.arrConductores = []

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
            if lyr.name()[:6] == 'Lineas':
                str_tension = lyr.name() [7 - len(lyr.name()):]
                for tension in tensiones:
                    if str(tension[0])==str_tension:
                        self.cmbCapa.addItem(str_tension)
                        self.cmbNivelTension.addItem(str_tension)
                        self.lista_tensiones=self.lista_tensiones + ',' + str_tension

        self.cmbConductor.addItem('Todos')
        self.cmbNuevoConductor.addItem('<No Modificar>')

        cursor = cnn.cursor()
        cursor.execute("SELECT id, Descripcion FROM Elementos_Lineas")
        #convierto el cursor en array
        rows = tuple(cursor)
        cursor.close()
        for row in rows:
            self.arrConductores.append(row)
            self.cmbNuevoConductor.addItem(row[1])

        cursor = cnn.cursor()
        cursor.execute("SELECT DISTINCT id, Descripcion FROM Elementos_Lineas INNER JOIN Lineas ON Elementos_Lineas.id=Lineas.elmt WHERE geoname IN (" + self.inn + ")")
        #convierto el cursor en array
        rows = tuple(cursor)
        cursor.close()
        for row in rows:
            self.cmbConductor.addItem(row[1])

        self.cmbFase.addItem('Todas')
        self.cmbFase.addItem('Trifásicas')
        self.cmbFase.addItem('Bifásicas')
        self.cmbFase.addItem('Monofásicas')
        self.cmbFase.addItem('12')
        self.cmbFase.addItem('23')
        self.cmbFase.addItem('13')
        self.cmbFase.addItem('1')
        self.cmbFase.addItem('2')
        self.cmbFase.addItem('3')

        self.cmbZona.addItem('Todas')
        self.cmbZona.addItem('Rural')
        self.cmbZona.addItem('Urbana')

        self.cmbNuevaFase.addItem('<No Modificar>')
        self.cmbNuevaFase.addItem('123')
        self.cmbNuevaFase.addItem('12')
        self.cmbNuevaFase.addItem('23')
        self.cmbNuevaFase.addItem('13')
        self.cmbNuevaFase.addItem('1')
        self.cmbNuevaFase.addItem('2')
        self.cmbNuevaFase.addItem('3')

        self.cmbDisposicion.addItem('<No Modificar>')
        self.cmbDisposicion.addItem('No Aplica')
        self.cmbDisposicion.addItem('Horizontal')
        self.cmbDisposicion.addItem('Vertical')
        self.cmbDisposicion.addItem('Triangular')
        
        self.cmbTernas.addItem('<No Modificar>')
        self.cmbTernas.addItem('Simple Terna')
        self.cmbTernas.addItem('2 Ternas')
        self.cmbTernas.addItem('3 Ternas')
        self.cmbTernas.addItem('4 Ternas')
        self.cmbTernas.addItem('Alumbrado')

        self.cmbEstado.addItem('<No Modificar>')
        self.cmbEstado.addItem('Bueno')
        self.cmbEstado.addItem('Regular')
        self.cmbEstado.addItem('Malo')

        self.chkAcometida.setCheckState(1)

        self.cmdUUCC.clicked.connect(self.elegir_uucc)
        self.chkInstalacion.clicked.connect(self.cambiar_fecha)
        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)

        pass

    def elegir_uucc(self):
        self.where = "(Tipo = 'CABLE SUBTERRANEO' OR Tipo = 'LINEA AEREA' OR Tipo = 'ACOMETIDA')"

        if self.cmbCapa.currentText() != 'Todas':
            self.lista_tensiones = self.cmbCapa.currentText()

            tension = int(self.cmbCapa.currentText())
            if tension <= 1000:
                self.where = self.where + " AND Tipo_Instalacion IN ('LBT', 'CAS BT')"
            elif tension > 1000 and tension < 50000:
                self.where = self.where + " AND Tipo_Instalacion IN ('LMT RPT', 'LMT 7,6', 'LMT 13,2', 'LMT 33', 'CAS 13,2', 'CAS 33')"
            else:
                self.where = self.where + " AND Tipo_Instalacion IN ('LAT 132', 'LAT 220', 'LAT 66', 'CAS 132')"

        if self.cmbFase.currentText() != 'Todas':
            if self.cmbFase.currentText() == 'Trifásicas':
                self.where = self.where + " AND Fases=3"
            elif self.cmbFase.currentText() == 'Bifásicas' or self.cmbFase.currentText() == '12' or self.cmbFase.currentText() == '23' or self.cmbFase.currentText() == '13':
                self.where = self.where + " AND Fases=2"
            elif self.cmbFase.currentText() == 'Monofásicas' or self.cmbFase.currentText() == '1' or self.cmbFase.currentText() == '2' or self.cmbFase.currentText() == '3':
                self.where = self.where + " AND Fases=1"

        self.uucc = ""
        from .frm_elegir_uucc import frmElegirUUCC
        dialogo = frmElegirUUCC(self.conn, self.lista_tensiones, self.where, self.uucc)
        dialogo.exec()
        if dialogo.uucc != '':
            self.txtUUCC.setText(dialogo.uucc)
        dialogo.close()
        pass

    def cambiar_fecha(self):
        if self.chkInstalacion.checkState()==2:
            self.datInstalacion.setEnabled(True)
        else:
            self.datInstalacion.setEnabled(False)
        pass

    def aceptar(self):
        str_where = "geoname IN (" + self.inn + ")"
        if self.cmbCapa.currentText() != 'Todas':
            str_where = str_where + " AND Tension=" + self.cmbCapa.currentText()
        if self.cmbConductor.currentText() != 'Todos':
            for i in range (0, len(self.arrConductores)):
                if self.cmbConductor.currentText()==self.arrConductores[i][1]:
                    str_where = str_where + " AND elmt='" + str(self.arrConductores[i][0]) + "'"
        if self.cmbFase.currentText() != 'Todas':
            if self.cmbFase.currentText() == 'Trifásicas':
                str_where = str_where + " AND Fase='123'"
            elif self.cmbFase.currentText() == 'Bifásicas':
                str_where = str_where + " AND Fase IN ('12','23','13')"
            elif self.cmbFase.currentText() == 'Monofásicas':
                str_where = str_where + " AND Fase IN ('1','2','3')"
            else:
                str_where = str_where + " AND Fase='" + self.cmbFase.currentText() + "'"

        if self.cmbZona.currentText() != 'Todas':
            str_where = str_where + " AND Zona='" + self.cmbZona.currentText() + "'"

        if self.cmbNivelTension.currentText() != '<No Modificar>':
            str_set = "tension = " + self.cmbNivelTension.currentText()
        else:
            str_set = "tension=tension"

        if self.cmbNuevoConductor.currentText() != '<No Modificar>':
            for i in range (0, len(self.arrConductores)):
                if self.cmbNuevoConductor.currentText()==self.arrConductores[i][1]:
                    str_set = str_set + ", elmt=" + str(self.arrConductores[i][0])
        if self.cmbNuevaFase.currentText() != '<No Modificar>':
            str_set = str_set + ", fase='" + self.cmbNuevaFase.currentText() + "'"
        if self.txtExpediente.text()!= "####/####":
            str_set = str_set + ", expediente='" + self.txtExpediente.text() + "'"
        if self.chkAcometida.checkState() == 2:
            str_set = str_set + ", acometida=1"
        if self.chkAcometida.checkState() == 0:
            str_set = str_set + ", acometida=0"
        if self.cmbDisposicion.currentText() != '<No Modificar>':
            str_set = str_set + ", disposicion='" + self.cmbDisposicion.currentText() + "'"
        if self.cmbTernas.currentText() != '<No Modificar>':
            str_set = str_set + ", ternas='" + self.cmbTernas.currentText() + "'"
        if self.cmbEstado.currentText() != '<No Modificar>':
            str_set = str_set + ", conservacion='" + self.cmbEstado.currentText() + "'"
        if self.chkInstalacion.isChecked() == True:
            str_set = str_set + ", modificacion='" + str(self.datInstalacion.date().toPyDate()).replace('-','') + "'"
        if self.txtUUCC.text()!= "#":
            str_set = str_set + ", uucc='" + self.txtUUCC.text() + "'"

        reply = QMessageBox.question(None, 'EnerGis 6', 'Desea cambiar los datos de las líneas seleccionadas ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        cnn = self.conn
        cursor = cnn.cursor()
        try:
            cursor.execute("UPDATE Lineas SET " + str_set + " WHERE " + str_where)
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudo actualizar la Base de Datos')
        pass

    def salir(self):
        self.close()
        pass
