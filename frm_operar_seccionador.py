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
#from copy import deepcopy

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_operar_seccionador.ui'))
basepath = os.path.dirname(os.path.realpath(__file__))

class frmOperarSeccionador(DialogType, DialogBase):
        
    def __init__(self, conn, geoname, elmt, estado, capa):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.conn = conn
        self.geoname = geoname
        self.elmt = elmt
        self.estado = estado
        self.capa = capa
        self.reconfiguro = False

        if self.elmt==2:
            self.lblElemento.setText('CERRADO')
        else:
            self.lblElemento.setText('ABIERTO')
        if self.estado==2:
            self.lblEstado.setText('CERRADO')
        else:
            self.lblEstado.setText('ABIERTO')
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT aux, tension FROM mNodos WHERE Geoname=" + str(self.geoname))
        #convierto el cursor en array
        rst = tuple(cursor)
        cursor.close()
        self.tension = rst[0][1]
        self.cmdOperar.clicked.connect(self.operar)
        self.cmdReconfigurar.clicked.connect(self.reconfigurar)
        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)
        
    def operar(self):
        if self.estado==2:
            self.estado=3
            self.lblEstado.setText('ABIERTO')
        else:
            self.estado=2
            self.lblEstado.setText('CERRADO')

    def reconfigurar(self):
        if self.elmt==2:
            self.elmt=3
            self.lblElemento.setText('ABIERTO')
            self.estado=3
            self.lblEstado.setText('ABIERTO')
        else:
            self.elmt=2
            self.lblElemento.setText('CERRADO')
            self.estado=2
            self.lblEstado.setText('CERRADO')
            self.reconfiguro = True

    def aceptar(self):
        cnn = self.conn
        cursor = cnn.cursor()
        try:
            cursor.execute('UPDATE Nodos SET elmt=' + str(self.elmt) + ', estado=' + str(self.estado) + ' WHERE geoname=' + str(self.geoname))
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudo actualizar')
        if self.reconfiguro == True:
            #----------------------------------------------------------------------------
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM mNodos ORDER BY Aux")
            #convierto el cursor en array
            self.mnodos = tuple(cursor)
            cursor.close()
            cursor = self.conn.cursor()
            cursor.execute("UPDATE mLineas SET alim=0 WHERE alim IS NULL")
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM mLineas ORDER BY Aux")
            #convierto el cursor en array
            self.mlineas = tuple(cursor)
            cursor.close()
            #----------------------------------------------------------------------------
            import clr
            # Cargar el ensamblado
            clr.AddReference(os.path.join(basepath, 'NavRed6.dll'))
            from EnerGis6.NavRed6 import NavRed
            from System import Int64, Array
            # Crear arreglos
            mnodos = Array.CreateInstance(Int64, len(self.mnodos), len(self.mnodos[0]))
            mlineas = Array.CreateInstance(Int64, len(self.mlineas), len(self.mlineas[0]))
            # Copiar valores a mnodos
            for i in range(len(self.mnodos)):
                if self.geoname == self.mnodos[i][1]:
                    nodo = Int64(self.mnodos[i][0])
                for j in range(len(self.mnodos[0])):
                    mnodos[i, j] = self.mnodos[i][j]
            # Copiar valores a mlineas
            for i in range(len(self.mlineas)):
                for j in range(len(self.mlineas[0])):
                    mlineas[i, j] = self.mlineas[i][j]
            #----------------------------------------------------------------------------
            # Instanciar la clase NavRed
            navred_instance = NavRed()
            # Llamar a la función
            resultado = navred_instance.Navegar_a_los_extremos(mnodos,mlineas,nodo)
            if resultado[0]!="Ok":
                QMessageBox.critical(None, 'EnerGis 6', '❌ ' + resultado[0])
                return
            #----------------------------------------------------------------------------
            cursor = self.conn.cursor()
            cursor.execute("SELECT Id, Id_Alim,Tension FROM Alimentadores")
            alimentadores = cursor.fetchall()
            cursor.close()
            str_nodos="-1"
            alimentadores_nodos = [list(fila) for fila in alimentadores]
            for fila in alimentadores_nodos:
                fila.append('-1')
            for n in range(mnodos.GetLength(0)):
                if mnodos.GetValue(n,41) == 1:
                    if mnodos.GetValue(n,46)==0:
                        str_nodos=str_nodos + "," + str(mnodos.GetValue(n,1))
                    elif mnodos.GetValue(n,40) != mnodos.GetValue(n,46):
                        #en la posicion a de alimentadores pongo el nodo
                        for i in range(len(alimentadores_nodos)):
                            if alimentadores_nodos[i][0] == mnodos.GetValue(n,46):
                                alimentadores_nodos[i][3] = alimentadores_nodos[i][3] + ',' + str(mnodos.GetValue(n,1))
            str_lineas="-1"
            alimentadores_lineas = [list(fila) for fila in alimentadores]
            for fila in alimentadores_lineas:
                fila.append('-1')
            for l in range(mlineas.GetLength(0)):
                if mlineas.GetValue(l,7) == 1:
                    if mlineas.GetValue(l,13)==0:
                        str_lineas=str_lineas + "," + str(mlineas.GetValue(l,1))
                    elif mlineas.GetValue(l,8) != mlineas.GetValue(l,13):
                        #en la posicion a de alimentadores pongo el nodo
                        for i in range(len(alimentadores_lineas)):
                            if alimentadores[i][0] == mlineas.GetValue(l,13):
                                alimentadores_lineas[i][3] = alimentadores_lineas[i][3] + ',' + str(mlineas.GetValue(l,1))
            for i in range(len(alimentadores_nodos)):
                id_alimentador=alimentadores_nodos[i][0]
                alimentador=alimentadores_nodos[i][1]
                tension=alimentadores_nodos[i][2]
                cursor = self.conn.cursor()
                cursor.execute("UPDATE mNodos SET alim=" + str(id_alimentador) + " WHERE tension=" + str(tension) + " AND geoname IN (" + alimentadores_nodos[i][3] + ")")
                cursor.execute("UPDATE Nodos SET Alimentador='" + alimentador + "' WHERE tension=" + str(tension) + " AND geoname IN (" + alimentadores_nodos[i][3] + ")")
                self.conn.commit()
            for i in range(len(alimentadores_lineas)):
                id_alimentador=alimentadores_nodos[i][0]
                alimentador=alimentadores_nodos[i][1]
                tension=alimentadores_nodos[i][2]
                cursor = self.conn.cursor()
                cursor.execute("UPDATE mLineas SET alim=" + str(id_alimentador) + " WHERE tension=" + str(tension) + " AND geoname IN (" + alimentadores_lineas[i][3] + ")")
                cursor.execute("UPDATE Lineas SET Alimentador='" + alimentador + "' WHERE tension=" + str(tension) + " AND geoname IN (" + alimentadores_lineas[i][3] + ")")
                self.conn.commit()
            cursor = self.conn.cursor()
            cursor.execute("UPDATE Nodos SET Alimentador='#NA' WHERE geoname IN (" + str_nodos + ")")
            cursor.execute("UPDATE Lineas SET Alimentador='#NA' WHERE geoname IN (" + str_lineas + ")")
            self.conn.commit()
        self.capa.triggerRepaint()
        self.salir()

    def salir(self):
        self.close()
