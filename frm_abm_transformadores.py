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

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_abm_transformadores.ui'))

class frmAbmTransformadores(DialogType, DialogBase):

    def __init__(self, tipo_usuario, conn, id):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        #basepath = os.path.dirname(os.path.realpath(__file__))
        self.tipo_usuario = tipo_usuario
        self.conn = conn
        self.id = id
        vint = QIntValidator()
        vfloat = QDoubleValidator()
        self.txtPotencia.setValidator(vfloat)
        self.txtAnio.setValidator(vint)
        if self.tipo_usuario==4:
            self.groupBox.setTitle('Datos del Transformador')
            self.cmdAceptar.setEnabled(False)
        self.cmbV1.addItem('220000')
        self.cmbV1.addItem('132000')
        self.cmbV1.addItem('66000')
        self.cmbV1.addItem('33000')
        self.cmbV1.addItem('19000')
        self.cmbV1.addItem('13200')
        self.cmbV1.addItem('7620')
        self.cmbV1.addItem('6600')
        self.cmbV2.addItem('132000')
        self.cmbV2.addItem('66000')
        self.cmbV2.addItem('33000')
        self.cmbV2.addItem('19000')
        self.cmbV2.addItem('13200')
        self.cmbV2.addItem('7620')
        self.cmbV2.addItem('6600')
        self.cmbV2.addItem('400')
        self.cmbV2.addItem('231')
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
        self.txtTrafo.setText(str(self.id))
        self.txtAceite.setText("0")
        self.txtAceite.setValidator(vfloat)
        self.txtPeso.setText("0")
        self.txtPeso.setValidator(vfloat)
        cnn = self.conn
        if self.id!=0: #edit
            cursor = cnn.cursor()
            cursor.execute("SELECT Potencia,Conexionado,Tension_1,Tension_2,Marca,N_chapa,Tipo,Anio_fabricacion,Obs,Prop_usuario,Kit,Cromatografia,Anomalia,Fecha_norm,Obs_pcb,Certificado,ISNULL(aceite,0),ISNULL(aislacion,'Aceite'),ISNULL(peso,0) FROM Transformadores WHERE id_trafo=" + str(self.id))
            #convierto el cursor en array
            datos_trafo = tuple(cursor)
            cursor.close()
            self.txtPotencia.setText(str(datos_trafo[0][0]))
            for i in range (0, self.cmbConexionado.count()):
                if self.cmbConexionado.itemText(i) == str(datos_trafo[0][1]):
                    self.cmbConexionado.setCurrentIndex(i)
            for i in range (0, self.cmbV1.count()):
                if int(self.cmbV1.itemText(i)) == datos_trafo[0][2]:
                    self.cmbV1.setCurrentIndex(i)
            for i in range (0, self.cmbV2.count()):
                if int(self.cmbV2.itemText(i)) == datos_trafo[0][3]:
                    self.cmbV2.setCurrentIndex(i)
            self.txtMarca.setText(datos_trafo[0][4])
            self.txtNroChapa.setText(datos_trafo[0][5])
            if datos_trafo[0][6]==1:
                self.cmbTipo.setCurrentIndex(0)
            elif datos_trafo[0][6]==2:
                self.cmbTipo.setCurrentIndex(1)
            else:
                self.cmbTipo.setCurrentIndex(2)
            self.txtAnio.setText(datos_trafo[0][7])
            self.txtObservaciones.setText(datos_trafo[0][8])
            if datos_trafo[0][9]==1:
                self.chkPropiedadUsuario.setChecked(True)
            else:
                self.chkPropiedadUsuario.setChecked(False)
            self.txtKit.setText(datos_trafo[0][10])
            self.txtCromatografia.setText(datos_trafo[0][11])
            #me fijo si lo que tengo en la base esta en el combo
            b_existe = False
            for i in range (0, self.cmbAnomalia.count()):
                if self.cmbAnomalia.itemText(i) == datos_trafo[0][12].strip():
                    self.cmbAnomalia.setCurrentIndex(i)
                    b_existe=True
            if b_existe==False:
                if datos_trafo[0][12].strip() == "":
                    self.cmbAnomalia.setCurrentIndex(0)
                else:
                    #si no esta lo agrego y selecciono
                    self.cmbAnomalia.addItem (datos_trafo[0][12].strip() + ' *')
                    self.cmbAnomalia.setCurrentIndex(self.cmbAnomalia.count())
            if datos_trafo[0][13]!=None:
                self.datNormalizacion.setDate(datos_trafo[0][13])
            self.txtObservacionesPCB.setText(datos_trafo[0][14])
            if datos_trafo[0][15]==1:
                self.chkCertificado.setChecked(True)
            else:
                self.chkCertificado.setChecked(False)
            self.txtAceite.setText(str(datos_trafo[0][16]))
            for i in range (0, self.cmbAislacion.count()):
                if self.cmbAislacion.itemText(i) == str(datos_trafo[0][17]):
                    self.cmbAislacion.setCurrentIndex(i)
            self.txtPeso.setText(str(datos_trafo[0][18]))
        self.cmbConexionado.activated.connect(self.elijo_conexionado)
        self.cmbTipo.activated.connect(self.elijo_tipo)
        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)
        self.cmdParametros.clicked.connect(self.parametros)

    def elijo_conexionado(self):
        if self.cmbConexionado.currentText()=="M":
            self.cmbTipo.setCurrentIndex(0)
        else:
            if self.cmbConexionado.currentText()=="B":
                self.cmbTipo.setCurrentIndex(1)
            else:
                self.cmbTipo.setCurrentIndex(2)

    def elijo_tipo(self):
        if self.cmbTipo.currentText()=="Monofásico":
            if self.cmbConexionado.currentText()!="M":
                QMessageBox.warning(None, 'EnerGis 6', '❌ Verificar Conexionado')
        if self.cmbTipo.currentText()=="Bifásico":
            if self.cmbConexionado.currentText()!="B":
                QMessageBox.warning(None, 'EnerGis 6', '❌ Verificar Conexionado')
        if self.cmbTipo.currentText()=="Trifásico":
            if self.cmbConexionado.currentText()=="M" or self.cmbConexionado.currentText()=="B":
                QMessageBox.warning(None, 'EnerGis 6', '❌ Verificar Conexionado')

    def aceptar(self):
        cnn = self.conn
        if self.cmbTipo.currentText()=='Monofásico':
            tipo=1
        else:
            if self.cmbTipo.currentText()=='Bifásico':
                tipo=2
            else:
                tipo=3
        if self.chkCertificado.isChecked() == True:
            certificado=1
        else:
            certificado=0
        if self.chkPropiedadUsuario.isChecked() == True:
            prop_usuario=1
        else:
            prop_usuario=0
        if self.txtPotencia.text() == "":
            QMessageBox.critical(None, 'EnerGis 6', "❌ Debe ingresar una potencia")
            return
        if self.txtAnio.text() == "":
            self.txtAnio.setText("1900")
        if self.id==0: #Nuevo
            reply = QMessageBox.question(None, 'EnerGis 6', 'Guardar los datos ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                cursor = cnn.cursor()
                cursor.execute("SELECT MAX(Id_Trafo) FROM Transformadores")
                rows = cursor.fetchall()
                cursor.close()
                if rows[0][0]==None:
                    self.id  = 1
                else:
                    self.id  = rows[0][0] + 1
                try:
                    cursor = cnn.cursor()
                    cnn.commit()
                    cursor.execute("INSERT INTO Transformadores (Id_Trafo,Potencia,Conexionado,Marca,N_chapa,Tension_1,Tension_2,Tipo,Anio_fabricacion,Obs,Kit,Cromatografia,Anomalia,Fecha_norm,Certificado,Obs_pcb,aceite,Prop_usuario,Aislacion,Peso,Usado) VALUES (" + str(self.id) + "," + self.txtPotencia.text() + ",'" + self.cmbConexionado.currentText() + "','" + self.txtMarca.text() + "','" + self.txtNroChapa.text() + "'," + self.cmbV1.currentText() + "," + self.cmbV2.currentText() + "," + str(tipo) + ",'" + self.txtAnio.text() + "','" + self.txtObservaciones.toPlainText() + "','" + self.txtKit.text() + "','" + self.txtCromatografia.text() + "','" + self.cmbAnomalia.currentText() + "','" + str(self.datNormalizacion.date().toPyDate()).replace('-','') + "'," + str(certificado) + ",'" + self.txtObservacionesPCB.text() + "'," + self.txtAceite.text() + "," + str(prop_usuario) + ",'" + self.cmbAislacion.currentText() + "'," + self.txtPeso.text() + ",1)")
                    QMessageBox.information(None, 'EnerGis 6', "ℹ️ Transformador agregado !")
                except:
                    cnn.rollback()
                    QMessageBox.warning(None, 'EnerGis 6', "❌ No  se pudo grabar !")
                    return
        else: #edicion
            str_set = "Potencia=" + self.txtPotencia.text() + ", "
            str_set = str_set + "Conexionado='" + self.cmbConexionado.currentText() + "', "
            str_set = str_set + "Marca='" + self.txtMarca.text() + "', "
            str_set = str_set + "N_chapa='" + self.txtNroChapa.text() + "', "
            str_set = str_set + "Tension_1=" + self.cmbV1.currentText() + ", "
            str_set = str_set + "Tension_2=" + self.cmbV2.currentText() + ", "
            str_set = str_set + "Tipo=" + str(tipo) + ", "
            str_set = str_set + "Anio_fabricacion=" + self.txtAnio.text() + ", "
            str_set = str_set + "Obs='" + self.txtObservaciones.toPlainText() + "', "
            str_set = str_set + "Kit='" + self.txtKit.text() + "', "
            str_set = str_set + "Cromatografia='" + self.txtCromatografia.text() + "', "
            str_set = str_set + "Anomalia='" + self.cmbAnomalia.currentText() + "', "
            str_set = str_set + "Fecha_norm='" + str(self.datNormalizacion.date().toPyDate()).replace('-','') + "', "
            str_set = str_set + "Certificado=" + str(certificado) + ", "
            str_set = str_set + "Obs_pcb='" + self.txtObservacionesPCB.text() + "', "
            str_set = str_set + "aceite='" + self.txtAceite.text() + "', "
            str_set = str_set + "Prop_usuario=" + str(prop_usuario) + ", "
            str_set = str_set + "Aislacion='" + self.cmbAislacion.currentText() + "', "
            str_set = str_set + "Peso=" + self.txtPeso.text()
            reply = QMessageBox.question(None, 'EnerGis 6', 'Desea guardar los cambios ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    cursor = cnn.cursor()
                    cursor.execute("UPDATE Transformadores SET " + str_set + " WHERE id_trafo=" + str(self.id))
                    cnn.commit()
                    QMessageBox.information(None, 'EnerGis 6', "ℹ️ Actualizado !")
                    #from .frm_mover_trafo import frmMoverTrafo
                    #self.dialogo = frmMoverTrafo(self.conn, 0, self.txtCT.text(),1)
                    #self.dialogo.exec()
                    #self.dialogo.close()
                except:
                    cnn.rollback()
                    QMessageBox.warning(None, 'EnerGis 6', "❌ No  se pudo actualizar !")
                    return
        self.close()

    def parametros(self):
        if self.id==0:
            self.aceptar()
        if self.id==0:
            return
        from .frm_parametros_trafo import frmParametrosTrafo
        dialogo = frmParametrosTrafo(self.tipo_usuario, self.conn, self.id, float(self.txtPotencia.text()))
        dialogo.exec()
        dialogo.close()

    def salir(self):
        self.close()
