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
from PyQt6.QtWidgets import QMessageBox, QTreeWidgetItem, QTableWidgetItem, QFileDialog
from PyQt6 import uic, QtCore
from dateutil.relativedelta import relativedelta

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_datos_seleccion.ui'))

class frmDatosSeleccion(DialogType, DialogBase):

    def __init__(self, id_usuario_sistema, tipo_usuario, mapCanvas, conn):
        super().__init__()
        self.setupUi(self)
        #self.setFixedSize(self.size())
        self.id_usuario_sistema = id_usuario_sistema
        self.tipo_usuario = tipo_usuario
        self.mapCanvas = mapCanvas
        self.conn = conn
        self.ftrs_nodos=[]
        self.ftrs_lineas=[]
        self.ftrs_postes=[]
        self.ftrs_parcelas=[]
        self.str_lista_nodos=""

        # 1. Preparación inicial
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.fast_executemany = True
        # Lista para acumular TODOS los registros antes de insertar
        datos_para_insertar = []
        # Diccionario de mapeo
        mapeo_capas = {
            'Nodos': (1, self.ftrs_nodos),
            'Lineas': (2, self.ftrs_lineas),
            'Postes': (3, self.ftrs_postes),
            'Parcelas': (4, self.ftrs_parcelas)
        }
        # 2. Recolección de datos
        layers = [self.mapCanvas.layer(i) for i in range(self.mapCanvas.layerCount())]
        for lyr in layers:
            nombre = lyr.name()
            # Identificamos el tipo de elemento según el nombre
            tipo_elemento = None
            lista_destino = None
            if nombre.startswith('Nodos'): tipo_elemento, lista_destino = mapeo_capas['Nodos']
            elif nombre.startswith('Lineas'): tipo_elemento, lista_destino = mapeo_capas['Lineas']
            elif nombre.startswith('Postes'): tipo_elemento, lista_destino = mapeo_capas['Postes']
            elif nombre == 'Parcelas': tipo_elemento, lista_destino = mapeo_capas['Parcelas']
            if tipo_elemento:
                for ftr in lyr.selectedFeatures():
                    fid = ftr.id()
                    lista_destino.append(fid) # Guardamos en tu lista local
                    # Guardamos la tupla para SQL: (id_usuario, tipo, geoname)
                    datos_para_insertar.append((self.id_usuario_sistema, tipo_elemento, fid))

        # 3. Ejecución masiva (Lógica SQL)
        if datos_para_insertar:
            try:
                # Borramos lo anterior
                cursor.execute("DELETE FROM Selecciones WHERE id_usuario_sistema = ?", (self.id_usuario_sistema,))
                # Insertamos todo de golpe
                query = "INSERT INTO Selecciones (id_usuario_sistema, elemento, geoname) VALUES (?, ?, ?)"
                cursor.executemany(query, datos_para_insertar)
                cnn.commit()
            except:
                cnn.rollback()

        self.treeWidget.clear()
        self.treeWidget.setColumnCount(2)
        self.treeWidget.setHeaderLabels(["Elemento", "Cant"])
        self.treeWidget.setColumnWidth(0, 250)
        self.treeWidget.setColumnWidth(1, 50)
        #self.treeWidget.setColumnAlignment(1, 1)
        if len(self.ftrs_nodos)>0:
            self.nodos = QTreeWidgetItem(["Nodos", str(len(self.ftrs_nodos))])
            self.treeWidget.addTopLevelItem(self.nodos)
        if len(self.ftrs_lineas)>0:
            self.lineas = QTreeWidgetItem(["Lineas", str(len(self.ftrs_lineas))])
            self.treeWidget.addTopLevelItem(self.lineas)
        if len(self.ftrs_postes)>0:
            self.postes = QTreeWidgetItem(["Postes", str(len(self.ftrs_postes))])
            self.treeWidget.addTopLevelItem(self.postes)
        if len(self.ftrs_parcelas)>0:
            self.parcelas = QTreeWidgetItem(["Parcelas", str(len(self.ftrs_parcelas))])
            self.treeWidget.addTopLevelItem(self.parcelas)
        cnn = self.conn
        #--------------- ANALISIS DE CARGA ---------------
        self.str_lista_nodos='0'
        for ftr in self.ftrs_nodos:
            self.str_lista_nodos=self.str_lista_nodos + ',' + str(ftr)
        cursor = cnn.cursor()
        cursor.execute("SELECT Sum(CAST((CASE Val1 WHEN NULL THEN '0' WHEN '' THEN '0' ELSE Val1 END) AS DECIMAL(8,2))) As kVA, Count(Nodos.Geoname) As Cant FROM Nodos WHERE Nodos.Elmt=4 AND Geoname IN (" + self.str_lista_nodos + ")")
        #convierto el cursor en array
        recordset = tuple(cursor)
        cursor.close()
        self.txtTransformadores.setText(str(recordset[0][1]))
        self.txtPotenciaInstalada.setText(str(recordset[0][0]))
        cursor = cnn.cursor()
        cursor.execute("SELECT Count(Usuarios.id_usuario) As Cant FROM Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro WHERE ES=1 AND Suministros.id_nodo IN (" + self.str_lista_nodos + ")")
        #convierto el cursor en array
        recordset = tuple(cursor)
        cursor.close()
        self.txtUsuarios.setText(str(recordset[0][0]))
        self.txtCantUsuarios.setText(str(recordset[0][0]))
        cursor = cnn.cursor()
        cursor.execute("SELECT Min(Energia_Facturada.Desde) As Desde, Max(Energia_Facturada.Hasta) As Hasta FROM Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro INNER JOIN Energia_Facturada ON Usuarios.id_usuario = Energia_Facturada.id_usuario WHERE Suministros.id_nodo IN (" + self.str_lista_nodos + ")")
        #convierto el cursor en array
        recordset = tuple(cursor)
        cursor.close()
        try:
            self.datDesde.setDate(recordset[0][0])
            self.datHasta.setDate(recordset[0][1])
            desde = recordset[0][0]
            hasta = recordset[0][1]
            if desde < hasta + relativedelta(years=-1):
                desde = hasta + relativedelta(years=-1)
                self.datDesde.setDate(desde)
            self.cambio_fecha()
        except:
            pass
        #mediciones adicionales
        #"SELECT SUM(CAST(LEFT(RIGHT([mediciones].[nombre],LEN([mediciones].[nombre])-2),LEN([mediciones].[nombre])-5) AS DECIMAL(8,2))) FROM Nodos_Temp_" & Codigo_Usuario & " INNER JOIN mediciones ON Nodos_Temp_" & Codigo_Usuario & ".Geoname = mediciones.Geoname WHERE (((Right([mediciones].[Nombre],3))='kVA') AND ((Left([mediciones].[Nombre],2))='SC'));"
        #------------- FIN ANALISIS DE CARGA -------------
        self.cmbTension.addItem('Todos')
        self.cmbTension.addItem('AT')
        self.cmbTension.addItem('MT')
        self.cmbTension.addItem('BT')
        self.campos=[]
        self.campos.append('Tension')
        self.campos.append('Descripcion')
        self.campos.append('Fase')
        self.campos.append('Zona')
        self.campos.append('Alimentador')
        self.campos.append('Material')
        self.campos.append('Tipo')
        if len(self.ftrs_lineas)>0:
            str_lista='0'
            for ftr in self.ftrs_lineas:
                str_lista=str_lista + ',' + str(ftr)
            self.str_sql="SELECT Descripcion, CASE WHEN Tension>50000 THEN 'AT' WHEN Tension<1000 THEN 'BT' ELSE 'MT' END AS Nivel_Tension, Lineas.Tension, CASE LEN(Lineas.Fase) WHEN 1 THEN 'Monofásicas' WHEN 2 THEN 'Bifásicas' ELSE 'Trifásicas' END AS Fase, Lineas.Zona, Lineas.Alimentador, Elementos_Lineas.Val9 AS Material, CASE Elementos_Lineas.Val8 WHEN 'A' THEN 'Aéreo' WHEN 'S' THEN 'Subterráneo' WHEN 'P' THEN 'Preensamblado' WHEN 'C' THEN 'Compacta' END AS Tipo, Lineas.Longitud / 1000 AS Longitud FROM Lineas INNER JOIN Elementos_Lineas ON Lineas.Elmt = Elementos_Lineas.Id WHERE Tension>0 AND geoname IN (" + str_lista + ")"
        else:
            self.str_sql="SELECT Descripcion, CASE WHEN Tension>50000 THEN 'AT' WHEN Tension<1000 THEN 'BT' ELSE 'MT' END AS Nivel_Tension, Lineas.Tension, CASE LEN(Lineas.Fase) WHEN 1 THEN 'Monofásicas' WHEN 2 THEN 'Bifásicas' ELSE 'Trifásicas' END AS Fase, Lineas.Zona, Lineas.Alimentador, Elementos_Lineas.Val9 AS Material, CASE Elementos_Lineas.Val8 WHEN 'A' THEN 'Aéreo' WHEN 'S' THEN 'Subterráneo' WHEN 'P' THEN 'Preensamblado' WHEN 'C' THEN 'Compacta' END AS Tipo, Lineas.Longitud / 1000 AS Longitud FROM Lineas INNER JOIN Elementos_Lineas ON Lineas.Elmt = Elementos_Lineas.Id WHERE Tension>0"
        if self.tipo_usuario==4:
            self.cmdActualizarDatos.setEnabled(False)
        #--------------- ANALISIS DE MULTA ---------------
        cnn = self.conn
        try:
            cursor = cnn.cursor()
            cursor.execute("SELECT Costo_ENS AS CostoEnS FROM CENS WHERE Tarifa IN ('T1R','T2BT') AND (Desde = (SELECT MAX(Desde) FROM CENS AS CENS_1)) ORDER BY Tarifa")
            #convierto el cursor en array
            cens = tuple(cursor)
            cursor.close()
            self.txtCens1.setText(str(cens[0][0]))
            self.txtCens2.setText(str(cens[1][0]))
        except:
            self.txtCens1.setText('0')
            self.txtCens2.setText('0')
        self.txtCens1.setEnabled(False)
        self.txtCens2.setEnabled(False)
        #------------- FIN ANALISIS DE MULTA -------------

        #------------- FACTORES DE ESCALA -------------
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT SUM(Cargas_Nodos.P), SUM(Cargas_Nodos.P * Cargas_Nodos.Fe), SUM(Cargas_Nodos.Q * Cargas_Nodos.Fe) FROM Selecciones INNER JOIN Cargas_Nodos ON Selecciones.geoname = Cargas_Nodos.geoname INNER JOIN Nodos ON Selecciones.geoname=Nodos.geoname WHERE Nodos.estado=6 AND Selecciones.id_usuario_sistema=" + str(self.id_usuario_sistema))
        #convierto el cursor en array
        carga_original = tuple(cursor)
        cursor.close()
        self.p=0.0
        self.q=0.0
        fe=1
        if len(carga_original)>0:
            if not carga_original[0][1] == None:
                self.p = carga_original[0][1]
            if not carga_original[0][2] == None:
                self.q = carga_original[0][2]
            if not carga_original[0][0]==None:
                fe = self.p/carga_original[0][0]
        self.lblDemanda.setText(f"{self.p:.1f} kW +j {self.q:.1f} kVAr")
        self.lblFactorEscala.setText(str(fe))
        self.lblDemandaFinal.setText(self.lblDemanda.text())
        #------------- FIN FACTORES DE ESCALA -------------

        self.cmdActualizarDatos.clicked.connect(self.actualizar_datos)
        self.cmdExportar.clicked.connect(self.exportar)
        self.cmdExportarLineas.clicked.connect(self.exportar)
        self.cmdCalcularMulta.clicked.connect(self.calculo_multa)
        self.cmdAplicar.clicked.connect(self.aplicar_factor_escala)
        self.cmdSalir.clicked.connect(self.salir)
        self.tblResultado.itemClicked.connect(self.elijo_item)
        self.treeWidget.itemDoubleClicked.connect(self.elijo_rama)
        self.datDesde.dateChanged.connect(self.cambio_fecha)
        self.datHasta.dateChanged.connect(self.cambio_fecha)
        self.timHoraDesde.timeChanged.connect(self.cambio_hora_calidad)
        self.timHoraHasta.timeChanged.connect(self.cambio_hora_calidad)
        self.txtFactorCarga.textChanged.connect(self.cambio_fc)
        self.txtMultiplicador.textChanged.connect(self.cambio_fe)
        self.cmbTension.activated.connect(self.elijo_tension)
        self.cmbAgrupar1.activated.connect(self.elijo_agrupar1)
        self.cmbAgrupar2.activated.connect(self.elijo_agrupar2)
        self.cmbAgrupar3.activated.connect(self.elijo_agrupar3)
        self.cmbAgrupar4.activated.connect(self.elijo_agrupar4)

    def cambio_fe(self):
       p = self.p * float(self.txtMultiplicador.text())
       q = self.q * float(self.txtMultiplicador.text())
       self.lblDemandaFinal.setText(f"{p:.1f} kW +j {q:.1f} kVAr")

    def aplicar_factor_escala(self):
        fe = float(self.txtMultiplicador.text())
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("UPDATE Cargas_Nodos SET Fe=Fe*" + str(fe) + " WHERE geoname IN (SELECT geoname FROM Selecciones WHERE id_usuario_sistema=" + str(self.id_usuario_sistema) + ")")
        cnn.commit()
        self.lblDemanda.setText("{self.p*fe:.1f} kW +j {self.q*fe:.1f} kVAr")
        self.txtMultiplicador.setText('1.000')
        self.lblFactorEscala.setText(str(fe*float(self.lblFactorEscala.text())))
        self.lblDemandaFinal.setText(self.lblDemanda.text())

    def elijo_tension(self):
        if self.cmbTension.currentText()=='Todos':
            self.str_where = 'Tension<>0'
            self.str_groupby = ''
        elif self.cmbTension.currentText()=='AT':
            self.str_where = 'Tension>50000'
            self.str_groupby = 'Nivel_Tension'
        elif self.cmbTension.currentText()=='MT':
            self.str_where = 'Tension>=1000 AND Tension<=50000'
            self.str_groupby = 'Nivel_Tension'
        else:
            self.str_where = 'Tension<1000'
            self.str_groupby = 'Nivel_Tension'

        self.cmbAgrupar1.clear()
        self.cmbAgrupar1.addItem('')
        for i in range (0, len(self.campos)):
            self.cmbAgrupar1.addItem(self.campos[i])
        self.cmbAgrupar2.clear()
        self.cmbAgrupar3.clear()
        self.cmbAgrupar4.clear()
        self.lleno_tabla()

    def elijo_agrupar1(self):
        if self.cmbAgrupar1.currentText()=='':
            return
        self.cmbAgrupar2.clear()
        self.cmbAgrupar3.clear()
        self.cmbAgrupar4.clear()
        self.str_groupby = self.cmbAgrupar1.currentText()
        self.cmbAgrupar2.addItem('')
        for i in range (0, len(self.campos)):
            if self.campos[i]!=self.cmbAgrupar1.currentText():
                self.cmbAgrupar2.addItem(self.campos[i])
        self.lleno_tabla()

    def elijo_agrupar2(self):
        if self.cmbAgrupar2.currentText()=='':
            return
        self.cmbAgrupar3.clear()
        self.cmbAgrupar4.clear()
        self.str_groupby = self.str_groupby + ',' + self.cmbAgrupar2.currentText()
        self.cmbAgrupar3.addItem('')
        for i in range (0, len(self.campos)):
            if self.campos[i]!=self.cmbAgrupar1.currentText() and self.campos[i]!=self.cmbAgrupar2.currentText():
                self.cmbAgrupar3.addItem(self.campos[i])
        self.lleno_tabla()

    def elijo_agrupar3(self):
        if self.cmbAgrupar3.currentText()=='':
            return
        self.cmbAgrupar4.clear()
        self.str_groupby = self.str_groupby + ',' + self.cmbAgrupar3.currentText()
        self.cmbAgrupar4.addItem('')
        for i in range (0, len(self.campos)):
            if self.campos[i]!=self.cmbAgrupar1.currentText() and self.campos[i]!=self.cmbAgrupar2.currentText() and self.campos[i]!=self.cmbAgrupar3.currentText():
                self.cmbAgrupar4.addItem(self.campos[i])
        self.lleno_tabla()

    def elijo_agrupar4(self):
        if self.cmbAgrupar4.currentText()=='':
            return
        self.str_groupby = self.str_groupby + ',' + self.cmbAgrupar4.currentText()
        self.lleno_tabla()

    def lleno_tabla(self):
        cnn = self.conn
        cursor = cnn.cursor()
        if self.str_groupby=='':
            cursor.execute("SELECT Sum(longitud) AS km FROM (" + self.str_sql + ") A WHERE " + self.str_where)
        else:
            cursor.execute("SELECT " + self.str_groupby + ", Sum(longitud) AS km FROM (" + self.str_sql + ") A WHERE " + self.str_where + " GROUP BY " + self.str_groupby)
        #convierto el cursor en array
        elementos = tuple(cursor)
        encabezado = [column[0] for column in cursor.description]
        cursor.close()
        self.tblLongitudes.setRowCount(0)
        if len(elementos) > 0:
            self.tblLongitudes.setRowCount(len(elementos))
            self.tblLongitudes.setColumnCount(len(elementos[0]))
        total=0
        for i in range (0, len(elementos)):
            for j in range (len(elementos[0])):
                if j == len(elementos[0])-1:
                    item = QTableWidgetItem(str(round(elementos[i][j],2)))
                    total=total+elementos[i][j]
                else:
                    item = QTableWidgetItem(str(elementos[i][j]))
                self.tblLongitudes.setItem(i,j,item)
        self.tblLongitudes.setHorizontalHeaderLabels(encabezado)
        self.lblLongitudTotal.setText(str(round(total,2)))

    def elijo_rama(self):
        cnn = self.conn
        cursor = cnn.cursor()
        items = self.treeWidget.selectedItems()
        if len(items) != 0:
            item = items[0]
        #self.treeWidget.resizeColumnToContents(0)
        if item.data(1,QtCore.Qt.ItemDataRole.DisplayRole)!='0':
            #------------------------ NODOS --------------------------
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Nodos':
                str_lista='0'
                for ftr in self.ftrs_nodos:
                    str_lista=str_lista + ',' + str(ftr)
                try:
                    cursor.execute('DROP TABLE #Nodos')
                    cnn.commit()
                except:
                    cnn.rollback()
                try:
                    cursor.execute("SELECT geoname, nombre, Nodos.descripcion, CASE WHEN LEFT(Elementos_Nodos.Descripcion,14) = 'Elemento Corte' THEN 'Elemento Corte' ELSE ISNULL(Elementos_Nodos.Descripcion, 'Nodo Simple') END AS elemento, tension, zona, alimentador, uucc INTO #Nodos FROM Nodos LEFT JOIN Elementos_Nodos ON Nodos.elmt=Elementos_Nodos.id WHERE geoname IN (" + str_lista + ")")
                    cnn.commit()
                except:
                    cnn.rollback()
                if item.childCount()==0:
                    cursor.execute('SELECT Elemento, count(*) FROM #Nodos GROUP BY Elemento')
                    elementos = tuple(cursor)
                    for elemento in elementos:
                        self.nodos.addChild(QTreeWidgetItem([elemento[0], str(elemento[1])]))
                    cursor.close()
                cursor = cnn.cursor()
                cursor.execute("SELECT * FROM #Nodos")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Nodo Simple':
                cursor.execute("SELECT * FROM #Nodos WHERE elemento='Nodo Simple'")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Fuente':
                cursor.execute("SELECT * FROM #Nodos WHERE elemento='Fuente'")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Elemento Corte':
                cursor.execute("SELECT * FROM #Nodos WHERE elemento='Elemento Corte'")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Centro Transformación':
                cursor.execute("SELECT #Nodos.*, Tension_2, Mat_Plataf, Tipo_ct, Potencia, Conexionado, Marca, N_Chapa FROM #Nodos LEFT JOIN Ct ON #Nodos.nombre=Ct.id_ct LEFT JOIN Transformadores ON #Nodos.nombre = Transformadores.id_ct WHERE elemento='Centro Transformación'")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                cursor = cnn.cursor()
                cursor.execute("SELECT COUNT(*) AS Cantidad, SUM(Cargas_Nodos.P * Cargas_Nodos.Fe) AS P, SUM(Cargas_Nodos.Q * Cargas_Nodos.Fe) AS Q FROM Cargas_Nodos INNER JOIN #Nodos ON Cargas_Nodos.Geoname = #Nodos.Geoname WHERE elemento='Centro Transformación'")
                cargas = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                if cargas[0][0]>0:
                    if item.childCount()==0:
                        item.addChild(QTreeWidgetItem(['Demandas', str(cargas[0][0])]))
                return
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Suministro':
                cursor.execute("SELECT * FROM #Nodos WHERE elemento='Suministro'")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                if len(elementos)>0:
                    cursor = cnn.cursor()
                    cursor.execute("SELECT COUNT(Usuarios.id_usuario) FROM #Nodos INNER JOIN Suministros ON #Nodos.geoname=Suministros.id_nodo INNER JOIN Usuarios ON Suministros.id_suministro=Usuarios.id_suministro WHERE elemento='Suministro'")
                    usuarios = tuple(cursor)
                    encabezado = [column[0] for column in cursor.description]
                    cursor.close()
                    if usuarios[0][0]>0:
                        if item.childCount()==0:
                            item.addChild(QTreeWidgetItem(['Usuarios', str(usuarios[0][0])]))

                            cursor = cnn.cursor()
                            cursor.execute("SELECT COUNT(*) AS Cantidad, SUM(Cargas_Nodos.P * Cargas_Nodos.Fe) AS P, SUM(Cargas_Nodos.Q * Cargas_Nodos.Fe) AS Q FROM Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro INNER JOIN Cargas_Nodos ON Suministros.id_nodo = Cargas_Nodos.geoname INNER JOIN #Nodos ON Suministros.id_nodo = #Nodos.Geoname WHERE elemento='Suministro'")
                            cargas = tuple(cursor)
                            encabezado = [column[0] for column in cursor.description]
                            cursor.close()
                            if cargas[0][0]>0:
                                item.addChild(QTreeWidgetItem(['Cargas', str(cargas[0][0])]))
                return
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Capacitor':
                cursor.execute("SELECT * FROM #Nodos WHERE elemento='Capacitor'")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Salida de Alimentador':
                cursor.execute("SELECT * FROM #Nodos WHERE elemento='Salida de Alimentador'")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Regulador de Tensión':
                cursor.execute("SELECT * FROM #Nodos WHERE elemento='Regulador de Tensión'")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Generador':
                cursor.execute("SELECT * FROM #Nodos WHERE elemento='Generador'")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Usuarios':
                cursor.execute("SELECT Usuarios.* FROM #Nodos INNER JOIN Suministros ON #Nodos.geoname=Suministros.id_nodo INNER JOIN Usuarios ON Suministros.id_suministro=Usuarios.id_suministro WHERE elemento='Suministro'")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Cargas':
                cursor.execute("SELECT Cargas.EtF, Cargas.dias, Cargas.P, Cargas.Q, Cargas.Fe, Cargas.Carga00, Cargas.Carga01, Cargas.Carga02, Cargas.Carga03, Cargas.Carga04, Cargas.Carga05, Cargas.Carga06, Cargas.Carga07, Cargas.Carga08, Cargas.Carga09, Cargas.Carga10, Cargas.Carga11, Cargas.Carga12, Cargas.Carga13, Cargas.Carga14, Cargas.Carga15, Cargas.Carga16, Cargas.Carga17, Cargas.Carga18, Cargas.Carga19, Cargas.Carga20, Cargas.Carga21, Cargas.Carga22, Cargas.Carga23 FROM Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro INNER JOIN #Nodos ON Suministros.id_nodo = #Nodos.Geoname INNER JOIN Cargas ON Usuarios.id_usuario = Cargas.Id_Usuario WHERE elemento = 'Suministro'")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Demandas':
                cursor.execute("SELECT #Nodos.geoname, Nombre, Descripcion, Tension, Zona, Alimentador, Cargas_Nodos.P * Cargas_Nodos.Fe AS P, Cargas_Nodos.Q * Cargas_Nodos.Fe AS Q FROM Cargas_Nodos INNER JOIN #Nodos ON Cargas_Nodos.geoname = #Nodos.Geoname WHERE elemento='Centro Transformación'")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return
            #------------------------ LINEAS --------------------------
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Lineas':
                str_lista='0'
                for ftr in self.ftrs_lineas:
                    str_lista=str_lista + ',' + str(ftr)
                try:
                    cursor.execute('DROP TABLE #Lineas')
                except:
                    pass
                try:
                    cursor.execute("SELECT geoname, fase, descripcion, longitud, tension, zona, alimentador, disposicion, conservacion, ternas, acometida, uucc INTO #Lineas FROM Lineas INNER JOIN Elementos_Lineas ON Lineas.elmt=Elementos_Lineas.id WHERE geoname IN (" + str_lista + ")")
                    cnn.commit()
                except:
                    cnn.rollback()
                pass
                if item.childCount()==0:
                    cursor.execute("SELECT tension, count(*) FROM #Lineas GROUP BY tension")
                    tensiones = tuple(cursor)
                    for tension in tensiones:
                        self.lineas.addChild(QTreeWidgetItem(['Lineas ' + str(tension[0]), str(tension[1])]))
                    cursor.close()
                cursor = cnn.cursor()
                cursor.execute("SELECT * FROM #Lineas")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))[:7]=='Lineas ':
                nombre_item=str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))
                str_tension = nombre_item [7 - len(nombre_item):]
                cursor = cnn.cursor()
                cursor.execute("SELECT * FROM #Lineas WHERE tension=" + str_tension)
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return
            #------------------------ POSTES --------------------------
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Postes':
                str_lista='0'
                for ftr in self.ftrs_postes:
                    str_lista=str_lista + ',' + str(ftr)
                try:
                    cursor.execute('DROP TABLE #Postes')
                except:
                    pass
                try:
                    cursor.execute("SELECT geoname, elementos_postes.descripcion as montaje, altura, estructuras.descripcion as estructura, tipo, ternas, aislacion, tension, zona INTO #Postes FROM Postes INNER JOIN Elementos_Postes ON Postes.elmt=Elementos_Postes.id INNER JOIN Estructuras ON Postes.Estructura = Estructuras.id WHERE geoname IN (" + str_lista + ")")
                    cnn.commit()
                except:
                    cnn.rollback()
                if item.childCount()==0:
                    cursor.execute("SELECT tension, count(*) FROM #Postes GROUP BY tension")
                    tensiones = tuple(cursor)
                    for tension in tensiones:
                        self.postes.addChild(QTreeWidgetItem(['Postes ' + str(tension[0]), str(tension[1])]))
                    cursor.close()
                cursor = cnn.cursor()
                cursor.execute("SELECT * FROM #Postes")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))[:7]=='Postes ':
                nombre_item=str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))
                str_tension = nombre_item [7 - len(nombre_item):]
                cursor = cnn.cursor()
                cursor.execute("SELECT * FROM #Postes WHERE tension=" + str_tension)
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return
            #------------------------ PARCELAS --------------------------
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Parcelas':
                str_lista='0'
                for ftr in self.ftrs_parcelas:
                    str_lista=str_lista + ',' + str(ftr)
                try:
                    cursor.execute('DROP TABLE #Parcelas')
                except:
                    pass
                try:
                    cursor.execute("SELECT geoname,parcela,manzana,chacra,quinta,seccion,circunscripcion,zona INTO #Parcelas FROM Parcelas WHERE geoname IN (" + str_lista + ")")
                    cnn.commit()
                except:
                    cnn.rollback()

                cursor = cnn.cursor()
                cursor.execute("SELECT * FROM #Parcelas")
                elementos = tuple(cursor)
                encabezado = [column[0] for column in cursor.description]
                cursor.close()
                self.lleno_grilla(encabezado, elementos)
                return

    def cambio_fecha(self):
        from datetime import datetime
        if self.datHasta.date() < self.datDesde.date():
            QMessageBox.exclamation(None, 'EnerGis 6', '❌ La fecha hasta debe ser mayor a la fecha desde')
            return
        fecha_desde = self.datDesde.date().toString('yyyyMMdd')
        fecha_hasta = self.datHasta.date().toString('yyyyMMdd')
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT SUM(EtF) AS EtF, MIN(Desde) AS Desde, MAX(Hasta) AS Hasta FROM Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro INNER JOIN Energia_Facturada ON Usuarios.id_usuario = Energia_Facturada.id_usuario WHERE Suministros.id_nodo IN (" + self.str_lista_nodos + ") AND Energia_Facturada.Desde>='" + fecha_desde + "' AND Energia_Facturada.Hasta<='" + fecha_hasta + "'")
        #convierto el cursor en array
        recordset = tuple(cursor)
        cursor.close()
        self.txtEnergiaTotal.setText('0')
        self.txtHoras.setText('0')
        self.txtDemanda.setText('-')
        self.txtMemoria.clear()
        try:
            self.txtEnergiaTotal.setText(str(format(recordset[0][0], ".2f")))
            self.txtHoras.setText('0')
            desde = datetime.date(recordset[0][1])
            hasta = datetime.date(recordset[0][2])
            self.txtHoras.setText(str(((hasta - desde).days)*24))
            self.calculo_demanda()
        except:
            pass

    def cambio_hora_calidad(self):
        if self.timHoraHasta.time() < self.timHoraDesde.time():
            QMessageBox.exclamation(None, 'EnerGis 6', '❌ La fecha hasta debe ser mayor a la fecha desde')
            return
        self.txtMemoriaCalidad.setText('')

    def cambio_fc(self):
        self.txtDemanda.setText('-')
        self.calculo_demanda()

    def calculo_demanda(self):
        self.txtMemoria.clear()
        self.txtMemoria.append("Cálculo de la Demanda")
        self.txtMemoria.append("---------------------")
        self.txtMemoria.append("")
        try:
            energia = float(self.txtEnergiaTotal.text())
            horas = float(self.txtHoras.text())
            fc = float(self.txtFactorCarga.text())
            demanda = energia / horas / fc
            self.txtDemanda.setText(str(format(demanda, ".2f")))
            self.txtMemoria.append("    Energía Total = " + str(energia) + " [kWh]")
            self.txtMemoria.append("")
            self.txtMemoria.append(" Período Energías = desde " + str(self.datDesde.date().toString('yyyy-MM-dd')) + " hasta " + str(self.datHasta.date().toString('yyyy-MM-dd')))
            self.txtMemoria.append("    Horas Totales = " + str(horas) + " [h]")
            self.txtMemoria.append("")
            self.txtMemoria.append("  Factor de Carga : Es una medida de la tasa de utilización o eficiencia del uso de energía eléctrica. Un factor de carga bajo indica que la carga no está ejerciendo presión sobre el sistema eléctrico, mientras que los consumidores o los generadores que ejercen más presión sobre la distribución eléctrica tendrán un factor de carga alto.")
            self.txtMemoria.append("")
            self.txtMemoria.append("     Factor Carga = Carga Media / Carga Máxina = " + str(fc))
            self.txtMemoria.append("")
            self.txtMemoria.append("Demanda Calculada = Energía Total / (Horas Totales * Factor Carga)")
            self.txtMemoria.append("Demanda Calculada = " + str(format(demanda, ".2f")) + " [kW]")
        except:
            pass

    def calculo_multa(self):
        hora_desde = self.timHoraDesde.time().hour()
        minuto_desde = self.timHoraDesde.time().minute()
        hora_hasta = self.timHoraHasta.time().hour()
        minuto_hasta = self.timHoraHasta.time().minute()
        if hora_hasta<hora_desde:
            QMessageBox.exclamation(None, 'EnerGis 6', '❌ La hora de finalización debe ser mayor a la de inicio del corte')
            return
        minutos_corte = abs(hora_hasta * 60 + minuto_hasta - hora_desde * 60 - minuto_desde)
        cnn = self.conn
        cursor = cnn.cursor()
        cursor.execute("SELECT tarifa, hora, ki FROM curvas_ki ORDER BY tarifa, hora")
        #convierto el cursor en array
        self.curvas = tuple(cursor)
        cursor.close()

        str_lista = '0'
        for ftr in self.ftrs_nodos:
            str_lista = str_lista + ',' + str(ftr)

        cursor = cnn.cursor()
        try:
            cursor.execute('TRUNCATE TABLE Nodos_Afectados')
            cursor.execute("INSERT INTO Nodos_Afectados SELECT geoname FROM Nodos WHERE elmt=6 AND geoname IN (" + str_lista + ")")
            cursor.execute("TRUNCATE TABLE Multa_Sim")
            cursor.execute("TRUNCATE TABLE E_Facturada_Sim")
            cursor.execute("TRUNCATE TABLE Afectados_Sim")
            cursor.execute("INSERT INTO E_Facturada_Sim SELECT Energia_Facturada.id_usuario, SUM(EtF) FROM Energia_Facturada INNER JOIN Usuarios_Afectados ON Energia_Facturada.id_usuario = Usuarios_Afectados.id_usuario WHERE Desde>= (SELECT DATEADD(M, -6, (SELECT MAX(Hasta) FROM Energia_Facturada WHERE (Hasta < GETDATE())))) GROUP BY Energia_Facturada.id_usuario")
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.critical(None, 'EnerGis 6', '❌ Error al precalcular los datos')
            return
        cursor = cnn.cursor()
        cursor.execute("SELECT SUM(EtF) FROM E_Facturada_Sim")
        #convierto el cursor en array
        energias = tuple(cursor)
        cursor.close()
        if energias[0][0]==None:
            energia = 0
        else:
            energia = energias[0][0]
        self.txtMemoriaCalidad.setText('')
        cursor = cnn.cursor()
        cursor = cnn.cursor()
        cursor.execute("SELECT Usuarios_Afectados.id_usuario, Usuarios_Afectados.tarifa FROM Usuarios_Afectados INNER JOIN Tarifas ON Usuarios_Afectados.tarifa = Tarifas.Tarifa")
        #convierto el cursor en array
        afectados = tuple(cursor)
        cursor.close()
        usuarios_afectados = len(afectados)
        for afectado in afectados:
            #calculo el TI*KI de este usuario
            usuario = afectado[0]
            tarifa = afectado[1] #.strip()
            ki = 0
            tiki = 0
            if minuto_desde + minutos_corte > 60:
                #-------------------------------------
                ki = self.ki(tarifa, hora_desde)
                if ki == -1:
                    QMessageBox.exclamation(None, 'EnerGis 6', '❌ No se encuentra el valor de ki para la tarifa ' + tarifa + ' a la hora ' + str(hora_desde))
                    return
                #-------------------------------------
                tiki = (60 - minuto_desde) * ki
                for t in range (1, int((minutos_corte - (60 - minuto_desde)) / 60)):
                    hora_desde = hora_desde + 1
                    if hora_desde > 23:
                        hora_desde = 0
                    #-------------------------------------
                    ki = self.ki(tarifa, hora_desde)
                    if ki == -1:
                        QMessageBox.exclamation(None, 'EnerGis 6', '❌ No se encuentra el valor de ki para la tarifa ' + tarifa + ' a la hora ' + str(hora_desde))
                        return
                    #-------------------------------------
                    tiki = tiki + 60 * ki
                if ((minutos_corte - (60 - minuto_desde)) / 60) - (int((minutos_corte - (60 - minuto_desde)) / 60)) != 0 :
                    hora_desde = hora_desde + 1
                    if hora_desde > 23:
                        hora_desde = 0
                        #-------------------------------------
                        ki = self.ki(tarifa, hora_desde)
                        if ki == -1:
                            QMessageBox.exclamation(None, 'EnerGis 6', '❌ No se encuentra el valor de ki para la tarifa ' + tarifa + ' a la hora ' + str(hora_desde))
                            return
                        #-------------------------------------
                    tiki = tiki + (minutos_corte - (60 - minuto_desde) - (60 * int((minutos_corte - (60 - minuto_desde)) / 60))) * ki
            else:
                #-------------------------------------
                ki = self.ki(tarifa, hora_desde)
                if ki == -1:
                    QMessageBox.exclamation(None, 'EnerGis 6', '❌ No se encuentra el valor de ki para la tarifa ' + tarifa + ' a la hora ' + str(hora_desde))
                    return
                #-------------------------------------
                tiki = minutos_corte * ki
            #Inserto en Afectados SIM directamente
            try:
                cursor = cnn.cursor()
                cursor.execute("INSERT INTO Afectados_Sim (id_usuario,tarifa,hora,tiempo_interrumpido,tiki) VALUES ('" + str(usuario) + "','" + tarifa + "'," + str(hora_desde) + "," + str(minutos_corte) + "," + str(tiki) + ")")
                cnn.commit()
            except:
                QMessageBox.critical(None, 'EnerGis 6', "❌ No se pudo grabar la interrupción del usuario" + "INSERT INTO Afectados_Sim (id_usuario,tarifa,hora,tiempo_interrumpido,tiki) VALUES ('" + str(usuario) + "','" + tarifa + "'," + str(hora_desde) + "," + str(minutos_corte) + "," + str(tiki) + ")")
                cnn.rollback()
        cursor = cnn.cursor()
        cursor.execute('SELECT Tarifas.id_OCEBA, COUNT(Usuarios.id_usuario), SUM(E_Facturada_Sim.EtF) AS Etf, SUM((Afectados_sim.tiki * E_Facturada_Sim.EtF * C.CostoEnS) / (4380 * 60)) AS Sancion FROM Afectados_sim INNER JOIN Usuarios ON Afectados_sim.id_usuario = Usuarios.id_usuario INNER JOIN E_Facturada_Sim ON Usuarios.id_usuario = E_Facturada_Sim.Id_usuario INNER JOIN Tarifas ON Usuarios.tarifa = Tarifas.Tarifa INNER JOIN (SELECT Tarifa, Costo_ENS AS CostoEnS FROM CENS WHERE (Desde = (SELECT MAX(Desde) FROM CENS AS CENS_1))) AS C ON Tarifas.id_OCEBA = C.Tarifa WHERE (Usuarios.ES = 1) GROUP BY Tarifas.id_OCEBA')
        #convierto el cursor en array
        multas = tuple(cursor)
        cursor.close()
        multa_total = 0
        self.txtMemoriaCalidad.append("               Cálculo de Multa por Corte")
        self.txtMemoriaCalidad.append("               --------------------------")
        self.txtMemoriaCalidad.append("")
        self.txtMemoriaCalidad.append("    Cantidad de Usuarios Interrumpidos = " + str(usuarios_afectados))
        self.txtMemoriaCalidad.append("            Energía Semestral Estimada = " + str(energia) + " [kWh]")
        self.txtMemoriaCalidad.append("                    Duración del Corte = " + str(minutos_corte) + " [min]")
        self.txtMemoriaCalidad.append("    *** Se calcula la multa del corte sin descartes ***")
        self.txtMemoriaCalidad.append("")
        for multa in multas:
            self.txtMemoriaCalidad.append(str(multa[1]).rjust(5) + " " + multa[0].rjust(7) + ";  EtF = " + str(multa[2]).rjust(10) + " kWh;  multa = $ " + str(format(multa[3], ".2f")).rjust(10))
            multa_total = multa_total + multa[3]
        self.txtMemoriaCalidad.append("")
        self.txtMemoriaCalidad.append("")
        self.txtMemoriaCalidad.append("               Multa Calculada $ " + str(format(multa_total, ".2f")))

    def ki(self, tarifa, hora):
        for curva in self.curvas:
            if str(curva[0])==tarifa.strip():
                if curva[1]==hora:
                    return curva[2]
                    break
        return -1

    def lleno_grilla(self, encabezado, elementos):
        self.tblResultado.setRowCount(0)
        if len(elementos) > 0:
            self.tblResultado.setRowCount(len(elementos))
            self.tblResultado.setColumnCount(len(elementos[0]))
        for i in range (0, len(elementos)):
            for j in range (len(elementos[0])):
                item = QTableWidgetItem(str(elementos[i][j]))
                self.tblResultado.setItem(i,j,item)
        self.tblResultado.setHorizontalHeaderLabels(encabezado)

    def elijo_item(self):
        self.mapCanvas.refresh()

    def exportar(self):
        #pip install xlwt
        import xlwt
        if self.tabWidget.currentIndex()==0:
            tbl=self.tblResultado
        elif self.tabWidget.currentIndex()==2:
            tbl=self.tblLongitudes
        else:
            return
        if tbl.rowCount()==0:
            return
        filename = QFileDialog.getSaveFileName(self, 'Guardar Archivo', '', ".xls(*.xls)")
        if filename[0]=='' or filename[1]=='':
            return
        wbk = xlwt.Workbook()
        sheet = wbk.add_sheet("listado", cell_overwrite_ok=True)
        for currentColumn in range(tbl.columnCount()):
            for currentRow in range(tbl.rowCount()):
                teext = str(tbl.item(currentRow, currentColumn).text())
                sheet.write(currentRow, currentColumn, teext)
        wbk.save(filename[0])
        QMessageBox.information(None, 'EnerGis 6', 'ℹ️ Exportado !')

    def actualizar_datos(self):
        if self.tblResultado.rowCount()==0:
            return
        items = self.treeWidget.selectedItems()
        if len(items) != 0:
            item = items[0]
        else:
            return
        if item.data(1,QtCore.Qt.ItemDataRole.DisplayRole)!='0':
            str_lista='0'
            for currentRow in range(self.tblResultado.rowCount()):
                str_lista=str_lista + ',' + str(self.tblResultado.item(currentRow, 0).text())
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Nodos':
                from .frm_reasignar_nodos import frmReasignarNodos
                self.dialogo = frmReasignarNodos(self.mapCanvas, self.conn, str_lista)
                self.dialogo.show()
                return
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Nodo Simple':
                from .frm_reasignar_nodos import frmReasignarNodos
                self.dialogo = frmReasignarNodos(self.mapCanvas, self.conn, str_lista)
                self.dialogo.show()
                return
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Fuente':
                from .frm_reasignar_nodos import frmReasignarNodos
                self.dialogo = frmReasignarNodos(self.mapCanvas, self.conn, str_lista)
                self.dialogo.show()
                return
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Elemento Corte':
                from .frm_reasignar_nodos import frmReasignarNodos
                self.dialogo = frmReasignarNodos(self.mapCanvas, self.conn, str_lista)
                self.dialogo.show()
                return
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Centro Transformación':
                from .frm_reasignar_nodos import frmReasignarNodos
                self.dialogo = frmReasignarNodos(self.mapCanvas, self.conn, str_lista)
                self.dialogo.show()
                return
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Suministro':
                from .frm_reasignar_nodos import frmReasignarNodos
                self.dialogo = frmReasignarNodos(self.mapCanvas, self.conn, str_lista)
                self.dialogo.show()
                return
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Capacitor':
                from .frm_reasignar_nodos import frmReasignarNodos
                self.dialogo = frmReasignarNodos(self.mapCanvas, self.conn, str_lista)
                self.dialogo.show()
                return
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Salida de Alimentador':
                from .frm_reasignar_nodos import frmReasignarNodos
                self.dialogo = frmReasignarNodos(self.mapCanvas, self.conn, str_lista)
                self.dialogo.show()
                return
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Regulador de Tensión':
                from .frm_reasignar_nodos import frmReasignarNodos
                self.dialogo = frmReasignarNodos(self.mapCanvas, self.conn, str_lista)
                self.dialogo.show()
                return
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Generador':
                from .frm_reasignar_nodos import frmReasignarNodos
                self.dialogo = frmReasignarNodos(self.mapCanvas, self.conn, str_lista)
                self.dialogo.show()
                return
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Usuarios':
                return
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))[:6]=='Lineas':
                from .frm_reasignar_lineas import frmReasignarLineas
                self.dialogo = frmReasignarLineas(self.mapCanvas, self.conn, str_lista)
                self.dialogo.show()
                return
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))[:6]=='Postes':
                from .frm_reasignar_postes import frmReasignarPostes
                self.dialogo = frmReasignarPostes(self.mapCanvas, self.conn, str_lista)
                self.dialogo.show()
                return
            if str(item.data(0,QtCore.Qt.ItemDataRole.DisplayRole))=='Parcelas':
                return

    def salir(self):
        self.close()
