    # encoding: utf-8
#-----------------------------------------------------------
# Copyright (C) 2018 Juan Messina
#-----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#---------------------------------------------------------------------

import os
from .mod_coordenadas import convertir_coordenadas
from PyQt6.QtWidgets import QMessageBox, QApplication, QProgressDialog

def __init__(self):
    pass

def exportar_google(self, mapCanvas, conn, srid, nombre_modelo):

    #try:
    if os.path.isdir('c:/gis/energis6/Google/')==False:
        os.mkdir('c:/gis/energis6/Google/')
    if nombre_modelo == None or nombre_modelo == '':
        nombre_modelo = 'EnerGis6'
    str_archivo = 'c:/gis/energis6/Google/' + nombre_modelo + '.kml'
    f = open(str_archivo,'w')
    f.writelines('<?xml version=' + '"' + '1.0' + '"' + ' encoding=' + '"' + 'UTF-8' + '"' + '?>' + '\n')
    f.writelines('<kml xmlns=' + '"' + 'http://earth.google.com/kml/2.2' + '"' + '>' + '\n')
    f.writelines('<Document>' + '\n')
    #nombre del documento
    f.writelines('<name></name>' + '\n')
    f.writelines('<description></description>' + '\n')
    f.close()
    #---------------------------------------
    f = open(str_archivo,'a')
    #estilos de nodos
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM Elementos_Nodos')
    #convierto el cursor en array
    elementos = tuple(cursor)
    cursor.close()
    #----------------------------------------------------------------------------
    progress = QProgressDialog("Elementos...", "Cancelar", 0, len(elementos))
    progress.setWindowTitle("Progreso")
    progress.setWindowModality(True)  # Hace que la ventana de progreso sea modal
    progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
    progress.setValue(0)  # Inicia el progreso en 0
    #----------------------------------------------------------------------------
    for e in range (0, len(elementos)):
        #----------------------------------------------------------------------------
        # Actualiza el progreso
        progress.setValue(e)
        if progress.wasCanceled():
            break
        # Permitir que la GUI se actualice (similar a DoEvents)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
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
    f.close()
    #---------------------------------------
    f = open(str_archivo,'a')
    #estilos de líneas
    f.writelines('<Style id="default">' + '\n')
    f.writelines(' <LineStyle>' + '\n')
    f.writelines('  <color>FF00FF00</color>' + '\n') #verde
    f.writelines('  <width>2</width>' + '\n')
    f.writelines(' </LineStyle>' + '\n')
    f.writelines(' <PolyStyle>' + '\n')
    f.writelines('  <color>FF00FF00</color>' + '\n')
    f.writelines('  <width>2</width>' + '\n')
    f.writelines(' </PolyStyle>' + '\n')
    f.writelines('</Style>' + '\n')
    n = mapCanvas.layerCount()
    layers = [mapCanvas.layer(i) for i in range(n)]
    for lyr in layers:
        if lyr.name()[:6] == 'Lineas' and lyr.name() != 'Lineas_Proyecto':
            if lyr.name() [7 - len(lyr.name()):].isnumeric():
                str_tension = lyr.name() [7 - len(lyr.name()):]
                # Obtengo los estilos de los alimentadores
                estilos = obtener_estilos_de_linea(lyr)
                for estilo in estilos:
                    alimentador = estilo['label'].replace('<','').replace('>','')
                    #Ancho = estilo['width']
                    #tengo que pasar de #AABBCC a FFCCAABB
                    color = estilo['color'].replace('#','')
                    color = color[-4:] + color[:2]
                    color = 'ff' + color
                    if int(str_tension)>1000:
                        f.writelines('<Style id="' + alimentador + '2">' + '\n')
                        f.writelines(' <LineStyle>' + '\n')
                        f.writelines('  <color>' + color + '</color>' + '\n')
                        f.writelines('  <width>2</width>' + '\n')
                        f.writelines(' </LineStyle>' + '\n')
                        f.writelines(' <PolyStyle>' + '\n')
                        f.writelines('  <color>' + color + '</color>' + '\n')
                        f.writelines('  <width>2</width>' + '\n')
                        f.writelines(' </PolyStyle>' + '\n')
                        f.writelines('</Style>' + '\n')
                        #---------------------------------------
                        f.writelines('<Style id="' + alimentador + '3">' + '\n')
                        f.writelines(' <LineStyle>' + '\n')
                        f.writelines('  <color>' + color + '</color>' + '\n')
                        f.writelines('  <width>3</width>' + '\n')
                        f.writelines(' </LineStyle>' + '\n')
                        f.writelines(' <PolyStyle>' + '\n')
                        f.writelines('  <color>' + color + '</color>' + '\n')
                        f.writelines('  <width>3</width>' + '\n')
                        f.writelines(' </PolyStyle>' + '\n')
                        f.writelines('</Style>' + '\n')
                    else:
                        f.writelines('<Style id="' + alimentador + '1">' + '\n')
                        f.writelines(' <LineStyle>' + '\n')
                        f.writelines('  <color>' + color + '</color>' + '\n')
                        f.writelines('  <width>1</width>' + '\n')
                        f.writelines(' </LineStyle>' + '\n')
                        f.writelines(' <PolyStyle>' + '\n')
                        f.writelines('  <color>' + color + '</color>' + '\n')
                        f.writelines('  <width>1</width>' + '\n')
                        f.writelines(' </PolyStyle>' + '\n')
                        f.writelines('</Style>' + '\n')
    f.close()
    #---------------------------------------
    #Tensiones
    cursor = conn.cursor()
    cursor.execute('SELECT Tension FROM Niveles_Tension WHERE Tension<>0 ORDER BY Tension DESC')
    #convierto el cursor en array
    tensiones = tuple(cursor)
    cursor.close()
    for t in range (0, len(tensiones)):
        str_tension = str(tensiones[t][0])
        #---------------------------------------
        f = open(str_archivo,'a')
        f.writelines('<Folder>' + '\n')
        f.writelines('<name>' + str_tension + '</name>' + '\n')
        f.close()
        #---------------------------------------
        f = open(str_archivo,'a')
        #Nodos
        cursor = conn.cursor()
        cursor.execute('SELECT geoname, nombre, elmt, val1, descripcion, xcoord, ycoord FROM Nodos WHERE elmt<>0 AND Tension=' + str_tension)
        #convierto el cursor en array
        nodos = tuple(cursor)
        cursor.close()
        #----------------------------------------------------------------------------
        progress = QProgressDialog("Nodos " + str_tension + "...", "Cancelar", 0, len(nodos))
        progress.setWindowTitle("Progreso")
        progress.setWindowModality(True)  # Hace que la ventana de progreso sea modal
        progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
        progress.setValue(0)  # Inicia el progreso en 0
        #----------------------------------------------------------------------------
        for n in range (0, len(nodos)):
            #----------------------------------------------------------------------------
            # Actualiza el progreso
            progress.setValue(n)
            if progress.wasCanceled():
                break
            # Permitir que la GUI se actualice (similar a DoEvents)
            QApplication.processEvents()
            #----------------------------------------------------------------------------
            str_nombre = ''
            str_descripcion = ''
            if nodos[n][2] == 6:
                f.writelines('  <Folder>' + '\n')
                f.writelines('   <name></name>' + '\n')
            else: #en los suministros, el placemark va despues
                f.writelines('  <Placemark id="' + str(nodos[n][0]) + '">' + '\n')
                if nodos[n][1] != None:
                    str_nombre = nodos[n][1]
                    str_nombre = str_nombre.replace('<','*')
                    str_nombre = str_nombre.replace('>','*')
                    str_nombre = str_nombre.replace('+','*')
                    str_nombre = str_nombre.replace('','')
                    str_nombre = str_nombre.replace('&','Y')
                    f.writelines('   <name>' + str_nombre + '</name>' + '\n')
                    f.writelines('   <styleUrl>#' + str(nodos[n][2]) + 's</styleUrl>' + '\n') #notese que tiene la 's'
            if nodos[n][2] == 2 or nodos[n][2] == 3:
                f.writelines('   <description>' + '\n')
                if nodos[n][3] != None:
                    str_descripcion = nodos[n][3]
                    str_descripcion = str_descripcion.replace('ï¿½','-')
                    str_descripcion = str_descripcion.replace('<','*')
                    str_descripcion = str_descripcion.replace('>','*')
                    str_descripcion = str_descripcion.replace('+','*')
                    str_descripcion = str_descripcion.replace('','')
                    str_descripcion = str_descripcion.replace('&','Y')
                    f.writelines('    ' + str_descripcion + '\n')
                f.writelines('   </description>' + '\n')
            if nodos[n][2] == 4 :
                f.writelines('   <description>' + '\n')
                str_descripcion = ''
                if nodos[n][3] != None:
                    str_descripcion = nodos[n][3]
                    if nodos[n][4] != None:
                        str_descripcion = nodos[n][4] + ' - ' + nodos[n][3] + ' kVA'
                str_descripcion = str_descripcion.replace('ï¿½','-')
                str_descripcion = str_descripcion.replace('<','*')
                str_descripcion = str_descripcion.replace('>','*')
                str_descripcion = str_descripcion.replace('+','*')
                str_descripcion = str_descripcion.replace('','')
                str_descripcion = str_descripcion.replace('&','Y')
                f.writelines('    ' + str_descripcion + '\n')
                f.writelines('   </description>' + '\n')
            if nodos[n][2] == 8:
                f.writelines('   <description>' + '\n')
                if nodos[n][4] != None:
                    str_descripcion = nodos[n][3]
                    str_descripcion = 'Salida ' + str_descripcion
                    str_descripcion = str_descripcion.replace('<','*')
                    str_descripcion = str_descripcion.replace('>','*')
                    str_descripcion = str_descripcion.replace('+','*')
                    str_descripcion = str_descripcion.replace('','')
                    str_descripcion = str_descripcion.replace('&','Y')
                    f.writelines('    ' + str_descripcion + '\n')
                f.writelines('   </description>' + '\n')
            coords = convertir_coordenadas(self, nodos[n][5], nodos[n][6], srid, 4326)
            str_longitud = str(coords[1])
            str_latitud = str(coords[0])
            if nodos[n][2]!= 6: #para suministros, son 1 punto por usuario
                f.writelines('    <Point>' + '\n')
                f.writelines('     <coordinates>' + str_longitud + ',' + str_latitud + ',0</coordinates>' + '\n')
                f.writelines('    </Point>' + '\n')
                f.writelines('  </Placemark>' + '\n')
            else:
                f.writelines('   <description></description>' + '\n')
                #f.writelines('   <open>1</open>' + '\n')
                cursor = conn.cursor()
                cursor.execute('SELECT id_usuario, usuarios.nombre FROM Usuarios INNER JOIN Suministros ON Usuarios.id_suministro=Suministros.id_suministro INNER JOIN Nodos ON Suministros.id_nodo=Nodos.geoname WHERE geoname=' + str(nodos[n][0]) + ' AND Tension=' + str_tension)
                #convierto el cursor en array
                usuarios = tuple(cursor)
                cursor.close()
                if len(usuarios)==0:
                    f.writelines('   <Placemark>' + '\n')
                    f.writelines('     <name></name>' + '\n')
                    f.writelines('     <description></description>' + '\n')
                    f.writelines('     <styleUrl>#6s</styleUrl>' + '\n')
                    f.writelines('     <Point>' + '\n')
                    f.writelines('     <coordinates>' + str_longitud + ',' + str_latitud + ',0</coordinates>' + '\n')
                    f.writelines('     </Point>' + '\n')
                    f.writelines('   </Placemark>' + '\n')
                else:
                    for u in range (0, len(usuarios)):
                        str_descripcion = str(usuarios[u][0]) + ' - ' + usuarios[u][1]
                        str_descripcion = str_descripcion.replace('<', '*')
                        str_descripcion = str_descripcion.replace('>', '*')
                        str_descripcion = str_descripcion.replace('+', '*')
                        str_descripcion = str_descripcion.replace('', '')
                        str_descripcion = str_descripcion.replace('&','Y')
                        f.writelines('   <Placemark>' + '\n')
                        f.writelines('     <name></name>' + '\n')
                        f.writelines('     <description>' + str_descripcion + '</description>' + '\n')
                        f.writelines('     <styleUrl>#6s</styleUrl>' + '\n')
                        f.writelines('     <Point>' + '\n')
                        f.writelines('     <coordinates>' + str_longitud + ',' + str_latitud + ',0</coordinates>' + '\n')
                        f.writelines('     </Point>' + '\n')
                        f.writelines('   </Placemark>' + '\n')
                f.writelines('  </Folder>' + '\n')
        f.close()
        #---------------------------------------
        f = open(str_archivo,'a')
        #Lineas
        cursor = conn.cursor()
        cursor.execute('SELECT geoname, fase, descripcion, tension, alimentador, obj.ToString() FROM Lineas INNER JOIN Elementos_Lineas ON Lineas.Elmt = Elementos_Lineas.Id WHERE Tension=' + str_tension)
        #convierto el cursor en array
        lineas = tuple(cursor)
        cursor.close()
        #----------------------------------------------------------------------------
        progress = QProgressDialog("Lineas " + str_tension + "...", "Cancelar", 0, len(lineas))
        progress.setWindowTitle("Progreso")
        progress.setWindowModality(True)  # Hace que la ventana de progreso sea modal
        progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
        progress.setValue(0)  # Inicia el progreso en 0
        #----------------------------------------------------------------------------
        for l in range (0, len(lineas)):
            #----------------------------------------------------------------------------
            # Actualiza el progreso
            progress.setValue(l)
            if progress.wasCanceled():
                break
            # Permitir que la GUI se actualice (similar a DoEvents)
            QApplication.processEvents()
            #----------------------------------------------------------------------------
            f.writelines('  <Placemark id="' + str(lineas[l][0]) + '">' + '\n')
            f.writelines('  <name>' + str(lineas[l][0]) + '</name>' + '\n')
            str_descripcion = lineas[l][2]
            str_descripcion = str_descripcion.replace('<','*')
            str_descripcion = str_descripcion.replace('>','*')
            str_descripcion = str_descripcion.replace('+','*')
            str_descripcion = str_descripcion.replace('','')
            f.writelines('  <description>' + str_descripcion + '</description>' + '\n')
            alimentador = lineas[l][4].replace('<','').replace('>','')
            if alimentador=='' or alimentador=='SD' or alimentador=='desc.':
                f.writelines('  <styleUrl>#default</styleUrl>' + '\n')
            else:
                if lineas[l][3] < 1000:
                    f.writelines('  <styleUrl>#' + alimentador + '1</styleUrl>' + '\n')
                else:
                    if str(lineas[l][1])=='123':
                        f.writelines('  <styleUrl>#' + alimentador + '3</styleUrl>' + '\n')
                    else:
                        f.writelines('  <styleUrl>#' + alimentador + '2</styleUrl>' + '\n')
            f.writelines('  <LineString>' + '\n')
            f.writelines('   <extrude>1</extrude>' + '\n')
            f.writelines('   <tessellate>1</tessellate>' + '\n')
            f.writelines('   <altitudeMode>RelativeToGround</altitudeMode>' + '\n')
            f.writelines('    <coordinates>' + '\n')
            str_polilinea = lineas[l][5].replace('LINESTRING (','').replace(')','')
            coordenadas = str_polilinea.split(', ')
            for coordenada in coordenadas:
                x, y = coordenada.split(' ')
                coords = convertir_coordenadas(self, x, y, srid, 4326)
                str_longitud = str(coords[1])
                str_latitud = str(coords[0])
                f.writelines(str_longitud + ',' + str_latitud + ',0' + '\n')
            f.writelines('    </coordinates>' + '\n')
            f.writelines('  </LineString>' + '\n')
            f.writelines(' </Placemark>' + '\n')
        f.writelines('</Folder>' + '\n')
        f.close()
    #Pie
    f = open(str_archivo,'a')
    f.writelines('</Document>' + '\n')
    f.writelines('</kml>' + '\n')
    f.close()
    return 'Exportado en ' + str_archivo
    #except:
    #    return 'No se pudo exportar'

def obtener_estilos_de_linea(capa):
    estilos = []
    # Obtener el renderer de la capa
    renderer = capa.renderer()
    # Obtener los símbolos del renderer
    # Iterar sobre todas las categorías
    for category in renderer.categories():
        label = category.label()
        value = category.value()
        symbol = category.symbol()
        color = symbol.color().name()
        width = symbol.width()
        estilos.append({
            'value': value,
            'label': label,
            'color': color,
            'width': width
        })
    return estilos
