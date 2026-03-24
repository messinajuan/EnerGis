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
from .mod_coordenadas import convertir_coordenadas

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_exportar_kml.ui'))

class frmExportarKml(DialogType, DialogBase):

    def __init__(self, conn, srid, str_nodos, str_lineas, str_postes, ftrs_nodos, ftrs_lineas, ftrs_postes):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())
        self.conn = conn
        self.srid = srid
        self.str_nodos = str_nodos
        self.str_lineas = str_lineas
        self.str_postes = str_postes
        self.ftrs_nodos = ftrs_nodos
        self.ftrs_lineas = ftrs_lineas
        self.ftrs_postes = ftrs_postes
        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)

    def aceptar(self):
        try:
            if self.txtNombre.text().strip()=='':
                return
            if os.path.isdir('c:/gis/energis6/DPE/')==False:
                os.mkdir('c:/gis/energis6/DPE/')

            str_archivo = 'c:/gis/energis6/DPE/' + self.txtNombre.text().replace(' ','_').replace('/','-') + '.kml'
            f = open(str_archivo,'w')
            f.writelines('<?xml version=' + '"' + '1.0' + '"' + ' encoding=' + '"' + 'UTF-8' + '"' + '?>' + '\n')
            f.writelines('<kml xmlns=' + '"' + 'http://earth.google.com/kml/2.2' + '"' + '>' + '\n')
            f.writelines('<Document>' + '\n')
            #nombre del documento
            f.writelines('<name></name>' + '\n')
            f.writelines('<description></description>' + '\n')
            #estilos de nodos

            cursor = self.conn.cursor()
            cursor.execute('SELECT id FROM Elementos_Nodos')
            #convierto el cursor en array
            elementos = tuple(cursor)
            cursor.close()
            for e in range (0, len(elementos)):
                str_elemento = str(elementos[e][0])
                #Icono del elemento
                f.writelines('<Style id="' + str_elemento + '">' + '\n')
                f.writelines(' <IconStyle>' + '\n')
                f.writelines('  <Icon>' + '\n')
                f.writelines('   <href>https://www.servimap.com.ar/images/' + str_elemento + '.png</href>' + '\n')
                f.writelines('  </Icon>' + '\n')
                f.writelines(' </IconStyle>' + '\n')
                f.writelines('</Style>' + '\n')
                #Estilo del elemento
                f.writelines('<StyleMap id="' + str_elemento + 's' + '">' + '\n') #la 's' es para definir trafos a partir de trafo, etc
                f.writelines(' <Pair>' + '\n')
                f.writelines('  <key>normal</key>' + '\n')
                f.writelines('  <styleUrl>#' + str_elemento + '</styleUrl>' + '\n')
                f.writelines(' </Pair>' + '\n')
                f.writelines(' <Pair>' + '\n')
                f.writelines('  <key>highlight</key>' + '\n')
                f.writelines('  <styleUrl>#' + str_elemento + '</styleUrl>' + '\n')
                f.writelines(' </Pair>' + '\n')
                f.writelines('</StyleMap>' + '\n')

            #estilos de líneas
            f.writelines('<Style id="LMT1">' + '\n')
            f.writelines(' <LineStyle>' + '\n')
            f.writelines('  <color>FF00FF00</color>' + '\n') #verde
            f.writelines('  <width>1</width>' + '\n')
            f.writelines(' </LineStyle>' + '\n')
            f.writelines(' <PolyStyle>' + '\n')
            f.writelines('  <color>FF00FF00</color>' + '\n') #verde
            f.writelines(' </PolyStyle>' + '\n')
            f.writelines('</Style>' + '\n')

            f.writelines('<Style id="LMT2">' + '\n')
            f.writelines(' <LineStyle>' + '\n')
            f.writelines('  <color>FF00FF00</color>' + '\n') #verde
            f.writelines('  <width>2</width>' + '\n')
            f.writelines(' </LineStyle>' + '\n')
            f.writelines(' <PolyStyle>' + '\n')
            f.writelines('  <color>FF00FF00</color>' + '\n') #verde
            f.writelines(' </PolyStyle>' + '\n')
            f.writelines('</Style>' + '\n')

            f.writelines('<Style id="LMT3">' + '\n')
            f.writelines(' <LineStyle>' + '\n')
            f.writelines('  <color>FF00FF00</color>' + '\n') #verde
            f.writelines('  <width>3</width>' + '\n')
            f.writelines(' </LineStyle>' + '\n')
            f.writelines(' <PolyStyle>' + '\n')
            f.writelines('  <color>FF00FF00</color>' + '\n') #verde
            f.writelines(' </PolyStyle>' + '\n')
            f.writelines('</Style>' + '\n')

            f.writelines('<Style id="LBT">' + '\n')
            f.writelines(' <LineStyle>' + '\n')
            f.writelines('  <color>FF0000FF</color>' + '\n') #azul
            f.writelines('  <width>1</width>' + '\n')
            f.writelines(' </LineStyle>' + '\n')
            f.writelines(' <PolyStyle>' + '\n')
            f.writelines('  <color>FF0000FF</color>' + '\n') #azul
            f.writelines(' </PolyStyle>' + '\n')
            f.writelines('</Style>' + '\n')

            f.close()

            #Nodos
            f = open(str_archivo,'a')
            cursor = self.conn.cursor()
            cursor.execute('SELECT nombre, elmt, Val1, descripcion, geoname FROM Nodos WHERE elmt<>0 AND geoname IN (' + self.str_nodos + ')')
            #convierto el cursor en array
            nodos = tuple(cursor)
            cursor.close()
            for n in range (0, len(nodos)):
                str_nombre = ''
                str_descripcion = ''

                if nodos[n][1] == 6:
                    f.writelines(' <Folder>' + '\n')
                    f.writelines('  <name></name>' + '\n')
                else: #en los suministros, el placemark va despues
                    f.writelines(' <Placemark id="' + str(nodos[n][0]) + '">' + '\n')

                if nodos[n][1] != 6 and nodos[n][1] != 8:
                    if nodos[n][0] != None:
                        str_nombre = nodos[n][0]
                        str_nombre = str_nombre.replace('<','*')
                        str_nombre = str_nombre.replace('>','*')
                        str_nombre = str_nombre.replace('+','*')
                        str_nombre = str_nombre.replace('','')
                    f.writelines('  <name>' + str_nombre + '</name>' + '\n')
                    f.writelines('  <styleUrl>#' + str(nodos[n][1]) + 's</styleUrl>' + '\n') #notese que tiene la 's'

                if nodos[n][1] == 2 or nodos[n][1] == 3:
                    f.writelines('  <description>' + '\n')
                    if nodos[n][2] != None:
                        str_descripcion = nodos[n][2]
                        str_descripcion = str_descripcion.replace('ï¿½','-')
                        str_descripcion = str_descripcion.replace('<','*')
                        str_descripcion = str_descripcion.replace('>','*')
                        str_descripcion = str_descripcion.replace('+','*')
                        str_descripcion = str_descripcion.replace('','')
                    f.writelines('   ' + str_descripcion + '\n')
                    f.writelines('  </description>' + '\n')

                if nodos[n][1] == 4 :
                    f.writelines('  <description>' + '\n')
                    str_descripcion = ''
                    if nodos[n][2] != None:
                        str_descripcion = nodos[n][2]
                    if nodos[n][3] != None:
                        str_descripcion = nodos[n][3] + ' - ' + nodos[n][2] + ' kVA'
                    str_descripcion = str_descripcion.replace('ï¿½','-')
                    str_descripcion = str_descripcion.replace('<','*')
                    str_descripcion = str_descripcion.replace('>','*')
                    str_descripcion = str_descripcion.replace('+','*')
                    str_descripcion = str_descripcion.replace('','')
                    f.writelines('   ' + str_descripcion + '\n')
                    f.writelines('  </description>' + '\n')

                if nodos[n][1] == 8:
                    f.writelines('  <description>' + '\n')
                    if nodos[n][3] != None:
                        str_descripcion = nodos[n][2]
                        str_descripcion = 'Salida ' + str_descripcion
                        str_descripcion = str_descripcion.replace('<','*')
                        str_descripcion = str_descripcion.replace('>','*')
                        str_descripcion = str_descripcion.replace('+','*')
                        str_descripcion = str_descripcion.replace('','')
                    f.writelines('   ' + str_descripcion + '\n')
                    f.writelines('  </description>' + '\n')

                for ftr in self.ftrs_nodos:

                    if ftr.id() == nodos[n][4]:
                        geom = ftr.geometry()
                        coords = convertir_coordenadas(self, geom.asPoint().x(), geom.asPoint().y(), self.srid, 4326)
                        str_longitud = str(coords[1])
                        str_latitud = str(coords[0])

                if nodos[n][1]!= 6: #para suministros, son 1 punto por usuario
                    f.writelines('   <Point>' + '\n')
                    f.writelines('    <coordinates>' + str_longitud + ',' + str_latitud + ',0</coordinates>' + '\n')
                    f.writelines('   </Point>' + '\n')
                    f.writelines(' </Placemark>' + '\n')
                else:
                    f.writelines('  <description></description>' + '\n')
                    f.writelines('  <open>1</open>' + '\n')

                    cursor = self.conn.cursor()
                    cursor.execute('SELECT id_usuario, Nombre FROM Usuarios INNER JOIN Suministros ON Usuarios.id_suministro=Suministros.id_suministro WHERE id_nodo=' + str(nodos[n][4]))
                    #convierto el cursor en array
                    usuarios = tuple(cursor)
                    cursor.close()
                    for u in range (0, len(usuarios)):
                        str_descripcion = str(usuarios[u][0]) + ' - ' + usuarios[u][1]
                        str_descripcion = str_descripcion.replace('<', '*')
                        str_descripcion = str_descripcion.replace('>', '*')
                        str_descripcion = str_descripcion.replace('+', '*')
                        str_descripcion = str_descripcion.replace('', '')
                        f.writelines('  <Placemark>' + '\n')
                        f.writelines('    <name></name>' + '\n')
                        f.writelines('    <description>' + str_descripcion + '</description>' + '\n')
                        f.writelines('    <styleUrl>#6s</styleUrl>' + '\n')
                        f.writelines('    <Point>' + '\n')
                        f.writelines('    <coordinates>' + str_longitud + ',' + str_latitud + ',0</coordinates>' + '\n')
                        f.writelines('    </Point>' + '\n')
                        f.writelines('  </Placemark>' + '\n')
                    f.writelines(' </Folder>' + '\n')
            f.close()

            #Lineas
            f = open(str_archivo,'a')
            cursor = self.conn.cursor()
            cursor.execute('SELECT Geoname, Fase, Descripcion, Tension, Alimentador FROM Lineas INNER JOIN Elementos_Lineas ON Lineas.Elmt = Elementos_Lineas.Id WHERE Lineas.Geoname IN (' + self.str_lineas + ')')
            #convierto el cursor en array
            lineas = tuple(cursor)
            cursor.close()
            for l in range (0, len(lineas)):
                f.writelines(' <Placemark id="' + str(lineas[l][0]) + '">' + '\n')
                f.writelines(' <name>' + str(lineas[l][0]) + '</name>' + '\n')
                str_descripcion = lineas[l][2]
                str_descripcion = str_descripcion.replace('<','*')
                str_descripcion = str_descripcion.replace('>','*')
                str_descripcion = str_descripcion.replace('+','*')
                str_descripcion = str_descripcion.replace('','')
                f.writelines(' <description>' + str_descripcion + '</description>' + '\n')
                if lineas[l][3] < 1000:
                    f.writelines(' <styleUrl>#LBT</styleUrl>' + '\n')
                else:
                    if len(lineas[l][1])==1:
                        f.writelines(' <styleUrl>#LMT1</styleUrl>' + '\n')
                    elif len(lineas[l][1])==2:
                        f.writelines(' <styleUrl>#LMT2</styleUrl>' + '\n')
                    else:
                        f.writelines(' <styleUrl>#LMT3</styleUrl>' + '\n')
                f.writelines(' <LineString>' + '\n')
                f.writelines('  <extrude>1</extrude>' + '\n')
                f.writelines('  <tessellate>1</tessellate>' + '\n')
                f.writelines('  <altitudeMode>RelativeToGround</altitudeMode>' + '\n')
                f.writelines('   <coordinates>' + '\n')

                for ftr in self.ftrs_lineas:
                    if ftr.id()==lineas[l][0]:
                        geom = ftr.geometry()
                        line_strings = [geom.asPolyline()]
                        for line_string in line_strings:
                            for point in line_string:
                                coords = convertir_coordenadas(self, point.x(), point.y(), self.srid, 4326)
                                str_longitud = str(coords[1])
                                str_latitud = str(coords[0])
                                f.writelines(str_longitud + ',' + str_latitud + ',0' + '\n')
                f.writelines('   </coordinates>' + '\n')
                f.writelines(' </LineString>' + '\n')
                f.writelines('</Placemark>' + '\n')
            f.close()

            #Pie
            f = open(str_archivo,'a')
            f.writelines('</Document>' + '\n')
            f.writelines('</kml>' + '\n')
            f.close()

            QMessageBox.information(None, 'EnerGis 6', 'ℹ️ Exportado en ' + str_archivo)
        except:
            QMessageBox.warning(None, 'EnerGis 6', '❌ No se pudo exportar')
        self.close()

    def salir(self):
        self.close()
