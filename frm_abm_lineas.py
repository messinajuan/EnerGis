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

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_abm_lineas.ui'))

class frmAbmLineas(DialogType, DialogBase):

    def __init__(self, tipo_usuario, conn, id):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.tipo_usuario = tipo_usuario
        self.conn = conn
        self.id = id
        vint = QIntValidator()
        vfloat = QDoubleValidator()
        self.txtCorriente.setValidator(vfloat)
        self.txtR1.setValidator(vfloat)
        self.txtX1.setValidator(vfloat)
        self.txtR0.setValidator(vfloat)
        self.txtX0.setValidator(vfloat)
        self.txtXc.setValidator(vfloat)
        self.txtSubconductores.setValidator(vint)

        if self.tipo_usuario==4:
            self.groupBox.setTitle('Datos de la línea')
            self.cmdAceptar.setEnabled(False)

        self.cmbTipo.addItem('Aéreo Convencional')
        self.cmbTipo.addItem('Subterráneo')
        self.cmbTipo.addItem('Concéntrico')
        self.cmbTipo.addItem('Preensamblado')
        self.cmbTipo.addItem('Línea Compacta')

        self.cmbMaterial.addItem('Al')
        self.cmbMaterial.addItem('Al/Al')
        self.cmbMaterial.addItem('Cu')
        self.cmbMaterial.addItem('Ac')
        self.cmbMaterial.addItem('Al/Ac')
        self.cmbMaterial.addItem('AcZn')
        self.cmbMaterial.addItem('AcCu')
        self.cmbMaterial.addItem('AcAl')

        self.cmbAislacion.addItem('Desnudo')
        self.cmbAislacion.addItem('PVC')
        self.cmbAislacion.addItem('XLPE')

        self.cmbMaterialNeutro.addItem('')
        self.cmbMaterialNeutro.addItem('Al')
        self.cmbMaterialNeutro.addItem('Al/Al')
        self.cmbMaterialNeutro.addItem('Cu')
        self.cmbMaterialNeutro.addItem('Ac')
        self.cmbMaterialNeutro.addItem('Al/Ac')
        self.cmbMaterialNeutro.addItem('AcZn')
        self.cmbMaterialNeutro.addItem('AcCu')
        self.cmbMaterialNeutro.addItem('AcAl')

        self.cmbMaterialHG.addItem('Acero')
        self.cmbMaterialHG.addItem('OPWG')

        self.cmbMaterialAL.addItem('')
        self.cmbMaterialAL.addItem('Al')
        self.cmbMaterialAL.addItem('Al/Al')
        self.cmbMaterialAL.addItem('Cu')
        self.cmbMaterialAL.addItem('Ac')
        self.cmbMaterialAL.addItem('Al/Ac')

        self.txtCorriente.setText('0')
        self.txtR1.setText('0')
        self.txtX1.setText('0')
        self.txtR0.setText('0')
        self.txtX0.setText('0')
        self.txtXc.setText('0')

        fase = [4, 5.94, 6, 6.63, 7.06, 8.37, 9.4, 10, 10.55, 11.94, 16, 19.95, 25, 25.05, 35, 50, 70, 95, 120, 150, 185, 240, 300, 340, 380, 435, 550, 680]
        neutro = [4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300, 340, 380, 435, 550, 680]
        hiloguardia = [4, 6, 10, 16, 25, 35, 50, 70, 95, 120]
        alumbrado = [16, 25, 35, 50]

        for s in fase:
            self.cmbSeccionFase.addItem(str(s))
        for s in neutro:
            self.cmbSeccionNeutro.addItem(str(s))
        for s in hiloguardia:
            self.cmbSeccionHG.addItem(str(s))
        for s in alumbrado:
            self.cmbSeccionAL.addItem(str(s))

        cnn = self.conn
        if self.id!=0:
            cursor = cnn.cursor()
            cursor.execute("SELECT Descripcion,Val1,Val2,Val3,Val4,Val5,Val6,Val7,Val8,Val9,Val10,Val11,Val12,Val13,Val14,Val15,Val16,Val17,Val18,uso FROM Elementos_Lineas WHERE id=" + str(self.id))
            #convierto el cursor en array
            datos_elemento = tuple(cursor)
            cursor.close()

            self.txtElemento.setText(datos_elemento[0][0])
            self.txtCorriente.setText(datos_elemento[0][1])

            for i in range (0, self.cmbSeccionFase.count()):
                if self.cmbSeccionFase.itemText(i) == str(datos_elemento[0][2]):
                    self.cmbSeccionFase.setCurrentIndex(i)

            self.txtR1.setText(datos_elemento[0][3])
            self.txtX1.setText(datos_elemento[0][4])
            self.txtR0.setText(datos_elemento[0][5])
            self.txtX0.setText(datos_elemento[0][6])
            self.txtXc.setText(datos_elemento[0][7])

            for i in range (0, self.cmbTipo.count()):
                if self.cmbTipo.itemText(i)[:1] == str(datos_elemento[0][8]):
                    self.cmbTipo.setCurrentIndex(i)

            for i in range (0, self.cmbMaterial.count()):
                if self.cmbMaterial.itemText(i) == str(datos_elemento[0][9]):
                    self.cmbMaterial.setCurrentIndex(i)

            for i in range (0, self.cmbAislacion.count()):
                if self.cmbAislacion.itemText(i) == str(datos_elemento[0][10]):
                    self.cmbAislacion.setCurrentIndex(i)

            if datos_elemento[0][11]=="1":
                self.grpNeutro.setChecked(True)
                for i in range (0, self.cmbMaterialNeutro.count()):
                    if self.cmbMaterialNeutro.itemText(i) == str(datos_elemento[0][12]):
                        self.cmbMaterialNeutro.setCurrentIndex(i)

            for i in range (0, self.cmbSeccionNeutro.count()):
                if self.cmbSeccionNeutro.itemText(i) == str(datos_elemento[0][13]):
                    self.cmbSeccionNeutro.setCurrentIndex(i)

            self.txtSubconductores.setText(datos_elemento[0][14])
            if datos_elemento[0][15]!='N':
                self.grpHG.setChecked(True)
                for i in range (0, self.cmbMaterialHG.count()):
                    if self.cmbMaterialHG.itemText(i) == str(datos_elemento[0][15]):
                        self.cmbMaterialHG.setCurrentIndex(i)

            for i in range (0, self.cmbSeccionHG.count()):
                if self.cmbSeccionHG.itemText(i) == str(datos_elemento[0][16]):
                    self.cmbSeccionHG.setCurrentIndex(i)

            if datos_elemento[0][17]!='N':
                self.grpAL.setChecked(True)
                for i in range (0, self.cmbMaterialAL.count()):
                    if self.cmbMaterialAL.itemText(i) == str(datos_elemento[0][17]):
                        self.cmbMaterialAL.setCurrentIndex(i)

            for i in range (0, self.cmbSeccionAL.count()):
                if self.cmbSeccionAL.itemText(i) == str(datos_elemento[0][18]):
                    self.cmbSeccionAL.setCurrentIndex(i)

            if datos_elemento[0][19]==1:
                self.rbTodo.setChecked(True)
            if datos_elemento[0][19]==2:
                self.rbAt.setChecked(True)
            if datos_elemento[0][19]==3:
                self.rbMt.setChecked(True)
            if datos_elemento[0][19]==4:
                self.rbBt.setChecked(True)
            if datos_elemento[0][19]==5:
                self.rbAcometida.setChecked(True)

        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)

        pass

    def aceptar(self):

        if self.txtElemento.text() == "":
            QMessageBox.critical(None, 'EnerGis 6', "❌ Debe ingresar un elemento")
            return
        if self.cmbMaterial.currentText() == "":
            QMessageBox.critical(None, 'EnerGis 6', "❌ Cargar sección del conductor !")
            return
        if self.cmbMaterial.currentText() == "":
            QMessageBox.critical(None, 'EnerGis 6', "❌ Seleccionar material del conductor !")
            return

        if self.grpNeutro.isChecked() == True:
            chk_neutro=1
        else:
            chk_neutro=0

        if chk_neutro==1:
            if self.cmbSeccionNeutro.currentText() == "":
                QMessageBox.critical(None, 'EnerGis 6', "❌ Cargar sección del neutro !")
                return
        if chk_neutro==1 and self.cmbMaterialNeutro.currentText() == "":
            QMessageBox.critical(None, 'EnerGis 6', "❌ Seleccionar material del neutro !")
            return

        if self.rbTodo.isChecked() == True:
            chk_uso=1
        if self.rbAt.isChecked() == True:
            chk_uso=2
        if self.rbMt.isChecked() == True:
            chk_uso=3
        if self.rbBt.isChecked() == True:
            chk_uso=4
        if self.rbAcometida.isChecked() == True:
            chk_uso=5

        if self.grpHG.isChecked() == True:
            chk_hg=1
        else:
            chk_hg=0

        if chk_hg==1:
            if self.cmbSeccionHG.currentText() == "":
                QMessageBox.critical(None, 'EnerGis 6', "❌ Cargar sección del hilo de guardia !")
                return
            if self.cmbMaterialHG.currentText() == "":
                QMessageBox.critical(None, 'EnerGis 6', "❌ Seleccionar material del hilo de guardia !")
                return
            material_hg=self.cmbMaterialHG.currentText()
        else:
            material_hg='N'

        if self.grpAL.isChecked() == True:
            chk_al=1
        else:
            chk_al=0

        if chk_al==1:
            if self.cmbSeccionAL.currentText() == "":
                QMessageBox.critical(None, 'EnerGis 6', "❌ Cargar sección del conductor de alumbrado !")
                return
            if self.cmbMaterialAL.currentText() == "":
                QMessageBox.critical(None, 'EnerGis 6', "❌ Seleccionar material del conductor de alumbrado !")
                return
            material_al=self.cmbMaterialAL.currentText()
        else:
            material_al='N'

        cnn = self.conn
        cursor = cnn.cursor()

        if self.id==0: #Nuevo
            cursor = cnn.cursor()
            cursor.execute("SELECT * FROM Elementos_Lineas WHERE Descripcion='" + self.txtElemento.text() + "'")
            #convierto el cursor en array
            rst = tuple(cursor)
            cursor.close()

            if len(rst)!=0:
                QMessageBox.critical(None, 'EnerGis 6', "❌ El elemento ya existe")
                return

            reply = QMessageBox.question(None, 'EnerGis 6', 'Guardar los datos ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:

                cursor = cnn.cursor()
                cursor.execute("SELECT MAX(id) FROM Elementos_Lineas")
                rows = cursor.fetchall()
                cursor.close()
                id = rows[0][0] + 1
                try:
                    cursor = cnn.cursor()
                    cursor.execute("INSERT INTO Elementos_Lineas (Id,Descripcion,Estilo,Val1,Val2,Val3,Val4,Val5,Val6,Val7,Val8,Val9,Val10,Val11,Val12,Val13,Val14,Val15,Val16,Val17,Val18,uso) VALUES (" + str(id) + ",'" + self.txtElemento.text() + "','0-False-1-1-0','" + self.txtCorriente.text() + "','" + self.cmbSeccionFase.currentText() + "','" + self.txtR1.text() + "','" + self.txtX1.text() + "','" + self.txtR0.text() + "','" + self.txtX0.text() + "','" + self.txtXc.text() + "','" + self.cmbTipo.currentText()[:1] + "','" + self.cmbMaterial.currentText() + "','" + self.cmbAislacion.currentText() + "','" + str(chk_neutro) + "','" + self.cmbMaterialNeutro.currentText() + "','" + self.cmbSeccionNeutro.currentText() + "','" + self.txtSubconductores.text() + "','" + material_hg + "','" + self.cmbSeccionHG.currentText() + "','" + material_al + "','" + self.cmbSeccionAL.currentText() + "'," + str(chk_uso) + ")")
                    cnn.commit()
                    QMessageBox.information(None, 'EnerGis 6', "ℹ️ Conductor agregado !")
                except:
                    cnn.rollback()
                    QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo grabar !")
                    return

        else: #edicion

            reply = QMessageBox.question(None, 'EnerGis 6', 'Desea guardar los cambios ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    cursor = cnn.cursor()
                    cursor.execute("UPDATE Elementos_Lineas SET Descripcion='" + self.txtElemento.text() + "',Estilo='0-False-1-1-0',Val1='" + self.txtCorriente.text() + "',Val2='" + self.cmbSeccionFase.currentText() + "',Val3='" + self.txtR1.text() + "',Val4='" + self.txtX1.text() + "',Val5='" + self.txtR0.text() + "',Val6='" + self.txtX0.text() + "',Val7='" + self.txtXc.text() + "',Val8='" + self.cmbTipo.currentText()[:1] + "',Val9='" + self.cmbMaterial.currentText() + "',Val10='" + self.cmbAislacion.currentText() + "',Val11='" + str(chk_neutro) + "',Val12='" + self.cmbMaterialNeutro.currentText() + "',Val13='" + self.cmbSeccionNeutro.currentText() + "',Val14='" + self.txtSubconductores.text() + "',Val15='" + material_hg + "',Val16='" + self.cmbSeccionHG.currentText() + "',Val17='" + material_al + "',Val18='" + self.cmbSeccionAL.currentText() + "', uso=" + str(chk_uso) + " WHERE id=" + str(self.id))
                    cnn.commit()
                    QMessageBox.information(None, 'EnerGis 6', "ℹ️ Actualizado !")
                except:
                    cnn.rollback()
                    QMessageBox.warning(None, 'EnerGis 6', "❌ No se pudo actualizar !")
                    return
        self.close()
        pass

    def salir(self):
        self.close()
        pass
