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
from PyQt6.QtWidgets import QMessageBox, QListWidgetItem, QTableWidgetItem, QApplication
from qgis.core import QgsProject, QgsGeometry, QgsPoint, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsRectangle, QgsFeatureRequest, QgsMapLayerType
from PyQt6.QtCore import QDate
from PyQt6 import uic
import math

from datetime import date

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_usuarios_nuevos.ui'))

class frmUsuariosNuevos(DialogType, DialogBase):

    def __init__(self, mapCanvas, conn):
        super().__init__()
        self.setupUi(self)
        #self.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)

        try:
            # Obtener la resolución de la pantalla
            screen_resolution = QApplication.primaryScreen().availableGeometry()
            #screen_width = screen_resolution.width()
            screen_height = screen_resolution.height()
            # Establecer la altura del form
            self.setFixedHeight(screen_height // 1.5)
            # Establecer la posición a la derecha de la pantalla
            #widget_width = self.width()
            widget_height = self.height()
            x_position = 0
            y_position = (screen_height - widget_height) // 2  # Centramos verticalmente
            self.move(x_position, y_position)
        except:
            pass

        self.mapCanvas = mapCanvas
        self.conn = conn
        self.suministro=''
        self.m_separar_suministros.triggered.connect(self.separar_suministros)
        self.m_suministros_sin_usuarios.triggered.connect(self.suministros_sin_usuarios)
        self.m_conectar_suministros_aislados.triggered.connect(self.conectar_suministros_aislados)
        self.m_suministros_con_coordenadas_externas.triggered.connect(self.suministros_con_coordenadas_externas)
        self.m_suministros_con_ejes_de_calle.triggered.connect(self.suministros_con_ejes_de_calle)
        self.m_suministros_por_catastro.triggered.connect(self.suministros_por_catastro)
        cursor = self.conn.cursor()
        cursor.execute("SELECT Valor FROM Configuracion WHERE Variable='SRID'")
        rows = cursor.fetchall()
        cursor.close()
        self.srid = rows[0][0]
        self.m_salir.triggered.connect(self.salir)
        self.cmdActualizar.clicked.connect(self.actualizar)
        self.cmdAproximar.clicked.connect(self.aproximar)
        self.tblSuministros.clicked.connect(self.elijo_suministro)
        self.actualizar_grilla()

    def separar_suministros(self):
        reply = QMessageBox.question(None, 'EnerGis 6', 'Desea separar a los usuarios del suministro ' + self.suministro + ' ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.conn.autocommit = False
            cursor = self.conn.cursor()
            try:
                cursor.execute("UPDATE Usuarios SET id_suministro=id_usuario WHERE id_suministro='" + self.suministro + "'")
                self.conn.commit()
            except:
                self.conn.rollback()

    def suministros_sin_usuarios(self):
        cursor = self.conn.cursor()
        self.conn.autocommit = True
        cursor.execute("SELECT Nodos.Geoname, Nodos.Tension FROM ((Nodos LEFT JOIN Lineas AS Lineas_1 ON Nodos.Geoname = Lineas_1.Hasta) LEFT JOIN (Suministros LEFT JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) ON Nodos.Geoname = Suministros.id_nodo) LEFT JOIN Lineas ON Nodos.Geoname = Lineas.Desde WHERE Nodos.Elmt = 6 GROUP BY Nodos.Geoname, Nodos.Tension, Nodos.Elmt HAVING (COUNT(Lineas_1.Geoname) + COUNT(Lineas.Geoname) = 1) AND (COUNT(Usuarios.id_usuario) = 0) OR (COUNT(Lineas_1.Geoname) + COUNT(Lineas.Geoname) = 0) AND (COUNT(Usuarios.id_usuario) = 0)")
        #convierto el cursor en array
        recordset = tuple(cursor)
        cursor.close()
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                lyr.removeSelection()
        self.seleccion_n = []
        for n in range(0, len(recordset)):
            self.seleccion_n.append(recordset[n][0])
        n = self.mapCanvas.layerCount()
        layers = [self.mapCanvas.layer(i) for i in range(n)]
        for lyr in layers:
            if lyr.name()[:5] == 'Nodos':
                lyr.select(self.seleccion_n)
        from .frm_seleccion import frmSeleccion
        self.dialogo = frmSeleccion(self.mapCanvas)
        for m in range (0, len(self.seleccion_n)):
            self.dialogo.liwNodos.addItem(QListWidgetItem(str(self.seleccion_n[m])))
        self.dialogo.show()

    def conectar_suministros_aislados(self):
        from .frm_conectar_aislados import frmConectarAislados
        dialogo = frmConectarAislados(self.mapCanvas, self.conn)
        dialogo.exec()
        if dialogo.elmt_mono == 0 or dialogo.elmt_trif == 0 or dialogo.long_maxima == 0:
            return
        long_maxima = dialogo.long_maxima
        elmt_mono = dialogo.elmt_mono
        elmt_trif = dialogo.elmt_trif
        uucc_mono = dialogo.txtUUCCmono.text()
        uucc_trif = dialogo.txtUUCCtrif.text()
        tension = dialogo.tension
        dialogo.close()
        #Busco suministros aislados
        cursor = self.conn.cursor()
        self.conn.autocommit = True
        cursor.execute("SELECT Nodos.Geoname, Fases.fases, Nodos.Tension, Aux, XCoord, YCoord FROM Nodos INNER JOIN (SELECT Suministros.id_nodo, MAX(Usuarios.fase) AS fases FROM Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro GROUP BY Suministros.id_nodo) AS Fases ON Nodos.Geoname = Fases.id_nodo WHERE Nodos.Tension = " + str(tension) + " AND (((Nodos.Geoname) Not In (SELECT Desde FROM Lineas) AND (Nodos.Geoname) Not In (SELECT Hasta FROM Lineas AS Lineas_1)) AND ((Nodos.Elmt)=6))")
        #convierto el cursor en array
        aislados = tuple(cursor)
        cursor.close()
        #Dibujo las lineas
        for n in range(0, len(aislados)):
            x1 = aislados[n][4]
            y1 = aislados[n][5]
            #Busco el nodo del mismo nivel de tensión a menos de 20m
            cursor = self.conn.cursor()
            self.conn.autocommit = True
            cursor.execute("SELECT TOP (1) Nodos.Geoname, Nodos.Zona, Nodos.Alimentador, Nodos.subzona, Nodos.Elmt, Nodos.Tension, ISNULL(mNodos.fases, 123) AS Fase, Nodos.XCoord, Nodos.YCoord, Nodos.obj.STEnvelope().ToString() AS Ubicacion, ISNULL(Lineas_1.Estilo,'') AS estilo1, ISNULL(Lineas.Estilo,'') AS estilo2, Sqrt(Power(XCoord - " + str(x1) + ", 2) + Power(YCoord - " + str(y1) + ", 2)) AS distancia FROM Nodos LEFT OUTER JOIN Lineas ON Nodos.Geoname = Lineas.Desde LEFT OUTER JOIN Lineas AS Lineas_1 ON Nodos.Geoname = Lineas_1.Hasta LEFT OUTER JOIN mNodos ON Nodos.Geoname = mNodos.geoname WHERE Sqrt(Power(XCoord - " + str(x1) + ", 2) + Power(YCoord - " + str(y1) + ", 2)) <= " + str(long_maxima) + " AND nodos.Elmt = 0 AND nodos.Tension <> 0 AND nodos.Tension = " + str(tension) + " ORDER BY Sqrt(Power(XCoord - " + str(x1) + ", 2) + Power(YCoord - " + str(y1) + ", 2))")
            #convierto el cursor en array
            nodo = tuple(cursor)
            cursor.close()
            if len(nodo)==1:
                geom = QgsGeometry.fromWkt(str(nodo[0][9]))
                box = geom.buffer(25,1).boundingBox()
                self.mapCanvas.setExtent(box)
                self.mapCanvas.refresh()
                reply = QMessageBox.question(None, 'EnerGis 6', 'Conectar Suministro ❓', QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    nodo_desde = aislados[n][0]
                    nodo_hasta = nodo[0][0]
                    if nodo[0][6]==123:
                        fase = aislados[n][1]
                    else:
                        fase = nodo[0][6]
                    zon_lin = nodo[0][1]
                    alim_lin = nodo[0][2]
                    volt_lin = nodo[0][5]
                    x2 = nodo[0][7]
                    y2 = nodo[0][8]
                    elemento = elmt_trif
                    uucc = uucc_trif
                    if fase != 123:
                        elemento = elmt_mono
                        uucc = uucc_mono
                    if nodo[0][10]!='':
                        estilo = nodo[0][10]
                    else:
                        if nodo[0][11]!='':
                            estilo = nodo[0][11]
                        else:
                            estilo = '0-0-2-0-0'
                    longitud = nodo[0][12]
                    self.conn.autocommit = False
                    cursor = self.conn.cursor()
                    self.conn.autocommit = True
                    cursor.execute("SELECT iid FROM iid")
                    iid = tuple(cursor)
                    id = iid[0][0] + 1
                    cursor.execute("UPDATE iid SET iid =" + str(id))
                    self.conn.commit()
                    cursor = self.conn.cursor()
                    self.conn.autocommit = False
                    cursor.execute("SELECT MAX(Aux) FROM Lineas")
                    auxlineas = tuple(cursor)
                    cursor.close()
                    aux = auxlineas[0][0] + 1
                    obj = "geometry::STGeomFromText('LINESTRING (" + str(x1) + " " + str(y1) + "," + str(x2) + " " + str(y2) + ")'," + self.srid + ")"
                    cursor = self.conn.cursor()
                    str_valores = str(id) + ", "
                    str_valores = str_valores + "'" + str(fase) + "', "
                    str_valores = str_valores + str(elemento) + ", "
                    str_valores = str_valores + str(nodo_desde) + ", "
                    str_valores = str_valores + str(nodo_hasta) + ", "
                    str_valores = str_valores + "'', " #Quiebres
                    str_valores = str_valores + str(longitud) + ", "
                    str_valores = str_valores + "'" + estilo + "', "
                    str_valores = str_valores + str(volt_lin) + ", "
                    str_valores = str_valores + "'" + zon_lin + "', "
                    str_valores = str_valores + "'" + alim_lin + "', "
                    str_valores = str_valores + str(aux) + ", "
                    str_valores = str_valores + "'" + str(date.today()).replace('-','') + "', "
                    str_valores = str_valores + "'1111/2001', "
                    str_valores = str_valores + "'No Aplica', "
                    str_valores = str_valores + "'Bueno', "
                    str_valores = str_valores + "'Simple Terna', "
                    str_valores = str_valores + "'" + uucc + "', "
                    str_valores = str_valores + "'1', "
                    str_valores = str_valores + obj
                    try:
                        cursor.execute("INSERT INTO Lineas (Geoname, Fase, Elmt, Desde, Hasta, Quiebres, Longitud, Estilo, Tension, Zona, Alimentador, Aux, Modificacion, Exp, Disposicion, Conservacion, Ternas, UUCC, Acometida, obj) VALUES (" + str_valores + ")")
                        self.conn.commit()
                    except:
                        QMessageBox.warning(None, 'EnerGis 6', '❌ No se puede insertar la línea en la base de datos')
                        self.conn.rollback()

        QMessageBox.information(None, 'EnerGis 6', "ℹ️  "Suministros conectados")

    def lyr_visible(self, layer):
        layer_tree_root = QgsProject.instance().layerTreeRoot()
        layer_tree_layer = layer_tree_root.findLayer(layer)
        return layer_tree_layer.isVisible()

    def suministros_con_coordenadas_externas(self):
        self.conn.autocommit = False
        cursor = self.conn.cursor()
        try:
            cursor.execute("UPDATE A SET d=o FROM (SELECT Suministros_Coordenadas.id_suministro as d, Usuarios.id_suministro as o FROM Suministros_Coordenadas INNER JOIN Usuarios ON Suministros_Coordenadas.id_usuario = Usuarios.id_usuario INNER JOIN Suministros_Nuevos ON Usuarios.id_suministro = Suministros_Nuevos.id_suministro WHERE Suministros_Coordenadas.id_suministro <> Usuarios.id_suministro) A")
            self.conn.commit()
        except:
            self.conn.rollback()
        self.conn.autocommit = True
        cursor = self.conn.cursor()
        cursor.execute("SELECT Suministros_Coordenadas.id_usuario, Suministros_Coordenadas.Lat, Suministros_Coordenadas.Lon, Suministros_Coordenadas.Tension, Suministros_Coordenadas.id_suministro FROM Nodos RIGHT JOIN ((Suministros_Coordenadas INNER JOIN Usuarios ON Suministros_Coordenadas.id_usuario = Usuarios.id_usuario) LEFT JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) ON Nodos.Geoname = Suministros.id_nodo WHERE (((Nodos.Geoname) Is Null)) GROUP BY Suministros_Coordenadas.id_usuario, Suministros_Coordenadas.Lat, Suministros_Coordenadas.Lon, Suministros_Coordenadas.Tension, Suministros_Coordenadas.id_suministro")
        #convierto el cursor en array
        suministros = tuple(cursor)
        cursor.close()
        for n in range(0, len(suministros)):
            pt = QgsPoint(suministros[n][2],suministros[n][1])
            geom = QgsGeometry(pt)
            origen = QgsCoordinateReferenceSystem('EPSG:4326')
            destino = QgsCoordinateReferenceSystem('EPSG:' + str(self.srid))
            tr = QgsCoordinateTransform(origen, destino, QgsProject.instance())
            geom.transform(tr)
            pt=geom.asPoint()
            nivel_tension = suministros[n][3]
            b_existe = False
            m = self.mapCanvas.layerCount()
            layers = [self.mapCanvas.layer(i) for i in range(m)]
            for lyr in layers:
                if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                    if self.lyr_visible(lyr) is True:
                        if lyr.name()[:5] == 'Nodos' and lyr.name() [6 - len(lyr.name()):] == str(nivel_tension):
                            #Me fijo si ya hay un punto en esa zona
                            radio_busqueda = 2.5
                            rect = QgsRectangle(pt.x() - radio_busqueda, pt.y() - radio_busqueda, pt.x() + radio_busqueda, pt.y() + radio_busqueda)
                            int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                            ftrs = lyr.getFeatures(int)
                            i = 0
                            for ftr in ftrs:
                                i = i + 1
                                if i == 1:
                                    cursor = self.conn.cursor()
                                    self.conn.autocommit = True
                                    cursor.execute("SELECT geoname FROM Nodos WHERE elmt=6 AND geoname=" + str(ftr.id()))
                                    #convierto el cursor en array
                                    nodo_proximo = tuple(cursor)
                                    cursor.close()
                                    if len(nodo_proximo) > 0:
                                        b_existe = True
                                    for k in range(0, len(nodo_proximo)):
                                        cursor = self.conn.cursor()
                                        self.conn.autocommit = False
                                        try:
                                            #genero el suministro
                                            cursor.execute("DELETE FROM Suministros WHERE id_suministro='" + suministros[n][4] + "'")
                                            cursor.execute("INSERT INTO Suministros (id_nodo, id_suministro) VALUES (" + str(nodo_proximo[k][0]) + ",'" + suministros[n][4] + "')")
                                            #coloco al usuario en el suministro
                                            cursor.execute("UPDATE Usuarios SET id_suministro='" + suministros[n][4] + "' WHERE id_usuario='" + str(suministros[n][0]) + "'")
                                            #borro el registro original
                                            #cursor.execute("DELETE FROM Suministros_Coordenadas WHERE id_usuario='" + suministros[n][0] + "'")
                                            self.conn.commit()
                                        except:
                                            self.conn.rollback()
                                            QMessageBox.critical(None, 'EnerGis 6', '❌ Error al grabar')
                                            return
                            lyr.triggerRepaint()
            if b_existe == False :
                #genero el nodo
                self.conn.autocommit = False
                cursor = self.conn.cursor()
                box = geom.buffer(25,1).boundingBox()
                self.mapCanvas.setExtent(box)
                self.mapCanvas.refresh()
                zona = 0
                for lyr in layers:
                    if lyr.name() == 'Areas':
                        width = 5 * self.mapCanvas.mapUnitsPerPixel()
                        rect = QgsRectangle(pt.x() - width, pt.y() - width, pt.x() + width, pt.y() + width)
                        #rect = self.mapCanvas.mapRenderer().mapToLayerCoordinates(lyr, rect)
                        int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                        ftrs = lyr.getFeatures(int)
                        for ftr in ftrs:
                            zona = ftr.id()
                if zona!=0:
                    cursor = self.conn.cursor()
                    self.conn.autocommit = True
                    cursor.execute("SELECT Nombre, Localidad, Descripcion FROM Areas WHERE geoname=" + str(zona))
                    #convierto el cursor en array
                    rs = tuple(cursor)
                    cursor.close()
                    zona = rs[0][0]
                    localidad = rs[0][1]
                    subzona = rs[0][2]
                else:
                    zona = 'Rural'
                    localidad = 1
                    subzona = ''
                self.conn.autocommit = False
                cursor = self.conn.cursor()
                cursor.execute("SELECT iid FROM iid")
                iid = tuple(cursor)
                id = iid[0][0] + 1
                cursor.execute("UPDATE iid SET iid =" + str(id))
                self.conn.commit()
                cursor = self.conn.cursor()
                self.conn.autocommit = True
                cursor.execute("SELECT MAX(Aux) FROM Nodos")
                auxnodos = tuple(cursor)
                cursor.close()
                aux = auxnodos[0][0] + 1
                try:
                    obj = "geometry::Point(" + str(pt.x()) + "," + str(pt.y()) + "," + self.srid + ")"
                    cursor = self.conn.cursor()
                    cursor.execute("INSERT INTO Nodos (Geoname, elmt, nivel, modificacion, XCoord, YCoord, zona, localidad, subzona, Tension, Estilo, Aux, obj, estado) VALUES (" + str(id) + ",6,0,'" + QDate.currentDate().toString("yyyyMMdd") + "'," + str(pt.x()) + "," + str(pt.y()) + ",'" + zona + "'," + str(localidad) + ",'" + subzona + "'," + str(nivel_tension) + ",'35 - EnerGIS - 0 - 4227327 - 10 - 0'," + str(aux) + "," + str(obj) + ",6)")
                    #genero el suministro
                    cursor.execute("DELETE FROM Suministros WHERE id_suministro='" + suministros[n][4] + "'")
                    cursor.execute("INSERT INTO Suministros (id_nodo, id_suministro) VALUES (" + str(id) + ",'" + suministros[n][4] + "')")
                    #coloco al usuario en el suministro
                    cursor.execute("UPDATE Usuarios SET id_suministro='" + suministros[n][4] + "' WHERE id_usuario='" + str(suministros[n][0]) + "'")
                    #borro el registro original
                    #cursor.execute("DELETE FROM Suministros_Coordenadas WHERE id_usuario='" + suministros[n][0]) + "'")
                    self.conn.commit()
                except:
                    self.conn.rollback()
                    QMessageBox.critical(None, 'EnerGis 6', '❌Error al grabar')
                    return
                lyr.triggerRepaint()
        QMessageBox.information(None, 'EnerGis 6', "ℹ️  'Suministros dibujados')

    def suministros_con_ejes_de_calle(self):
        f = open('c:/gis/energis6/debug.txt','w')
        f.writelines('Suministros por Ejes de Calle' + '\n')
        f.close()

        distancia_desde_eje = 10
        self.conn.autocommit = True
        cursor = self.conn.cursor()
        #Si tiene * no tomo en cuenta localidad, o sea hay ids de calle unicos !
        cursor.execute("SELECT count(*) FROM VW_GISGEOCODIFICAR WHERE ciudad='*'")
        #convierto el cursor en array
        ciudades = tuple(cursor)
        if ciudades[0][0] == 0:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id_usuario, ciudad, calle, altura, id_suministro, tension FROM VW_GISGEOCODIFICAR")
            #convierto el cursor en array
            geocodificar = tuple(cursor)
            for n in range(0, len(geocodificar)):
                id_usuario = geocodificar[n][0]
                tension = geocodificar[n][5]
                id_suministro = geocodificar[n][4]
                cursor = self.conn.cursor()
                self.conn.autocommit = False
                try:
                    cursor.execute("DELETE FROM Suministros_Coordenadas WHERE id_usuario='" + geocodificar[n][0] + "'")
                    self.conn.commit()
                except:
                    self.conn.rollback()
                altura = geocodificar[n][3]
                sql = "SELECT geoname, calle, izqde, izqa, derde, dera, x1, y1, x2, y2 FROM Ejes WHERE (Ciudad = '" + str(geocodificar[n][1]) + "' AND Calle = " + str(geocodificar[n][2]) + " AND IzqDe <= " + str(altura) + " AND IzqA > " + str(altura) + ")"
                sql = sql + " OR (Ciudad = '" + str(geocodificar[n][1]) + "' AND Calle = " + str(geocodificar[n][2]) + " AND DerDe <= " + str(altura) + " AND DerA > " + str(altura) + ")"
                sql = sql + " OR (Ciudad = '" + str(geocodificar[n][1]) + "' AND Calle = " + str(geocodificar[n][2]) + " AND IzqA = " + str(altura) + ")"
                sql = sql + " OR (Ciudad = '" + str(geocodificar[n][1]) + "' AND Calle = " + str(geocodificar[n][2]) + " AND DerA = " + str(altura) + ")"
                cursor = self.conn.cursor()
                cursor.execute(sql)
                #convierto el cursor en array
                ejes = tuple(cursor)
                k = self.mapCanvas.layerCount()
                for m in range(0, len(ejes)):
                    lyrs = [self.mapCanvas.layer(j) for j in range(k)]
                    for lyr in lyrs:
                        if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                            if self.lyr_visible(lyr) is True:
                                if lyr.name() == 'Ejes de Calle':
                                    ftrs = lyr.getFeatures()
                                    for ftr in ftrs:
                                        if ftr.id()==ejes[m][0]:
                                            try:
                                                geom = ftr.geometry()
                                                vertices  = geom.asPolyline()
                                                xz1=vertices [0][0]
                                                yz1=vertices [0][1]
                                                xz2=vertices [1][0]
                                                yz2=vertices [1][1]

                                                #aca hay que ver si vengo con pares o impares, entonces veo la longitud por derecha y por izquierda que pueden ser <>s
                                                largo_cuadra = abs(ejes[m][3] - ejes[m][2])
                                                if altura / 100 == 0:
                                                    d = 0
                                                else:
                                                    d = math.sqrt(math.pow((xz2-xz1),2) + math.pow((yz2-yz1),2)) - distancia_desde_eje * 2
                                                    d = ((altura - ejes[m][2]) * d / largo_cuadra) + distancia_desde_eje
                                                if altura / 2 == int(altura / 2): #par
                                                    espar = True
                                                else:
                                                    espar = False

                                                f = open('c:/gis/energis6/debug.txt','a')
                                                f.writelines('eje '+ str(ejes[m][0]) + '\n')
                                                f.writelines('usuario ' + str(id_usuario) + '\n')
                                                f.writelines('vertices ' + str(vertices) + '\n')
                                                f.writelines('d ' +  str(d) + '\n')
                                                f.writelines('espar ' + str(espar) + '\n')
                                                f.writelines('distancia_desde_eje ' + str(distancia_desde_eje) + '\n')
                                                f.close()

                                                px, py = self.colocar_punto_eje(xz1, yz1, xz2, yz2, d, espar, distancia_desde_eje)
                                                cursor = self.conn.cursor()
                                                self.conn.autocommit = False
                                                try:
                                                    cursor.execute("INSERT INTO Suministros_Coordenadas (id_usuario, Lat, Lon, Tension, id_suministro) VALUES ('" + str(id_usuario) + "'," + str(py) + "," + str(px) + "," + str(tension) + ",'" + id_suministro + "')")
                                                    self.conn.commit()
                                                except:
                                                    QMessageBox.critical(None, 'EnerGis 6', '❌ Error al grabar Coordenadas')
                                                    self.conn.rollback()
                                                    break
                                            except:
                                                pass

        else:

            cursor = self.conn.cursor()
            cursor.execute("SELECT id_usuario, ciudad, calle, altura, id_suministro, tension FROM VW_GISGEOCODIFICAR")
            #convierto el cursor en array
            geocodificar = tuple(cursor)
            for n in range(0, len(geocodificar)):
                id_usuario = geocodificar[n][0]
                tension = geocodificar[n][5]
                id_suministro = geocodificar[n][4]
                cursor = self.conn.cursor()
                self.conn.autocommit = False
                try:
                    cursor.execute("DELETE FROM Suministros_Coordenadas WHERE id_usuario='" + geocodificar[n][0] + "'")
                    self.conn.commit()
                except:
                    self.conn.rollback()
                altura = geocodificar[n][3]
                sql = "SELECT geoname, calle, izqde, izqa, derde, dera, x1, y1, x2, y2 FROM Ejes WHERE (Calle = " + str(geocodificar[n][2])
                sql = sql + " AND IzqDe <= " + str(altura) + " AND IzqA > " + str(altura) + ")"
                sql = sql + " OR ( Calle = " + str(geocodificar[n][2]) + " AND DerDe <= " + str(altura) + " AND DerA > " + str(altura) + ")"
                sql = sql + " OR ( Calle = " + str(geocodificar[n][2]) + " AND IzqA = " + str(altura) + ")"
                sql = sql + " OR ( Calle = " + str(geocodificar[n][2]) + " AND DerA = " + str(altura) + ")"
                self.conn.autocommit = True
                cursor = self.conn.cursor()
                cursor.execute(sql)
                #convierto el cursor en array
                ejes = tuple(cursor)
                k = self.mapCanvas.layerCount()
                for m in range(0, len(ejes)):
                    lyrs = [self.mapCanvas.layer(j) for j in range(k)]
                    for lyr in lyrs:
                        if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                            if self.lyr_visible(lyr) is True:
                                if lyr.name() == 'Ejes de Calle':
                                    ftrs = lyr.getFeatures()
                                    for ftr in ftrs:
                                        if ftr.id()==ejes[m][0]:
                                            try:
                                                geom = ftr.geometry()
                                                vertices  = geom.asPolyline()
                                                xz1=vertices [0][0]
                                                yz1=vertices [0][1]
                                                xz2=vertices [1][0]
                                                yz2=vertices [1][1]

                                                #aca hay que ver si vengo con pares o impares, entonces veo la longitud por derecha y por izquierda que pueden ser <>s
                                                largo_cuadra = abs(ejes[m][3] - ejes[m][2])
                                                if altura / 100 == 0:
                                                    d = 0
                                                else:
                                                    d = math.sqrt(math.pow((xz2-xz1),2) + math.pow((yz2-yz1),2)) - distancia_desde_eje * 2
                                                    d = ((altura - ejes[m][2]) * d / largo_cuadra) + distancia_desde_eje
                                                if altura / 2 == int(altura / 2): #par
                                                    espar = True
                                                else:
                                                    espar = False
                                                px, py = self.colocar_punto_eje(xz1, yz1, xz2, yz2, d, espar, distancia_desde_eje)
                                                self.conn.autocommit = False
                                                cursor = self.conn.cursor()
                                                try:
                                                    cursor.execute("INSERT INTO Suministros_Coordenadas (id_usuario, Lat, Lon, Tension, id_suministro) VALUES ('" + str(id_usuario) + "'," + str(py) + "," + str(px) + "," + str(tension) + ",'" + id_suministro + "')")
                                                    self.conn.commit()
                                                except:
                                                    QMessageBox.critical(None, 'EnerGis 6', '❌ Error al grabar Coordenadas')
                                                    self.conn.rollback()
                                                    break
                                            except:
                                                pass
        self.suministros_con_coordenadas_externas()

    def suministros_por_catastro(self):
        self.conn.autocommit = True
        cursor = self.conn.cursor()
        #Si tiene * no tomo en cuenta localidad, o sea hay ids de calle unicos !
        cursor.execute("SELECT Usuarios.id_usuario, Catastro.coord_x, Catastro.coord_y, 400 AS tension, Suministros_Nuevos.id_suministro FROM VW_CCDATOSCOMERCIALES INNER JOIN Usuarios ON VW_CCDATOSCOMERCIALES.Id_Usuario = Usuarios.id_usuario INNER JOIN Catastro ON LEFT(VW_CCDATOSCOMERCIALES.Nomenclatura_Catastral, LEN(Catastro.nomenclatura_catastral) + 1) = Catastro.nomenclatura_catastral + '-' INNER JOIN Suministros_Nuevos ON Usuarios.id_suministro = Suministros_Nuevos.id_suministro INNER JOIN Tarifas ON VW_CCDATOSCOMERCIALES.Tarifa = Tarifas.Tarifa WHERE VW_CCDATOSCOMERCIALES.fecha_baja Is Null")
        #convierto el cursor en array
        catastro = tuple(cursor)
        for n in range(0, len(catastro)):
            pt = QgsPoint(catastro[n][1],catastro[n][2])
            geom = QgsGeometry(pt)
            origen = QgsCoordinateReferenceSystem('EPSG:4326')
            destino = QgsCoordinateReferenceSystem('EPSG:' + str(self.srid))
            tr = QgsCoordinateTransform(origen, destino, QgsProject.instance())
            geom.transform(tr)
            pt=geom.asPoint()
            nivel_tension = catastro[n][3]
            b_existe = False
            m = self.mapCanvas.layerCount()
            layers = [self.mapCanvas.layer(i) for i in range(m)]
            for lyr in layers:
                if lyr.type() == QgsMapLayerType.VectorLayer: #si es una capa vectorial
                    if self.lyr_visible(lyr) is True:
                        if lyr.name()[:5] == 'Nodos' and lyr.name() [6 - len(lyr.name()):] == str(nivel_tension):
                            #Me fijo si ya hay un punto en esa zona
                            width = 15
                            rect = QgsRectangle(pt.x() - width, pt.y() - width, pt.x() + width, pt.y() + width)
                            int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                            ftrs = lyr.getFeatures(int)
                            i = 0
                            for ftr in ftrs:
                                i = i + 1
                                if i == 1:
                                    self.conn.autocommit = True
                                    cursor = self.conn.cursor()
                                    cursor.execute("SELECT geoname FROM Nodos WHERE elmt=6 AND geoname=" + str(ftr.id()))
                                    #convierto el cursor en array
                                    nodo_proximo = tuple(cursor)
                                    if len(nodo_proximo) > 0:
                                        b_existe = True
                                        for k in range(0, len(nodo_proximo)):
                                            self.conn.autocommit = False
                                            cursor = self.conn.cursor()
                                            try:
                                                #genero el suministro
                                                cursor.execute("DELETE FROM Suministros WHERE id_suministro='" + catastro[n][4] + "'")
                                                cursor.execute("INSERT INTO Suministros (id_nodo, id_suministro) VALUES (" + str(nodo_proximo[k][0]) + ",'" + catastro[n][4] + "')")
                                                #coloco al usuario en el suministro
                                                cursor.execute("UPDATE Usuarios SET id_suministro='" + catastro[n][4] + "' WHERE id_usuario='" + str(catastro[n][0]) + "'")
                                                #borro el registro original
                                                #cursor.execute("DELETE FROM Suministros_Coordenadas WHERE id_usuario='" + suministros[n][0] + "'")
                                                self.conn.commit()
                                            except:
                                                self.conn.rollback()
                                                QMessageBox.critical(None, 'EnerGis 6', '❌ Error al grabar')
                                                return
                                lyr.triggerRepaint()
            if b_existe == False :
                #genero el nodo
                self.conn.autocommit = False
                cursor = self.conn.cursor()
                box = geom.buffer(25,1).boundingBox()
                self.mapCanvas.setExtent(box)
                self.mapCanvas.refresh()
                zona = 0
                for lyr in layers:
                    if lyr.name() == 'Areas':
                        width = 5 * self.mapCanvas.mapUnitsPerPixel()
                        rect = QgsRectangle(pt.x() - width, pt.y() - width, pt.x() + width, pt.y() + width)
                        #rect = self.mapCanvas.mapRenderer().mapToLayerCoordinates(lyr, rect)
                        int = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.ExactIntersect)
                        ftrs = lyr.getFeatures(int)
                        for ftr in ftrs:
                            zona = ftr.id()
                if zona!=0:
                    self.conn.autocommit = True
                    cursor = self.conn.cursor()
                    cursor.execute("SELECT Nombre, Localidad, Descripcion FROM Areas WHERE geoname=" + str(zona))
                    #convierto el cursor en array
                    rs = tuple(cursor)
                    zona = rs[0][0]
                    localidad = rs[0][1]
                    subzona = rs[0][2]
                else:
                    zona = 'Rural'
                    localidad = 1
                    subzona = ''
                self.conn.autocommit = False
                cursor = self.conn.cursor()
                cursor.execute("SELECT iid FROM iid")
                iid = tuple(cursor)
                id = iid[0][0] + 1
                cursor.execute("UPDATE iid SET iid =" + str(id))
                self.conn.commit()
                self.conn.autocommit = True
                cursor = self.conn.cursor()
                cursor.execute("SELECT MAX(Aux) FROM Nodos")
                auxnodos = tuple(cursor)
                aux = auxnodos[0][0] + 1
                try:
                    obj = "geometry::Point(" + str(pt.x()) + "," + str(pt.y()) + "," + self.srid + ")"
                    self.conn.autocommit = False
                    cursor = self.conn.cursor()
                    cursor.execute("INSERT INTO Nodos (Geoname, elmt, nivel, modificacion, XCoord, YCoord, zona, localidad, subzona, Tension, Estilo, Aux, obj, estado) VALUES (" + str(id) + ",6,0,'" + QDate.currentDate().toString("yyyyMMdd") + "'," + str(pt.x()) + "," + str(pt.y()) + ",'" + zona + "'," + str(localidad) + ",'" + subzona + "'," + str(nivel_tension) + ",'35 - EnerGIS - 0 - 4227327 - 10 - 0'," + str(aux) + "," + str(obj) + ",6)")
                    #genero el suministro
                    cursor.execute("DELETE FROM Suministros WHERE id_suministro='" + catastro[n][4] + "'")
                    cursor.execute("INSERT INTO Suministros (id_nodo, id_suministro) VALUES (" + str(id) + ",'" + catastro[n][4] + "')")
                    #coloco al usuario en el suministro
                    cursor.execute("UPDATE Usuarios SET id_suministro='" + catastro[n][4] + "' WHERE id_usuario='" + str(catastro[n][0]) + "'")
                    #borro el registro original
                    #cursor.execute("DELETE FROM Suministros_Coordenadas WHERE id_usuario='" + suministros[n][0] + "'")
                    self.conn.commit()
                except:
                    self.conn.rollback()
                    QMessageBox.critical(None, 'EnerGis 6', '❌ Error al grabar')
                    return
                lyr.triggerRepaint()
        QMessageBox.information(None, 'EnerGis 6', "ℹ️ Suministros dibujados")

    def colocar_punto_eje(self, x1, y1, x2, y2, d, par, dsep):
        dx = abs(x2-x1)
        dy = abs(y2-y1)
        if x1 - x2 < 0:
            if y1 - y2 < 0:
                i_cuadrante = 1
            if y1 - y2 > 0:
                i_cuadrante = 4
            if y1 == y2:
                i_cuadrante = 1
        elif x1 - x2 > 0:
            if y1 - y2 < 0:
                i_cuadrante = 2
            if y1 - y2 > 0:
                i_cuadrante = 3
            if y1 == y2:
                i_cuadrante = 2
        else:
            if y1 - y2 < 0:
                i_cuadrante = 1
            if y1 - y2 > 0:
                i_cuadrante = 4
            if y1 == y2:
                i_cuadrante = 1

        dxy = math.sqrt(math.pow(dx,2) + math.pow(dy,2))
        if dxy==0:
            return x1, y1

        dxf = d * dx / dxy
        dyf = d * dy / dxy
        sepx = dsep * dy / dxy
        sepy = dsep * dx / dxy
        if i_cuadrante == 1:
            if par == True:
                dxp = x1 + dxf - sepx
                dyp = y1 + dyf + sepy
            else:
                dxp = x1 + dxf + sepx
                dyp = y1 + dyf - sepy
        elif i_cuadrante == 2:
            if par == True:
                dxp = x1 - dxf - sepx
                dyp = y1 + dyf - sepy
            else:
                dxp = x1 - dxf + sepx
                dyp = y1 + dyf + sepy
        elif i_cuadrante == 3:
            if par == True:
                dxp = x1 - dxf + sepx
                dyp = y1 - dyf - sepy
            else:
                dxp = x1 - dxf - sepx
                dyp = y1 - dyf + sepy
        elif i_cuadrante == 4:
            if par == True:
                dxp = x1 + dxf + sepx
                dyp = y1 - dyf + sepy
            else:
                dxp = x1 + dxf - sepx
                dyp = y1 - dyf - sepy

        pt = QgsPoint(dxp,dyp)
        geom = QgsGeometry(pt)
        origen = QgsCoordinateReferenceSystem('EPSG:' + str(self.srid))
        destino = QgsCoordinateReferenceSystem('EPSG:4326')
        tr = QgsCoordinateTransform(origen, destino, QgsProject.instance())
        geom.transform(tr)
        pt=geom.asPoint()

        f = open('c:/gis/energis6/debug.txt','a')
        f.writelines('punto inicial '+ str(x1) + ', ' + str(y1) + '\n')
        f.writelines('desplazamiento eje '+ str(dxf) + ', ' + str(dyf) + '\n')
        f.writelines('desplazamiento perp ' +  str(sepx) + ', ' + str(sepy) + '\n')
        f.writelines('punto ' + str(dxp) + ', ' + str(dyp) + '\n')
        f.writelines('punto ' +  str(pt) + '\n')
        f.writelines('\n')
        f.close()

        return pt.x(), pt.y()

    def actualizar(self):
        self.conn.autocommit = False
        cursor = self.conn.cursor()
        try:
            cursor.execute("TRUNCATE TABLE Suministros_Nuevos")
            cursor.execute("INSERT INTO Suministros_Nuevos (id_suministro) SELECT usuarios.id_suministro FROM suministros RIGHT JOIN usuarios ON suministros.id_suministro = usuarios.id_suministro WHERE usuarios.ES=1 AND suministros.id_suministro IS NULL GROUP BY usuarios.id_suministro HAVING usuarios.id_suministro IS NOT NULL")
            self.conn.commit()
        except:
            self.conn.rollback()
        self.actualizar_grilla()

    def aproximar(self):
        self.seleccion=''
        self.sql="SELECT Min(Nodos.Geoname) AS geoname, Usuarios.calle + ' ' + Usuarios.altura AS direccion, VW_CCDATOSCOMERCIALES.Ruta AS Ruta FROM (Nodos INNER JOIN (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) ON Nodos.Geoname = Suministros.id_nodo) LEFT JOIN VW_CCDATOSCOMERCIALES ON Usuarios.id_usuario = VW_CCDATOSCOMERCIALES.Id_Usuario WHERE Usuarios.calle LIKE '%" + self.txtCalle.toPlainText() + "%' GROUP BY VW_CCDATOSCOMERCIALES.Ruta, Usuarios.calle, Usuarios.altura ORDER BY VW_CCDATOSCOMERCIALES.Ruta, Usuarios.calle, Usuarios.altura"
        from .frm_elegir import frmElegir
        dialogo = frmElegir(self.mapCanvas, self.conn, self.sql)
        dialogo.exec()
        if dialogo.seleccionado != '':
            self.seleccion = dialogo.seleccionado
            if self.suministro!='':
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM Suministros WHERE id_suministro='" + self.suministro + "'")
                cursor.execute("INSERT INTO Suministros (id_nodo,id_suministro) VALUES ( " + self.seleccion + ",'" + self.suministro + "')")
                cursor.commit()
                self.actualizar()
        dialogo.close()
        pass

    def actualizar_grilla(self):
        self.conn.autocommit = True
        cursor = self.conn.cursor()
        cursor.execute("SELECT Usuarios.Calle, Usuarios.Altura, VW_CCDATOSCOMERCIALES.Ruta, Suministros_Nuevos.id_suministro FROM (Suministros_Nuevos INNER JOIN Usuarios ON Suministros_Nuevos.id_suministro = Usuarios.id_suministro) LEFT JOIN VW_CCDATOSCOMERCIALES ON Usuarios.id_usuario = VW_CCDATOSCOMERCIALES.Id_Usuario ORDER BY VW_CCDATOSCOMERCIALES.Ruta, Usuarios.Calle, Usuarios.Altura")
        #convierto el cursor en array
        recordset = tuple(cursor)

        self.tblSuministros.setRowCount(len(recordset))
        self.tblSuministros.setColumnCount(4)
        self.tblSuministros.setHorizontalHeaderLabels(["calle", "numero", "ruta", "suministro"])
        self.tblSuministros.setColumnWidth(0, 120)
        self.tblSuministros.setColumnWidth(1, 60)
        self.tblSuministros.setColumnWidth(2, 50)
        self.tblSuministros.setColumnWidth(3, 60)
        for i in range (0, len(recordset)):
            self.tblSuministros.setItem(i, 0, QTableWidgetItem(recordset[i][0]))
            self.tblSuministros.setItem(i, 1, QTableWidgetItem(recordset[i][1]))
            self.tblSuministros.setItem(i, 2, QTableWidgetItem(recordset[i][2]))
            self.tblSuministros.setItem(i, 3, QTableWidgetItem(recordset[i][3]))

    def elijo_suministro(self):
        self.suministro = self.tblSuministros.item(self.tblSuministros.currentRow(),3).text()

        self.conn.autocommit = True
        cursor = self.conn.cursor()
        cursor.execute("SELECT Usuarios.id_usuario, Usuarios.nombre, Usuarios.calle, Usuarios.altura, Usuarios.altura_ex FROM Usuarios INNER JOIN Suministros_Nuevos ON Usuarios.id_suministro = Suministros_Nuevos.id_suministro WHERE Suministros_Nuevos.id_suministro ='" + self.suministro + "'")
        #convierto el cursor en array
        recordset = tuple(cursor)

        self.txtUsuario.setText(str(recordset[0][0]))
        self.txtNombre.setText(str(recordset[0][1]).strip())
        self.txtCalle.setText(str(recordset[0][2]).strip())
        self.txtNumero.setText(str(recordset[0][3].strip()) + ' - ' + str(recordset[0][4]).strip())

    def elijo_item(self):
        geom = QgsGeometry.fromWkt(self.tblResultado.selectedItems()[3].text())
        box = geom.buffer(25,1).boundingBox()
        self.mapCanvas.setExtent(box)
        self.mapCanvas.refresh()

    def salir(self):
        self.close()
