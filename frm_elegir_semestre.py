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
from PyQt6.QtWidgets import QApplication, QProgressDialog
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_elegir_semestre.ui'))

class frmElegirSemestre(DialogType, DialogBase):

    def __init__(self, conn):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.conn = conn
        cursor = self.conn.cursor()
        cursor.execute("SELECT id_semestre,Fecha_Desde,Fecha_Hasta,numero FROM Semestre")
        #convierto el cursor en array
        semestre = tuple(cursor)
        cursor.close()
        self.lbl_semestre_actual.setText(str(semestre[0][3]))
        self.lbl_actual_desde.setText(str(semestre[0][1])[:10])
        self.lbl_actual_hasta.setText(str(semestre[0][2])[:10])
        cursor = self.conn.cursor()
        cursor.execute("SELECT Semestre,Desde,Hasta,Cerrado FROM Semestres")
        #convierto el cursor en array
        semestres = tuple(cursor)
        cursor.close()
        for i in range (0, len(semestres)):
            self.cmbSemestre.addItem(str(semestres[i][0]))
            if str(semestres[i][0])==str(semestre[0][3]):
                j=i
        self.cmbSemestre.setCurrentIndex(j)
        self.elijo_semestre()
        self.cmbSemestre.activated.connect(self.elijo_semestre)
        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)

    def aceptar(self):
        #----------------------------------------------------------------------------
        progress = QProgressDialog("Procesando...", "Cancelar", 0, 100,self)
        progress.setWindowTitle("Progreso")
        progress.setWindowModality(True)  # Hace que la ventana de progreso sea modal
        progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
        progress.setValue(0)  # Inicia el progreso en 0
        #----------------------------------------------------------------------------
        from datetime import datetime
        if datetime.now() < datetime.strptime(self.lbl_elegido_hasta.text(), "%Y-%m-%d"):
            QMessageBox.information(None, 'EnerGis 6', "ℹ️ Atención !!! Es conveniente que la cadena se exporte luego del informe semestral")

        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT '0' AS Sucursal, Usuarios.id_usuario AS Codigo_Suministro, Tarifas.id_OCEBA AS Tarifa, Cadena_Electrica.[Alimentador BT], Cadena_Electrica.[Centro MTBT], Cadena_Electrica.[Centro Distribucion], Cadena_Electrica.[Alimentador MT], Cadena_Electrica.SSEE, Usuarios.Fase, 0 AS Consumo, CONVERT(VARCHAR, GETDATE(), 103) AS Fecha FROM Usuarios INNER JOIN Cadena_Electrica ON Usuarios.id_usuario = Cadena_Electrica.id_usuario INNER JOIN Tarifas ON Usuarios.tarifa = Tarifas.Tarifa WHERE Usuarios.ES=1")
        #convierto el cursor en array
        cadena = tuple(cursor)
        cursor.close()
        #----------------------------------------------------------------------------
        progress.setValue(25)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        str_semestre = self.cmbSemestre.currentText()
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM E_Facturada WHERE Semestre=" + str_semestre)
        self.conn.commit()
        cursor.execute("INSERT INTO E_Facturada (id_usuario,EtF,semestre) SELECT Energia_Facturada.Id_usuario, Sum(Energia_Facturada.EtF) AS EtF, " + str_semestre + " AS Semestre FROM Energia_Facturada WHERE (((Energia_Facturada.Desde) >= '" + self.lbl_elegido_desde.text().replace("-","") + "') AND ((Energia_Facturada.Hasta) <= '" +  self.lbl_elegido_hasta.text().replace("-","") + "')) GROUP BY Energia_Facturada.Id_usuario")
        self.conn.commit()
        #----------------------------------------------------------------------------
        progress.setValue(50)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        cursor = self.conn.cursor()
        cursor.execute("SELECT Codigo FROM Empresa")
        #convierto el cursor en array
        empresa = tuple(cursor)
        cursor.close()
        str_codigo_empresa = empresa[0][0]
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT '0' AS Sucursal, Usuarios.id_usuario AS Codigo_Suministro, Tarifas.id_OCEBA AS Tarifa, Cadena_Electrica.[Alimentador BT], Cadena_Electrica.[Centro MTBT], Cadena_Electrica.[Centro Distribucion], Cadena_Electrica.[Alimentador MT], Cadena_Electrica.SSEE, Usuarios.fase, ISNULL(E_Facturada.EtF, 0) AS Consumo, CONVERT(VARCHAR, CONVERT(DATE,'" + self.lbl_elegido_hasta.text() + "'), 103) As Fecha FROM Usuarios INNER JOIN Cadena_Electrica ON Usuarios.id_usuario = Cadena_Electrica.id_usuario INNER JOIN Tarifas ON Usuarios.tarifa = Tarifas.Tarifa INNER JOIN VW_CCDATOSCOMERCIALES ON Usuarios.Id_usuario = VW_CCDATOSCOMERCIALES.Id_usuario LEFT OUTER JOIN E_Facturada ON Usuarios.id_usuario = E_Facturada.Id_usuario WHERE E_Facturada.Semestre = " + str_semestre + " AND VW_CCDATOSCOMERCIALES.Fecha_Alta <='" + self.lbl_elegido_hasta.text().replace("-","") + "'")
        #convierto el cursor en array
        cadena = tuple(cursor)
        cursor.close()
        #----------------------------------------------------------------------------
        progress.setValue(75)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        if os.path.isdir('c:/gis/energis6/OCEBA/')==False:
            os.mkdir('c:/gis/energis6/OCEBA/')
        f = open('c:/gis/energis6/OCEBA/semestre_' + str_semestre + '_cadena_2.txt','w')
        f.writelines('Semestre;Distribuidora;Sucursal;Codigo_Suministro;Tarifa;Alimentador BT;Centro MTBT;Centro Distribucion;Alimentador MT;SSEE;fase;Consumo;Fecha' + '\n')
        for i in range (0, len(cadena)):

            str_linea = str_semestre + ";" + str_codigo_empresa + ";"
            for j in range (0, len(cadena[0])):
                if cadena[i][j]==None:
                    str_linea = str_linea + ";"
                else:
                    str_linea = str_linea + str(cadena[i][j]) + ";"
            f.writelines(str_linea[:-1] + "\n")
        f.close()
        # Forzar el cierre del QProgressDialog
        progress.close()
        QMessageBox.information(None, 'EnerGis 6', "ℹ️ Exportado en C:/GIS/EnerGis6/OCEBA/semestre_" + str_semestre + "_cadena_2.txt")
        #----------------------------------------------------------------------------
        progress.setValue(100)
        QApplication.processEvents()
        #----------------------------------------------------------------------------

    def elijo_semestre(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT Desde,Hasta FROM Semestres WHERE Semestre=" + self.cmbSemestre.currentText())
        #convierto el cursor en array
        semestre = tuple(cursor)
        cursor.close()
        self.lbl_elegido_desde.setText(str(semestre[0][0])[:10])
        self.lbl_elegido_hasta.setText(str(semestre[0][1])[:10])

    def salir(self):
        self.close()
