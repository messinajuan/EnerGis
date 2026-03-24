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
from PyQt6 import QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTreeWidgetItem
from PyQt6.QtWidgets import QMessageBox, QApplication, QProgressDialog
from PyQt6.QtGui import QIcon, QBrush, QColor
from PyQt6.QtCore import QDate
from PyQt6 import uic
from datetime import datetime

basepath = os.path.dirname(os.path.realpath(__file__))

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_contingencias.ui'))

class frmContingencias (DialogType, DialogBase):

    def __init__(self, conn, mapCanvas, tipo_usuario, mnodos, mlineas, red_verificada):
        super().__init__()
        self.setupUi(self)
        self.installEventFilter(self)

        self.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowTitleHint | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowCloseButtonHint)

        self.mapCanvas=mapCanvas
        self.tipo_usuario=tipo_usuario
        self.conn = conn
        import clr
        from System import Int64, Array
        if red_verificada==True:
            # Crear arreglos
            self.amnodos = Array.CreateInstance(Int64, len(mnodos), len(mnodos[0]))
            self.amlineas = Array.CreateInstance(Int64, len(mlineas), len(mlineas[0]))
            # Copiar valores a mnodos
            for i in range(len(mnodos)):
                for j in range(len(mnodos[0])):
                    self.amnodos[i, j] = mnodos[i][j]
            # Copiar valores a mlineas
            for i in range(len(mlineas)):
                for j in range(len(mlineas[0])):
                    self.amlineas[i, j] = mlineas[i][j]
            # Cargar el ensamblado
            clr.AddReference(os.path.join(basepath, 'NavRed6.dll'))
            from EnerGis6.NavRed6 import NavRed
            # Instanciar la clase NavRed
            self.navred_instance = NavRed()
        self.txtResponsable.setText("SD")
        self.elementos = []
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT * FROM Causas")
        #convierto el cursor en array
        self.causas = tuple(cursor)
        cursor.close()
        for i in range (0, len(self.causas)):
            self.cmbCausa.addItem(self.causas[i][2])
        self.cmbTipo.addItem("Aparato Maniobra MT")
        self.cmbTipo.addItem("Aparato Maniobra BT")
        self.cmbTipo.addItem("Usuario")
        self.cmbTipo.addItem("Centro Transformación")
        self.datFecha.setDate(QDate.currentDate())
        self.cmbTipoOperacion.addItem("Apertura")
        self.cmbTipoOperacion.addItem("Cierre")
        self.cmbTipoZona.addItem("Aerea")
        self.cmbTipoZona.addItem("Subterránea")
        self.cmbZona.addItem("Rural")
        self.cmbZona.addItem("Urbana")
        self.cmbListar.addItem("Contingencia")
        self.cmbListar.addItem("Fecha")
        self.cmbListar.addItem("Elemento")
        self.cmbTiempo.addItem("Bueno")
        self.cmbTiempo.addItem("Bueno - Ventoso")
        self.cmbTiempo.addItem("Lluvioso")
        self.cmbTiempo.addItem("Nublado - Posible lluvia")
        self.cmbTiempo.addItem("Tormenta Eléctrica")
        self.cmbTiempo.addItem("Ventoso")
        self.cmbTiempo.addItem("Ventoso - Lluvia")
        self.cmbTiempo.addItem("Ventoso - Lluvia - Descargas")
        self.seleccionado = -1
        self.id_causa = 0
        self.id_contingencia = 0
        self.advertencias =[]
        cursor = cnn.cursor()
        cursor.execute("SELECT ult_cont FROM log_ope")
        ult_cont = tuple(cursor)
        cursor.close()
        self.ult_contingencia = ult_cont[0][0] + 1
        self.lblContingencia.setText(str(self.ult_contingencia))
        self.cmbListar.activated.connect(self.buscar)
        self.cmdBuscar.clicked.connect(self.buscar)
        self.chkExpandir.stateChanged.connect(self.expandir)
        self.cmbTipoOperacion.activated.connect(self.cambiar_tipo_operacion)
        self.cmbCausa.activated.connect(self.cambiar_causa)
        self.cmdNuevaContingencia.clicked.connect(self.nueva_contingencia)
        self.cmdNuevoEvento.clicked.connect(self.nuevo_evento)
        self.cmdImportar.clicked.connect(self.importar)
        self.cmdReclamos.clicked.connect(self.reclamos)
        self.cmdEditar.clicked.connect(self.editar)
        self.cmdElemento.clicked.connect(self.elemento)
        self.cmdBorrar.clicked.connect(self.borrar)
        self.cmdGrabar.clicked.connect(self.grabar)
        self.cmdCancelar.clicked.connect(self.cancelar)
        self.cmdVerificar.clicked.connect(self.verificar)
        self.cmdRegistrar.clicked.connect(self.registrar)
        self.cmdSalir.clicked.connect(self.salir)
        self.trvContingencias.itemClicked.connect(self.elijo_elemento)
        self.bloquear_controles(False)
        self.cmbListar.setCurrentIndex(0)
        self.buscar()
        cursor = cnn.cursor()
        cursor.execute("UPDATE Importo_Operaciones SET tipo_elemento='Elem_ManiobraMT' WHERE tipo_elemento IS NULL")
        cnn.commit()
        cursor.close()
        if self.tipo_usuario==4:
            self.cmdImportar.setEnabled(False)
            self.cmdNuevaContingencia.setEnabled(False)
            self.cmdNuevoEvento.setEnabled(False)
            self.cmdRegistrar.setEnabled(False)
        else:
             self.cmdRegistrar.setEnabled(red_verificada)

    def bloquear_controles(self, estado):
        self.cmbTipo.setEnabled(estado)
        self.txtNombre.setEnabled(estado)
        self.cmdElemento.setEnabled(estado)
        self.cmbTipoOperacion.setEnabled(estado)
        self.datFecha.setEnabled(estado)
        self.timHora.setEnabled(estado)
        self.cmbCausa.setEnabled(estado)
        self.cmbTipoInstalacion.setEnabled(estado)
        self.cmbTipoZona.setEnabled(estado)
        self.cmbZona.setEnabled(estado)
        self.txtResponsable.setEnabled(estado)
        self.cmbTiempo.setEnabled(estado)
        self.txtObservaciones.setEnabled(estado)

    def expandir(self):
        if self.chkExpandir.isChecked() == True:
            self.trvContingencias.expandAll()
            #self.chkExpandir.setCurrentText('Colapsar')
        else:
            self.trvContingencias.collapseAll()

    def listar(self, variable):
        fecha = ''
        nombre = ''
        tipo = 2
        contingencia = ''
        cnn = self.conn
        cursor = cnn.cursor()
        if self.cmbListar.currentText()=="Fecha":
            if variable!=None:
                fecha = datetime.strptime(variable, "%d/%m/%Y")
                dia = fecha.day
                mes = fecha.month
                anio = fecha.year
                cursor = cnn.cursor()
                cursor.execute("SELECT id,fechahora,contingencia,nombre,importo_operaciones.tipo,motivo,tipo_elemento,elemento_falla,zona_falla,tipo_zona_falla,est_tiempo,responsable,observaciones FROM Importo_Operaciones INNER JOIN Causas ON Importo_Operaciones.Causa = Causas.Id_Causa WHERE incorporada=0 AND day(fechahora)=" + str(dia) + " AND month(fechahora)=" + str(mes) + " AND year(fechahora)=" + str(anio) + " ORDER BY fechahora, nombre, tipo")
                self.elementos = tuple(cursor)
                cursor.close()
            else:
                cursor = cnn.cursor()
                cursor.execute("SELECT id,fechahora,contingencia,nombre,importo_operaciones.tipo,motivo,tipo_elemento,elemento_falla,zona_falla,tipo_zona_falla,est_tiempo,responsable,observaciones FROM Importo_Operaciones INNER JOIN Causas ON Importo_Operaciones.Causa = Causas.Id_Causa WHERE incorporada=0 ORDER BY fechahora, nombre, tipo")
                self.elementos = tuple(cursor)
                cursor.close()
            self.trvContingencias.clear()
            self.trvContingencias.setColumnCount(3)
            self.trvContingencias.setHeaderLabels(["Fecha          Elemento", "Hora          Tipo", "Causa"])
            for i in range (0, len(self.elementos)):
                if str(self.elementos[i][1])[:10] != fecha:
                    fecha = str(self.elementos[i][1])[:10]
                    root = QTreeWidgetItem(self.trvContingencias, [fecha])
                    nombre = ''
                    tipo = 2
                if self.elementos[i][3] != nombre:
                    nombre = str(self.elementos[i][3])
                    icon1 = QIcon(os.path.join(basepath,"icons", 'img_usuario3.png'))
                    if self.elementos[i][6] == "Elem_ManiobraBT":
                        icon1 = QIcon(os.path.join(basepath,"icons", 'img_seccionador_bt.png'))
                    if self.elementos[i][6] == "Elem_ManiobraMT":
                        icon1 = QIcon(os.path.join(basepath,"icons", 'img_seccionador_mt.png'))
                        if nombre[:2] == "ST":
                            icon1 = QIcon(os.path.join(basepath,"icons", 'img_transformador2.png'))
                    if self.elementos[i][6] == "Transformador":
                        icon1 = QIcon(os.path.join(basepath,"icons", 'img_transformador2.png'))
                    child = QTreeWidgetItem(root, [nombre])
                    child.setIcon(0, icon1)
                    tipo = 2
                if self.elementos[i][4] != tipo:
                    tipo = self.elementos[i][4]
                    causa = self.elementos[i][5]
                    hora = self.elementos[i][1].strftime("%H:%M")
                    if tipo == -1:
                        icon2 = QIcon(os.path.join(basepath,"icons", 'img_abrir_elemento_maniobra.png'))
                        schild = QTreeWidgetItem(child, [str(i), hora + ' Apertura', causa])
                        schild.setIcon(1, icon2)
                    else:
                        icon2 = QIcon(os.path.join(basepath,"icons", 'img_cerrar_elemento_maniobra.png'))
                        schild = QTreeWidgetItem(child, [str(i), hora + ' Cierre', causa])
                        schild.setIcon(1, icon2)
                    schild.setForeground(0, QBrush(QColor('white')))
                self.trvContingencias.setRootIsDecorated(True)
        if self.cmbListar.currentText()=="Contingencia":
            cursor = cnn.cursor()
            if variable!=None:
                cursor.execute("SELECT id,fechahora,contingencia,nombre,importo_operaciones.tipo,motivo,tipo_elemento,elemento_falla,zona_falla,tipo_zona_falla,est_tiempo,responsable,observaciones FROM Importo_Operaciones INNER JOIN Causas ON Importo_Operaciones.Causa = Causas.Id_Causa WHERE incorporada=0 AND contingencia=" + str(variable) + " ORDER BY contingencia, fechahora, nombre, tipo")
                self.elementos = tuple(cursor)
                cursor.close()
            else:
                cursor.execute("SELECT id,fechahora,contingencia,nombre,importo_operaciones.tipo,motivo,tipo_elemento,elemento_falla,zona_falla,tipo_zona_falla,est_tiempo,responsable,observaciones FROM Importo_Operaciones INNER JOIN Causas ON Importo_Operaciones.Causa = Causas.Id_Causa WHERE incorporada=0 ORDER BY contingencia, fechahora, nombre, tipo")
                self.elementos = tuple(cursor)
                cursor.close()
            self.trvContingencias.clear()
            self.trvContingencias.setColumnCount(3)
            self.trvContingencias.setHeaderLabels(["Contingencia          Fecha", "Elemento", "Tipo       Causa"])
            for i in range (0, len(self.elementos)):
                if str(self.elementos[i][2]) != contingencia:
                    root = QTreeWidgetItem(self.trvContingencias, [str(self.elementos[i][2])])
                    contingencia = str(self.elementos[i][2])
                    fecha = ''
                    nombre = ''
                if str(self.elementos[i][1])[:10] != fecha:
                    fecha = str(self.elementos[i][1])[:16]
                    child = QTreeWidgetItem(root, [fecha])
                    nombre = ''
                if self.elementos[i][3] != nombre:
                    nombre = str(self.elementos[i][3])
                    icon1 = QIcon(os.path.join(basepath,"icons", 'img_usuario3.png'))
                    if self.elementos[i][6] == "Elem_ManiobraBT":
                        icon1 = QIcon(os.path.join(basepath,"icons", 'img_seccionador_bt.png'))
                    if self.elementos[i][6] == "Elem_ManiobraMT":
                        icon1 = QIcon(os.path.join(basepath,"icons", 'img_seccionador_mt.png'))
                        if nombre[:2] == "ST":
                            icon1 = QIcon(os.path.join(basepath,"icons", 'img_transformador2.png'))
                    if self.elementos[i][6] == "Transformador":
                        icon1 = QIcon(os.path.join(basepath,"icons", 'img_transformador2.png'))
                    causa = self.elementos[i][5]
                if self.elementos[i][4] == -1:
                    icon2 = QIcon(os.path.join(basepath,"icons", 'img_abrir_elemento_maniobra.png'))
                    schild = QTreeWidgetItem(child, [str(i), nombre, 'Apertura     ' + causa])
                else:
                    icon2 = QIcon(os.path.join(basepath,"icons", 'img_cerrar_elemento_maniobra.png'))
                    schild = QTreeWidgetItem(child, [str(i), nombre, 'Cierre         ' + causa])
                schild.setForeground(0, QBrush(QColor('white')))
                schild.setIcon(1, icon1)
                schild.setIcon(2, icon2)
                self.trvContingencias.setRootIsDecorated(True)
        if self.cmbListar.currentText()=="Elemento":
            cursor = cnn.cursor()
            if variable!=None:
                cursor.execute("SELECT id,fechahora,contingencia,nombre,importo_operaciones.tipo,motivo,tipo_elemento,elemento_falla,zona_falla,tipo_zona_falla,est_tiempo,responsable,observaciones FROM Importo_Operaciones INNER JOIN Causas ON Importo_Operaciones.Causa = Causas.Id_Causa WHERE incorporada=0 AND nombre LIKE '%" + str(variable) + "%' ORDER BY nombre, fechahora, tipo")
                self.elementos = tuple(cursor)
                cursor.close()
            else:
                cursor.execute("SELECT id,fechahora,contingencia,nombre,importo_operaciones.tipo,motivo,tipo_elemento,elemento_falla,zona_falla,tipo_zona_falla,est_tiempo,responsable,observaciones FROM Importo_Operaciones INNER JOIN Causas ON Importo_Operaciones.Causa = Causas.Id_Causa WHERE incorporada=0 ORDER BY nombre, fechahora, tipo")
                self.elementos = tuple(cursor)
                cursor.close()
            self.trvContingencias.clear()
            self.trvContingencias.setColumnCount(3)
            self.trvContingencias.setHeaderLabels(["Elemento          Fecha", "Tipo", "Causa"])
            for i in range (0, len(self.elementos)):
                if self.elementos[i][3] != nombre:
                    nombre = str(self.elementos[i][3])
                    icon1 = QIcon(os.path.join(basepath,"icons", 'img_usuario3.png'))
                    if self.elementos[i][6] == "Elem_ManiobraBT":
                        icon1 = QIcon(os.path.join(basepath,"icons", 'img_seccionador_bt.png'))
                    if self.elementos[i][6] == "Elem_ManiobraMT":
                        icon1 = QIcon(os.path.join(basepath,"icons", 'img_seccionador_mt.png'))
                        if nombre[:2] == "ST":
                            icon1 = QIcon(os.path.join(basepath,"icons", 'img_transformador2.png'))                            
                    if self.elementos[i][6] == "Transformador":
                        icon1 = QIcon(os.path.join(basepath,"icons", 'img_transformador2.png'))
                    root = QTreeWidgetItem(self.trvContingencias, [nombre])
                    causa = self.elementos[i][5]
                    fecha = ''
                    root.setIcon(0, icon1)
                if str(self.elementos[i][1])[:10] != fecha:
                    fecha = str(self.elementos[i][1])[:16]
                    child = QTreeWidgetItem(root, [fecha])
                if self.elementos[i][4] == -1:
                    icon2 = QIcon(os.path.join(basepath,"icons", 'img_abrir_elemento_maniobra.png'))
                    schild = QTreeWidgetItem(child, [str(i), 'Apertura', causa])
                else:
                    icon2 = QIcon(os.path.join(basepath,"icons", 'img_cerrar_elemento_maniobra.png'))
                    schild = QTreeWidgetItem(child, [str(i), 'Cierre', causa])
                schild.setForeground(0, QBrush(QColor('white')))
                schild.setIcon(1, icon2)
                self.trvContingencias.setRootIsDecorated(True)
        self.trvContingencias.setColumnWidth(0, 150)
        self.trvContingencias.setColumnWidth(1, 150)
        if self.chkExpandir.isChecked() == True:
            self.trvContingencias.expandAll()

    def buscar(self):
        if self.txtABuscar.text().strip()=="":
            self.listar(None)
        else:
            if self.cmbListar.currentText()=="Fecha":
                try:
                    datetime.strptime(self.txtABuscar.text(), "%d-%m-%Y")
                    self.listar(self.txtABuscar.text())
                except:
                    pass
            if self.cmbListar.currentText()=="Contingencia":
                if self.txtABuscar.text().isnumeric():
                    self.listar(self.txtABuscar.text())
            if self.cmbListar.currentText()=="Elemento":
                self.listar(self.txtABuscar.text())

    def elijo_elemento(self, item):
        if str(item.text(1)) == '': #no es un evento
            if self.cmbListar.currentText()=="Contingencia":
                padre = item.parent()
                if padre: #aparato
                    self.lblEvento.setText("<Automatico>")
                else:
                    self.lblContingencia.setText(item.text(0))
                    self.lblEvento.setText("<Automatico>")

        elif str(item.text(2)) != '': #evento
            #id,fechahora,contingencia,nombre,importo_operaciones.tipo,motivo,tipo_elemento,elemento_falla,zona_falla,tipo_zona_falla,est_tiempo,responsable,observaciones
            i = int(item.text(0))
            self.lblEvento.setText(str(self.elementos[i][0]))
            self.lblContingencia.setText(str(self.elementos[i][2]))
            if self.elementos[i][6] == "Elem_ManiobraMT":
                self.cmbTipo.setCurrentText("Aparato Maniobra MT")
            if self.elementos[i][6] == "Elem_ManiobraBT":
                self.cmbTipo.setCurrentText("Aparato Maniobra BT")
            if self.elementos[i][6] == "Transformador":
                self.cmbTipo.setCurrentText("Centro Transformación")
            if self.elementos[i][6] == "Usuario":
                self.cmbTipo.setCurrentText("Usuario")
            self.txtNombre.setText(self.elementos[i][3])
            if self.elementos[i][4]==-1:
                self.cmbTipoOperacion.setCurrentText('Apertura')
            else:
                self.cmbTipoOperacion.setCurrentText('Cierre')
            date = datetime.strptime(str(self.elementos[i][1]), "%Y-%m-%d %H:%M:%S")
            self.datFecha.setDate(date)
            self.timHora.setTime(date.time())
            self.cmbCausa.setCurrentText(self.elementos[i][5])
            self.id_causa = self.cmbCausa.currentIndex()
            self.setear_elemento_falla()
            for j in range (0, len(self.tipo_instalacion)):
                if str(self.tipo_instalacion[j][0]) == str(self.elementos[i][7]):
                    self.cmbTipoInstalacion.setCurrentIndex(j)
            self.cmbZona.setCurrentText(self.elementos[i][8])
            self.cmbTipoZona.setCurrentText(self.elementos[i][9])
            self.cmbTiempo.setCurrentText(self.elementos[i][10])
            self.txtResponsable.setText(self.elementos[i][11])
            self.txtObservaciones.setText(self.elementos[i][12])
            if self.tipo_usuario!=4:
                self.cmdEditar.setEnabled(True)
                self.cmdBorrar.setEnabled(True)
            self.cmdGrabar.setEnabled(False)
            self.cmdCancelar.setEnabled(False)
        if self.tipo_usuario!=4:
            self.cmdEditar.setEnabled(True)
            self.cmdBorrar.setEnabled(True)
        self.cmdGrabar.setEnabled(False)
        self.cmdCancelar.setEnabled(False)

    def cambiar_tipo_operacion(self):
        self.id_causa = self.cmbCausa.currentIndex()
        self.setear_elemento_falla()

    def cambiar_causa(self):
        self.id_causa = self.cmbCausa.currentIndex()
        self.setear_elemento_falla()

    def setear_elemento_falla(self):
        tipo_falla = self.causas[self.id_causa][5]

        if self.cmbTipoOperacion.currentText()=="Apertura":
            self.tipo_instalacion = [[701,"ET AT/MT"],
            [702,"CD MT"],
            [703,"SE MT/BT"],
            [704,"LMT"],
            [705,"LBT"],
            [706,"Caja Esquinera/Buzón"],
            [707,"Acometida Domiciliaria"],
            [708,"Cliente"],
            [709,"Alumbrado"]]
            self.cmbTipoInstalacion.clear()
            for i in range (0, len(self.tipo_instalacion)):
                self.cmbTipoInstalacion.addItem(self.tipo_instalacion[i][1])
            if self.cmbTipo.currentText() == "Usuario":
                self.cmbTipoInstalacion.setCurrentIndex(7)
            if self.cmbTipo.currentText() == "Aparato Maniobra BT":
                self.cmbTipoInstalacion.setCurrentIndex(4)
            if self.cmbTipo.currentText() == "Aparato Maniobra MT":
                self.cmbTipoInstalacion.setCurrentIndex(3)
            if self.cmbTipo.currentText() == "Centro Transformación":
                self.cmbTipoInstalacion.setCurrentIndex(2)
        else:
            self.tipo_instalacion = [[707903,"Acometida Domiciliaria - Cortado"],
            [707901,"Acometida Domiciliaria - Cortocircuito"],
            [707905,"Acometida Domiciliaria - Desatado"],
            [707904,"Acometida Domiciliaria - Deshilachado"],
            [707907,"Acometida Domiciliaria - Erosionado/Sulfatado"],
            [707910,"Acometida Domiciliaria - Flojo/a"],
            [707911,"Acometida Domiciliaria - Normal"],
            [707908,"Acometida Domiciliaria - Quemado"],
            [707916,"Acometida Domiciliaria - Robo"],
            [709901,"Alumbrado - Cortocircuito"],
            [709907,"Alumbrado - Erosionado/Sulfatado"],
            [709910,"Alumbrado - Flojo/a"],
            [709911,"Alumbrado - Normal"],
            [709908,"Alumbrado - Quemado"],
            [709916,"Alumbrado - Robo"],
            [709906,"Alumbrado - Roto/a"],
            [706901,"Caja Esquinera/Buzón - Cortocircuito"],
            [706911,"Caja Esquinera/Buzón - Normal"],
            [706908,"Caja Esquinera/Buzón - Quemado"],
            [706906,"Caja Esquinera/Buzón - Roto/a"],
            [702901,"CD MT - Cortocircuito"],
            [702913,"CD MT - Falla Interna"],
            [702401912,"CD MT - Interruptor MT - Abierto"],
            [702401913,"CD MT - Interruptor MT - Falla Interna"],
            [702401908,"CD MT - Interruptor MT - Quemado"],
            [702911,"CD MT - Normal"],
            [702916,"CD MT - Robo"],
            [708913,"Cliente - Falla Interna"],
            [708911,"Cliente - Normal"],
            [701901,"ET AT/MT - Cortocircuito"],
            [701913,"ET AT/MT - Falla Interna"],
            [701401912,"ET AT/MT - Interruptor MT - Abierto"],
            [701401913,"ET AT/MT - Interruptor MT - Falla Interna"],
            [701401908,"ET AT/MT - Interruptor MT - Quemado"],
            [701911,"ET AT/MT - Normal"],
            [705903,"LBT - Cortado"],
            [705901,"LBT - Cortocircuito"],
            [705905,"LBT - Desatado"],
            [705904,"LBT - Deshilachado"],
            [705911,"LBT - Normal"],
            [705908,"LBT - Quemado"],
            [705916,"LBT - Robo"],
            [705906,"LBT - Roto/a"],
            [704903,"LMT - Cortado"],
            [704901,"LMT - Cortocircuito"],
            [704905,"LMT - Desatado"],
            [704904,"LMT - Deshilachado"],
            [701401912,"LMT - Interruptor MT - Abierto"],
            [701401913,"LMT - Interruptor MT - Falla Interna"],
            [704401908,"LMT - Interruptor MT - Quemado"],
            [704403908,"LMT - Reconectador MT - Quemado"],
            [704404908,"LMT - Seccionalizador MT - Quemado"],
            [704402908,"LMT - Seccionador MT - Quemado"],
            [704413908,"LMT - Fusible MT - Quemado"],
            [704911,"LMT - Normal"],
            [704916,"LMT - Robo"],
            [704906,"LMT - Roto/a"],
            [703901,"SE MT/BT - Cortocircuito"],
            [703913,"SE MT/BT - Falla Interna"],
            [703908,"SE MT/BT - Quemado"],
            [703911,"SE MT/BT - Normal"],
            [703916,"SE MT/BT - Robo"],
            [703906,"SE MT/BT - Roto/a"]]
            self.cmbTipoInstalacion.clear()
            for i in range (0, len(self.tipo_instalacion)):
                self.cmbTipoInstalacion.addItem(self.tipo_instalacion[i][1])
            if self.cmbTipo.currentText() == "Usuario":
                codigo = 708
            if self.cmbTipo.currentText() == "Aparato Maniobra BT":
                codigo = 705
            if self.cmbTipo.currentText() == "Aparato Maniobra MT":
                codigo = 704
            if self.cmbTipo.currentText() == "Centro Transformación":
                codigo = 703
            for i in range (0, len(self.cmbTipoInstalacion)):
                if str(self.tipo_instalacion[i][0])[:3] == str(codigo):
                    self.cmbTipoInstalacion.setCurrentIndex(i)
            for i in range (0, len(self.cmbTipoInstalacion)):
                if str(self.tipo_instalacion[i][0])[:3] == str(codigo) and str(self.tipo_instalacion[i][0])[-3:] == str(tipo_falla):
                    self.cmbTipoInstalacion.setCurrentIndex(i)

    def verificar(self):
        from .frm_elegir_fechas import frmElegirFechas
        dialogo = frmElegirFechas()
        dialogo.exec()
        if dialogo.fecha_desde==None and dialogo.fecha_hasta==None:
            return
        self.fecha_desde = dialogo.fecha_desde
        self.fecha_hasta = dialogo.fecha_hasta
        str_sql=''
        if self.fecha_desde!=None:
            str_sql = str_sql + " AND fechahora>='" + str(self.fecha_desde)[:19].replace('-','') + "'"

        if self.fecha_hasta!=None:
            str_sql = str_sql + " AND fechahora<='" + str(self.fecha_hasta)[:19].replace('-','') + "'"
        cnn = self.conn
        self.advertencias =[]
        linea=[]
        #analizo que esten los elementos en el mapa
        cursor = cnn.cursor()
        cursor.execute("SELECT DISTINCT nombre, id FROM Importo_Operaciones WHERE incorporada=0 AND tipo_elemento<>'Usuario'" + str_sql + " AND nombre NOT IN (SELECT nombre FROM nodos WHERE Nodos.Tension>0 AND elmt=2 OR elmt=3)")
        rst = tuple(cursor)
        cursor.close()
        for rs in rst:
            b_existe=False
            for j in range(0, len(self.advertencias)):
                if rs[0]==self.advertencias[j][2]:
                    b_existe=True
                    break
            if b_existe==False:
                linea=[]
                linea.append("Error")
                linea.append("No se encuentra en el plano el aparato: " + rs[0])
                linea.append(rs[0])
                linea.append(str(rs[1]))
                linea.append('Elem_Maniobra')
                self.advertencias.append (linea)
        #analizo que esten los usuarios
        cursor = cnn.cursor()
        cursor.execute("SELECT DISTINCT nombre, id FROM Importo_Operaciones WHERE incorporada=0 AND tipo_elemento='Usuario'" + str_sql + " AND nombre NOT IN (SELECT id_usuario FROM usuarios)")
        rst = tuple(cursor)
        cursor.close()
        for rs in rst:
            b_existe=False
            for j in range(0, len(self.advertencias)):
                if rs[0]==self.advertencias[j][2]:
                    b_existe=True
                    break
            if b_existe==False:
                linea=[]
                linea.append("Error")
                linea.append("No se encuentra en el plano el usuario: " + str(rs[0]))
                linea.append(str(rs[0]))
                linea.append(str(rs[1]))
                linea.append('Usuario')
                self.advertencias.append (linea)
        #analizo si hay una apertura y cierre a la misma hora
        cursor = cnn.cursor()
        cursor.execute("SELECT nombre, fechahora, ISNULL(tipo_elemento, 'Elem_ManiobraMT') AS tipo_elemento, Count(tipo) AS cant, Min(id) FROM Importo_Operaciones WHERE incorporada=0 AND nombre<>''" + str_sql + " GROUP BY nombre, fechahora, tipo_elemento HAVING Count(tipo)>1")
        rst = tuple(cursor)
        cursor.close()
        for rs in rst:
            b_existe=False
            for j in range(0, len(self.advertencias)):
                if rs[0]==self.advertencias[j][2]:
                    b_existe=True
                    break
            if b_existe==False:
                linea=[]
                linea.append("Advertencia")
                linea.append("El elemento " + rs[2] + ": " + rs[0] + " tiene cargados " + str(rs[3]) + " eventos para un mismo instante: " + str(rs[1]))
                linea.append(rs[0])
                linea.append(str(rs[4]))
                linea.append('Elem_Maniobra')
                self.advertencias.append (linea)
        #analizo si hay una apertura y cierre a la misma hora
        cursor = cnn.cursor()
        cursor.execute("SELECT nombre, count(*), SUM(tipo), Min(id) FROM Importo_Operaciones WHERE incorporada=0 AND tipo_elemento = 'Usuario'" + str_sql + " GROUP BY nombre HAVING count(*)/2<> -1*SUM(tipo)")
        rst = tuple(cursor)
        cursor.close()
        for rs in rst:
            b_existe=False
            for j in range(0, len(self.advertencias)):
                if rs[0]==self.advertencias[j][2]:
                    b_existe=True
                    break
            if b_existe==False:
                linea=[]
                linea.append("Advertencia")
                linea.append("El usuario " + str(rs[0]) + " tiene eventos faltantes")
                linea.append(str(rs[0]))
                linea.append(str(rs[3]))
                linea.append('Usuario')
                self.advertencias.append (linea)
        #analizo aperturas y cierres
        tmin = 10000
        tmax = 0
        cursor = cnn.cursor()
        cursor.execute("SELECT nombre, tipo, CONVERT(CHAR(19),fechahora,121) as fecha, ISNULL(tipo_elemento, 'Elem_ManiobraMT') AS tipo_elemento, id FROM Importo_Operaciones WHERE incorporada=0 AND tipo_elemento<>'Usuario'" + str_sql + " ORDER BY nombre, fechahora")
        rst = tuple(cursor)
        cursor.close()
        nombre = ""
        estado = ""
        amin = ""
        amax = ""
        for rs in rst:
            if rs[0] == nombre: #es el mismo aparato
                if rs[1] == estado: #se repite
                    if estado == -1:
                        b_existe=False
                        for j in range(0, len(self.advertencias)):
                            if rs[0]==self.advertencias[j][2]:
                                b_existe=True
                                break
                        if b_existe==False:
                            linea=[]
                            linea.append("Advertencia")
                            linea.append("El aparato: " + rs[0] + " tiene 2 aperturas seguidas - " + rs[2])
                            linea.append(rs[0])
                            linea.append(str(rs[4]))
                            linea.append('Elem_Maniobra')
                            self.advertencias.append (linea)
                    else:
                        b_existe=False
                        for j in range(0, len(self.advertencias)):
                            if rs[0]==self.advertencias[j][2]:
                                b_existe=True
                                break
                        if b_existe==False:
                            linea=[]
                            linea.append("Advertencia")
                            linea.append("El aparato: " + rs[0] + " tiene 2 cierres seguidos - " + rs[2])
                            linea.append(rs[0])
                            linea.append(str(rs[4]))
                            linea.append('Elem_Maniobra')
                            self.advertencias.append (linea)
                            try:
                                cursor = cnn.cursor()
                                cursor.execute("SELECT nombre,cierre,causa,id_reclamo,apertura FROM VW_GISCIERRESRECLAMOS WHERE nombre='" + rs[0] + "' AND cierre = '" + rs[2].replace("-", "") + "' ORDER BY cierre")
                                rst2 = tuple(cursor)
                                cursor.close()
                                if len(rst2) > 0:
                                    QMessageBox.warning(self, "EnerGis 6", "❌ El aparato: " + rs[0] + " tiene 2 cierres seguidos - " + rs[2])
                                    reply = QMessageBox.question(self, "EnerGis 6", "Desea cargar la apertura a la fecha y hora del reclamo ❓", QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
                                    if reply == QMessageBox.StandardButton.Yes:
                                        str_valores = "'" + rst[0][0] + "',"
                                        str_valores = str_valores + "-1,"
                                        str_valores = str_valores + "'" + rst2[0][4] + "',"
                                        str_valores = str_valores + rst[0][2] + ","
                                        str_valores = str_valores + str(rst[0][3]) + ","
                                        str_valores = str_valores + "'" + rst[0][4] + "',"
                                        str_valores = str_valores + "'" + rst[0][5] + "',"
                                        str_valores = str_valores + "'ape.aut.',"
                                        str_valores = str_valores + rst[0][5] + "',"
                                        str_valores = str_valores + rst[0][6] + "',"
                                        str_valores = str_valores + rst[0][7] + "',"
                                        str_valores = str_valores + rst[0][8] + "',"
                                        str_valores = str_valores + "0,"
                                        str_valores = str_valores + "99" + "," #codigo_usuario
                                        str_valores = str_valores + "0"
                                        cursor = cnn.cursor()
                                        try:
                                            cursor.execute("INSERT INTO Importo_Operaciones (nombre,tipo,fechahora,causa,contingencia,responsable,est_tiempo,observaciones,elemento_falla,zona_falla,tipo_zona_falla,tipo_elemento,incorporada,usuario,validada) VALUES (" + str_valores + ")")
                                            cnn.commit()
                                        except:
                                            cnn.rollback()
                                            QMessageBox.warning(self, "EnerGis 6", "❌ No se pudieron insertar Contingencias !")
                            except:
                                pass
            else: #es un nuevo aparato
                #me fijo si empieza con apertura o cierre
                estado_inicial = rs[1]
                if rs[3] == "Elem_ManiobraBT" or rs[3] == "Elem_ManiobraMT":
                    cursor = cnn.cursor()
                    cursor.execute("SELECT elmt, estado FROM nodos WHERE Nodos.Tension>0 AND nombre='" + rs[0] + "'")
                    rst2 = tuple(cursor)
                    cursor.close()
                    for rs2 in rst2:
                        if estado_inicial == 0 and rs2[0] == 2:
                            b_existe=False
                            for j in range(0, len(self.advertencias)):
                                if rs[0]==self.advertencias[j][2]:
                                    b_existe=True
                                    break
                            if b_existe==False:
                                linea=[]
                                linea.append("Advertencia")
                                linea.append("La maniobra para el aparato NC " + rs[0] + ", comienza con un cierre. El " + str(rs[1]))
                                linea.append(rs[0])
                                linea.append(str(rs[4]))
                                linea.append('Elem_Maniobra')
                                self.advertencias.append (linea)
                        if estado_inicial == -1 and rs2[0] == 3:
                            b_existe=False
                            for j in range(0, len(self.advertencias)):
                                if rs[0]==self.advertencias[j][2]:
                                    b_existe=True
                                    break
                            if b_existe==False:
                                linea=[]
                                linea.append("Advertencia")
                                linea.append("La maniobra para el aparato NA " + rs[0] + ", comienza con una apertura. El " + str(rs[1]))
                                linea.append(rs[0])
                                linea.append(str(rs[4]))
                                linea.append('Elem_Maniobra')
                                self.advertencias.append (linea)
                if rs[3] == "Transformador" or (rs[3] == "Elem_ManiobraMT" and rs[0][:2] == "ST"):
                    if estado_inicial == 0:
                        b_existe=False
                        for j in range(0, len(self.advertencias)):
                            if rs[0]==self.advertencias[j][2]:
                                b_existe=True
                                break
                        if b_existe==False:
                            linea=[]
                            linea.append("Advertencia")
                            linea.append("La maniobra para el Ct " + rs[0] + ", comienza con un cierre. El " + str(rs[1]))
                            linea.append(rs[0])
                            linea.append(str(rs[4]))
                            linea.append('Elem_Maniobra')
                            self.advertencias.append (linea)
            nombre = rs[0]
            estado = rs[1]
            if estado == estado_inicial:
                tini = datetime.strptime(rs[2], "%Y-%m-%d %H:%M:%S")
            else:
                tfin = datetime.strptime(rs[2], "%Y-%m-%d %H:%M:%S")
                if tini == tfin:
                    linea=[]
                    linea.append("Error")
                    linea.append("Elemento: " + rs[0] + ". El cierre y la apertura se suceden al mismo instante: " + str(tini))
                    b_existe=False
                    for j in range(0, len(self.advertencias)):
                        if rs[0]==self.advertencias[j][2]:
                            b_existe=True
                            break
                    if b_existe==False:
                        linea.append(rs[0])
                        linea.append(str(rs[4]))
                        linea.append('Elem_Maniobra')
                        self.advertencias.append (linea)
                else:
                    dt = (tfin - tini).seconds / 3600
                    if dt < tmin:
                        tmin = dt
                        amin = rs[3] + " " + rs[0]
                    if dt > tmax:
                        tmax = dt
                        amax = rs[3] + " " + rs[0]
        cursor = cnn.cursor()
        cursor.execute("SELECT Importo_Operaciones.nombre, Importo_Operaciones.fechahora, id FROM (Importo_Operaciones INNER JOIN (SELECT nombre, MIN(fechahora) AS fecha FROM Importo_Operaciones AS Importo_Operaciones_1 GROUP BY nombre) AS A ON (Importo_Operaciones.fechahora = A.fecha) AND (Importo_Operaciones.nombre = A.nombre)) INNER JOIN Nodos ON A.nombre = Nodos.Nombre WHERE incorporada=0 AND tipo_elemento<>'Usuario'" + str_sql + " AND ((Importo_Operaciones.tipo = - 1 AND Nodos.Elmt = 3) OR (Importo_Operaciones.tipo = 0 AND Nodos.Elmt = 2))")
        rst = tuple(cursor)
        cursor.close()
        for rs in rst:
            b_existe=False
            for j in range(0, len(self.advertencias)):
                if rs[0]==self.advertencias[j][2]:
                    b_existe=True
                    break
            if b_existe==False:
                linea=[]
                linea.append("Advertencia")
                linea.append("No coincide el estado normal del seccionador " + rs[0] + " con la maniobra. El " + str(rs[1]))
                linea.append(rs[0])
                linea.append(str(rs[2]))
                linea.append('Elem_Maniobra')
                self.advertencias.append (linea)
        #analizo cambios de configuración
        cursor = cnn.cursor()
        cursor.execute("SELECT nombre, MAX(Importo_Operaciones.fechahora) AS fecha, MIN(id) AS id FROM Importo_Operaciones WHERE incorporada = 0 AND tipo_elemento <> 'Usuario'" + str_sql + " GROUP BY nombre HAVING COUNT(id) % 2 = 1")
        rst = tuple(cursor)
        cursor.close()
        for rs in rst:
            linea=[]
            linea.append("Advertencia")
            linea.append("El aparato: " + rs[0] + " cambió de configuración en el período")
            linea.append(rs[0])
            linea.append(str(rs[2]))
            linea.append('Elem_Maniobra')
            self.advertencias.append (linea)
        #analizo entrada y salida de usuarios
        cursor = cnn.cursor()
        cursor.execute("SELECT nombre, tipo, CONVERT(CHAR(19),fechahora,121), ISNULL(tipo_elemento, 'Elem_ManiobraMT') AS tipo_elemento, id FROM Importo_Operaciones WHERE incorporada=0 AND tipo_elemento='Usuario'" + str_sql + " ORDER BY nombre, fechahora")
        rst = tuple(cursor)
        cursor.close()
        for rs in rst:
            if rs[0] == nombre: #es el mismo usuario
                if estado == rs[1]: #se repite
                    if estado == -1:
                        QMessageBox.warning(self, "EnerGis 6", "❌ El usuario: " + rs[0] + " tiene 2 salidas seguidas - " + rs[2])
                    else:
                        QMessageBox.warning(self, "EnerGis 6", "❌ El usuario: " + rs[0] + " tiene 2 entradas seguidas - " + rs[2])
                        cursor = cnn.cursor()
                        cursor.execute("SELECT nombre, apertura, causa, contingencia, responsable, elemento_falla, est_tiempo, zona_falla, tipo_zona_falla, ISNULL(tipo_elemento, 'Elem_ManiobraMT') AS tipo_elemento FROM VW_GISCIERRESRECLAMOS WHERE tipo_elemento='Usuario' AND nombre='" + rs[0] + "' AND cierre = '" + rs[2].replace("-", "") + "' ORDER BY cierre")
                        rst2 = tuple(cursor)
                        cursor.close()
                        if len(rst2) > 0:
                            reply = QMessageBox.question(self, "EnerGis 6", "Desea cargar la apertura a la fecha y hora del reclamo ❓", QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
                            if reply == QMessageBox.StandardButton.Yes:
                                str_valores = "'" + rst2[0][0] + "',"
                                str_valores = str_valores + "-1,"
                                str_valores = str_valores + "'" + rst2[0][1] + "',"
                                str_valores = str_valores + rst2[0][2] + ","
                                str_valores = str_valores + str(rst2[0][3]) + ","
                                str_valores = str_valores + "'" + rst2[0][4] + "',"
                                str_valores = str_valores + "'" + rst2[0][5] + "',"
                                str_valores = str_valores + "'ape.aut.',"
                                str_valores = str_valores + rst2[0][5] + "',"
                                str_valores = str_valores + rst2[0][6] + "',"
                                str_valores = str_valores + rst2[0][7] + "',"
                                str_valores = str_valores + rst2[0][8] + "',"
                                str_valores = str_valores + "0,"
                                str_valores = str_valores + "99" + "," #codigo_usuario
                                str_valores = str_valores + "0"
                                cursor = cnn.cursor()
                                try:
                                    cursor.execute("INSERT INTO Importo_Operaciones (nombre,tipo,fechahora,causa,contingencia,responsable,est_tiempo,observaciones,elemento_falla,zona_falla,tipo_zona_falla,tipo_elemento,incorporada,usuario,validada) VALUES (" + str_valores + ")")
                                    cnn.commit()
                                except:
                                    cnn.rollback()
                                    QMessageBox.warning(self, "EnerGis 6", "❌ No se pudieron insertar Contingencias !")
                    return
            else: #es un nuevo usuario
                #me fijo si empieza con apertura o cierre
                estado_inicial = rs[1]
                if estado_inicial == 0:
                    b_existe=False
                    for j in range(0, len(self.advertencias)):
                        if rs[0]==self.advertencias[j][2]:
                            b_existe=True
                            break
                    if b_existe==False:
                        linea=[]
                        linea.append("Advertencia")
                        linea.append("Para el usuario: " + str(rs[0]) + " la maniobra comienza con un cierre. El " + rs[2])
                        linea.append(str(rs[0]))
                        linea.append(str(rs[4]))
                        linea.append('Usuario')
                        self.advertencias.append (linea)
            nombre = rs[0]
            estado = rs[1]
            if estado == estado_inicial:
                tini = datetime.strptime(rs[2], "%Y-%m-%d %H:%M:%S")
            else:
                tfin = datetime.strptime(rs[2], "%Y-%m-%d %H:%M:%S")
                dt = (tfin - tini).seconds / 3600
                if dt < tmin:
                    tmin = dt
                    amin = rs[3] + " " + rs[0]
                if dt > tmax:
                    tmax = dt
                    amax = rs[3] + " " + rs[0]
        if len(self.advertencias)> 0:
            encabezado = ["Tipo", "Descripción", "Elemento", "Evento","Tipo Elemento"]
            from .frm_lista import frmLista
            self.dialogo = frmLista(self.mapCanvas, encabezado, self.advertencias)
            self.dialogo.setWindowTitle("Resultados Verificación")
            self.dialogo.resize(900,self.dialogo.height())
            self.dialogo.show()
            self.buscar()
            return
        if tmax>0:
            QMessageBox.information(self, "EnerGis 6", "ℹ️ El mayor tiempo de interrupción es de " + str(format(tmax, ".2f")) + " hs. (" + amax + ") y el mínimo es de " + str(format(tmin, ".2f")) + " hs. (" + amin + ")")
        QMessageBox.information(self, "EnerGis 6", "ℹ️ Contingencias cargadas correctamente !")

    def importar(self):
        cnn = self.conn
        ult_rec = 0
        #try:
        str_sql = "SELECT orden_atencion, id_reclamo, nombre, tipo, causa, fechahora, responsable, est_tiempo, observaciones, elemento_falla, zona_falla, tipo_zona_falla, ISNULL(tipo_elemento, 'Elem_ManiobraMT') AS tipo_elemento FROM VW_GISCONTINGENCIAS ORDER BY nombre, fechahora"
        cursor = cnn.cursor()
        cursor.execute(str_sql)
        rst = tuple(cursor)
        cursor.close()
        for rs in rst:
            if rs[0] == 0:
                ultimo_reclamo = rs[1]
            else:
                ultimo_reclamo = rs[0]
            if ultimo_reclamo != ult_rec:
                cnn = self.conn
                cursor = cnn.cursor()
                cursor.execute("SELECT ult_cont FROM log_ope")
                ult_cont = tuple(cursor)
                cursor.close()
                self.ult_contingencia = ult_cont[0][0] + 1
                cnn = self.conn
                cnn.autocommit = False
                cursor = cnn.cursor()
                cursor.execute("UPDATE log_ope SET ult_cont =" + str(self.ult_contingencia))
                cnn.commit()
                ult_rec = ultimo_reclamo
            str_valores = "'" + str(rs[2]).replace(" ","") + "'"
            str_valores = str_valores + "," + str(rs[3])
            str_valores = str_valores + ",'" + str(rs[5]).replace(":00.000","") + "'"
            str_valores = str_valores + "," + str(rs[4])
            str_valores = str_valores + "," + str(self.ult_contingencia)
            str_valores = str_valores + ",'" + rs[6] + "'"
            str_valores = str_valores + ",'" + rs[7] + "'"
            str_valores = str_valores + ",'" + str(rs[8]) + "'"
            str_valores = str_valores + "," + str(rs[9])
            str_valores = str_valores + ",'" + rs[10] + "'"
            str_valores = str_valores + ",'" + rs[11] + "'"
            str_valores = str_valores + ",'" + rs[12] + "'"
            str_valores = str_valores + ",0"
            str_valores = str_valores + ",99"
            str_valores = str_valores + ",1"
            cursor = cnn.cursor()
            try:
                str_sql = "INSERT INTO Importo_Operaciones (nombre,tipo,fechahora,causa,contingencia,responsable,est_tiempo,observaciones,elemento_falla,zona_falla,tipo_zona_falla,tipo_elemento,incorporada,usuario,validada) VALUES (" + str_valores + ")"
                cursor.execute(str_sql)
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(self, "EnerGis 6", "❌ No se pudieron insertar Contingencias !")
        if rs[0] == 0:
            cursor = cnn.cursor()
            try:
                str_sql = "INSERT INTO Reclamos_Contingencias (id_contingencia,id_reclamo) VALUES (" + str(self.ult_contingencia) + "," + str(rs[1]) + ")"
                cursor.execute(str_sql)
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(self, "EnerGis 6", "❌ No se pudieron insertar Reclamos !")
        else:
            cursor = cnn.cursor()
            try:
                str_sql = "INSERT INTO Reclamos_Contingencias SELECT " + self.ult_contingencia + " AS id_contingencia,id AS id_reclamo FROM VW_GISRECLAMOS INNER JOIN VW_GISCONTINGENCIAS ON VW_GISRECLAMOS.orden_atencion = VW_GISCONTINGENCIAS.orden_atencion WHERE VW_GISRECLAMOS.orden_atencion <> 0 AND VW_GISCONTINGENCIAS.orden_atencion = " + str(rs[0])
                cursor.execute(str_sql)
                cnn.commit()
            except:
                cnn.rollback()
                QMessageBox.warning(self, "EnerGis 6", "❌ No se pudieron insertar Reclamos ! " + str_sql)
        self.lblContingencia.setText(str(self.ult_contingencia))
        #except:
        #    pass

    def reclamos(self):
        contingencia = int(self.lblContingencia.text())
        from .frm_contingencias_reclamos import frmContingenciasReclamos
        self.dialogo = frmContingenciasReclamos(self.tipo_usuario, self.conn, contingencia)
        self.dialogo.show()

    def nueva_contingencia(self):
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT ult_cont FROM log_ope")
        ult_cont = tuple(cursor)
        cursor.close()
        self.ult_contingencia = ult_cont[0][0] + 1
        self.id_contingencia = self.ult_contingencia
        self.lblContingencia.setText(str(self.id_contingencia))
        self.bloquear_controles(True)
        self.cmdEditar.setEnabled(False)
        self.cmdBorrar.setEnabled(False)
        self.cmdGrabar.setEnabled(True)
        self.cmdCancelar.setEnabled(True)
        self.trvContingencias.setEnabled(False)

    def nuevo_evento(self):
        self.lblEvento.setText("<Automatico>")
        self.bloquear_controles(True)
        self.cmdEditar.setEnabled(False)
        self.cmdBorrar.setEnabled(False)
        self.cmdGrabar.setEnabled(True)
        self.cmdCancelar.setEnabled(True)
        self.trvContingencias.setEnabled(False)

    def editar(self):
        self.bloquear_controles(True)
        self.cmdEditar.setEnabled(False)
        self.cmdGrabar.setEnabled(True)
        self.cmdBorrar.setEnabled(False)
        self.cmdCancelar.setEnabled(True)
        self.trvContingencias.setEnabled(False)
        #if self.seleccionado!=-1:
        #    self.tblLista.selectRow(self.seleccionado)

    def elemento(self):
        cnn = self.conn
        if self.cmbTipo.currentText() == "Usuario":
            cursor = cnn.cursor()
            cursor.execute("SELECT id_usuario FROM Usuarios WHERE id_usuario='" + self.txtNombre.text() + "'")
            rst = tuple(cursor)
            cursor.close()
            if len(rst)==0:
                QMessageBox.critical(self, "EnerGis 6", "❌ No se encontró el usuario")
                return
            self.txtNombre.setText(str(rst[0][0]).strip())
            if self.cmbTipoOperacion.currentText()=="Apertura":
                self.cmbTipoOperacion.setCurrentText("Cierre")
            else:
                self.cmbTipoOperacion.setCurrentText("Apertura")
        elif self.cmbTipo.currentText() == "Aparato Maniobra BT":
            cursor = cnn.cursor()
            cursor.execute("SELECT Nombre FROM Nodos WHERE (elmt = 2 or elmt = 3) AND tension <= 1000 AND nombre='" + self.txtNombre.text() + "'")
            rst = tuple(cursor)
            cursor.close()
            if len(rst)==0:
                QMessageBox.critical(self, "EnerGis 6", "❌ No se encontró el seccionamiento de baja tensión")
                return
            self.txtNombre.setText(str(rst[0][0]).strip())
            if self.cmbTipoOperacion.currentText()=="Apertura":
                self.cmbTipoOperacion.setCurrentText("Cierre")
            else:
                self.cmbTipoOperacion.setCurrentText("Apertura")
        else:
            cursor = cnn.cursor()
            cursor.execute("SELECT Nombre FROM Nodos WHERE (elmt = 2 or elmt = 3) AND nombre='" + self.txtNombre.text() + "'")
            rst = tuple(cursor)
            cursor.close()
            if len(rst)==0:
                QMessageBox.critical(self, "EnerGis 6", "❌ No se encontró el elemento")
                return
            self.txtNombre.setText(str(rst[0][0]).strip())
            if self.cmbTipoOperacion.currentText()=="Apertura":
                self.cmbTipoOperacion.setCurrentText("Cierre")
            else:
                self.cmbTipoOperacion.setCurrentText("Apertura")
        self.setear_elemento_falla()

    def borrar(self):
        item = self.trvContingencias.currentItem()
        if item==None:
            return
        if str(item.text(1)) == '': #no es un evento
            if self.cmbListar.currentText()=="Contingencia":
                padre = item.parent()
                if padre: #aparato
                    self.lblEvento.setText("<Automatico>")
                else:
                    if self.lblEvento.text()=="<Automatico>":
                        reply = QMessageBox.question(self, "EnerGis 6", "Desea borrar la contingencia " + str(self.lblContingencia.text()) + " ❓", QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
                        if reply == QMessageBox.StandardButton.No:
                            return
                        cnn = self.conn
                        cursor = cnn.cursor()
                        try:
                            cursor.execute("DELETE FROM Importo_Operaciones WHERE contingencia=" + str(self.lblContingencia.text()))
                            cnn.commit()
                            QMessageBox.information(self, "EnerGis 6", "ℹ️ Borrado !")
                            self.listar(None)
                        except:
                            cnn.rollback()
                        QMessageBox.warning(self, "EnerGis 6", "❌ No se pudo Borrar !")
        else:
            if self.lblEvento.text()!="<Automatico>":
                reply = QMessageBox.question(self, "EnerGis 6", "Desea borrar el evento " + str(self.lblEvento.text()) + " ❓", QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.No:
                    return
                cnn = self.conn
                cursor = cnn.cursor()
                try:
                    cursor.execute("DELETE FROM Importo_Operaciones WHERE id=" + str(self.lblEvento.text()))
                    cnn.commit()
                    QMessageBox.information(self, "EnerGis 6", "ℹ️ Borrado !")
                    self.listar(None)
                except:
                    cnn.rollback()
                    QMessageBox.warning(self, "EnerGis 6", "❌ No se pudo Borrar !")

    def cancelar(self):
        self.bloquear_controles(False)
        self.cmdEditar.setEnabled(False)
        self.cmdBorrar.setEnabled(False)
        self.cmdGrabar.setEnabled(False)
        self.trvContingencias.setEnabled(True)
        #if self.seleccionado!=-1:
        #    self.tblLista.selectRow(self.seleccionado)
        self.lblEvento.setText("<Automatico>")

    def grabar(self):
        cnn = self.conn
        reply = QMessageBox.question(self, "EnerGis 6", "Desea grabar ❓", QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
                return
        self.id_contingencia = self.lblContingencia.text()
        if self.cmbTipo.currentText() == "Aparato Maniobra MT":
            tipo_elemento = "Elem_ManiobraMT"
        if self.cmbTipo.currentText() == "Centro Transformación":
            tipo_elemento = "Transformador"
        if self.cmbTipo.currentText() == "Aparato Maniobra BT":
            tipo_elemento = "Elem_ManiobraBT"
        if self.cmbTipo.currentText() == "Usuario":
            tipo_elemento = "Usuario"
        if self.txtNombre.text() == "":
            QMessageBox.critical(self, "EnerGis 6", "❌ Falta el código del " + self.cmbTipo.currentText())
            return
        if self.cmbCausa.currentText() == "":
            QMessageBox.critical(self, "EnerGis 6", "❌ Causa erronea")
            return
        if self.txtResponsable.text() == "":
            QMessageBox.critical(self, "EnerGis 6", "❌ Responsable erroneo")
            return
        if self.cmbTiempo.currentText() == "":
            QMessageBox.critical(self, "EnerGis 6", "❌ Falta estado del Tiempo")
            return
        if self.txtObservaciones.toPlainText() == "":
            self.txtObservaciones.setText("<SD>")
        self.txtObservaciones.setText(self.txtObservaciones.toPlainText().replace(chr(9)," "))
        self.txtObservaciones.setText(self.txtObservaciones.toPlainText().replace(chr(10)," "))
        self.txtObservaciones.setText(self.txtObservaciones.toPlainText().replace(chr(13)," "))
        zona_falla = self.cmbZona.currentText()[:1]
        tipo_zona_falla = self.cmbTipoZona.currentText()[:1]
        if self.cmbTipoInstalacion.currentText() == "":
            QMessageBox.warning(self, "EnerGis 6", "❌ Debe escoger una instalación !")
            return
        for i in range (0, len(self.tipo_instalacion)):
            if self.cmbTipoInstalacion.currentText()==self.tipo_instalacion[i][1]:
                elemento_falla=str(self.tipo_instalacion[i][0])[:3]
        if self.cmbTipoOperacion.currentText()=="Apertura":
            tipo_operacion = -1
        else:
            tipo_operacion = 0
        fechahora = str(self.datFecha.date().toPyDate()).replace("-","") + " " + str(self.timHora.time().toPyTime())
        for i in range (0, len(self.causas)):
            if self.cmbCausa.currentText()==self.causas[i][2]:
                causa = self.causas[i][0]
        cursor = cnn.cursor()
        if self.lblEvento.text()=="<Automatico>":
            try:
                cursor.execute("INSERT INTO Importo_Operaciones (nombre,tipo,fechahora,causa,contingencia,responsable,est_tiempo,observaciones,elemento_falla,tipo_elemento,zona_falla,tipo_zona_falla,incorporada,usuario,validada) VALUES ('" + self.txtNombre.text() + "'," + str(tipo_operacion) + ",'" + fechahora + "'," +  str(causa) + "," + str(self.id_contingencia) + ",'" + self.txtResponsable.text() + "','" + self.cmbTiempo.currentText() + "','" + self.txtObservaciones.toPlainText() + "'," + str(elemento_falla) + ",'" + tipo_elemento + "','" + zona_falla + "','" + tipo_zona_falla + "',0," + "99" + ",0)")
                cnn.commit()
                QMessageBox.information(self, "EnerGis 6", "ℹ️ Grabado !")
            except:
                cnn.rollback()
                QMessageBox.warning(self, "EnerGis 6", "❌ No se pudo insertar en la Base de Datos !")
                return
        else:
            try:
                cursor.execute("UPDATE Importo_Operaciones SET nombre='" + self.txtNombre.text() + "',tipo=" + str(tipo_operacion) + ",fechahora='" + fechahora + "',causa=" +  str(causa) + ",contingencia=" + str(self.id_contingencia) + ",responsable='" + self.txtResponsable.text() + "',est_tiempo='" + self.cmbTiempo.currentText() + "',observaciones='" + self.txtObservaciones.toPlainText() + "',elemento_falla=" + str(elemento_falla) + ",tipo_elemento='" + tipo_elemento + "',zona_falla='" + zona_falla + "',tipo_zona_falla = '" + tipo_zona_falla + "' WHERE id=" + self.lblEvento.text())
                cnn.commit()
                QMessageBox.information(self, "EnerGis 6", "ℹ️ Grabado !")
            except:
                cnn.rollback()
                QMessageBox.warning(self, "EnerGis 6", "❌ No se pudo grabar en la Base de Datos !")
                return
        cursor.execute("UPDATE log_ope SET ult_cont=" + str(self.ult_contingencia))
        cnn.commit()
        self.cancelar()
        self.listar(None)
        #if self.seleccionado!=-1:
        #    self.tblLista.selectRow(self.seleccionado)

    def salir(self):
        self.close()

    def registrar(self):
        reply = QMessageBox.question(self, "EnerGis 6", "Desea registrar las contingencias ❓", QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        from .frm_elegir_fechas import frmElegirFechas
        dialogo = frmElegirFechas()
        dialogo.exec()
        self.fecha_desde = dialogo.fecha_desde
        self.fecha_hasta = dialogo.fecha_hasta
        str_sql=''
        if self.fecha_desde!=None:
            str_sql = str_sql + " AND fechahora>='" + str(self.fecha_desde)[:19].replace('-','') + "'"
        if self.fecha_hasta!=None:
            str_sql = str_sql + " AND fechahora<='" + str(self.fecha_hasta)[:19].replace('-','') + "'"
        cursor = self.conn.cursor()
        cursor.execute("UPDATE nodos SET val4=REPLACE(val4, '0,','')")
        cursor.execute("UPDATE nodos SET val4=0 WHERE elmt=4 AND (val4='' OR val4 IS null)")
        cursor.execute("UPDATE nodos SET val1=0 WHERE elmt=4 AND (val1='' OR val1 IS null)")
        cursor.execute("UPDATE Importo_Operaciones SET tipo_elemento='Elem_ManiobraMT' WHERE tipo_elemento='Transformador'")
        cursor.commit()
        cursor = self.conn.cursor()
        cursor.execute("SELECT id,nombre,tipo,fechahora,causa,contingencia,responsable,est_tiempo,observaciones,elemento_falla,ISNULL(tipo_elemento, 'Elem_ManiobraMT') AS tipo_elemento, ISNULL(zona_falla,'A'),ISNULL(tipo_zona_falla,'R') FROM Importo_Operaciones WHERE incorporada=0" + str_sql + " ORDER BY fechahora")
        contingencias = cursor.fetchall()
        cursor.close()
        if len(contingencias)==0:
            QMessageBox.critical(self, "EnerGis 6", "❌ No hay datos para procesar")
            return

        f = open('c:/gis/energis6/log_operaciones.txt','a')
        f.writelines('-------------------------------------' + '\n')
        f.close()
        #----------------------------------------------------------------------------
        progress = QProgressDialog("Procesando...", "Cancelar", 0, 100, self)
        progress.setWindowTitle("Progreso")
        progress.setWindowModality(True)  # Hace que la ventana de progreso sea modal
        progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
        progress.setValue(0)  # Inicia el progreso en 0
        #----------------------------------------------------------------------------
        for n in range (0, len(contingencias)):
            #----------------------------------------------------------------------------
            # Actualiza el progreso
            progress.setValue(int((n / len(contingencias)) * 100))
            if progress.wasCanceled():
                break
            # Permitir que la GUI se actualice (similar a DoEvents)
            QApplication.processEvents()
            #----------------------------------------------------------------------------
            id = contingencias[n][0]
            nombre = contingencias[n][1]
            tipo = contingencias[n][2]
            fechahora = contingencias[n][3]
            causa = contingencias[n][4]
            contingencia = contingencias[n][5]
            responsable = contingencias[n][6]
            est_tiempo = contingencias[n][7]
            observaciones = contingencias[n][8]
            elemento_falla = contingencias[n][9]
            tipo_elemento = contingencias[n][10]
            #zona_falla = contingencias[n][11]
            #tipo_zona_falla = contingencias[n][12]
            #-------------------------------------------------------------------------------------
            # Incorporo Movimientos
            #-------------------------------------------------------------------------------------
            cursor = self.conn.cursor()
            cursor.execute("SELECT Id_usuario, Id_Suministro, Tarifa, Tipo_Mov FROM Movimientos WHERE incorp=0 AND fecha_hora<" + fechahora.strftime('%Y-%m-%d').replace("'","") + " ORDER BY fecha_hora, movimientos.tipo_mov DESC")
            movimientos = cursor.fetchall()
            cursor.close()
            for m in range (0, len(movimientos)):
                if movimientos[m][3]=='A': #Alta
                    cursor = self.conn.cursor()
                    cursor.execute("UPDATE Usuarios SET Id_Suministro='" + movimientos[m][1] + "', ES=1, Tarifa='" + movimientos[m][2] + "' WHERE Id_Usuario='" + movimientos[m][0] + "'")
                    self.conn.commit()
                elif movimientos[m][3]=='B': #Baja
                    cursor = self.conn.cursor()
                    cursor.execute("UPDATE Usuarios SET ES=0 WHERE Id_Usuario='" + movimientos[m][0] + "'")
                    self.conn.commit()
            #-------------------------------------------------------------------------------------
            if tipo_elemento=="Elem_ManiobraMT":
                fase="RST"
                tipo_corte="T"
                cursor = self.conn.cursor()
                cursor.execute("SELECT geoname, aux FROM Nodos WHERE elmt IN (2,3) AND nombre='" + nombre + "'")
                nodo = cursor.fetchall()
                cursor.close()
                if len(nodo)==0:
                    pass
                else:
                    geoname = nodo[0][0]
                    aux = nodo[0][1]
                    cursor = self.conn.cursor()
                    cursor.execute("SELECT ISNULL(Codigo, 402) AS cod_elemento FROM Nodos LEFT JOIN Elementos_Maniobra ON Nodos.Val1 COLLATE SQL_Latin1_General_CP1_CI_AS = Elementos_Maniobra.Descripcion COLLATE SQL_Latin1_General_CP1_CI_AS WHERE Geoname=" + str(geoname))
                    elemento = cursor.fetchall()
                    cursor.close()
                    cod_elemento = elemento[0][0]
                    #try:
                    cursor = self.conn.cursor()
                    cursor.execute("SELECT ult_ope FROM log_ope")
                    log_ope = tuple(cursor)
                    cursor.close()
                    ult_ope = log_ope[0][0] + 1
                    #----------------------------------------------------------------------
                    #Operamos la Red

                    cursor = self.conn.cursor()
                    if tipo==-1:
                        nodos_afectados = self.afectados(aux)
                        if not nodos_afectados is None:
                            f = open('c:/gis/energis6/log_operaciones.txt','a')
                            f.writelines(str(fechahora) + '; Apertura de ' + nombre + '; Afecta a ' + str(len(nodos_afectados)) + ' suministros' + '\n')
                            f.close()
                            cursor.execute("UPDATE Nodos SET estado=3 WHERE geoname=" + str(geoname))
                            cursor.execute("UPDATE mNodos SET estado=3 WHERE geoname=" + str(geoname))
                            self.amnodos[aux,2]=3
                    else:
                        cursor.execute("UPDATE Nodos SET estado=2 WHERE geoname=" + str(geoname))
                        cursor.execute("UPDATE mNodos SET estado=2 WHERE geoname=" + str(geoname))
                        self.amnodos[aux,2]=2
                        nodos_afectados = self.afectados(aux)
                        if not nodos_afectados is None:
                            f = open('c:/gis/energis6/log_operaciones.txt','a')
                            f.writelines(str(fechahora) + '; Cierre de ' + nombre + '; Afecta a ' + str(len(nodos_afectados)) + ' suministros' + '\n')
                            f.close()
                    cursor.execute("TRUNCATE TABLE Nodos_Afectados")
                    #cursor.execute("TRUNCATE TABLE Lineas_Afectadas")
                    usuarios=[]
                    if nodos_afectados:
                        for m in range (0, len(nodos_afectados)):
                            str_sql = "INSERT INTO Nodos_Afectados (id_nodo) VALUES (" + str(nodos_afectados[m]) + ")"
                            cursor.execute("INSERT INTO Nodos_Afectados (id_nodo) VALUES (" + str(nodos_afectados[m]) + ")")
                        #for m in range (0, len(lineas_afectadas)):
                        #    cursor.execute("INSERT INTO Lineas_Afectadas (id_linea) VALUES (" + str(lineas_afectadas[m]) + ")")
                        rst = self.conn.cursor()
                        rst.execute("SELECT DISTINCT id_usuario,tarifa,ct,alimentador FROM Usuarios_Afectados")
                        usuarios = rst.fetchall()
                        rst.close()
                    #----------------------------------------------------------------------
                    #OPERACION
                    str_valores = str(ult_ope) + "," + str(tipo) + ",2," + str(geoname) + "," + str(causa) + ",'" + str(fechahora).replace("-","") + "','" + str(observaciones) + "'," + str(contingencia) + ",'" + tipo_corte + "','" + fase + "','" + nombre + "','" + str(est_tiempo) + "','" + str(responsable) + "'," + str(cod_elemento) + "," + str(elemento_falla)
                    cursor.execute("INSERT INTO Operaciones (id_operacion,tipo_operacion,tipo_el,elemento,causa,fecha_hora,observaciones,id_contingencia,tipo_corte,fase,desc_nodo,est_tiempo,jefe_guardia,cod_elemento,elemento_falla) VALUES (" + str_valores + ")")
                    #INTERRUPCION USUARIO
                    for u in range (0, len(usuarios)):
                        usuario = usuarios[u][0]
                        tarifa = usuarios[u][1].strip()
                        ct = usuarios[u][2]
                        alimentador = usuarios[u][3]
                        str_valores = "'" + str(usuario) + "','" + str(tarifa) + "'," + str(ult_ope) + "," + str(tipo) + ",'" + str(ct) + "','" + str(alimentador) + "'"
                        str_sql = "INSERT INTO Interrupciones (id_usuario,tarifa,id_operacion,tipo_operacion,ct,alimentador) VALUES (" + str_valores + ")"
                        cursor.execute("INSERT INTO Interrupciones (id_usuario,tarifa,id_operacion,tipo_operacion,ct,alimentador) VALUES (" + str_valores + ")")
                    cursor.execute("UPDATE log_ope SET ult_ope =" + str(ult_ope))
                    cursor.execute("UPDATE Importo_Operaciones SET incorporada=1 WHERE id=" + str(id))
                    self.conn.commit()
                    #except:
                    #    self.conn.rollback()
            if tipo_elemento=="Usuario":
                fase="RST"
                tipo_corte="T"
                cursor = self.conn.cursor() #AGREGAR FASE
                cursor.execute("SELECT Suministros.id_nodo AS geoname,Usuarios.tarifa, ISNULL(Nodos.Nombre, '<SD>') AS ct, ISNULL(Nodos.Alimentador, '<SD>') AS alimentador FROM Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro LEFT OUTER JOIN Nodos_Trafos ON Suministros.id_nodo = Nodos_Trafos.Geoname_n LEFT OUTER JOIN Nodos ON Nodos_Trafos.Geoname_t = Nodos.Geoname WHERE Usuarios.id_usuario=" + nombre)
                usuarios = cursor.fetchall()
                cursor.close()
                if len(usuarios)==0:
                    pass
                else:
                    usuario = nombre
                    geoname = usuarios[0][0]
                    tarifa = usuarios[0][1]
                    ct = usuarios[0][2]
                    alimentador = usuarios[0][3]
                    cod_elemento = 402
                    try:
                        #APERTURA
                        cursor = self.conn.cursor()
                        cursor.execute("SELECT ult_ope FROM log_ope")
                        log_ope = tuple(cursor)
                        cursor.close()
                        ult_ope = log_ope[0][0] + 1
                        #OPERACION
                        cursor = self.conn.cursor()
                        str_valores = str(ult_ope) + ",-1,6," + str(geoname) + "," + str(causa) + ",'" + str(fechahora).replace("-","") + "','" + str(observaciones) + "'," + str(contingencia) + ",'" + tipo_corte + "','" + fase + "','" + nombre + "','" + str(est_tiempo) + "','" + str(responsable) + "'," + str(cod_elemento) + "," + str(elemento_falla)
                        cursor.execute("INSERT INTO Operaciones (id_operacion,tipo_operacion,tipo_el,elemento,causa,fecha_hora,observaciones,id_contingencia,tipo_corte,fase,desc_nodo,est_tiempo,jefe_guardia,cod_elemento,elemento_falla) VALUES (" + str_valores + ")")
                        str_valores = "'" + str(usuario) + "','" + str(tarifa) + "'," + str(ult_ope) + ",-1,'" + str(ct) + "','" + str(alimentador) + "'"
                        cursor.execute("INSERT INTO Interrupciones (id_usuario,tarifa,id_operacion,tipo_operacion,ct,alimentador) VALUES (" + str_valores + ")")
                        #CIERRE
                        ult_ope = ult_ope + 1
                        #OPERACION
                        str_valores = str(ult_ope) + ",0,6," + str(geoname) + "," + str(causa) + ",'" + str(fechahora).replace("-","") + "','" + str(observaciones) + "'," + str(contingencia) + ",'" + tipo_corte + "','" + fase + "','" + nombre + "','" + str(est_tiempo) + "','" + str(responsable) + "'," + str(cod_elemento) + "," + str(elemento_falla) + '911'
                        cursor.execute("INSERT INTO Operaciones (id_operacion,tipo_operacion,tipo_el,elemento,causa,fecha_hora,observaciones,id_contingencia,tipo_corte,fase,desc_nodo,est_tiempo,jefe_guardia,cod_elemento,elemento_falla) VALUES (" + str_valores + ")")
                        str_valores = "'" + str(usuario) + "','" + str(tarifa) + "'," + str(ult_ope) + ",0,'" + str(ct) + "','" + str(alimentador) + "'"
                        cursor.execute("INSERT INTO Interrupciones (id_usuario,tarifa,id_operacion,tipo_operacion,ct,alimentador) VALUES (" + str_valores + ")")
                        #FINAL
                        cursor.execute("UPDATE log_ope SET ult_ope =" + str(ult_ope))
                        cursor.execute("UPDATE Importo_Operaciones SET incorporada=1 WHERE id=" + str(id))
                        self.conn.commit()
                    except:
                        QMessageBox.warning(self, "EnerGis 6", "❌ No se pudo cargar la Operacón del Usuario !")
                        self.conn.rollback()
        #----------------------------------------------------------------------------
        progress.setValue(100)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        QMessageBox.information(self, "EnerGis 6", "ℹ️ Operaciones Registradas !")
        self.buscar()

    def afectados(self, aux):
        import clr
        from System import Int64
        # Blanquear variables
        #----------------------------------------------------------------------------
        nodo=Int64(aux)
        if nodo==Int64(0):
            return
        #----------------------------------------------------------------------------
        for n in range(self.amnodos.GetLength(0)):
            self.amnodos[n,41] = 0
        for l in range(self.amlineas.GetLength(0)):
            self.amlineas[l,7] = 0
        #----------------------------------------------------------------------------
        # Cargar el ensamblado
        clr.AddReference(os.path.join(basepath, 'NavRed6.dll'))
        from EnerGis6.NavRed6 import NavRed
        #----------------------------------------------------------------------------
        # Instanciar la clase NavRed
        navred_instance = NavRed()
        #--------------------------------------------
        # Llamar a la función
        resultado = navred_instance.Navegar_a_los_extremos(self.amnodos,self.amlineas,nodo)
        if resultado[0]!="Ok":
            return []
        #--------------------------------------------
        self.suministros_afectados = []
        try:
            for m in range(self.amnodos.GetLength(0)):
                if self.amnodos.GetValue(m,41) == 1 and self.amnodos.GetValue(m,2) == 6 :
                    self.suministros_afectados.append(self.amnodos.GetValue(m,1))
        except:
            QMessageBox.critical(self, "EnerGis 6", "❌ Error al calcular suministros afectados !")
        return self.suministros_afectados
