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
from PyQt6.QtGui import QIntValidator
from PyQt6.QtGui import QDoubleValidator
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_transformadores.ui'))

class frmTransformadores(DialogType, DialogBase):

    def __init__(self, tipo_usuario, conn, geoname, tension, nombre):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        #basepath = os.path.dirname(os.path.realpath(__file__))
        self.tipo_usuario = tipo_usuario
        self.conn = conn
        self.geoname = geoname
        self.tension = tension
        self.nombre = nombre
        self.id = 0
        vint = QIntValidator()
        vfloat = QDoubleValidator()
        self.txtPotencia.setValidator(vfloat)
        self.txtV1.setValidator(vfloat)
        self.txtV2.setValidator(vfloat)
        self.txtAceite.setValidator(vfloat)
        self.txtAnio.setValidator(vint)
        if self.tipo_usuario==4:
            self.cmdEditar.setText('Datos')
            self.cmdNuevo.setEnabled(False)
            self.cmdAgregar.setEnabled(False)
            self.cmdQuitar.setEnabled(False)
        self.i_trafo=0
        self.cmbConexionado.addItem('M')
        self.cmbConexionado.addItem('B')
        self.cmbConexionado.addItem('Yy0')
        self.cmbConexionado.addItem('Yd5')
        self.cmbConexionado.addItem('Yd11')
        self.cmbConexionado.addItem('Dy5')
        self.cmbConexionado.addItem('Dy11')
        self.cmbTipo.addItem('Monofásico')
        self.cmbTipo.addItem('Bifásico')
        self.cmbTipo.addItem('Trifásico')
        self.cmbAnomalia.addItem('Sin Anomalía')
        self.cmbAnomalia.addItem('Pérdida de Aceite')
        self.cmbAnomalia.addItem('Emanación de Olores')
        self.cmbAnomalia.addItem('Contaminación Auditiva')
        self.cmbAnomalia.addItem('Obra Civil Defectuosa')
        self.cmbAislacion.addItem('Aceite')
        self.cmbAislacion.addItem('Resina')
        self.txtCT.setText(self.nombre)
        self.actualizar_campos()
        #self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdMas.clicked.connect(self.mas)
        self.cmdMenos.clicked.connect(self.menos)
        self.cmdNuevo.clicked.connect(self.nuevo)
        self.cmdEditar.clicked.connect(self.editar)
        self.cmdParametros.clicked.connect(self.parametros)
        self.cmdAgregar.clicked.connect(self.agregar)
        self.cmdQuitar.clicked.connect(self.quitar)
        self.cmdSalir.clicked.connect(self.salir)

    def parametros(self):
        from .frm_parametros_trafo import frmParametrosTrafo
        dialogo = frmParametrosTrafo(self.tipo_usuario, self.conn, self.id, float(self.txtPotencia.text()))
        dialogo.exec()
        dialogo.close()

    def actualizar_campos(self):
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT Transformadores.Id_trafo, Transformadores.Conexionado, Transformadores.Potencia, Transformadores.Tension_1, Transformadores.Tension_2, Transformadores.Tipo, Transformadores.Marca, Transformadores.N_chapa, Transformadores.Obs, Transformadores.Fecha_ult_mant, Transformadores.Cod_ult_mant, Transformadores.Anio_fabricacion, Ct.Id_ct, Ct.Mat_plataf, Ct.Tipo_ct, Ct.Ubicacion, Transformadores.Kit,  Transformadores.Cromatografia, Transformadores.Anomalia, Transformadores.Fecha_norm, Transformadores.Certificado, Transformadores.Obs_pcb, Transformadores.aceite, Transformadores.Prop_usuario, M.Alta, Transformadores.Peso, Transformadores.Aislacion FROM Ct INNER JOIN Transformadores ON Ct.Id_ct = Transformadores.Id_ct LEFT OUTER JOIN (SELECT id_trafo, MAX(fecha) AS Alta FROM Movimiento_Transformadores WHERE tipo_mov = 2 and mov_hasta=3 GROUP BY id_trafo) AS M ON Transformadores.Id_trafo = M.id_trafo WHERE Ct.id_ct='" + self.nombre + "'")
        #convierto el cursor en array
        self.transformadores = tuple(cursor)
        cursor.close()
        self.cantidad_trafos=len(self.transformadores)
        if len(self.transformadores)==0:
            self.lblTransformadores.setText("Cantidad de Transformadores 0, Potencia Total Instalada 0 kVA")
            return
        self.id = self.transformadores[self.i_trafo][0]
        self.txtTrafo.setText(str(self.id))
        for i in range (0, self.cmbConexionado.count()):
            if self.cmbConexionado.itemText(i) == str(self.transformadores[self.i_trafo][1]):
                self.cmbConexionado.setCurrentIndex(i)
        self.txtPotencia.setText(str(self.transformadores[self.i_trafo][2]))
        self.txtV1.setText(str(self.transformadores[self.i_trafo][3]))
        self.txtV2.setText(str(self.transformadores[self.i_trafo][4]))
        self.cmbTipo.setCurrentIndex(self.transformadores[self.i_trafo][5] - 1)
        self.txtMarca.setText(self.transformadores[self.i_trafo][6])
        self.txtNroChapa.setText(self.transformadores[self.i_trafo][7])
        self.txtObservaciones.setText(self.transformadores[self.i_trafo][8])
        if self.transformadores[self.i_trafo][9]!=None:
            self.datMantenimiento.setDate(self.transformadores[self.i_trafo][9])
        self.txtIntervencion.setText(self.transformadores[self.i_trafo][10])
        self.txtAnio.setText(self.transformadores[self.i_trafo][11])
        #self.txtCT.setText(self.transformadores[self.i_trafo][12])
        self.txtMaterial.setText(self.transformadores[self.i_trafo][13])
        self.txtTipoCT.setText(self.transformadores[self.i_trafo][14])
        self.txtUbicacion.setText(self.transformadores[self.i_trafo][15])
        self.txtKit.setText(self.transformadores[self.i_trafo][16])
        self.txtCromatografia.setText(self.transformadores[self.i_trafo][17])
        #me fijo si lo que tengo en la base esta en el combo
        b_existe = False
        for i in range (0, self.cmbAnomalia.count()):
            if self.transformadores[self.i_trafo][18]!=None:
                if self.cmbAnomalia.itemText(i) == self.transformadores[self.i_trafo][18].strip():
                    self.cmbAnomalia.setCurrentIndex(i)
                    b_existe=True
        if b_existe==False:
            if self.transformadores[self.i_trafo][18]!=None:
                if self.transformadores[self.i_trafo][18].strip() == "":
                    self.cmbAnomalia.setCurrentIndex(0)
                else:
                    #si no esta lo agrego y selecciono
                    self.cmbAnomalia.addItem (self.transformadores[self.i_trafo][18].strip() + ' *')
                    self.cmbAnomalia.setCurrentIndex(self.cmbAnomalia.count())
        if self.transformadores[self.i_trafo][19]!=None:
            self.datNormalizacion.setDate(self.transformadores[self.i_trafo][19])
        if self.transformadores[self.i_trafo][20]==1:
            self.chkCertificado.setChecked(True)
        else:
            self.chkCertificado.setChecked(False)
        self.txtObservacionesPCB.setText(self.transformadores[self.i_trafo][21])
        self.txtAceite.setText(str(self.transformadores[self.i_trafo][22]))
        self.chkPropiedadUsuario.setChecked(self.transformadores[self.i_trafo][23])
        if self.transformadores[self.i_trafo][24]!=None:
            self.datInstalacion.setDate(self.transformadores[self.i_trafo][24])
        self.txtPeso.setText(str(self.transformadores[self.i_trafo][25]))
        for i in range (0, self.cmbAislacion.count()):
            if self.cmbAislacion.itemText(i) == str(self.transformadores[self.i_trafo][26]):
                self.cmbAislacion.setCurrentIndex(i)
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT count(Transformadores.Id_trafo), sum(Transformadores.Potencia) FROM Transformadores WHERE Transformadores.id_ct='" + self.transformadores[self.i_trafo][12] + "'")
        #convierto el cursor en array
        self.recordset = tuple(cursor)
        cursor.close()
        if self.recordset[0][0]!=None:
            self.lblTransformadores.setText("Cantidad de Transformadores " + str(self.recordset[0][0]) + ", Potencia Total Instalada " + str(self.recordset[0][1]) + " kVA")

    def mas(self):
        self.i_trafo=self.i_trafo+1
        if self.i_trafo > self.cantidad_trafos-1:
            self.i_trafo=self.cantidad_trafos-1
        self.actualizar_campos()

    def menos(self):
        self.i_trafo=self.i_trafo-1
        if self.i_trafo<0:
            self.i_trafo=0
        self.actualizar_campos()

    def nuevo(self):
        from .frm_abm_transformadores import frmAbmTransformadores
        self.dialogo = frmAbmTransformadores(self.tipo_usuario, self.conn, 0)
        self.dialogo.show()

    def editar(self):
        if self.id == 0:
            return
        from .frm_abm_transformadores import frmAbmTransformadores
        self.dialogo = frmAbmTransformadores(self.tipo_usuario, self.conn, self.id)
        self.dialogo.exec()
        self.dialogo.close()
        self.actualizar_campos()

    def agregar(self):
        from .frm_mover_trafo import frmMoverTrafo
        self.dialogo = frmMoverTrafo(self.conn, 0, self.txtCT.text(),9)
        self.dialogo.exec()
        self.dialogo.close()
        self.actualizar_campos()

    def quitar(self):
        if self.id == 0:
            return
        from .frm_mover_trafo import frmMoverTrafo
        self.dialogo = frmMoverTrafo(self.conn, self.id, self.txtCT.text(),-1)
        self.dialogo.exec()
        self.dialogo.close()
        self.actualizar_campos()

    def aceptar(self):
        #esto funciona pero se deshabilito por el 'editar'
        cnn = self.conn
        cursor = cnn.cursor()
        str_set = "Potencia=" + self.txtPotencia.text() + ", "
        str_set = str_set + "Conexionado='" + self.cmbConexionado.currentText() + "', "
        str_set = str_set + "Marca='" + self.txtMarca.text() + "', "
        str_set = str_set + "N_chapa='" + self.txtNroChapa.text() + "', "
        str_set = str_set + "Tension_1=" + self.txtV1.text() + ", "
        str_set = str_set + "Tension_2=" + self.txtV2.text() + ", "
        if self.cmbTipo.currentText()=='Monofásico':
            str_set = str_set + str(self.cmbTipo.setCurrentIndex + 1) + ", "
        else:
            if self.cmbTipo.currentText()=='Bifásico':
                str_set = str_set + "Tipo=2, "
            else:
                str_set = str_set + "Tipo=3, "
        str_set = str_set + "Anio_fabricacion=" + self.txtAnio.text() + ", "
        str_set = str_set + "Obs='" + self.txtObservaciones.toPlainText().replace("'","") + "', "
        str_set = str_set + "Kit='" + self.txtKit.text().replace("'","") + "', "
        str_set = str_set + "Cromatografia='" + self.txtCromatografia.text().replace("'","") + "', "
        str_set = str_set + "Anomalia='" + self.cmbAnomalia.currentText().replace("'","") + "', "
        str_set = str_set + "Fecha_norm='" + str(self.datNormalizacion.date().toPyDate()).replace('-','') + "', "
        if self.chkCertificado.isChecked() == True:
            str_set = str_set + "Certificado=1, "
        else:
            str_set = str_set + "Certificado=0, "
        str_set = str_set + "Obs_pcb='" + self.txtObservacionesPCB.text().replace("'","") + "', "
        str_set = str_set + "aceite='" + self.txtAceite.text() + "', "
        if self.chkPropiedadUsuario.isChecked() == True:
            str_set = str_set + "Prop_usuario=1"
        else:
            str_set = str_set + "Prop_usuario=0"
        str_set = str_set + "Asilacion='" + self.cmbAislacion.currentText() + "', "
        str_set = str_set + "Peso='" + self.txtPeso.text() + "', "
        try:
            cursor.execute("UPDATE Transformadores SET " + str_set + " WHERE id_trafo=" + self.txtTrafo.text())
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudo actualizar')
        self.close()

    def salir(self):
        self.close()
