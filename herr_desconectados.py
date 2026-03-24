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
from qgis.gui import QgsMapTool

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

class herrDesconectados(QgsMapTool):

    def __init__(self, mapCanvas, conn):
        QgsMapTool.__init__(self, mapCanvas)
        self.mapCanvas = mapCanvas
        self.conn = conn

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM mNodos ORDER BY Aux")
        #convierto el cursor en array
        self.mnodos = tuple(cursor)
        cursor.close()
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM mLineas ORDER BY Aux")
        #convierto el cursor en array
        self.mlineas = tuple(cursor)
        cursor.close()

        #--------------------------------------------
        from .mod_navegacion_ant import buscar_desconectados
        self.seleccion_n, self.seleccion_l = buscar_desconectados(self, self.mnodos, self.mlineas)
        #--------------------------------------------

        if len(self.seleccion_l)==0:
            QMessageBox.exclamation(None, 'EnerGis 6', '❌ No hay desconectados !')
        #retval = self.h_elementos_seleccionados()
        self.h_elementos_seleccionados()

    def h_elementos_seleccionados(self):
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyr.select(self.seleccion_n)
            if lyr.name()[:6] == 'Lineas':
                lyr.select(self.seleccion_l)
        from .frm_seleccion import frmSeleccion
        self.dialogo = frmSeleccion(self.mapCanvas)
        self.dialogo.show()

