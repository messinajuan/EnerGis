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

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_conectar_aislados.ui'))

class frmConectarAislados(DialogType, DialogBase):

    def __init__(self, mapCanvas, conn):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.mapCanvas = mapCanvas
        self.conn = conn

        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT Tension FROM Niveles_Tension WHERE Tension>=200")
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
                        self.cmbTension.addItem(str_tension)

        cursor = cnn.cursor()
        cursor.execute("SELECT id, descripcion FROM Elementos_Lineas")
        #convierto el cursor en array
        self.conductores = tuple(cursor)
        cursor.close()

        for i in range (0, len(self.conductores)):
            self.liwElementos_mono.addItem(self.conductores[i][1])
            self.liwElementos_trif.addItem(self.conductores[i][1])

        self.cmdUUCCmono.clicked.connect(self.elegir_uucc_mono)
        self.cmdUUCCtrif.clicked.connect(self.elegir_uucc_trif)
        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)
        pass

    def aceptar(self):
        self.tension = int(self.cmbTension.currentText())
        self.long_maxima=self.txtDistancia.text()

        if self.liwElementos_mono.currentItem()==None or self.liwElementos_trif.currentItem()==None:
            return
        for i in range (0, len(self.conductores)):
            if self.liwElementos_mono.currentItem().text()==self.conductores[i][1]:
                self.elmt_mono = self.conductores[i][0]
            if self.liwElementos_trif.currentItem().text()==self.conductores[i][1]:
                self.elmt_trif = self.conductores[i][0]
        self.ucc_mono=self.txtUUCCmono.text()
        self.ucc_trif=self.txtUUCCtrif.text()
        self.close()
        pass

    def elegir_uucc_mono(self):
        self.tension = int(self.cmbTension.currentText())
        self.where = "Tipo = 'ACOMETIDA' AND Fases<>3"

        from .frm_elegir_uucc import frmElegirUUCC
        dialogo = frmElegirUUCC(self.conn, self.tension, self.where, '')
        dialogo.exec()
        if dialogo.uucc != '':
            self.txtUUCCmono.setText(dialogo.uucc)
        dialogo.close()
        pass

    def elegir_uucc_trif(self):
        self.tension = int(self.cmbTension.currentText())
        self.where = "Tipo = 'ACOMETIDA' AND Fases=3"

        from .frm_elegir_uucc import frmElegirUUCC
        dialogo = frmElegirUUCC(self.conn, self.tension, self.where, '')
        dialogo.exec()
        if dialogo.uucc != '':
            self.txtUUCCtrif.setText(dialogo.uucc)
        dialogo.close()
        pass

    def salir(self):
        self.close()
        pass
