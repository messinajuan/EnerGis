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
from PyQt6.QtWidgets import QTableWidgetItem, QMessageBox, QFileDialog
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_calidad_producto.ui'))

class frmCalidadProducto(DialogType, DialogBase):

    def __init__(self, conn, ct):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.conn = conn
        self.ct = ct
        cursor = self.conn.cursor()
        cursor.execute("SELECT id_semestre,Fecha_Desde,Fecha_Hasta,numero FROM Semestre")
        #convierto el cursor en array
        semestre = tuple(cursor)
        cursor.close()
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

        cursor = self.conn.cursor()
        cursor.execute("SELECT MIN(Nodos.Zona) AS Zona, COUNT(Usuarios.id_usuario) AS Usuarios FROM Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro INNER JOIN Suministros_Trafos ON Suministros.id_nodo = Suministros_Trafos.Geoname_s INNER JOIN Nodos ON Suministros_Trafos.Geoname_t = Nodos.Geoname WHERE Nodos.Nombre='" + self.ct + "'")
        #convierto el cursor en array
        zona = tuple(cursor)
        cursor.close()
        self.limite=8
        if len(zona)>0:
            if zona[0][0]=='Rural' and zona[0][1]<10:
                self.limite=12

        cursor = self.conn.cursor()
        cursor.execute("SELECT Id_Medicion, RIGHT(CONVERT(VARCHAR(10), Periodo, 103),7) AS Periodo, '" + self.ct + "' AS CT FROM Mediciones_Producto WHERE Tipo=1 AND Codigo_Elemento='" + self.ct + "' ORDER BY Periodo DESC")
        #convierto el cursor en array
        mediciones_ct = tuple(cursor)
        encabezado = [column[0] for column in cursor.description]
        cursor.close()
        try:
            self.tblMedicionesCt.setRowCount(len(mediciones_ct))
            self.tblMedicionesCt.setColumnCount(len(mediciones_ct[0]))
            for i in range (0, len(mediciones_ct)):
                for j in range (len(mediciones_ct[0])):
                    item = QTableWidgetItem(str(mediciones_ct[i][j]))
                    self.tblMedicionesCt.setItem(i,j,item)
            self.tblMedicionesCt.setHorizontalHeaderLabels(encabezado)
            self.tblMedicionesCt.setColumnWidth(0, 100)
            self.tblMedicionesCt.setColumnWidth(1, 80)
            self.tblMedicionesCt.setColumnWidth(2, 80)
        except:
            pass

        cursor = self.conn.cursor()
        cursor.execute("SELECT Mediciones_Producto.Id_Medicion, RIGHT(CONVERT(VARCHAR(10), Periodo, 103),7) AS Periodo, Mediciones_Producto.Codigo_Elemento AS Id_Usuario FROM Suministros_Trafos INNER JOIN Nodos ON Suministros_Trafos.Geoname_t = Nodos.Geoname INNER JOIN Suministros ON Suministros_Trafos.Geoname_s = Suministros.id_nodo INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro INNER JOIN Mediciones_Producto ON CAST(Usuarios.id_usuario AS VARCHAR) = Mediciones_Producto.Codigo_Elemento WHERE (Mediciones_Producto.Tipo <> 1) AND (Nodos.Elmt = 4) AND (Nodos.Nombre = '" + self.ct + "') ORDER BY Mediciones_Producto.Periodo DESC")
        mediciones_usuarios = tuple(cursor)
        encabezado = [column[0] for column in cursor.description]
        cursor.close()
        try:
            self.tblMedicionesUsuarios.setRowCount(len(mediciones_usuarios))
            self.tblMedicionesUsuarios.setColumnCount(len(mediciones_usuarios[0]))
            for i in range (0, len(mediciones_usuarios)):
                for j in range (len(mediciones_usuarios[0])):
                    item = QTableWidgetItem(str(mediciones_usuarios[i][j]))
                    self.tblMedicionesUsuarios.setItem(i,j,item)
            self.tblMedicionesUsuarios.setHorizontalHeaderLabels(encabezado)
            self.tblMedicionesUsuarios.setColumnWidth(0, 100)
            self.tblMedicionesUsuarios.setColumnWidth(1, 80)
            self.tblMedicionesUsuarios.setColumnWidth(2, 80)
        except:
            pass

        self.cmbUsuariosCt.addItem('Todos los Usuarios del CT')
        self.cmbUsuariosCt.addItem('Usuarios en el 20% de distancia cercana al CT')
        self.cmbUsuariosCt.addItem('Usuarios en el 20% de distacia mas lejana al CT')
        self.listar_usuarios()
        self.tblMedicionesUsuarios.cellClicked.connect(self.seleccionar_medicion)
        self.tblUsuariosCt.cellClicked.connect(self.seleccionar_usuario)
        self.cmbUsuariosCt.activated.connect(self.listar_usuarios)
        self.cmbSemestre.activated.connect(self.elijo_semestre)
        self.cmdMedicionCt.clicked.connect(self.medicion_ct)
        self.cmdMedicionUsuario.clicked.connect(self.medicion_usuario)
        self.cmdExportar.clicked.connect(self.exportar)
        self.cmdSalir.clicked.connect(self.salir)

    def elijo_semestre(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT Desde,Hasta FROM Semestres WHERE Semestre=" + self.cmbSemestre.currentText())
        #convierto el cursor en array
        semestre = tuple(cursor)
        cursor.close()
        self.lbl_elegido_desde.setText(str(semestre[0][0])[:10])
        self.lbl_elegido_hasta.setText(str(semestre[0][1])[:10])
        self.cmbUsuariosCt.setCurrentIndex(-1)
        self.tblUsuariosCt.setRowCount(0)
        self.tblUsuariosCt.setColumnCount(0)
        cursor = self.conn.cursor()
        cursor.execute("SELECT SUM(Energia_Facturada.EtF) AS Energia, MAX(SQRT(POWER(Nodos.XCoord - Nodos_1.XCoord, 2) + POWER(Nodos.YCoord - Nodos_1.YCoord, 2))) AS d FROM Usuarios INNER JOIN Energia_Facturada ON Usuarios.id_usuario = Energia_Facturada.id_usuario INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro INNER JOIN Suministros_Trafos ON Suministros.id_nodo = Suministros_Trafos.Geoname_s INNER JOIN Nodos ON Suministros_Trafos.Geoname_t = Nodos.Geoname INNER JOIN Nodos AS Nodos_1 ON Suministros.id_nodo = Nodos_1.Geoname WHERE Desde>='" + self.lbl_elegido_desde.text().replace("-","") + "' AND Hasta<='" + self.lbl_elegido_hasta.text().replace("-","") + "' AND Nodos.Nombre='" + self.ct + "'")
        #convierto el cursor en array
        maximos = tuple(cursor)
        cursor.close()
        energia_total=maximos[0][0]
        self.txtEnergiaCt.setText(str(energia_total))

    def listar_usuarios(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT SUM(Energia_Facturada.EtF) AS Energia, MAX(SQRT(POWER(Nodos.XCoord - Nodos_1.XCoord, 2) + POWER(Nodos.YCoord - Nodos_1.YCoord, 2))) AS d FROM Usuarios INNER JOIN Energia_Facturada ON Usuarios.id_usuario = Energia_Facturada.id_usuario INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro INNER JOIN Suministros_Trafos ON Suministros.id_nodo = Suministros_Trafos.Geoname_s INNER JOIN Nodos ON Suministros_Trafos.Geoname_t = Nodos.Geoname INNER JOIN Nodos AS Nodos_1 ON Suministros.id_nodo = Nodos_1.Geoname WHERE Desde>='" + self.lbl_elegido_desde.text().replace("-","") + "' AND Hasta<='" + self.lbl_elegido_hasta.text().replace("-","") + "' AND Nodos.Nombre='" + self.ct + "'")
            #convierto el cursor en array
            maximos = tuple(cursor)
            cursor.close()
            energia_total=maximos[0][0]
            distancia_total=maximos[0][1]
            self.txtEnergiaCt.setText(str(energia_total))
            cursor = self.conn.cursor()
            if self.cmbUsuariosCt.currentText()=='Usuarios en el 20% de distancia cercana al CT':
                str_having = " HAVING ROUND(100 * SQRT(POWER(Nodos.XCoord - Nodos_1.XCoord, 2) + POWER(Nodos.YCoord - Nodos_1.YCoord, 2))/" + str(distancia_total) + ",1)<=20"
            elif self.cmbUsuariosCt.currentText()=='Usuarios en el 20% de distacia mas lejana al CT':
                str_having = " HAVING ROUND(100 * SQRT(POWER(Nodos.XCoord - Nodos_1.XCoord, 2) + POWER(Nodos.YCoord - Nodos_1.YCoord, 2))/" + str(distancia_total) + ",1)>=80"
            else:
                str_having = ""
            cursor.execute("SELECT Usuarios.id_usuario, Usuarios.tarifa, Usuarios.nombre, SUM(Energia_Facturada.EtF) AS Energia, ROUND(100 * SQRT(POWER(Nodos.XCoord - Nodos_1.XCoord, 2) + POWER(Nodos.YCoord - Nodos_1.YCoord, 2))/" + str(distancia_total) + ",1) AS [% dist] FROM Usuarios INNER JOIN Energia_Facturada ON Usuarios.id_usuario = Energia_Facturada.id_usuario INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro INNER JOIN Suministros_Trafos ON Suministros.id_nodo = Suministros_Trafos.Geoname_s INNER JOIN Nodos ON Suministros_Trafos.Geoname_t = Nodos.Geoname INNER JOIN Nodos AS Nodos_1 ON Suministros.id_nodo = Nodos_1.Geoname WHERE Desde>='" + self.lbl_elegido_desde.text().replace("-","") + "' AND Hasta<='" + self.lbl_elegido_hasta.text().replace("-","") + "' AND Nodos.Nombre='" + self.ct + "' GROUP BY Usuarios.id_usuario, Usuarios.tarifa, Usuarios.nombre, SQRT(POWER(Nodos.XCoord - Nodos_1.XCoord, 2) + POWER(Nodos.YCoord - Nodos_1.YCoord, 2))" + str_having)
            #convierto el cursor en array
            usuarios_ct = tuple(cursor)
            encabezado = [column[0] for column in cursor.description]
            cursor.close()
            try:
                self.tblUsuariosCt.setRowCount(len(usuarios_ct))
                self.tblUsuariosCt.setColumnCount(len(usuarios_ct[0]))
                for i in range (0, len(usuarios_ct)):
                    for j in range (len(usuarios_ct[0])):
                        item = QTableWidgetItem(str(usuarios_ct[i][j]))
                        self.tblUsuariosCt.setItem(i,j,item)
                self.tblUsuariosCt.setHorizontalHeaderLabels(encabezado)
                self.tblUsuariosCt.setColumnWidth(0, 80)
                self.tblUsuariosCt.setColumnWidth(1, 80)
                self.tblUsuariosCt.setColumnWidth(2, 300)
                self.tblUsuariosCt.setColumnWidth(3, 80)
                self.tblUsuariosCt.setColumnWidth(4, 60)
            except:
                pass
        except:
            pass

    def medicion_ct(self):
        if self.tblMedicionesCt.currentRow()==-1:
            return
        id_medicion=self.tblMedicionesCt.item(self.tblMedicionesCt.currentRow(),0).text()
        from .frm_mediciones import frmMediciones
        self.dialogo = frmMediciones(self.conn, id_medicion, self.limite)
        self.dialogo.show()

    def medicion_usuario(self):
        if self.tblMedicionesUsuarios.currentRow()==-1:
            return
        id_medicion=self.tblMedicionesUsuarios.item(self.tblMedicionesUsuarios.currentRow(),0).text()
        from .frm_mediciones import frmMediciones
        self.dialogo = frmMediciones(self.conn, id_medicion, self.limite)
        self.dialogo.show()

    def seleccionar_medicion(self, row, column):
        # Obtener el valor de la tercera columna de la fila seleccionada en QTableWidget1
        value_to_match = self.tblMedicionesUsuarios.item(row, 2).text()
        # Recorrer las filas de QTableWidget2
        for i in range(self.tblUsuariosCt.rowCount()):
            item = self.tblUsuariosCt.item(i, 0)  # Segunda columna de QTableWidget2
            if item and item.text() == value_to_match:
                # Seleccionar la fila si hay coincidencia
                self.tblUsuariosCt.selectRow(i)
                break
        else:
            # Si no hay coincidencias, quitar selección
            self.tblUsuariosCt.clearSelection()

    def seleccionar_usuario(self, row, column):
        # Obtener el valor de la tercera columna de la fila seleccionada en QTableWidget1
        value_to_match = self.tblUsuariosCt.item(row, 0).text()
        # Recorrer las filas de QTableWidget2
        for i in range(self.tblMedicionesUsuarios.rowCount()):
            item = self.tblMedicionesUsuarios.item(i, 2)  # Segunda columna de QTableWidget2
            if item and item.text() == value_to_match:
                # Seleccionar la fila si hay coincidencia
                self.tblMedicionesUsuarios.selectRow(i)
                break
        else:
            # Si no hay coincidencias, quitar selección
            self.tblMedicionesUsuarios.clearSelection()

    def exportar(self):
        import xlwt
        filename = QFileDialog.getSaveFileName(self, 'Guardar Archivo', '', ".xls(*.xls)")
        if filename[0]=='' or filename[1]=='':
            return
        wbk = xlwt.Workbook()
        sheet = wbk.add_sheet("usuarios", cell_overwrite_ok=True)
        for currentColumn in range(self.tblUsuariosCt.columnCount()):
            for currentRow in range(self.tblUsuariosCt.rowCount()):
                teext = str(self.tblUsuariosCt.item(currentRow, currentColumn).text())
                sheet.write(currentRow, currentColumn, teext)
        wbk.save(filename[0])
        QMessageBox.information(None, 'EnerGis 6', 'ℹ️ Exportado !')

    def salir(self):
        self.close()
